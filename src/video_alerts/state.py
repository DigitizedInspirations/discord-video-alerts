import base64
import copy
import hashlib
import json
import os
import re
import tempfile
from pathlib import Path
from uuid import uuid4
from .config import SOURCES
from .http import request
from .model import AlertError, Post, date, stamp, utcnow, video_url

STATUSES = {"baseline", "filtered", "expired", "disabled", "queued", "waiting_metadata", "sending", "uncertain", "sent", "failed", "deleted"}

def new_state():
    return {"schema_version": 1, "instance_id": str(uuid4()), "created_at": stamp(utcnow()), "sources": {}, "records": {}}

def validate_state(state):
    if not isinstance(state, dict) or set(state) != {"schema_version", "instance_id", "created_at", "sources", "records"} or type(state["schema_version"]) is not int or state["schema_version"] != 1:
        raise AlertError("Unsupported or corrupt state schema; manual recovery required")
    if not isinstance(state["instance_id"], str) or not state["instance_id"]:
        raise AlertError("Missing state identity")
    date(state["created_at"])
    if not isinstance(state["sources"], dict) or not isinstance(state["records"], dict):
        raise AlertError("Invalid state collections")
    for sid, source in state["sources"].items():
        if sid not in SOURCES or not isinstance(source, dict) or type(source.get("active")) is not bool or type(source.get("baseline_needed")) is not bool:
            raise AlertError("Invalid source state")
        for key in ("cutoff", "last_success", "last_attempt", "last_detected", "last_announcement"):
            if source.get(key) is not None:
                date(source[key])
        if type(source.get("consecutive_failures")) is not int or source["consecutive_failures"] < 0:
            raise AlertError("Invalid source health")
    for key, record in state["records"].items():
        try:
            post = Post(**record["post"])
            if key != post.key or post.source_id not in SOURCES or post.platform != SOURCES[post.source_id][0]:
                raise ValueError()
            pid, canonical = video_url(post.url, post.platform, SOURCES[post.source_id][1])
            if pid != post.post_id or canonical != post.url or record["status"] not in STATUSES:
                raise ValueError()
            if type(record["attempts"]) is not int or record["attempts"] < 0:
                raise ValueError()
            date(record["discovered_at"])
            if post.published_at is not None:
                date(post.published_at)
            if record.get("not_before") is not None:
                date(record["not_before"])
            mid = record.get("message_id")
            if mid is not None and (not isinstance(mid, str) or not re.fullmatch(r"[1-9]\d{16,19}", mid)):
                raise ValueError()
            if record["status"] in {"sent", "deleted"} and mid is None:
                raise ValueError()
        except (KeyError, TypeError, ValueError):
            raise AlertError("Inconsistent notification record; manual recovery required") from None

def encode(state):
    validate_state(state)
    payload = json.dumps(state, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return json.dumps({"sha256": hashlib.sha256(payload.encode()).hexdigest(), "state": state}, ensure_ascii=False, indent=2).encode("utf-8")

def decode(raw):
    try:
        envelope = json.loads(raw)
        if set(envelope) != {"sha256", "state"}:
            raise ValueError()
        state = envelope["state"]
        payload = json.dumps(state, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        if hashlib.sha256(payload.encode()).hexdigest() != envelope["sha256"]:
            raise ValueError()
        validate_state(state)
        return state
    except (ValueError, KeyError, TypeError, UnicodeError):
        raise AlertError("State checksum/schema failed; restore a validated checkpoint") from None

def atomic_write(path, raw):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(prefix=".checkpoint-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as file:
            file.write(raw)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)

class LocalStore:
    def __init__(self, path):
        self.path = Path(path)
        self.backup = self.path.with_suffix(".backup.json")

    def load(self):
        if not self.path.exists():
            raise AlertError("Missing state; explicit initialize or recovery required")
        return decode(self.path.read_bytes())

    def save(self, state):
        raw = encode(state)
        if self.path.exists():
            previous = self.path.read_bytes()
            decode(previous)
            atomic_write(self.backup, previous)
        atomic_write(self.path, raw)

    def initialize(self):
        if self.path.exists() or self.backup.exists():
            raise AlertError("State/checkpoint already exists; initialize refused")
        self.save(new_state())

    def restore(self, raw, confirm):
        if confirm != "RESTORE":
            raise AlertError("Restore requires RESTORE confirmation")
        restored = decode(raw)
        quarantine_sending(restored)
        if self.path.exists():
            atomic_write(self.path.with_suffix(".pre-restore.json"), self.path.read_bytes())
        atomic_write(self.path, encode(restored))

class MemoryStore:
    def __init__(self, state):
        self.state = copy.deepcopy(state)

    def load(self):
        return copy.deepcopy(self.state)

    def save(self, state):
        validate_state(state)
        self.state = copy.deepcopy(state)

def quarantine_sending(state):
    for rec in state["records"].values():
        if rec["status"] == "sending":
            rec["status"] = "uncertain"
            rec["error"] = "Interrupted after durable delivery intent; inspect Discord before recovery"

def merge_restore(current, checkpoint):
    """Preserve every newer tombstone/delivery and quarantine restored queue entries."""
    if current["instance_id"] != checkpoint["instance_id"]:
        raise AlertError("Restore belongs to a different state instance")
    result = copy.deepcopy(checkpoint)
    for key, rec in result["records"].items():
        if rec["status"] in {"queued", "sending", "waiting_metadata"}:
            rec["status"] = "uncertain"
            rec["error"] = "Restored queued entry needs operator review"
    result["records"].update(copy.deepcopy(current["records"]))
    result["sources"] = copy.deepcopy(current["sources"])
    quarantine_sending(result)
    validate_state(result)
    return result

def conservative_restore(checkpoint):
    result = copy.deepcopy(checkpoint)
    for source in result["sources"].values():
        source.update(active=False, baseline_needed=True, status="NOT VERIFIED", cutoff=stamp(utcnow()))
    for record in result["records"].values():
        if record["status"] in {"queued", "sending", "waiting_metadata"}:
            record.update(status="uncertain", error="Recovered from unavailable current state; inspect Discord before any retry")
    validate_state(result)
    return result

class GitHubStore:
    BRANCH = "notification-state"

    def __init__(self, repo, token, transport=request):
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo) or not token:
            raise AlertError("Missing/invalid GitHub state credentials")
        self.base = f"https://api.github.com/repos/{repo}"
        self.headers = {"Authorization": "Bearer " + token, "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
        self.transport = transport
        self.sha = None

    def api(self, method, path, data=None):
        body = None if data is None else json.dumps(data).encode()
        return self.transport(method, self.base + path, body, {**self.headers, "Content-Type": "application/json"})

    def load(self, ref=None):
        selected = ref or self.BRANCH
        if not re.fullmatch(r"notification-state|[a-f0-9]{40}", selected):
            raise AlertError("Restore ref must be a full commit SHA")
        res = self.api("GET", "/contents/state.json?ref=" + selected)
        if res.status != 200:
            raise AlertError(f"GitHub state unavailable: HTTP {res.status}; never auto-initialize")
        value = res.json()
        try:
            state = decode(base64.b64decode(value["content"]))
            if ref is None:
                self.sha = value["sha"]
            return state
        except (KeyError, ValueError, TypeError):
            raise AlertError("Invalid GitHub state response") from None

    def save(self, state):
        if not self.sha:
            raise AlertError("Load state before writing")
        data = {"message": "Notification checkpoint [skip ci]", "branch": self.BRANCH, "sha": self.sha, "content": base64.b64encode(encode(state)).decode()}
        res = self.api("PUT", "/contents/state.json", data)
        if res.status not in {200, 201}:
            raise AlertError(f"State checkpoint failed: HTTP {res.status}; stop all delivery")
        try:
            self.sha = res.json()["content"]["sha"]
        except (KeyError, TypeError):
            raise AlertError("State write acknowledgement invalid; stop") from None

    def initialize(self):
        exists = self.api("GET", "/git/ref/heads/" + self.BRANCH)
        if exists.status != 404:
            raise AlertError("State branch exists or cannot be checked; initialize refused")
        repo = self.api("GET", "")
        if repo.status != 200:
            raise AlertError("Cannot inspect repository")
        default = repo.json()["default_branch"]
        ref = self.api("GET", "/git/ref/heads/" + default)
        if ref.status != 200:
            raise AlertError("Cannot inspect default branch")
        created = self.api("POST", "/git/refs", {"ref": "refs/heads/" + self.BRANCH, "sha": ref.json()["object"]["sha"]})
        if created.status != 201:
            raise AlertError("Cannot create state branch")
        res = self.api("PUT", "/contents/state.json", {"message": "Initialize safe baseline [skip ci]", "branch": self.BRANCH, "content": base64.b64encode(encode(new_state())).decode()})
        if res.status != 201:
            raise AlertError("Branch created but state initialization failed; manual recovery required")

    def restore(self, ref, confirm):
        if confirm != "RESTORE" or not re.fullmatch(r"[a-f0-9]{40}", ref):
            raise AlertError("Cloud restore needs RESTORE and a full checkpoint commit SHA")
        branch = self.api("GET", "/git/ref/heads/" + self.BRANCH)
        if branch.status != 200:
            raise AlertError("State branch missing/inaccessible; reviewed Git branch recovery required")
        checkpoint = self.load(ref)
        current = self.api("GET", "/contents/state.json?ref=" + self.BRANCH)
        sha = None
        if current.status == 200:
            try:
                value = current.json()
                sha = value["sha"]
                raw = base64.b64decode(value["content"])
            except (AlertError, KeyError, ValueError, TypeError):
                raise AlertError("Cannot identify current state blob safely; recovery stopped") from None
            try:
                current_state = decode(raw)
            except AlertError:
                # Corrupt current data cannot supply delivery truth: never restore its queue as sendable.
                restored = conservative_restore(checkpoint)
            else:
                restored = merge_restore(current_state, checkpoint)
        elif current.status == 404:
            restored = conservative_restore(checkpoint)
        else:
            raise AlertError(f"Cloud state inaccessible: HTTP {current.status}; recovery stopped")
        data = {"message": "Explicit conservative state recovery [skip ci]", "branch": self.BRANCH, "content": base64.b64encode(encode(restored)).decode()}
        if sha:
            data["sha"] = sha
        response = self.api("PUT", "/contents/state.json", data)
        if response.status not in {200, 201}:
            raise AlertError(f"Recovery write failed: HTTP {response.status}; no delivery permitted")
        try:
            self.sha = response.json()["content"]["sha"]
        except (AlertError, KeyError, TypeError):
            raise AlertError("Recovery acknowledgement invalid; reload before monitoring") from None
        return restored

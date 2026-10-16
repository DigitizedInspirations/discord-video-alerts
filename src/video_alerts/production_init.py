"""One-time, creation-only publication of an empty production state.

No engine, adapters, baselining, delivery, update, recovery or retry operations.
"""
import hashlib
import json
import re
from urllib.parse import urlsplit
from uuid import UUID

import yaml

from .config import load_config
from .http import request
from .model import AlertError
from .state import GitHubStore, decode, encode

REPOSITORY = "DigitizedInspirations/discord-video-alerts"
BRANCH = "notification-state"
OPERATION = "initialize_empty_state"
CONFIRMATION = "INITIALIZE_EMPTY_NOTIFICATION_STATE_ONCE"
BASE = "https://api.github.com/repos/" + REPOSITORY
WORKFLOW = "initialize-state.yml"


def empty_state(state):
    decode(encode(state))
    if state["sources"] != {} or state["records"] != {}:
        raise AlertError("Initialization requires empty sources and records; no imports or baselines")
    try:
        identity = UUID(state["instance_id"])
        if identity.version != 4 or str(identity) != state["instance_id"]:
            raise ValueError()
    except (ValueError, TypeError, AttributeError):
        raise AlertError("Initialization requires a fresh UUID4 state identity") from None
    return state


def guard_environment(env, root):
    if any(name in env for name in ("DISCORD_WEBHOOK_URL", "YOUTUBE_API_KEY")):
        raise AlertError("State-only initialization must not receive service-secret variables")
    required = {"GITHUB_REPOSITORY": REPOSITORY, "GITHUB_REF": "refs/heads/main",
                "GITHUB_EVENT_NAME": "workflow_dispatch", "GITHUB_RUN_ATTEMPT": "1",
                "INIT_REPOSITORY": REPOSITORY, "INIT_BRANCH": BRANCH,
                "INIT_OPERATION": OPERATION, "INIT_CONFIRMATION": CONFIRMATION}
    if any(env.get(key) != value for key, value in required.items()):
        raise AlertError("Exact repository/main/operation/confirmation required; reruns forbidden")
    sha = env.get("INIT_EXPECTED_SHA", "")
    if not re.fullmatch(r"[a-f0-9]{40}", sha) or env.get("GITHUB_SHA") != sha:
        raise AlertError("Reviewed trusted-main SHA mismatch")
    if not env.get("GITHUB_RUN_ID", "").isdigit() or not env.get("GITHUB_TOKEN"):
        raise AlertError("Dedicated Actions run and token required")
    guard_local_settings(root)
    return sha


def guard_local_settings(root):
    try:
        config = load_config(root)
    except (AlertError, OSError, ValueError, TypeError, KeyError, AttributeError):
        raise AlertError("Local configuration preflight failed; invalid or unavailable settings") from None
    if type(config) is not dict or "master_enabled" not in config:
        raise AlertError("Local configuration preflight failed; invalid loader contract")
    if config["master_enabled"] is not False:
        raise AlertError("MASTER must remain OFF")
    if (root / ".github/workflows/scheduled.yml").exists():
        raise AlertError("Production schedule must remain disabled")
    for path in (root / ".github/workflows").glob("*.yml"):
        try:
            data = yaml.load(path.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
            if not isinstance(data, dict):
                raise ValueError()
        except (OSError, ValueError, yaml.YAMLError):
            raise AlertError("Local workflow preflight failed; invalid or unavailable YAML") from None
        trigger = data.get("on", {})
        if trigger == "schedule" or isinstance(trigger, (dict, list)) and "schedule" in trigger:
            raise AlertError("Active scheduling is forbidden during initialization")
    return config


class InitializationTransport:
    """Fence every actual request; publish one new ref last, never update it."""
    def __init__(self, expected_sha, run_id, state, *, transport=request, read_only=False,
                 tree_sha=None, commit_sha=None):
        if not re.fullmatch(r"[a-f0-9]{40}", expected_sha) or not str(run_id).isdigit():
            raise AlertError("Invalid reviewed SHA or run identity")
        if not read_only and (tree_sha is not None or commit_sha is not None):
            raise AlertError("Write transport must start without existing state objects")
        self.raw = encode(empty_state(state))
        self.blob_sha = hashlib.sha1(b"blob " + str(len(self.raw)).encode() + b"\0" + self.raw).hexdigest()
        self.expected_sha, self.run_id = expected_sha, str(run_id)
        self.message = "Initialize empty production state; run " + self.run_id + "; reviewed " + expected_sha + " [skip ci]"
        self.transport, self.read_only = transport, read_only
        self.tree_sha, self.commit_sha = tree_sha, commit_sha
        self.attempted = set()
        self.trace = []
        self.repo_ok = self.main_ok = self.branch_absent = self.file_absent = False
        self.published = False
        self.phase = "remote_preflight"

    def __call__(self, method, url, body=None, headers=None, **kwargs):
        parsed = urlsplit(url)
        if (parsed.scheme != "https" or parsed.netloc != "api.github.com" or
                parsed.fragment or not (url == BASE or url.startswith(BASE + "/"))):
            raise AlertError("Initialization repository/host fence rejected request")
        path = url[len(BASE):]
        reads = {"", "/git/ref/heads/main", "/git/ref/heads/" + BRANCH,
                 "/contents/state.json?ref=" + BRANCH}
        if self.tree_sha:
            reads.add("/git/trees/" + self.tree_sha)
        if self.commit_sha:
            reads.add("/git/commits/" + self.commit_sha)
        allowed = method == "GET" and body is None and path in reads
        if method == "POST" and not self.read_only and not parsed.query:
            try:
                data = json.loads(body)
            except (ValueError, TypeError):
                raise AlertError("Invalid initialization request body") from None
            if path == "/git/trees":
                expected = {"tree": [{"path": "state.json", "mode": "100644", "type": "blob", "content": self.raw.decode("utf-8")}]}
                allowed = (self.repo_ok and self.main_ok and self.branch_absent and self.file_absent
                           and data == expected and not self.tree_sha)
            elif path == "/git/commits":
                allowed = bool(self.tree_sha and not self.commit_sha and data == {
                    "message": self.message, "tree": self.tree_sha, "parents": []})
            elif path == "/git/refs":
                allowed = bool(self.repo_ok and self.main_ok and self.branch_absent and self.file_absent
                               and self.commit_sha and data == {"ref": "refs/heads/" + BRANCH, "sha": self.commit_sha})
            if path in self.attempted:
                allowed = False
        if not allowed:
            raise AlertError("Creation-only initialization API fence rejected request")
        if method == "POST":
            self.attempted.add(path)  # consume BEFORE I/O: no retry after uncertainty
        try:
            response = self.transport(method, url, body, headers or {}, **kwargs)
        except Exception:
            self.trace.append({"method": method, "path": path, "status": "unacknowledged"})
            raise AlertError("GitHub request unacknowledged; stop without retry or repair") from None
        self.trace.append({"method": method, "path": path, "status": response.status})
        if method == "GET":
            if path == "":
                value = response.json() if response.status == 200 else {}
                self.repo_ok = value.get("full_name") == REPOSITORY and value.get("default_branch") == "main"
            elif path == "/git/ref/heads/main":
                value = response.json() if response.status == 200 else {}
                self.main_ok = value.get("object", {}).get("sha") == self.expected_sha
            elif path == "/git/ref/heads/" + BRANCH:
                self.branch_absent = response.status == 404
            elif path == "/contents/state.json?ref=" + BRANCH:
                self.file_absent = response.status == 404
        return response

    def store(self, token):
        return GitHubStore(REPOSITORY, token, transport=self)

    def preflight(self, store):
        # Existing/inaccessible branch is a hard stop, even if its file is absent.
        store.api("GET", "")
        store.api("GET", "/git/ref/heads/main")
        if not self.repo_ok or not self.main_ok:
            raise AlertError("Remote repository/default/main does not match reviewed source")
        if store.api("GET", "/git/ref/heads/" + BRANCH).status != 404:
            raise AlertError("Production branch exists or is inaccessible; initialization refused")
        if store.api("GET", "/contents/state.json?ref=" + BRANCH).status != 404:
            raise AlertError("Production state exists or is inaccessible; initialization refused")

    def create(self, store, path, data):
        self.phase = {"/git/trees": "create_tree", "/git/commits": "create_commit", "/git/refs": "publish_branch"}.get(path, "creation_fence")
        response = store.api("POST", path, data)
        if response.status != 201:
            raise AlertError("GitHub creation refused; stop without retry, overwrite or repair")
        value = response.json()
        candidate = None
        if isinstance(value, dict):
            obj = value.get("object")
            candidate = value.get("sha") if path != "/git/refs" else obj.get("sha") if isinstance(obj, dict) else None
        if not isinstance(candidate, str) or not re.fullmatch(r"[a-f0-9]{40}", candidate):
            raise AlertError("GitHub creation acknowledgement is invalid; manual review required")
        return value


def validate_tree(value, guard):
    items = value.get("tree", [])
    if (value.get("sha") != guard.tree_sha or value.get("truncated") is not False or
            not isinstance(items, list) or len(items) != 1 or not isinstance(items[0], dict) or
            any(items[0].get(k) != x for k, x in {
                "path": "state.json", "mode": "100644", "type": "blob", "sha": guard.blob_sha}.items())):
        raise AlertError("State-only tree identity/content validation failed")


def verify_initialized(writer, token):
    # New fence AND new GitHubStore; no cached loaded state or write capability.
    reader = InitializationTransport(writer.expected_sha, writer.run_id, decode(writer.raw),
                                     transport=writer.transport, read_only=True,
                                     tree_sha=writer.tree_sha, commit_sha=writer.commit_sha)
    store = reader.store(token)
    store.api("GET", "")
    store.api("GET", "/git/ref/heads/main")
    if not reader.repo_ok or not reader.main_ok:
        raise AlertError("Trusted main changed during independent verification; manual review required")
    branch = store.api("GET", "/git/ref/heads/" + BRANCH)
    if branch.status != 200 or branch.json().get("object", {}).get("sha") != writer.commit_sha:
        raise AlertError("Published production branch commit mismatch")
    actual = empty_state(store.load())  # real schema and checksum validation
    if actual != decode(writer.raw) or store.sha != writer.blob_sha:
        raise AlertError("Fresh GitHubStore state identity/bytes mismatch")
    commit = store.api("GET", "/git/commits/" + writer.commit_sha)
    value = commit.json() if commit.status == 200 else {}
    if value.get("sha") != writer.commit_sha or value.get("parents") != [] or value.get("tree", {}).get("sha") != writer.tree_sha:
        raise AlertError("Production commit is not the expected independent root commit")
    tree = store.api("GET", "/git/trees/" + writer.tree_sha)
    if tree.status != 200:
        raise AlertError("Production state-only tree is unavailable")
    validate_tree(tree.json(), writer)
    final = store.api("GET", "/git/ref/heads/" + BRANCH)
    if final.status != 200 or final.json().get("object", {}).get("sha") != writer.commit_sha:
        raise AlertError("Production branch changed during independent verification")
    return actual, reader.trace


def initialize(writer, token):
    store = writer.store(token)
    writer.preflight(store)
    value = writer.create(store, "/git/trees", {"tree": [{"path": "state.json", "mode": "100644", "type": "blob", "content": writer.raw.decode("utf-8")}]})
    writer.tree_sha = value["sha"]
    validate_tree(value, writer)
    value = writer.create(store, "/git/commits", {"message": writer.message, "tree": writer.tree_sha, "parents": []})
    writer.commit_sha = value["sha"]
    if value.get("parents") != [] or value.get("tree", {}).get("sha") != writer.tree_sha:
        raise AlertError("Root commit acknowledgement is invalid; do not publish")
    # Recheck trusted main/absence after preparing immutable objects; final POST
    # creates a new ref atomically. Existing refs cause rejection, never update.
    writer.repo_ok = writer.main_ok = writer.branch_absent = writer.file_absent = False
    writer.phase = "remote_prepublication_preflight"
    writer.preflight(store)
    value = writer.create(store, "/git/refs", {"ref": "refs/heads/" + BRANCH, "sha": writer.commit_sha})
    if value.get("ref") != "refs/heads/" + BRANCH or value.get("object", {}).get("sha") != writer.commit_sha:
        raise AlertError("Branch publication acknowledgement is invalid; manual review required")
    writer.published = True
    writer.phase = "independent_verification"
    actual, trace = verify_initialized(writer, token)
    return {"mode": "PRODUCTION_EMPTY_STATE_INITIALIZATION", "repository": REPOSITORY,
            "branch": BRANCH, "source_sha": writer.expected_sha, "run_id": writer.run_id,
            "initial_branch_absent": True, "initial_file_absent": True,
            "schema_version": actual["schema_version"], "instance_id": actual["instance_id"],
            "created_at": actual["created_at"], "source_count": 0, "record_count": 0,
            "state_hash": json.loads(writer.raw)["sha256"], "state_blob_sha": writer.blob_sha,
            "tree_sha": writer.tree_sha, "commit_sha": writer.commit_sha,
            "root_parents": [], "tree_paths": ["state.json"], "creation_posts": len(writer.attempted),
            "fresh_store_verified": True, "canary_imported": False,
            "discord_requests": 0, "youtube_requests": 0, "master_enabled": False,
            "active_schedule": False, "passed": 10, "failed": 0,
            "checks": ["exact repository/reviewed main", "branch and file absent before creation",
                       "one empty schema/checksum state", "state-only tree without canary/source history",
                       "root commit with no parents", "new branch atomically published last",
                       "fresh read-only GitHubStore identity/checksum/blob match", "branch stable at exact commit",
                       "no service requests/imports/baselines/queue", "MASTER/schedule remain OFF"],
            "phase": "complete", "api_trace": writer.trace + trace}


def inspect_failure(writer, token):
    """Bounded read-only diagnosis after any creation attempt; never repair."""
    result = {"status": "manual_review_required", "tree_sha": writer.tree_sha,
              "commit_sha": writer.commit_sha, "write_attempts": sorted(writer.attempted)}
    reader = InitializationTransport(writer.expected_sha, writer.run_id, decode(writer.raw),
                                     transport=writer.transport, read_only=True)
    store = reader.store(token)
    try:
        branch = store.api("GET", "/git/ref/heads/" + BRANCH)
        result["branch_http"] = branch.status
        if branch.status == 200:
            result["branch_commit"] = branch.json().get("object", {}).get("sha")
            state = empty_state(store.load())
            result.update(empty_state_checksum_valid=True, instance_id=state["instance_id"],
                          matches_attempted_state=state == decode(writer.raw), state_blob_sha=store.sha)
    except (AlertError, KeyError, TypeError, ValueError, AttributeError):
        result["inspection"] = "unavailable_or_invalid; no automatic repair"
    result["api_trace"] = reader.trace
    return result

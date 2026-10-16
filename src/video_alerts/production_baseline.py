"""One approved baseline transaction; never invokes the monitoring/delivery engine."""
import base64
import copy
import hashlib
import json
import re
from datetime import timedelta
from urllib.parse import urlsplit

import yaml

from .config import SOURCES, load_config
from .http import request
from .model import AlertError, Post, date, stamp, utcnow, video_url
from .state import GitHubStore, decode, encode

REPOSITORY = "DigitizedInspirations/discord-video-alerts"
BRANCH = "notification-state"
WORKFLOW = "baseline-state.yml"
AUTHORIZATION = "four-source-baseline-87757f44"
CONFIRMATION = "BASELINE_FOUR_SOURCES_ONCE_NO_DISCORD"
INITIAL_COMMIT = "dffc5833c9c69d69acde3180e1b760255d116250"
INITIAL_BLOB = "6cb68f2eefbadf5ffc2d8efe611eaed29bffc055"
INITIAL_HASH = "ab2350425c1426621905f314f12ea723eb33ebb20fb816bf7bcd68e8e7a48b1c"
INITIAL_STATE = {"schema_version": 1, "instance_id": "e0dae2af-a0a5-424d-aa2e-216ca84c287a",
                 "created_at": "2026-10-16T19:42:22.688305+00:00", "sources": {}, "records": {}}
BASE = "https://api.github.com/repos/" + REPOSITORY
HISTORY = "/actions/workflows/" + WORKFLOW + "/runs?event=workflow_dispatch&per_page=100"


def blob_sha(raw):
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def checksum(state):
    return json.loads(encode(state))["sha256"]


def settings(root):
    cfg = load_config(root)  # real dict contract; no permissive default
    if type(cfg) is not dict or cfg.get("master_enabled") is not False:
        raise AlertError("Baseline requires validated MASTER strictly OFF")
    if (root / ".github/workflows/scheduled.yml").exists():
        raise AlertError("Production schedule must remain disabled")
    for path in (root / ".github/workflows").iterdir():
        if path.suffix not in {".yml", ".yaml"}:
            continue
        data = yaml.load(path.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
        if not isinstance(data, dict):
            raise AlertError("Invalid workflow configuration")
        trigger = data.get("on", {})
        if trigger == "schedule" or isinstance(trigger, (dict, list)) and "schedule" in trigger:
            raise AlertError("Active scheduling is forbidden")
    if set(cfg["channels"]) != set(SOURCES):
        raise AlertError("Exactly four approved sources required")
    return cfg


def guard(env, root, phase):
    if "DISCORD_WEBHOOK_URL" in env:
        raise AlertError("Baseline must never receive a Discord secret")
    expected = {"GITHUB_REPOSITORY": REPOSITORY, "GITHUB_REF": "refs/heads/main",
                "GITHUB_EVENT_NAME": "workflow_dispatch", "GITHUB_RUN_ATTEMPT": "1",
                "BASELINE_REPOSITORY": REPOSITORY, "BASELINE_BRANCH": BRANCH,
                "BASELINE_CONFIRMATION": CONFIRMATION, "BASELINE_AUTHORIZATION": AUTHORIZATION}
    if any(env.get(k) != v for k, v in expected.items()):
        raise AlertError("Exact baseline repository/main/branch/authorization/confirmation required; no reruns")
    sha = env.get("BASELINE_EXPECTED_SHA", "")
    if not re.fullmatch(r"[a-f0-9]{40}", sha) or env.get("GITHUB_SHA") != sha:
        raise AlertError("Reviewed main SHA mismatch")
    if not env.get("GITHUB_RUN_ID", "").isdigit():
        raise AlertError("Dedicated workflow run identity required")
    if phase == "metadata":
        if "GITHUB_TOKEN" in env or not env.get("YOUTUBE_API_KEY", "").strip():
            raise AlertError("Metadata step requires only the YouTube key; no GitHub write token")
    elif phase in {"preflight", "write"}:
        if "YOUTUBE_API_KEY" in env or not env.get("GITHUB_TOKEN"):
            raise AlertError("State step requires GitHub token only; no service secrets")
    else:
        raise AlertError("Unknown baseline phase")
    return settings(root)


def validate_post(post, sid, cfg, at):
    ch = cfg["channels"][sid]
    if not isinstance(post, Post) or post.source_id != sid or post.platform != ch["platform"]:
        raise AlertError("Source/platform identity mismatch")
    pid, canonical = video_url(post.url, ch["platform"], ch["account"])
    if pid != post.post_id or canonical != post.url:
        raise AlertError("Noncanonical post identity")
    owner = ch["channel_id"] if ch["platform"] == "youtube" else ch["account"]
    verified = post.owner_id == owner if ch["platform"] == "youtube" else (
        isinstance(post.owner_id, str) and post.owner_id.casefold() == owner.casefold())
    if not verified or post.public is not True:
        raise AlertError("Post ownership/public availability unverified")
    if post.published_at is None or date(post.published_at) > at:
        raise AlertError("Missing, invalid or future publication timestamp")
    if post.kind not in {"unknown", "regular", "short", "livestream"} or type(post.premiere) not in {bool, type(None)}:
        raise AlertError("Invalid classification; unknown subtype/premiere must stay unknown")


def build_proposal(cfg, selected, run_id, sha, report, clock=utcnow):
    """All four windows and every returned video must verify before a candidate exists."""
    at = clock()
    timestamp = stamp(at)
    state = copy.deepcopy(INITIAL_STATE)
    report.update(baseline_at=timestamp, sources={sid: {"status": "NOT_TESTED", "baseline_records": 0} for sid in SOURCES},
                  finite_windows_not_complete_history=True, api_requests=0, estimated_quota_units=0)
    listings = {}
    for sid in SOURCES:
        result = report["sources"][sid]
        try:
            posts = selected[sid].discover(sid)
            if type(posts) is not list or not 1 <= len(posts) <= 30:
                raise AlertError("Unavailable, empty, incomplete or oversized discovery window")
            keys = set()
            for post in posts:
                if not isinstance(post, Post) or post.source_id != sid or post.platform != cfg["channels"][sid]["platform"]:
                    raise AlertError("Discovery source identity mismatch")
                pid, url = video_url(post.url, post.platform, cfg["channels"][sid]["account"])
                if pid != post.post_id or url != post.url or post.key in keys:
                    raise AlertError("Invalid or duplicate discovery identity")
                keys.add(post.key)
            listings[sid] = posts
            result.update(status="DISCOVERED", discovered=len(posts),
                          discovery_method=getattr(selected[sid], "discovery_method", "public_profile_extractor"))
        except AlertError as exc:
            result.update(status="FAILED", reason=str(exc))
            raise AlertError(sid + ": " + str(exc)) from None
    # Shared API batches both YouTube accounts (<=60 ids, <=2 normal quota units).
    api = selected["youtube_dayz"].api
    api.prefetch([p.post_id for sid, posts in listings.items() if sid.startswith("youtube_") for p in posts])
    for sid, posts in listings.items():
        result = report["sources"][sid]
        try:
            for post in posts:
                enriched = selected[sid].enrich(post)
                if enriched.key != post.key:
                    raise AlertError("Enriched post identity mismatch")
                validate_post(enriched, sid, cfg, at)
                state["records"][enriched.key] = {
                    "post": enriched.dict(), "status": "baseline", "reason": "Approved finite historical baseline; never backfill",
                    "discovered_at": timestamp, "attempts": 0, "message_id": None, "not_before": None, "error": None}
            state["sources"][sid] = {"active": False, "baseline_needed": True, "cutoff": timestamp,
                "last_attempt": timestamp, "last_success": timestamp, "last_detected": None,
                "last_announcement": None, "consecutive_failures": 0, "status": "DISABLED", "error": None,
                "alerted_error": None, "metadata_verified": True}
            result.update(status="VERIFIED", baseline_records=len(posts),
                          owner_id=state["records"][posts[0].key]["post"]["owner_id"],
                          publication_min=min(state["records"][p.key]["post"]["published_at"] for p in posts),
                          publication_max=max(state["records"][p.key]["post"]["published_at"] for p in posts))
        except AlertError as exc:
            result.update(status="FAILED", reason=str(exc), baseline_records=0)
            raise AlertError(sid + ": " + str(exc)) from None
        finally:
            report.update(api_requests=api.requests, estimated_quota_units=api.requests)
    proposal = {"authorization": AUTHORIZATION, "run_id": str(run_id), "reviewed_sha": sha,
                "baseline_at": timestamp, "state": state, "report": copy.deepcopy(report)}
    validate_proposal(proposal, cfg, run_id, sha, clock())
    return proposal


def validate_proposal(proposal, cfg, run_id, sha, now):
    if set(proposal) != {"authorization", "run_id", "reviewed_sha", "baseline_at", "state", "report"} or (
        proposal["authorization"] != AUTHORIZATION or proposal["run_id"] != str(run_id) or proposal["reviewed_sha"] != sha):
        raise AlertError("Candidate authorization/run/source mismatch")
    at = date(proposal["baseline_at"])
    if not timedelta(0) <= now - at <= timedelta(minutes=30):
        raise AlertError("Stale or future baseline candidate")
    state = decode(encode(proposal["state"]))
    if any(state[k] != INITIAL_STATE[k] for k in ("schema_version", "instance_id", "created_at")) or set(state["sources"]) != set(SOURCES):
        raise AlertError("Baseline must preserve exact initialized identity and all four sources")
    counts = {sid: 0 for sid in SOURCES}
    for rec in state["records"].values():
        if set(rec) != {"post", "status", "reason", "discovered_at", "attempts", "message_id", "not_before", "error"} or (
            rec["status"] != "baseline" or rec["attempts"] != 0 or any(rec[k] is not None for k in ("message_id", "not_before", "error"))
            or rec["discovered_at"] != proposal["baseline_at"]):
            raise AlertError("Only historical baseline records allowed; no delivery state/history")
        post = Post(**rec["post"])
        validate_post(post, post.source_id, cfg, at)
        counts[post.source_id] += 1
    for sid, source in state["sources"].items():
        expected = {"active": False, "baseline_needed": True, "cutoff": proposal["baseline_at"],
            "last_attempt": proposal["baseline_at"], "last_success": proposal["baseline_at"], "last_detected": None,
            "last_announcement": None, "consecutive_failures": 0, "status": "DISABLED", "error": None,
            "alerted_error": None, "metadata_verified": True}
        if source != expected or not 1 <= counts[sid] <= 30:
            raise AlertError("Inactive/resume baseline invariant or bounded source count failed")
        summary = proposal["report"]["sources"][sid]
        if summary["status"] != "VERIFIED" or summary["baseline_records"] != counts[sid]:
            raise AlertError("Candidate source evidence mismatch")
    return state


class BaselineTransport:
    """Exact repo/branch/path/body fence. No initialization, recovery or write retries."""
    def __init__(self, sha, run_id, *, transport=request, proposal=None):
        if not re.fullmatch(r"[a-f0-9]{40}", sha) or not str(run_id).isdigit():
            raise AlertError("Invalid reviewed SHA/run identity")
        self.sha, self.run_id, self.transport = sha, str(run_id), transport
        self.proposal = proposal
        self.attempts = 0
        self.commit = None
        self.trace = []
        self.ready = False

    def store(self, token):
        return GitHubStore(REPOSITORY, token, transport=self)

    def __call__(self, method, url, body=None, headers=None):
        u = urlsplit(url)
        if u.scheme != "https" or u.netloc != "api.github.com" or u.fragment or not url.startswith(BASE):
            raise AlertError("Baseline GitHub request host/repository fence")
        path = url[len(BASE):]
        reads = {"", "/git/ref/heads/main", "/git/ref/heads/" + BRANCH,
                 "/contents/state.json?ref=" + BRANCH, HISTORY, "/actions/runs/" + self.run_id}
        if self.commit:
            reads.add("/git/commits/" + self.commit)
        if hasattr(self, "tree"):
            reads.add("/git/trees/" + self.tree)
        if method == "GET":
            if path not in reads or body is not None:
                raise AlertError("Unapproved baseline read path")
        elif method == "PUT":
            if path != "/contents/state.json" or not self.ready or self.attempts or self.proposal is None:
                raise AlertError("Unapproved or repeated production state write")
            expected = {"message": "Notification checkpoint [skip ci]", "branch": BRANCH, "sha": INITIAL_BLOB,
                        "content": base64.b64encode(encode(self.proposal["state"])).decode()}
            if json.loads(body) != expected:
                raise AlertError("Production state payload/branch/SHA fence")
            self.attempts += 1  # consumed BEFORE network, including lost acknowledgements
        else:
            raise AlertError("Creation/recovery/unrelated state request forbidden")
        self.trace.append({"method": method, "path": path, "status": None})
        response = self.transport(method, url, body, headers)
        self.trace[-1]["status"] = response.status
        if method == "GET" and path == "/contents/state.json?ref=" + BRANCH and response.status == 200:
            value = response.json()
            try:
                raw = base64.b64decode(value["content"])
                if value["sha"] != blob_sha(raw):
                    raise ValueError()
            except (ValueError, TypeError, KeyError):
                raise AlertError("GitHub Contents blob identity mismatch") from None
        if method == "PUT":
            if response.status != 200:
                raise AlertError("Baseline update failed or conflicted: HTTP " + str(response.status) + "; no retry")
            value = response.json()
            expected_blob = blob_sha(encode(self.proposal["state"]))
            commit = value.get("commit", {}).get("sha", "")
            if value.get("content", {}).get("sha") != expected_blob or not re.fullmatch(r"[a-f0-9]{40}", commit):
                raise AlertError("Ambiguous baseline acknowledgement; stop without retry")
            self.commit = commit
        return response


def preflight(fence, token):
    store = fence.store(token)
    repo = store.api("GET", "")
    if repo.status != 200 or repo.json().get("full_name") != REPOSITORY or repo.json().get("default_branch") != "main":
        raise AlertError("Exact trusted repository/default branch required")
    main = store.api("GET", "/git/ref/heads/main")
    if main.status != 200 or main.json().get("object", {}).get("sha") != fence.sha:
        raise AlertError("Reviewed main changed")
    runs = store.api("GET", HISTORY)
    run = store.api("GET", "/actions/runs/" + fence.run_id)
    history = runs.json() if runs.status == 200 else {}
    current = run.json() if run.status == 200 else {}
    if history.get("total_count") != 1 or [r.get("id") for r in history.get("workflow_runs", [])] != [int(fence.run_id)] or any(
        current.get(k) != v for k, v in {"id": int(fence.run_id), "head_sha": fence.sha, "head_branch": "main",
        "event": "workflow_dispatch", "run_attempt": 1, "path": ".github/workflows/" + WORKFLOW}.items()):
        raise AlertError("Single baseline authorization consumed or untrusted workflow run")
    initial = load_initial(store)
    fence.ready = True
    return store, initial


def load_initial(store):
    branch = store.api("GET", "/git/ref/heads/" + BRANCH)
    if branch.status != 200 or branch.json().get("object", {}).get("sha") != INITIAL_COMMIT:
        raise AlertError("Production branch missing, changed or already baselined; never repair")
    state = store.load()
    if state != INITIAL_STATE or store.sha != INITIAL_BLOB or checksum(state) != INITIAL_HASH:
        raise AlertError("Production identity/content/checksum/blob differs from approved empty initialization")
    branch = store.api("GET", "/git/ref/heads/" + BRANCH)
    if branch.status != 200 or branch.json().get("object", {}).get("sha") != INITIAL_COMMIT:
        raise AlertError("Concurrent production modification during preflight")
    return state


def write_once(fence, token, cfg, clock=utcnow):
    candidate = validate_proposal(fence.proposal, cfg, fence.run_id, fence.sha, clock())
    store, _ = preflight(fence, token)
    store.save(candidate)  # exactly one optimistic-SHA Contents API update; no retries
    # Independent read-only fence and NEW GitHubStore, with no candidate/write authority.
    reader = BaselineTransport(fence.sha, fence.run_id, transport=fence.transport)
    reader.commit = fence.commit
    fresh = reader.store(token)
    branch = fresh.api("GET", "/git/ref/heads/" + BRANCH)
    actual = fresh.load()
    if branch.status != 200 or branch.json().get("object", {}).get("sha") != fence.commit or actual != candidate or fresh.sha != blob_sha(encode(candidate)):
        raise AlertError("Independent baseline state/commit/blob mismatch; manual review required")
    value = fresh.api("GET", "/git/commits/" + fence.commit)
    commit = value.json() if value.status == 200 else {}
    if commit.get("sha") != fence.commit or [p.get("sha") for p in commit.get("parents", [])] != [INITIAL_COMMIT]:
        raise AlertError("Baseline commit ancestry mismatch")
    reader.tree = commit.get("tree", {}).get("sha", "")
    if not re.fullmatch(r"[a-f0-9]{40}", reader.tree):
        raise AlertError("Baseline tree identity unavailable")
    response = fresh.api("GET", "/git/trees/" + reader.tree)
    tree = response.json() if response.status == 200 else {}
    entries = tree.get("tree", [])
    if tree.get("sha") != reader.tree or tree.get("truncated") is not False or len(entries) != 1 or any(
        entries[0].get(k) != v for k, v in {"path": "state.json", "mode": "100644", "type": "blob", "sha": fresh.sha}.items()):
        raise AlertError("Production tree contains unexpected data")
    final = fresh.api("GET", "/git/ref/heads/" + BRANCH)
    if final.status != 200 or final.json().get("object", {}).get("sha") != fence.commit:
        raise AlertError("Production branch changed during independent verification")
    main = fresh.api("GET", "/git/ref/heads/main")
    if main.status != 200 or main.json().get("object", {}).get("sha") != fence.sha:
        raise AlertError("Trusted main changed during independent verification")
    return {"production_commit": fence.commit, "before_commit": INITIAL_COMMIT, "before_sha256": INITIAL_HASH,
            "before_blob": INITIAL_BLOB, "after_sha256": checksum(actual), "after_blob": fresh.sha,
            "instance_id": actual["instance_id"], "created_at": actual["created_at"], "schema_version": 1,
            "production_state_writes": fence.attempts, "independent_verification": "PASSED",
            "api_trace": fence.trace + reader.trace, "queued": 0, "sent": 0, "master_enabled": False,
            "schedule_enabled": False, "all_sources_active": False}

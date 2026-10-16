"""Two manual fresh-runner phases; real state API writes fenced to one synthetic branch."""
import base64
import copy
import hashlib
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"src"))
from video_alerts.canary import APPROVED_BRANCH, MARKER, REPOSITORY, CanaryTransport
from video_alerts.config import load_config
from video_alerts.model import AlertError, Post
from video_alerts.state import decode, encode, new_state, quarantine_sending

STAMP = "2000-01-01T00:00:00+00:00"


def fingerprint(state):
    return json.loads(encode(state))["sha256"]


def record(pid, status):
    post = Post("youtube", "youtube_dayz", pid, "https://www.youtube.com/watch?v="+pid,
                "SYNTHETIC CANARY - NEVER SEND", "SYNTHETIC", STAMP, "regular", True, False, "SYNTHETIC")
    return post.key, {"post": post.dict(), "status": status, "reason": "Synthetic isolated fixture",
                      "discovered_at": STAMP, "attempts": 0,
                      "message_id": "111111111111111111" if status in {"sent", "deleted"} else None,
                      "not_before": None, "error": None}


def put_marker(store, value, sha=None):
    data = {"branch": APPROVED_BRANCH, "message": "Synthetic phase checkpoint", "content": base64.b64encode(json.dumps(value, sort_keys=True).encode()).decode()}
    if sha:
        data["sha"] = sha
    response = store.api("PUT", "/contents/"+MARKER, data)
    if response.status not in {200, 201}:
        raise AlertError("Canary marker write failed")
    return response.json()["content"]["sha"]


def get_marker(store):
    response = store.api("GET", "/contents/"+MARKER+"?ref="+APPROVED_BRANCH)
    if response.status != 200:
        raise AlertError("Canary seed checkpoint unavailable; never initialize on verify")
    value = response.json()
    try:
        return json.loads(base64.b64decode(value["content"])), value["sha"]
    except (ValueError, KeyError, TypeError):
        raise AlertError("Canary marker invalid") from None


def guard_environment():
    if any(name in os.environ for name in ("DISCORD_WEBHOOK_URL", "YOUTUBE_API_KEY")):
        raise AlertError("Canary must never receive service-secret environment variables")
    if os.environ.get("CANARY_BRANCH") != APPROVED_BRANCH:
        raise AlertError("Canary target does not match exact approved branch")
    if os.environ.get("GITHUB_REPOSITORY") != REPOSITORY or os.environ.get("GITHUB_REF") != "refs/heads/main":
        raise AlertError("Canary requires the approved repository and trusted main")
    expected = os.environ.get("CANARY_EXPECTED_SHA", "")
    if not re.fullmatch(r"[a-f0-9]{40}", expected) or expected != os.environ.get("GITHUB_SHA"):
        raise AlertError("Canary reviewed code SHA mismatch")
    if os.environ.get("GITHUB_RUN_ATTEMPT") != "1" or not os.environ.get("GITHUB_RUN_ID", "").isdigit():
        raise AlertError("Canary automatic reruns are forbidden")
    cfg = load_config(ROOT)
    if cfg["master_enabled"] or (ROOT/".github/workflows/scheduled.yml").exists():
        raise AlertError("Canary requires MASTER OFF and scheduling disabled")
    if not os.environ.get("GITHUB_TOKEN"):
        raise AlertError("Dedicated canary token missing")


def execute(phase, transport, token, run_id, source_sha, seed_run_id=""):
    store = transport.store(token)
    checks = []
    result = {"mode": "ISOLATED_GITHUB_DURABLE_CANARY", "branch": APPROVED_BRANCH,
              "phase": phase, "run_id": run_id, "source_sha": source_sha,
              "discord_requests": 0, "youtube_requests": 0, "production_state_requests": 0}
    if phase == "seed":
        store.initialize()
        state = store.load()
        checks.append("real canary branch and checksum state initialization")
        state["sources"]["youtube_dayz"] = {"active": True, "baseline_needed": False, "cutoff": STAMP,
            "last_success": None, "last_attempt": None, "last_detected": None, "last_announcement": None,
            "consecutive_failures": 0, "status": "SYNTHETIC", "error": None, "metadata_verified": True}
        for pid, status in (("C4N4RY00001", "sent"), ("C4N4RY00002", "deleted"), ("C4N4RY00003", "queued")):
            key, value = record(pid, status)
            state["records"][key] = value
        store.save(state)
        checkpoint = transport.last_commit
        reread = transport.store(token).load()
        if reread != state:
            raise AlertError("Canary read-after-write mismatch")
        checks.append("real Contents API synthetic write and exact retrieval")
        marker = {"branch": APPROVED_BRANCH, "repository": REPOSITORY, "phase": "seed_complete",
                  "seed_run_id": run_id, "source_sha": source_sha, "instance_id": state["instance_id"],
                  "state_hash": fingerprint(state), "state_blob_sha": store.sha, "checkpoint_commit": checkpoint}
        put_marker(store, marker)
        checks.append("recoverable commit checkpoint and cross-run fingerprint stored")
        result.update(marker)
        result["phase"] = "seed"
    elif phase == "verify":
        marker, marker_sha = get_marker(store)
        if marker.get("branch") != APPROVED_BRANCH or marker.get("repository") != REPOSITORY or marker.get("phase") != "seed_complete" or marker.get("seed_run_id") != seed_run_id or seed_run_id == run_id or marker.get("source_sha") != source_sha:
            raise AlertError("Canary seed provenance/phase mismatch; no writes allowed")
        original = store.load()
        if fingerprint(original) != marker["state_hash"] or store.sha != marker["state_blob_sha"] or original["instance_id"] != marker["instance_id"]:
            raise AlertError("Cross-run canary state/hash mismatch; no writes allowed")
        checks.append("exact state/blob/hash durability from independent completed run")
        for pid, status in (("C4N4RY00001", "sent"), ("C4N4RY00002", "deleted")):
            if original["records"][record(pid, status)[0]]["status"] != status:
                raise AlertError("Synthetic dedup/tombstone changed across runs")
        checks.append("synthetic dedup records and tombstones survive fresh runner")
        first_checkpoint = marker["checkpoint_commit"]
        transport.approve_checkpoint(store, first_checkpoint)
        stale = transport.store(token)
        stale.load()
        updated = copy.deepcopy(original)
        key, value = record("C4N4RY00004", "sent")
        updated["records"][key] = value
        store.save(updated)
        try:
            stale.save(original)
        except AlertError as exc:
            if not any(code in str(exc) for code in ("409", "422")):
                raise
        else:
            raise AlertError("Optimistic conflict was incorrectly accepted")
        if transport.store(token).load() != updated:
            raise AlertError("Conflict overwrote winner state")
        checks.append("real optimistic stale-SHA conflict rejects overwrite")
        ambiguous = transport.store(token)
        ambiguous.load()
        intended = copy.deepcopy(updated)
        key, value = record("C4N4RY00005", "sending")
        intended["records"][key] = value
        def lost_ack(method, url, body=None, headers=None, **kwargs):
            response = transport(method, url, body, headers, **kwargs)
            if method == "PUT" and "/contents/state.json" in url and response.status in {200, 201}:
                raise AlertError("Injected lost acknowledgement after real canary write")
            return response
        ambiguous.transport = lost_ack
        try:
            ambiguous.save(intended)
        except AlertError:
            pass
        else:
            raise AlertError("Lost-ack injection failed")
        reconciled_store = transport.store(token)
        reconciled = reconciled_store.load()
        if reconciled != intended:
            raise AlertError("Ambiguous write could not be reconciled")
        quarantine_sending(reconciled)
        if reconciled["records"][key]["status"] != "uncertain":
            raise AlertError("Interrupted intent was not quarantined")
        reconciled_store.save(reconciled)
        checks.append("lost acknowledgement after actual write reconciled without resend; intent quarantined")
        recovery_checkpoint = transport.last_commit
        transport.approve_checkpoint(store, recovery_checkpoint)
        marker.update(phase="verify_in_progress", recovery_checkpoint=recovery_checkpoint,
                      recovery_state_hash=fingerprint(reconciled))
        marker_sha = put_marker(store, marker, marker_sha)
        checks.append("recoverable canary checkpoint preserved before destructive fault")
        current = transport.store(token)
        current.load()
        corrupt = json.loads(encode(reconciled))
        corrupt["sha256"] = "0"*64
        response = current.api("PUT", "/contents/state.json", {"branch": APPROVED_BRANCH, "sha": current.sha,
            "message": "Synthetic checksum corruption fault", "content": base64.b64encode(json.dumps(corrupt).encode()).decode()})
        if response.status not in {200, 201}:
            raise AlertError("Canary corruption injection failed")
        damaged = transport.store(token)
        try:
            damaged.load()
        except AlertError as exc:
            if "checksum" not in str(exc):
                raise
        else:
            raise AlertError("Corrupt canary checksum accepted")
        checks.append("actual corrupt GitHub state detected and never auto-initialized")
        count_before = len(transport.trace)
        try:
            damaged.save(reconciled)
        except AlertError:
            pass
        else:
            raise AlertError("Unloaded corrupt state allowed overwrite")
        if len(transport.trace) != count_before:
            raise AlertError("Corrupt save attempted an API write")
        checks.append("failed-load write blocked before network")
        restored = damaged.restore(recovery_checkpoint, "RESTORE")
        if restored["records"][record("C4N4RY00003", "queued")[0]]["status"] != "uncertain" or restored["sources"]["youtube_dayz"]["active"] or not restored["sources"]["youtube_dayz"]["baseline_needed"]:
            raise AlertError("Corrupt-state recovery did not fail closed")
        checks.append("real checkpoint recovery quarantines queue and requires safe baseline")
        merged = damaged.restore(first_checkpoint, "RESTORE")
        for pid, status in (("C4N4RY00001", "sent"), ("C4N4RY00002", "deleted"), ("C4N4RY00004", "sent"), ("C4N4RY00005", "uncertain")):
            if merged["records"][record(pid, status)[0]]["status"] != status:
                raise AlertError("Conservative restore lost dedup/delivery truth")
        if transport.store(token).load() != merged:
            raise AlertError("Final recovered canary state did not persist")
        checks.append("older-checkpoint merge preserves newer dedup/tombstones and final retrieval")
        final_state_commit = transport.last_commit
        marker.update(phase="verify_complete", verify_run_id=run_id, final_state_hash=fingerprint(merged),
                      final_state_blob_sha=damaged.sha, final_state_commit=final_state_commit)
        put_marker(damaged, marker, marker_sha)
        result.update(marker)
        result["phase"] = "verify"
        result["run_id"] = run_id
    else:
        raise AlertError("Unknown canary phase")
    checks.append("all actual API operations fenced to exact disposable branch; no production requests")
    result.update(checks=checks, passed=len(checks), failed=0, api_trace=transport.trace,
                  commits=transport.commits, branch_head_commit=transport.last_commit,
                  branch_retained=True, synthetic_only=True)
    return result


def main():
    guard_environment()
    phase = os.environ.get("CANARY_PHASE")
    if phase not in {"seed", "verify"}:
        raise AlertError("Unknown canary phase")
    transport = CanaryTransport(os.environ["CANARY_BRANCH"], initialize=phase == "seed")
    report = execute(phase, transport, os.environ["GITHUB_TOKEN"], os.environ["GITHUB_RUN_ID"],
                     os.environ["GITHUB_SHA"], os.environ.get("CANARY_SEED_RUN_ID", ""))
    target = ROOT/".validation"/("durable-canary-"+phase+".json")
    target.parent.mkdir(exist_ok=True)
    target.write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    print("DVA_REPORT "+json.dumps(report))


if __name__ == "__main__":
    try:
        main()
    except AlertError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
    except Exception:
        print("Canary failed; sensitive details withheld. Preserve branch/checkpoint for review.", file=sys.stderr)
        raise SystemExit(1)

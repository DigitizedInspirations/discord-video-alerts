"""Explicit, immutable approval for ONE corrected initialization dispatch."""
import hashlib
import json

from .model import AlertError

AUTHORIZATION_ID = "production-init-retry-5960a4af"
PREVIOUS_RUN = 38950215844
EXPECTED_RECORD = {
    "schema_version": 1,
    "authorization_id": AUTHORIZATION_ID,
    "approval_reference": "user attachment 5960a4af-853a-4b48-afa1-c27fe30327b0",
    "repository": "DigitizedInspirations/discord-video-alerts",
    "branch": "notification-state",
    "workflow": "initialize-state.yml",
    "operation": "initialize_empty_state",
    "confirmation": "INITIALIZE_EMPTY_NOTIFICATION_STATE_ONCE",
    "previous_failed_run": PREVIOUS_RUN,
    "previous_source_sha": "741f5e5a3b9da56d70a76b16767277d14b5b136f",
    "previous_evidence_sha256": "85231e3b0a382e47b93b5b1d91618ecd206cf6ed670ece7de29be6ab0d163e51",
    "previous_evidence_hash_format": "sha256-canonical-json-utf8",
    "max_new_dispatches": 1,
    "require_absent_branch_and_file": True,
    "allow_repair_or_overwrite": False,
}


def validate_record(root, authorization_id):
    try:
        record = json.loads((root / "docs/initialization-retry-authorization.json").read_text(encoding="utf-8"))
        evidence_raw = (root / f"docs/cloud/{PREVIOUS_RUN}-evidence.json").read_bytes()
        evidence = json.loads(evidence_raw)
        if authorization_id != AUTHORIZATION_ID or json.dumps(record, sort_keys=True) != json.dumps(EXPECTED_RECORD, sort_keys=True):
            raise ValueError()
        canonical = json.dumps(evidence, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        if hashlib.sha256(canonical).hexdigest() != record["previous_evidence_sha256"]:
            raise ValueError()
        run = evidence["run"]
        report = evidence["reports"]["DVA_REPORT"]
        if (run["id"] != PREVIOUS_RUN or run["head_sha"] != record["previous_source_sha"] or
                run["conclusion"] != "failure" or report.get("failed") != 1 or
                "api_trace" in report or "inspection" in report):
            raise ValueError()
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        raise AlertError("Explicit retry authorization or preserved zero-write failure evidence is invalid") from None
    return record


def authorize_dispatch(root, authorization_id, runs, previous_run):
    record = validate_record(root, authorization_id)
    # Any new attempt, including failure or cancellation, consumes this grant.
    if not isinstance(runs, list) or len(runs) != 1 or runs[0].get("id") != PREVIOUS_RUN:
        raise AlertError("Retry grant consumed or unexpected initialization history; dispatch refused")
    expected = {"id": PREVIOUS_RUN, "head_sha": record["previous_source_sha"], "head_branch": "main",
                "status": "completed", "conclusion": "failure", "event": "workflow_dispatch",
                "run_attempt": 1, "path": ".github/workflows/initialize-state.yml"}
    if not isinstance(previous_run, dict) or any(previous_run.get(k) != v for k, v in expected.items()):
        raise AlertError("Previously reviewed failed run does not match live GitHub metadata")
    return record

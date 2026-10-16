"""Dedicated approved one-time production initialization; no general operations."""
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from video_alerts.model import AlertError
from video_alerts.production_init import InitializationTransport, guard_environment, initialize, inspect_failure
from video_alerts.state import new_state
from video_alerts.initialization_authorization import AUTHORIZATION_ID, validate_record


def main():
    writer = None
    phase = "local_preflight"
    try:
        sha = guard_environment(os.environ, ROOT)
        phase = "local_authorization_preflight"
        validate_record(ROOT, AUTHORIZATION_ID)
        phase = "local_state_preparation"
        writer = InitializationTransport(sha, os.environ["GITHUB_RUN_ID"], new_state())
        phase = "remote_preflight"
        report = initialize(writer, os.environ["GITHUB_TOKEN"])
        phase = "post_verification_local_preflight"
        guard_environment(os.environ, ROOT)
        report["authorization_id"] = AUTHORIZATION_ID
        print("DVA_REPORT " + json.dumps(report, sort_keys=True))
        return 0
    except (AlertError, KeyError, TypeError, ValueError, AttributeError, OSError) as exc:
        failure_phase = writer.phase if writer is not None and phase != "post_verification_local_preflight" else phase
        report = {"mode": "PRODUCTION_EMPTY_STATE_INITIALIZATION", "failed": 1,
                  "phase": failure_phase, "authorization_id": AUTHORIZATION_ID,
                  "creation_requests_attempted": len(writer.attempted) if writer is not None else 0,
                  "error": str(exc) if isinstance(exc, AlertError) else "Validation failed in recorded phase; details withheld",
                  "no_retry_or_repair": True,
                  "discord_requests": 0, "youtube_requests": 0}
        if writer is not None:
            report["api_trace"] = writer.trace
            if writer.attempted:
                report["inspection"] = inspect_failure(writer, os.environ["GITHUB_TOKEN"])
        print("DVA_REPORT " + json.dumps(report, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

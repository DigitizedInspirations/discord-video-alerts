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


def main():
    writer = None
    try:
        sha = guard_environment(os.environ, ROOT)
        writer = InitializationTransport(sha, os.environ["GITHUB_RUN_ID"], new_state())
        report = initialize(writer, os.environ["GITHUB_TOKEN"])
        guard_environment(os.environ, ROOT)
        print("DVA_REPORT " + json.dumps(report, sort_keys=True))
        return 0
    except (AlertError, KeyError, TypeError, ValueError, AttributeError) as exc:
        report = {"mode": "PRODUCTION_EMPTY_STATE_INITIALIZATION", "failed": 1,
                  "error": str(exc) if isinstance(exc, AlertError) else "Invalid response/schema; stop for manual review",
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

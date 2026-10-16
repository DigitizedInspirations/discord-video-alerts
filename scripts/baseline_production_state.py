"""Dedicated single-attempt baseline phases; never import the engine or Discord client."""
import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from video_alerts.model import AlertError
from video_alerts.production_baseline import (AUTHORIZATION, BaselineTransport, build_proposal,
                                             guard, preflight, write_once)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("phase", choices=["preflight", "metadata", "write"])
    phase = p.parse_args().phase
    report = {"mode": "PRODUCTION_BASELINE_ONLY", "authorization": AUTHORIZATION, "phase": phase,
              "discord_requests": 0, "discord_secret_access": False, "production_state_writes": 0}
    fence = None
    try:
        cfg = guard(os.environ, ROOT, phase)
        sha, run_id = os.environ["BASELINE_EXPECTED_SHA"], os.environ["GITHUB_RUN_ID"]
        target = ROOT / ".validation/production-baseline-candidate.json"
        if phase == "metadata":
            from video_alerts.adapters import adapters
            proposal = build_proposal(cfg, adapters(cfg), run_id, sha, report)
            target.parent.mkdir(exist_ok=True)
            target.write_text(json.dumps(proposal, ensure_ascii=False), encoding="utf-8")
        else:
            proposal = json.loads(target.read_text(encoding="utf-8")) if phase == "write" else None
            fence = BaselineTransport(sha, run_id, proposal=proposal)
            if phase == "preflight":
                preflight(fence, os.environ["GITHUB_TOKEN"])
                report["initial_state_verified"] = True
            else:
                report.update(proposal["report"])
                report["phase"] = "write"
                report.update(write_once(fence, os.environ["GITHUB_TOKEN"], cfg))
        guard(os.environ, ROOT, phase)
        report["status"] = "PASSED"
        code = 0
    except Exception as exc:
        report.update(status="FAILED", error=str(exc) if isinstance(exc, AlertError) else "Baseline failed; sensitive details withheld",
                      no_retry_or_repair=True)
        code = 1
    if fence is not None:
        report.update(production_state_writes=fence.attempts, attempted_commit=fence.commit)
        report.setdefault("api_trace", fence.trace)
    print("DVA_REPORT " + json.dumps(report, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())

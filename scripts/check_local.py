"""Deterministic local verification with saved, non-secret test evidence."""
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
env = dict(os.environ, PYTHONPATH=str(ROOT / "src"), PYTHONUTF8="1")
commands = [[sys.executable, "-m", "compileall", "-q", "src", "tests", "scripts"], [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], [sys.executable, "-m", "video_alerts.cli", "validate"], [sys.executable, "scripts/validate_workflows.py"], [sys.executable, "scripts/security_scan.py"], [sys.executable, "-m", "pip", "check"]]
report = {"checked_at": datetime.now(timezone.utc).isoformat(), "environment": "Windows local", "checks": []}
for command in commands:
    result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, text=True, encoding="utf-8")
    report["checks"].append({"command": command[1:], "exit_code": result.returncode})
    if "unittest" in command:
        (ROOT / "docs/test-results.txt").write_text(result.stdout + result.stderr, encoding="utf-8")
    print(" ".join(command[1:]), "exit", result.returncode, flush=True)
    if result.returncode:
        print((result.stdout + result.stderr)[-4000:])
(ROOT / "docs/local_verification.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
raise SystemExit(1 if any(item["exit_code"] for item in report["checks"]) else 0)

"""Treat workflow inputs only as argument values, never shell commands."""
import os
import sys
from video_alerts.cli import main

operation = os.getenv("INPUT_OPERATION", "dryrun")
if operation not in {"validate", "initialize", "monitor", "dryrun", "manual", "test", "show", "edit", "delete", "resolve", "restore"}:
    raise SystemExit("Invalid workflow operation")
sys.argv = ["video-alerts", operation, "--github"]
raise SystemExit(main())

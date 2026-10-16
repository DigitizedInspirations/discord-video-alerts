"""Audit exact proposed/staged paths, never print detected credential values."""
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
staged = "--staged" in sys.argv
command = ["git", "diff", "--cached", "--name-only", "-z"] if staged else ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"]
paths = subprocess.check_output(command, cwd=ROOT).decode().split("\0")
patterns = {
    "Google API key": r"\bAIza[A-Za-z0-9_-]{35}\b",
    "webhook URL": r"https://(?:discord(?:app)?\.com)/api(?:/v\d+)?/webhooks/\d{17,20}/[A-Za-z0-9_-]{30,}",
    "GitHub token": r"\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,})\b",
    "AWS access key": r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b",
    "private key": r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
    "assigned credential": r"(?im)^\s*(?:api_key|password|access_token|auth_token|session_cookie)\s*[=:]\s*['\"]?[^\s'\"]{8,}",
}
findings = []
for name in sorted(set(paths)):
    if not name:
        continue
    path = ROOT/name
    if path.is_dir() or not path.exists():
        continue
    if any(part in {".venv", ".env", ".aws", ".tools", ".validation", "state", "__pycache__"} for part in path.relative_to(ROOT).parts) or path.name.startswith(".env") or path.suffix in {".pem", ".key"} or "cookie" in path.name.lower():
        findings.append({"path": name, "type": "private/local path"})
    raw = subprocess.check_output(["git", "show", ":" + name], cwd=ROOT) if staged else path.read_bytes()
    try:
        content = raw.decode("utf-8")
    except UnicodeDecodeError:
        if path.suffix.lower() not in {".gif", ".png", ".jpg", ".jpeg", ".webp"}:
            findings.append({"path": name, "type": "unexpected binary"})
        continue
    for label, pattern in patterns.items():
        if re.search(pattern, content):
            findings.append({"path": name, "type": label})
    if ".github/workflows/" in name and name.endswith(".yml"):
        if name.endswith(("ci.yml", "source-audit.yml", "validation.yml")) and "secrets.DISCORD_WEBHOOK_URL" in content:
            findings.append({"path": name, "type": "Discord secret in validation workflow"})
        if re.search(r"^\s+schedule:", content, re.M):
            findings.append({"path": name, "type": "active production schedule"})
config_bytes = subprocess.check_output(["git", "show", ":config/settings.json"], cwd=ROOT) if staged else (ROOT/"config/settings.json").read_bytes()
cfg = json.loads(config_bytes.decode("utf-8"))
if cfg["master_enabled"] is not False:
    findings.append({"type": "MASTER not OFF"})
report = {"checked_at": datetime.now(timezone.utc).isoformat(), "scope": "exact staged files" if staged else "proposed tracked/untracked nonignored files", "file_count": len(set(paths)-{""}), "findings": findings, "master_enabled": cfg["master_enabled"], "active_schedule": (ROOT/".github/workflows/scheduled.yml").exists()}
if not staged:
    (ROOT/"docs/prepush-audit.json").write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
print(json.dumps(report, indent=2))
raise SystemExit(bool(findings))

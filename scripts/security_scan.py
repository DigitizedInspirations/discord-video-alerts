"""Scope-limited static release checks; never prints matched secret values."""
import ast
import json
import re
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
findings = []
secret = re.compile(r"https://(?:discord(?:app)?\.com)/api(?:/v\d+)?/webhooks/\d{17,20}/[A-Za-z0-9_-]{30,}")
files = [p for directory in ("src", "tests", "scripts", "config", "docs", ".github") for p in (ROOT/directory).rglob("*") if p.is_file() and "__pycache__" not in p.parts]
files += list(ROOT.glob("*.md"))
for path in files:
    if path.suffix not in {".py", ".md", ".txt", ".json", ".yml", ".disabled"}:
        continue
    text = path.read_text(encoding="utf-8")
    if secret.search(text):
        findings.append({"path": str(path.relative_to(ROOT)), "problem": "Literal webhook-shaped secret"})
    if re.search(r"\bAIza[A-Za-z0-9_-]{35}\b", text):
        findings.append({"path": str(path.relative_to(ROOT)), "problem": "Literal Google API key"})
    if path.suffix == ".py" and "src" in path.parts:
        tree = ast.parse(text)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in {"eval", "exec"}:
                findings.append({"path": str(path.relative_to(ROOT)), "line": node.lineno, "problem": "Dynamic code execution"})
settings = json.loads((ROOT/"config/settings.json").read_text(encoding="utf-8"))
if settings["master_enabled"]:
    findings.append({"problem": "Initial master switch is not OFF"})
if (ROOT/".github/workflows/scheduled.yml").exists():
    findings.append({"problem": "Unapproved production schedule is active"})
report = {"checked_at": datetime.now(timezone.utc).isoformat(), "scope": "Tracked project source/config/docs/workflows, no dependency CVE database", "findings": findings}
(ROOT/"docs/security-scan.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print("Static security findings:", len(findings))
for finding in findings:
    print(json.dumps(finding))
raise SystemExit(bool(findings))

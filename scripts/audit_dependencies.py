"""Read-only OSV audit of exact locked versions. Never reads service credentials."""
import json
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def fetch(url, body=None):
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json", "User-Agent": "DiscordVideoAlerts-DependencyAudit"}, method="GET" if data is None else "POST")
    # No key, cookies, authorization or local environment data is sent.
    with urllib.request.urlopen(req, timeout=30) as result:
        raw = result.read(3_000_001)
    if len(raw) > 3_000_000:
        raise ValueError("Advisory response too large")
    return json.loads(raw)


def main():
    packages = []
    for line in (ROOT/"requirements.lock").read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        match = re.fullmatch(r"([A-Za-z0-9_.-]+)==([A-Za-z0-9_.+-]+)", line.strip())
        if not match:
            raise ValueError("Unsupported lock entry")
        packages.append({"name": match[1], "version": match[2]})
    result = fetch("https://api.osv.dev/v1/querybatch", {"queries": [{"package": {"name": p["name"], "ecosystem": "PyPI"}, "version": p["version"]} for p in packages]})
    if len(result["results"]) != len(packages):
        raise ValueError("Incomplete advisory response")
    findings = []
    for package, answer in zip(packages, result["results"]):
        if "error" in answer:
            raise ValueError("Advisory query failed")
        for item in answer.get("vulns", []):
            advisory_id = item["id"]
            if not re.fullmatch(r"[A-Za-z0-9_-]+", advisory_id):
                raise ValueError("Invalid advisory identifier")
            detail = fetch("https://api.osv.dev/v1/vulns/"+advisory_id)
            if detail.get("withdrawn"):
                continue
            findings.append({"package": package, "id": advisory_id, "aliases": detail.get("aliases", []), "summary": detail.get("summary", ""), "severity": detail.get("severity", []), "database_specific": {"severity": detail.get("database_specific", {}).get("severity")}, "url": "https://osv.dev/vulnerability/"+advisory_id})
    report = {"checked_at": datetime.now(timezone.utc).isoformat(), "source": "OSV querybatch plus advisory details", "packages": packages, "findings": findings, "limitations": ["Advisory database coverage is not a guarantee of no vulnerabilities", "requirements.lock has no wheel hashes", "GitHub Actions and build-only setuptools/pip are outside this PyPI runtime/dev lock audit"]}
    (ROOT/"docs/dependency-audit.json").write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return bool(findings)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:
        print("Dependency advisory audit unavailable; no credential data was accessed")
        raise SystemExit(2)

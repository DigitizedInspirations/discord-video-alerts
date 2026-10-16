"""Read-only integration evidence, including full metadata/owner verification."""
import json
import platform
import sys
import os
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from video_alerts.adapters import adapters
from video_alerts.config import load_config
from video_alerts.model import AlertError

cfg = load_config(ROOT)
if "DISCORD_WEBHOOK_URL" in os.environ:
    raise SystemExit("Read-only source validation must not receive a Discord secret")
report = {"checked_at": datetime.now(timezone.utc).isoformat(), "environment": platform.platform(), "sources": {}}
for sid, adapter in adapters(cfg).items():
    print("Checking", sid, flush=True)
    evidence = {"discovery": "NOT TESTED", "metadata": "NOT TESTED"}
    try:
        posts = adapter.discover(sid)
        evidence.update(discovery="VERIFIED", count=len(posts), ids=[p.post_id for p in posts[:3]])
        evidence["discovery_method"] = getattr(adapter, "discovery_method", "public_profile")
        if posts:
            post = adapter.enrich(posts[0])
            evidence.update(metadata="VERIFIED", public=post.public, kind=post.kind, published_at=post.published_at, owner_id=post.owner_id)
            if sid.startswith("youtube"):
                evidence["official_tab_classification"] = adapter.classify(post)
    except AlertError as exc:
        evidence["error"] = str(exc)
        if evidence["discovery"] != "VERIFIED":
            evidence["discovery"] = "BLOCKED"
        else:
            evidence["metadata"] = "BLOCKED"
    report["sources"][sid] = evidence
    print(sid, json.dumps(evidence), flush=True)
target = ROOT / "docs/adapter_probe.json"
target.parent.mkdir(exist_ok=True)
target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
archive = ROOT / "docs/probes"
archive.mkdir(exist_ok=True)
(archive / ("adapters-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + ".json")).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("Read-only source audit complete; no Discord calls")
print("DVA_REPORT " + json.dumps(report))
raise SystemExit(1 if any(source["discovery"] != "VERIFIED" or source["metadata"] != "VERIFIED" or source.get("public") is not True for source in report["sources"].values()) else 0)

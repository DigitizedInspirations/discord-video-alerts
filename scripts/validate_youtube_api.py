"""Read-only, stateless API validation, dispatched only after separate approval."""
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from video_alerts.adapters import adapters
from video_alerts.config import load_config
from video_alerts.model import AlertError


def main():
    if "DISCORD_WEBHOOK_URL" in os.environ:
        raise AlertError("YouTube validation must not receive a Discord secret")
    if not os.environ.get("YOUTUBE_API_KEY", "").strip():
        raise AlertError("YouTube validation requires YOUTUBE_API_KEY in the environment")
    cfg = load_config(ROOT)
    if cfg["master_enabled"] or (ROOT / ".github/workflows/scheduled.yml").exists():
        raise AlertError("Validation requires MASTER OFF and scheduling disabled")
    selected = {sid: adapter for sid, adapter in adapters(cfg).items() if sid.startswith("youtube_")}
    report = {"checked_at": datetime.now(timezone.utc).isoformat(), "mode": "READ_ONLY_STATELESS",
              "sources": {}, "discord_requests": 0, "production_state_writes": 0}
    for sid, adapter in selected.items():
        result = {"discovery": "NOT TESTED", "metadata": "NOT TESTED", "metadata_method": adapter.metadata_method}
        try:
            posts = adapter.discover(sid)
            if not posts:
                raise AlertError("No public posts available to validate metadata")
            result.update(discovery="VERIFIED", discovery_method=adapter.discovery_method, count=len(posts))
            post = adapter.enrich(posts[0])
            result.update(post_id=post.post_id, owner_id=post.owner_id, published_at=post.published_at,
                          public=post.public, kind=post.kind, premiere=post.premiere,
                          official_tab_classification=adapter.classify(post))
            if post.public is not True:
                raise AlertError("Latest API video is not verified public and ready")
            result["metadata"] = "VERIFIED"
        except AlertError as exc:
            result["error"] = str(exc)
            result["metadata" if result["discovery"] == "VERIFIED" else "discovery"] = "BLOCKED"
        report["sources"][sid] = result
    api = next(iter(selected.values())).api
    report.update(api_requests=api.requests, estimated_quota_units=api.requests,
                  subtype_and_premiere_limits="Unknown classification remains deferred by restrictive filters")
    target = ROOT / ".validation/youtube-api-validation.json"
    target.parent.mkdir(exist_ok=True)
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("DVA_REPORT " + json.dumps(report))
    return int(any(source["metadata"] != "VERIFIED" for source in report["sources"].values()))


if __name__ == "__main__":
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    try:
        raise SystemExit(main())
    except AlertError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
    except Exception:
        print("YouTube validation failed; sensitive details withheld", file=sys.stderr)
        raise SystemExit(1)

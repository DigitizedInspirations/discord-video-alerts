"""Read public hydration metadata; report structure without capturing user credentials."""
import json
import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
accounts = {"infinity.projectrp": "7694665449945959702", "milo.and.mia.world": "7695067403826334998"}
report = {}
for account, pid in accounts.items():
    url = f"https://www.tiktok.com/@{account}/video/{pid}"
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=25) as response:
            body = response.read(6_000_000).decode("utf-8", "replace")
        match = re.search(r'<script[^>]*id="__UNIVERSAL_DATA_FOR_REHYDRATION__"[^>]*>(.*?)</script>', body, re.S)
        data = json.loads(match[1]) if match else {}
        scope = data.get("__DEFAULT_SCOPE__", {})
        detail = scope.get("webapp.video-detail", {})
        item = detail.get("itemInfo", {}).get("itemStruct", {})
        report[account] = {"bytes": len(body), "scope_keys": list(scope), "detail_keys": list(detail), "detail_status": detail.get("statusCode"), "item_keys": list(item), "id": item.get("id"), "author": item.get("author", {}).get("uniqueId"), "createTime": item.get("createTime"), "privateItem": item.get("privateItem")}
    except Exception as exc:
        report[account] = {"error_type": type(exc).__name__}
    print(account, json.dumps(report[account]))
(ROOT / "docs/tiktok_hydration_probe.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

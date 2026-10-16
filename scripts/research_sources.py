"""Read-only public-source probes; never send to Discord or capture credentials."""
import json
import re
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
URLS = {
    "youtube_dayz": "https://www.youtube.com/@DayZMomentsTV",
    "youtube_milo_mia": "https://www.youtube.com/@milo-and-mia-world",
    "tiktok_dayz": "https://www.tiktok.com/@infinity.projectrp",
    "tiktok_milo_mia": "https://www.tiktok.com/@milo.and.mia.world",
}

def main():
    report = {"checked_at": datetime.now(timezone.utc).isoformat(), "environment": "Windows local", "sources": {}}
    for source, url in URLS.items():
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=25) as response:
                body = response.read(6_000_000).decode("utf-8", "replace")
                status = response.status
            ids = sorted(set(re.findall(r'"(?:externalId|channelId)":"(UC[\w-]{22})"', body)))
            report["sources"][source] = {"url": url, "http_status": status, "bytes": len(body), "channel_ids": ids, "has_public_post_data": "itemList" in body or "ItemModule" in body}
            if source.startswith("youtube") and len(ids) == 1:
                feed_url = "https://www.youtube.com/feeds/videos.xml?channel_id=" + ids[0]
                with urllib.request.urlopen(feed_url, timeout=25) as response:
                    feed = ET.fromstring(response.read(1_000_000))
                ns = {"a": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015"}
                report["sources"][source]["rss_channel_id"] = feed.findtext("yt:channelId", namespaces=ns)
                report["sources"][source]["rss_title"] = feed.findtext("a:title", namespaces=ns)
                report["sources"][source]["rss_entries"] = len(feed.findall("a:entry", ns))
        except Exception as exc:
            report["sources"][source] = {"url": url, "error_type": type(exc).__name__, "error": str(exc)}
        print(source, json.dumps(report["sources"][source]))
    (ROOT / "docs").mkdir(exist_ok=True)
    (ROOT / "docs" / "source_probe.json").write_text(json.dumps(report, indent=2), encoding="utf-8")

if __name__ == "__main__":
    main()

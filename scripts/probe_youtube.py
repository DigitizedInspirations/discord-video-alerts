"""Bounded public metadata diagnostics; never print raw extractor warnings/errors."""
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from video_alerts.config import load_config
from yt_dlp import YoutubeDL


class DiagnosticLogger:
    def __init__(self):
        self.categories = set()

    def debug(self, message):
        pass

    def warning(self, message):
        self.record(message)

    def error(self, message):
        self.record(message)

    def record(self, message):
        lowered = str(message).lower()
        for text, category in (("sign in", "authentication_requested"),
                               ("bot", "bot_check"),
                               ("javascript", "javascript_runtime"),
                               ("js runtime", "javascript_runtime"),
                               ("challenge", "challenge"),
                               ("unavailable", "unavailable"),
                               ("format", "formats_unavailable")):
            if text in lowered:
                self.categories.add(category)


if "DISCORD_WEBHOOK_URL" in os.environ:
    raise SystemExit("Read-only diagnostics must not receive a Discord secret")
cfg = load_config(ROOT)
report = {}
for sid, ch in cfg["channels"].items():
    if ch["platform"] != "youtube":
        continue
    logger = DiagnosticLogger()
    result = {"expected_channel_id": ch["channel_id"]}
    try:
        with YoutubeDL({"quiet": True, "no_warnings": False, "logger": logger,
                        "skip_download": True, "ignore_no_formats_error": True,
                        "extract_flat": True, "playlistend": 1,
                        "socket_timeout": 20, "retries": 1,
                        "extractor_retries": 1, "ignoreerrors": False}) as ydl:
            listing = ydl.extract_info("https://www.youtube.com/@" + ch["account"], download=False)
            if listing.get("channel_id") != ch["channel_id"]:
                raise ValueError("Unverified channel listing")
            item = next(iter(listing["entries"]))
            url = item.get("webpage_url") or item.get("url")
        from video_alerts.model import video_url
        pid, url = video_url(url, "youtube")
        result["post_id"] = pid
        with YoutubeDL({"quiet": True, "no_warnings": False, "logger": logger,
                        "skip_download": True, "ignore_no_formats_error": True,
                        "extract_flat": False, "socket_timeout": 20,
                        "retries": 1, "extractor_retries": 1,
                        "ignoreerrors": False}) as ydl:
            info = ydl.extract_info(url, download=False)
        result["metadata"] = {key: info.get(key) for key in (
            "id", "channel_id", "availability", "live_status", "timestamp",
            "release_timestamp", "age_limit", "was_live")}
        logger.record(info.get("__pending_error", ""))
        result["pending_error_present"] = bool(info.get("__pending_error"))
    except Exception as exc:
        logger.record(str(exc))
        result["extraction_failed"] = True
    result["warning_categories"] = sorted(logger.categories)
    report[sid] = result
print("DVA_YOUTUBE_DIAGNOSTIC " + json.dumps(report))

"""One-time local scaffolding; never writes outside this repository."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    "youtube_dayz": ("youtube", "DayZMomentsTV", "UCz5ka9rKYsdaeaxmN_7nHbg", "Infinity / DayZ", "infinity.gif"),
    "youtube_milo_mia": ("youtube", "milo-and-mia-world", "UCg1uoL9TtAaxvyn6dbQ08fA", "Milo & Mia", "milo-mia.gif"),
    "tiktok_dayz": ("tiktok", "infinity.projectrp", None, "Infinity / DayZ", "infinity.gif"),
    "tiktok_milo_mia": ("tiktok", "milo.and.mia.world", None, "Milo & Mia", "milo-mia.gif"),
}

if __name__ == "__main__":
    cfg = {"schema_version": 1, "master_enabled": False, "queue_delay_seconds": 10, "max_messages_per_run": 5, "max_video_age_hours": 24, "retry": {"attempts": 3, "base_seconds": 1, "max_seconds": 30}, "logging": {"level": "INFO"}, "health": {"failure_threshold": 3}, "channels": {}}
    for sid, (platform, account, channel_id, username, media) in SOURCES.items():
        cfg["channels"][sid] = {"platform": platform, "account": account, "enabled": True, "channel_id": channel_id, "template": f"config/messages/{sid}.txt", "username": username, "avatar_url": None, "avatar_fallback": "omit", "role": {"enabled": False, "id": None}, "preview": "native", "embed": {"enabled": False, "color": 0xD32F2F if platform == "youtube" else 0x00C9C9}, "media": {"enabled": False, "path": "assets/" + media, "fallback": "omit", "max_bytes": 10_000_000, "require_animation": True}, "publication_delay_minutes": 0, "filters": {"enabled": True, "include_keywords": [], "exclude_keywords": [], "video_types": "both", "exclude_livestreams": True, "exclude_premieres": False}}
    target = ROOT / "config/settings.json"
    if target.exists():
        raise SystemExit("Settings already exist; no overwrite")
    target.write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

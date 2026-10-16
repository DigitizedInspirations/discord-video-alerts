import json
import re
from pathlib import Path
from string import Formatter
from .model import AlertError, safe_url

SOURCES = {
    "youtube_dayz": ("youtube", "DayZMomentsTV"),
    "youtube_milo_mia": ("youtube", "milo-and-mia-world"),
    "tiktok_dayz": ("tiktok", "infinity.projectrp"),
    "tiktok_milo_mia": ("tiktok", "milo.and.mia.world"),
}
VARIABLES = {"VIDEO_URL", "VIDEO_TITLE", "CHANNEL_NAME", "PLATFORM", "PUBLISHED_AT"}

def keys(obj, expected, where):
    if not isinstance(obj, dict) or set(obj) != set(expected.split()):
        raise AlertError(f"Invalid or missing keys: {where}")

def boolean(v, where):
    if type(v) is not bool:
        raise AlertError(f"Expected true/false: {where}")

def number(v, low, high, where):
    if type(v) not in (int, float) or not low <= v <= high:
        raise AlertError(f"Expected number {low}..{high}: {where}")

def integer(v, low, high, where):
    if type(v) is not int or not low <= v <= high:
        raise AlertError(f"Expected integer {low}..{high}: {where}")

def relative(root, value):
    if not isinstance(value, str) or not value or Path(value).is_absolute() or "\\" in value or ":" in value:
        raise AlertError("Use a relative project path with forward slashes")
    base = Path(root).resolve()
    result = (base / value).resolve()
    if not result.is_relative_to(base) or result == base or any(part.startswith(".") for part in Path(value).parts):
        raise AlertError("Path escapes project or references a hidden path")
    return result

def template_fields(text):
    try:
        fields = set()
        for _, name, spec, conversion in Formatter().parse(text):
            if name is not None:
                if name not in VARIABLES or spec or conversion:
                    raise ValueError()
                fields.add(name)
        if "VIDEO_URL" not in fields:
            raise ValueError()
        if len(text) > 1800:
            raise ValueError()
    except ValueError:
        raise AlertError("Template needs {VIDEO_URL}; only documented plain placeholders are supported") from None
    return fields

def load_config(root, path="config/settings.json"):
    try:
        cfg = json.loads(relative(root, path).read_text(encoding="utf-8"), parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
    except (ValueError, OSError):
        raise AlertError("Cannot read valid UTF-8 settings JSON") from None
    validate(cfg, root)
    return cfg

def validate(cfg, root):
    keys(cfg, "schema_version master_enabled queue_delay_seconds max_messages_per_run max_video_age_hours retry logging health channels", "settings")
    if type(cfg["schema_version"]) is not int or cfg["schema_version"] != 1:
        raise AlertError("Unsupported settings schema")
    boolean(cfg["master_enabled"], "master_enabled")
    number(cfg["queue_delay_seconds"], 0, 60, "queue delay")
    integer(cfg["max_messages_per_run"], 1, 20, "queue limit")
    number(cfg["max_video_age_hours"], 1, 720, "maximum age")
    keys(cfg["retry"], "attempts base_seconds max_seconds", "retry")
    integer(cfg["retry"]["attempts"], 1, 5, "retry attempts")
    number(cfg["retry"]["base_seconds"], 0, 30, "retry base")
    number(cfg["retry"]["max_seconds"], 1, 120, "retry ceiling")
    keys(cfg["logging"], "level", "logging")
    if cfg["logging"]["level"] not in {"INFO", "WARNING"}:
        raise AlertError("Logging level must be INFO or WARNING")
    keys(cfg["health"], "failure_threshold", "health")
    integer(cfg["health"]["failure_threshold"], 1, 100, "health threshold")
    if not isinstance(cfg["channels"], dict) or set(cfg["channels"]) != set(SOURCES):
        raise AlertError("Exactly the four approved source IDs are required")
    for sid, ch in cfg["channels"].items():
        keys(ch, "platform account enabled channel_id template username avatar_url avatar_fallback role preview embed media publication_delay_minutes filters", sid)
        if (ch["platform"], ch["account"]) != SOURCES[sid]:
            raise AlertError(f"Account mismatch: {sid}")
        boolean(ch["enabled"], sid)
        if ch["channel_id"] is not None and not (ch["platform"] == "youtube" and isinstance(ch["channel_id"], str) and re.fullmatch(r"UC[\w-]{22}", ch["channel_id"])):
            raise AlertError(f"Invalid channel ID: {sid}")
        if not isinstance(ch["username"], str) or not 1 <= len(ch["username"]) <= 80 or any(ord(c) < 32 for c in ch["username"]):
            raise AlertError(f"Invalid webhook username: {sid}")
        if ch["avatar_url"] is not None:
            safe_url(ch["avatar_url"])
        if ch["avatar_fallback"] not in {"omit", "skip"}:
            raise AlertError("Invalid avatar fallback")
        try:
            template_fields(relative(root, ch["template"]).read_text(encoding="utf-8"))
        except OSError:
            raise AlertError(f"Missing template: {sid}") from None
        keys(ch["role"], "enabled id", "role")
        boolean(ch["role"]["enabled"], "role enabled")
        role = ch["role"]["id"]
        if role is not None and (not isinstance(role, str) or not re.fullmatch(r"[1-9]\d{16,19}", role)):
            raise AlertError("Role ID must be a Discord snowflake string")
        if ch["role"]["enabled"] and role is None:
            raise AlertError("Enabled role needs an ID")
        if ch["preview"] not in {"native", "disabled"}:
            raise AlertError("Preview supports native or disabled; external services need separate evaluation")
        keys(ch["embed"], "enabled color", "embed")
        boolean(ch["embed"]["enabled"], "embed")
        integer(ch["embed"]["color"], 0, 0xFFFFFF, "embed color")
        keys(ch["media"], "enabled path fallback max_bytes require_animation", "media")
        boolean(ch["media"]["enabled"], "media enabled")
        boolean(ch["media"]["require_animation"], "media animation")
        relative(root, ch["media"]["path"])
        if ch["media"]["fallback"] not in {"omit", "skip"}:
            raise AlertError("Invalid media fallback")
        integer(ch["media"]["max_bytes"], 1, 10_000_000, "media upload limit")
        number(ch["publication_delay_minutes"], 0, 1440, "publication delay")
        f = ch["filters"]
        keys(f, "enabled include_keywords exclude_keywords video_types exclude_livestreams exclude_premieres", "filters")
        for name in ("enabled", "exclude_livestreams", "exclude_premieres"):
            boolean(f[name], name)
        for name in ("include_keywords", "exclude_keywords"):
            if not isinstance(f[name], list) or any(not isinstance(s, str) or not s.strip() or len(s) > 100 for s in f[name]):
                raise AlertError("Keywords must be nonempty strings")
        if f["video_types"] not in {"both", "shorts", "regular"}:
            raise AlertError("Invalid video_types filter")

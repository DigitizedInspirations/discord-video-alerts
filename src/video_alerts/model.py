from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import re
from urllib.parse import parse_qs, urlsplit

class AlertError(Exception):
    """Operator-safe error; never include network exception strings."""

def utcnow():
    return datetime.now(timezone.utc)

def stamp(value):
    return value.astimezone(timezone.utc).isoformat()

def date(value):
    if not isinstance(value, str):
        raise AlertError("Publication timestamp must be timezone-aware ISO 8601")
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise AlertError("Invalid publication timestamp") from None
    if result.tzinfo is None:
        raise AlertError("Timestamp needs a timezone")
    return result.astimezone(timezone.utc)

def safe_url(value, hosts=None):
    if not isinstance(value, str) or any(ord(c) < 33 for c in value):
        raise AlertError("Invalid HTTPS URL")
    try:
        u = urlsplit(value)
        if u.scheme != "https" or not u.hostname or u.username or u.password or u.port not in (None, 443) or u.fragment:
            raise ValueError()
        if hosts and u.hostname not in hosts:
            raise ValueError()
    except ValueError:
        raise AlertError("URL host or scheme is not allowed") from None
    return u

def video_url(value, platform, account=None):
    hosts = {"www.youtube.com", "youtube.com", "youtu.be"} if platform == "youtube" else {"www.tiktok.com", "tiktok.com"}
    u = safe_url(value, hosts)
    if platform == "youtube":
        if u.hostname == "youtu.be":
            post = u.path.strip("/")
        elif u.path == "/watch":
            q = parse_qs(u.query)
            post = q.get("v", [""])[0] if len(q.get("v", [])) == 1 else ""
        else:
            match = re.fullmatch(r"/shorts/([\w-]{11})/?", u.path)
            post = match[1] if match else ""
        if not re.fullmatch(r"[\w-]{11}", post):
            raise AlertError("Invalid YouTube video ID")
        return post, "https://www.youtube.com/watch?v=" + post
    match = re.fullmatch(r"/@([A-Za-z0-9._]+)/video/(\d{10,25})/?", u.path)
    if not match or (account and match[1].casefold() != account.casefold()):
        raise AlertError("TikTok URL must belong to the selected account")
    return match[2], f"https://www.tiktok.com/@{match[1]}/video/{match[2]}"

def sanitize(value):
    text = str(value or "")
    text = "".join(c for c in text if c in "\n\t" or (ord(c) >= 32 and not 0x202A <= ord(c) <= 0x202E))
    text = text.replace("@", "@\u200b").replace("<", "‹").replace(">", "›")
    return re.sub(r"([\\`*_~|\[\]])", r"\\\1", text)[:500]

@dataclass
class Post:
    platform: str
    source_id: str
    post_id: str
    url: str
    title: str = ""
    channel_name: str = ""
    published_at: str | None = None
    kind: str = "unknown"
    public: bool | None = None
    premiere: bool | None = None
    owner_id: str | None = None

    @property
    def key(self):
        return f"{self.platform}:{self.source_id}:{self.post_id}"

    def dict(self):
        return asdict(self)

"""Official YouTube RSS discovery; public metadata extraction without login/cookies."""
import re
import json
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from .http import public_get
from .model import AlertError, Post, stamp, video_url

class QuietLogger:
    def debug(self, message):
        pass
    def warning(self, message):
        pass
    def error(self, message):
        pass

def extract(url, flat=False):
    try:
        from yt_dlp import YoutubeDL
        with YoutubeDL({"quiet": True, "no_warnings": True, "logger": QuietLogger(), "skip_download": True, "ignore_no_formats_error": True, "extract_flat": flat, "playlistend": 30, "socket_timeout": 20, "retries": 1, "extractor_retries": 1, "ignoreerrors": False}) as ydl:
            info = ydl.extract_info(url, download=False)
        if not isinstance(info, dict):
            raise ValueError()
        return info
    except Exception:
        raise AlertError("Public metadata extraction unavailable; no cookies or bypass attempted") from None

def from_metadata(info, source_id, ch):
    post_id, url = video_url(info.get("webpage_url") or info.get("url", ""), ch["platform"], ch["account"])
    if str(info.get("id")) != post_id:
        raise AlertError("Metadata post ID mismatch")
    ts = info.get("release_timestamp") or info.get("timestamp")
    published = None
    if type(ts) in (int, float):
        try:
            published = stamp(datetime.fromtimestamp(ts, timezone.utc))
        except (ValueError, OSError, OverflowError):
            pass
    if ch["platform"] == "youtube":
        owner = info.get("channel_id")
        if not ch["channel_id"] or owner != ch["channel_id"]:
            raise AlertError("YouTube metadata belongs to a different/unverified channel")
        status = info.get("live_status")
        kind = "livestream" if status in {"is_live", "was_live", "post_live"} or info.get("was_live") is True else "unknown"
        # Duration and URL shape cannot reliably prove Shorts membership.
        public = status not in {"is_upcoming"} and info.get("availability") in {"public", "unlisted"} and status is not None
        if info.get("availability") == "unlisted":
            public = False
        premiere = None  # yt-dlp does not reliably expose historical premiere identity.
    else:
        owner = info.get("uploader_id")
        if not isinstance(owner, str) or owner.lstrip("@").casefold() != ch["account"].casefold():
            raise AlertError("TikTok owner identity could not be verified")
        kind = "regular"
        public = info.get("availability") in {None, "public"}
        premiere = False
    return Post(ch["platform"], source_id, post_id, url, str(info.get("title") or ""), str(info.get("channel") or info.get("uploader") or ch["account"]), published, kind, public, premiere, owner)

class YouTubeAdapter:
    def __init__(self, ch, retry):
        self.ch, self.retry = ch, retry
        self._tab_membership = None
        self.discovery_method = "official_rss"

    def resolve(self):
        body = public_get("https://www.youtube.com/@" + self.ch["account"], self.retry).body.decode("utf-8", "replace")
        ids = set(re.findall(r'"externalId":"(UC[\w-]{22})"', body))
        if len(ids) != 1:
            raise AlertError("YouTube handle resolution is ambiguous or blocked")
        resolved = ids.pop()
        if self.ch["channel_id"] and self.ch["channel_id"] != resolved:
            raise AlertError("YouTube handle does not match configured channel ID")
        return resolved

    def discover(self, source_id):
        if not self.ch["channel_id"]:
            raise AlertError("YouTube channel ID has not been verified")
        try:
            response = public_get("https://www.youtube.com/feeds/videos.xml?channel_id=" + self.ch["channel_id"], self.retry)
        except AlertError as exc:
            if str(exc) != "Public source HTTP 404":
                raise
            self.discovery_method = "public_channel_fallback_after_rss_404"
            return self.discover_channel(source_id)
        self.discovery_method = "official_rss"
        return self.parse_feed(response.body, source_id)

    def discover_channel(self, source_id):
        info = extract("https://www.youtube.com/@" + self.ch["account"], flat=True)
        if info.get("channel_id") != self.ch["channel_id"] or info.get("entries") is None:
            raise AlertError("YouTube fallback channel listing identity is unverified")
        posts = []
        for item in info["entries"]:
            if not isinstance(item, dict) or item.get("channel_id") not in {None, self.ch["channel_id"]}:
                raise AlertError("YouTube fallback listing incomplete or wrong owner")
            pid, url = video_url(item.get("webpage_url") or item.get("url", ""), "youtube")
            if pid != item.get("id"):
                raise AlertError("YouTube fallback post identity mismatch")
            posts.append(Post("youtube", source_id, pid, url, str(item.get("title") or ""), self.ch["account"]))
            if len(posts) >= 30:
                break
        if not posts:
            raise AlertError("Empty YouTube fallback listing cannot establish a safe source check")
        return posts

    def parse_feed(self, raw, source_id):
        if b"<!DOCTYPE" in raw.upper() or b"<!ENTITY" in raw.upper():
            raise AlertError("Feed declarations are forbidden")
        try:
            feed = ET.fromstring(raw)
        except ET.ParseError:
            raise AlertError("Invalid RSS response; never treat as empty feed") from None
        ns = {"a": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015"}
        feed_id = feed.findtext("yt:channelId", namespaces=ns)
        # Current official feeds expose the top-level ID without the UC prefix.
        feed_id = feed_id if feed_id and feed_id.startswith("UC") else "UC" + (feed_id or "")
        if feed.tag != "{http://www.w3.org/2005/Atom}feed" or feed_id != self.ch["channel_id"]:
            raise AlertError("RSS identity mismatch")
        result = []
        for entry in feed.findall("a:entry", ns):
            pid = entry.findtext("yt:videoId", namespaces=ns)
            entry_id = entry.findtext("yt:channelId", namespaces=ns)
            entry_id = entry_id if entry_id and entry_id.startswith("UC") else "UC" + (entry_id or "")
            if not pid or not re.fullmatch(r"[\w-]{11}", pid) or entry_id != self.ch["channel_id"]:
                raise AlertError("RSS entry identity mismatch")
            result.append(Post("youtube", source_id, pid, "https://www.youtube.com/watch?v=" + pid, entry.findtext("a:title", default="", namespaces=ns), entry.findtext("a:author/a:name", default=self.ch["account"], namespaces=ns), entry.findtext("a:published", namespaces=ns)))
        return result

    def enrich(self, post):
        enriched = from_metadata(extract(post.url), post.source_id, self.ch)
        # Atom's timestamp is a publication instant; date-only upload_date is ignored.
        enriched.published_at = enriched.published_at or post.published_at
        if enriched.kind == "unknown" and self.ch["filters"]["enabled"] and self.ch["filters"]["video_types"] != "both":
            enriched.kind = self.classify(post)
        return enriched

    def classify(self, post):
        """Positive membership in an official source tab; absence never proves type."""
        if self._tab_membership is None:
            self._tab_membership = {}
            for tab, kind in (("shorts", "short"), ("videos", "regular")):
                try:
                    listing = extract("https://www.youtube.com/@" + self.ch["account"] + "/" + tab, flat=True)
                    if listing.get("channel_id") != self.ch["channel_id"] or listing.get("entries") is None:
                        continue
                    for item in listing["entries"]:
                        if not isinstance(item, dict) or item.get("channel_id") not in {None, self.ch["channel_id"]}:
                            continue
                        pid = item.get("id")
                        if isinstance(pid, str) and re.fullmatch(r"[\w-]{11}", pid):
                            previous = self._tab_membership.get(pid)
                            self._tab_membership[pid] = kind if previous in {None, kind} else "unknown"
                except AlertError:
                    continue
        return self._tab_membership.get(post.post_id, "unknown")

class TikTokAdapter:
    def __init__(self, ch, retry):
        self.ch, self.retry = ch, retry

    def discover(self, source_id):
        info = extract("https://www.tiktok.com/@" + self.ch["account"], flat=True)
        entries = info.get("entries")
        if entries is None:
            raise AlertError("TikTok profile response has no verifiable listing")
        result = []
        for entry in entries:
            if not isinstance(entry, dict):
                raise AlertError("TikTok listing incomplete")
            pid, url = video_url(entry.get("webpage_url") or entry.get("url", ""), "tiktok", self.ch["account"])
            ts = entry.get("timestamp")
            published = stamp(datetime.fromtimestamp(ts, timezone.utc)) if type(ts) in (int, float) else None
            result.append(Post("tiktok", source_id, pid, url, str(entry.get("title") or ""), self.ch["account"], published))
            if len(result) >= 30:
                break
        if not result:
            raise AlertError("Empty TikTok listing cannot be distinguished from blocked response")
        return result

    def enrich(self, post):
        # Public HTML contains author/timestamp/privacy metadata even when the
        # media-format extractor fails. No login, cookies or CAPTCHA handling.
        response = public_get(post.url, self.retry)
        return self.parse_detail(response.body, post)

    def parse_detail(self, raw, post):
        try:
            body = raw.decode("utf-8")
            match = re.search(r'<script[^>]*id="__UNIVERSAL_DATA_FOR_REHYDRATION__"[^>]*>(.*?)</script>', body, re.S)
            if not match:
                raise ValueError()
            detail = json.loads(match[1])["__DEFAULT_SCOPE__"]["webapp.video-detail"]
            if type(detail["statusCode"]) is not int or detail["statusCode"] != 0:
                raise ValueError()
            item = detail["itemInfo"]["itemStruct"]
            owner = item["author"]["uniqueId"]
            if item["id"] != post.post_id or owner.casefold() != self.ch["account"].casefold():
                raise ValueError()
            pid, canonical = video_url(post.url, "tiktok", owner)
            if pid != post.post_id or canonical != post.url:
                raise ValueError()
            if not isinstance(item["video"], dict) or not item["video"]:
                raise ValueError()
            # Unknown privacy fields fail closed; explicit false or numeric zero only.
            flags = [item[name] for name in ("privateItem", "secret", "forFriend", "isProhibited", "takeDown")]
            if any(type(flag) not in (bool, int) or flag not in (False, 0, True, 1) for flag in flags):
                raise ValueError()
            public = not any(flags)
            created = item["createTime"]
            if isinstance(created, str) and re.fullmatch(r"\d{9,12}", created):
                created = int(created)
            if type(created) is not int:
                raise ValueError()
            published = stamp(datetime.fromtimestamp(created, timezone.utc))
            return Post("tiktok", post.source_id, post.post_id, post.url, str(item.get("desc") or ""), str(item["author"].get("nickname") or owner), published, "regular", public, False, owner)
        except (KeyError, ValueError, TypeError, UnicodeError, AttributeError, OverflowError, OSError):
            raise AlertError("TikTok public HTML metadata missing, private, incomplete or identity mismatch") from None

def adapters(cfg):
    return {sid: (YouTubeAdapter if ch["platform"] == "youtube" else TikTokAdapter)(ch, cfg["retry"]) for sid, ch in cfg["channels"].items()}

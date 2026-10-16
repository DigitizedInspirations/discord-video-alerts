import json
import re
import time
import random
from uuid import uuid4
from .config import relative, template_fields
from .http import request
from .media import attachment, avatar
from .model import AlertError, sanitize, safe_url

class DeliveryError(AlertError):
    def __init__(self, message, uncertain=False, retryable=False, retry_after=0):
        super().__init__(message)
        self.uncertain, self.retryable, self.retry_after = uncertain, retryable, retry_after

def payload(root, ch, post, use_template=True, validate_avatar=True):
    text = relative(root, ch["template"]).read_text(encoding="utf-8") if use_template else "{VIDEO_URL}"
    template_fields(text)
    url = "<" + post.url + ">" if ch["preview"] == "disabled" else post.url
    values = {"VIDEO_URL": url, "VIDEO_TITLE": sanitize(post.title), "CHANNEL_NAME": sanitize(post.channel_name), "PLATFORM": {"youtube": "YouTube", "tiktok": "TikTok"}[post.platform], "PUBLISHED_AT": post.published_at or ""}
    content = text.format_map(values)
    role = ch["role"]["id"] if ch["role"]["enabled"] else None
    if role:
        content = f"<@&{role}>\n" + content
    if len(content) > 2000:
        raise AlertError("Rendered Discord message exceeds 2000 characters")
    out = {"content": content, "username": ch["username"], "allowed_mentions": {"parse": [], "roles": [role] if role else [], "users": [], "replied_user": False}}
    av = avatar(ch["avatar_url"], ch["avatar_fallback"]) if validate_avatar else None
    if av:
        out["avatar_url"] = av
    if ch["preview"] == "disabled":
        out["flags"] = 4  # SUPPRESS_EMBEDS
    elif ch["embed"]["enabled"]:
        out["embeds"] = [{"title": sanitize(post.title)[:256] or "New video", "url": post.url, "color": ch["embed"]["color"]}]
    media = attachment(root, ch["media"])
    if media:
        out["attachments"] = [{"id": 0, "filename": media["name"]}]
    return out, media

def wire(payload_value, media):
    if not media:
        return json.dumps(payload_value, ensure_ascii=False).encode(), "application/json"
    boundary = "alerts-" + uuid4().hex
    data = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"payload_json\"\r\nContent-Type: application/json\r\n\r\n".encode() + json.dumps(payload_value, ensure_ascii=False).encode() + f"\r\n--{boundary}\r\nContent-Disposition: form-data; name=\"files[0]\"; filename=\"{media['name']}\"\r\nContent-Type: {media['mime']}\r\n\r\n".encode() + media["raw"] + f"\r\n--{boundary}--\r\n".encode())
    return data, "multipart/form-data; boundary=" + boundary

class DiscordClient:
    def __init__(self, webhook, retry, transport=request, sleep=time.sleep):
        u = safe_url(webhook, {"discord.com"})
        if u.query or not re.fullmatch(r"/api(?:/v10)?/webhooks/[1-9]\d{16,19}/[A-Za-z0-9_-]{30,}", u.path):
            raise AlertError("Invalid Discord webhook URL; value withheld")
        self._url, self.retry, self.transport, self.sleep = webhook, retry, transport, sleep

    def send(self, value, media=None):
        return self._perform("POST", self._url + "?wait=true", value, media)

    def edit(self, message_id, value, media=None):
        self._message_id(message_id)
        return self._perform("PATCH", self._url + "/messages/" + message_id, value, media)

    def delete(self, message_id):
        self._message_id(message_id)
        return self._perform("DELETE", self._url + "/messages/" + message_id, None, None)

    def lookup(self, message_id):
        self._message_id(message_id)
        response = self.transport("GET", self._url + "/messages/" + message_id)
        if response.status != 200:
            raise AlertError(f"Cannot verify existing Discord message: HTTP {response.status}")
        result = response.json()
        if not isinstance(result, dict) or result.get("id") != message_id or not isinstance(result.get("content"), str):
            raise AlertError("Existing Discord message response identity invalid")
        return result

    def _message_id(self, value):
        if not isinstance(value, str) or not re.fullmatch(r"[1-9]\d{16,19}", value):
            raise AlertError("Invalid Discord message ID")

    def _perform(self, method, url, value, media):
        body, content_type = wire(value, media) if value is not None else (None, "application/json")
        for attempt in range(self.retry["attempts"]):
            try:
                response = self.transport(method, url, body, {"Content-Type": content_type})
            except AlertError:
                raise DeliveryError("Discord delivery uncertain after network failure", uncertain=True) from None
            if method == "DELETE" and response.status in {204, 404}:
                return None
            if response.status == 200:
                try:
                    result = response.json()
                    self._message_id(result.get("id"))
                    return result["id"]
                except (AlertError, AttributeError, KeyError, TypeError):
                    raise DeliveryError("Discord acknowledgement invalid; delivery uncertain", uncertain=True) from None
            if response.status == 429:
                try:
                    delay = max(float(response.json().get("retry_after", 1)), float(response.headers.get("Retry-After", 0)), 0)
                    if not 0 <= delay < 86400:
                        raise ValueError()
                except (AlertError, TypeError, ValueError):
                    delay = 60
                if attempt + 1 == self.retry["attempts"] or delay > self.retry["max_seconds"]:
                    raise DeliveryError("Discord rate limit deferred", retryable=True, retry_after=delay)
                self.sleep(delay + random.uniform(0, 0.2))
                continue
            if response.status >= 500 or response.status in {408, 200, 204}:
                raise DeliveryError(f"Discord HTTP {response.status}; delivery uncertain", uncertain=True)
            raise DeliveryError(f"Discord permanently rejected message: HTTP {response.status}")
        raise DeliveryError("Discord retry budget exhausted", retryable=True)

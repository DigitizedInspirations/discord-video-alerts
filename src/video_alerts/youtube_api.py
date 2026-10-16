"""Public YouTube Data API metadata. Secrets stay in request headers, never URLs/state."""
import copy
import math
import re
import time
from urllib.parse import urlencode

from .http import request
from .model import AlertError, Post, date, stamp, video_url

ENDPOINT = "https://www.googleapis.com/youtube/v3/videos"
FIELDS = "items(id,snippet(channelId,channelTitle,title,publishedAt,liveBroadcastContent),status(privacyStatus,uploadStatus),liveStreamingDetails(actualStartTime,actualEndTime,scheduledStartTime))"
MAX_REQUESTS_PER_RUN = 6
UNAVAILABLE = "YouTube API metadata unavailable for this video"


class YouTubeAPI:
    """One instance per adapters()/run; bounded retries and positive/negative run cache."""

    def __init__(self, key, retry, transport=None, sleep=None):
        self._key = key
        self.retry = retry
        self.transport = transport or request
        self.sleep = sleep or time.sleep
        self.requests = 0
        self.cache = {}
        self.errors = {}
        self.terminal_error = None

    def _fail(self, message, terminal=False):
        if terminal:
            self.terminal_error = message
        raise AlertError(message) from None

    def _batch(self, ids):
        if not isinstance(self._key, str) or not self._key.strip():
            self._fail("YouTube API key is not configured", terminal=True)
        if any(ord(char) < 33 or ord(char) > 126 for char in self._key):
            self._fail("YouTube API credentials invalid or access restricted", terminal=True)
        url = ENDPOINT + "?" + urlencode({"part": "snippet,status,liveStreamingDetails",
                                          "id": ",".join(ids), "fields": FIELDS})
        for attempt in range(self.retry["attempts"]):
            if self.requests >= MAX_REQUESTS_PER_RUN:
                self._fail("YouTube API per-run request budget exhausted", terminal=True)
            self.requests += 1
            response = None
            try:
                response = self.transport("GET", url, headers={"X-Goog-Api-Key": self._key})
            except Exception:
                # No urllib/SDK exception text or chained exception can contain the key.
                pass
            if response is not None:
                if response.status == 200:
                    try:
                        body = response.json()
                        if not isinstance(body, dict) or "error" in body or not isinstance(body.get("items"), list):
                            raise ValueError()
                        found = {}
                        for item in body["items"]:
                            if not isinstance(item, dict) or item.get("id") not in ids or item["id"] in found:
                                raise ValueError()
                            found[item["id"]] = item
                        return found
                    except (AlertError, ValueError, KeyError, TypeError):
                        self._fail("YouTube API returned invalid metadata")
                if response.status in {400, 401, 403}:
                    quota = False
                    try:
                        errors = response.json()["error"]["errors"]
                        quota = any(item.get("reason") in {"quotaExceeded", "dailyLimitExceeded", "userRateLimitExceeded", "rateLimitExceeded"} for item in errors if isinstance(item, dict))
                    except (AlertError, KeyError, TypeError, AttributeError):
                        pass
                    self._fail("YouTube API quota/rate limit reached" if quota else "YouTube API credentials invalid or access restricted", terminal=True)
                if response.status not in {429, 500, 502, 503, 504}:
                    self._fail("YouTube API request rejected; no redirect followed")
            if attempt + 1 == self.retry["attempts"]:
                self._fail("YouTube API temporarily unavailable; retry budget exhausted")
            delay = min(self.retry["max_seconds"], self.retry["base_seconds"] * 2**attempt)
            if response is not None and response.status == 429:
                try:
                    requested_delay = float(response.headers.get("Retry-After", delay))
                    if not math.isfinite(requested_delay) or not 0 <= requested_delay <= self.retry["max_seconds"]:
                        self._fail("YouTube API rate limited beyond retry budget", terminal=True)
                    delay = max(delay, requested_delay)
                except (TypeError, ValueError):
                    pass
                if not 0 <= delay <= self.retry["max_seconds"]:
                    self._fail("YouTube API rate limited beyond retry budget", terminal=True)
            self.sleep(delay)
        self._fail("YouTube API metadata request failed")

    def prefetch(self, ids):
        pending = []
        for pid in ids:
            if not isinstance(pid, str) or not re.fullmatch(r"[A-Za-z0-9_-]{11}", pid):
                raise AlertError("Invalid YouTube API video ID")
            if pid not in self.cache and pid not in self.errors and pid not in pending:
                pending.append(pid)
        for offset in range(0, len(pending), 50):
            batch = pending[offset:offset + 50]
            if self.terminal_error:
                for pid in batch:
                    self.errors[pid] = self.terminal_error
                continue
            try:
                found = self._batch(batch)
            except AlertError as exc:
                for pid in batch:
                    self.errors[pid] = str(exc)
                continue
            for pid in batch:
                if pid in found:
                    self.cache[pid] = copy.deepcopy(found[pid])
                else:
                    self.errors[pid] = UNAVAILABLE

    def get(self, pid):
        self.prefetch([pid])
        if pid in self.errors:
            raise AlertError(self.errors[pid])
        return copy.deepcopy(self.cache[pid])


def from_api(item, post, ch):
    """Require independent API video/channel proof; never trust RSS identity alone."""
    pid, url = video_url(post.url, "youtube")
    if not isinstance(item, dict) or post.platform != "youtube" or pid != post.post_id or item.get("id") != pid:
        raise AlertError("YouTube API video identity mismatch")
    try:
        snippet, status = item["snippet"], item["status"]
        owner = snippet["channelId"]
        if not ch["channel_id"] or owner != ch["channel_id"]:
            raise AlertError("YouTube API channel identity mismatch")
        published = stamp(date(snippet["publishedAt"]))
        live = snippet["liveBroadcastContent"]
        privacy, upload = status["privacyStatus"], status["uploadStatus"]
        if live not in {"none", "live", "upcoming"} or privacy not in {"public", "private", "unlisted"} or upload not in {"processed", "uploaded", "failed", "rejected", "deleted"}:
            raise ValueError()
        details = item.get("liveStreamingDetails", {})
        if not isinstance(details, dict):
            raise ValueError()
        for name in ("actualStartTime", "actualEndTime", "scheduledStartTime"):
            if name in details:
                date(details[name])
        is_broadcast = live in {"live", "upcoming"} or bool(details)
        upcoming = live == "upcoming" or ("scheduledStartTime" in details and "actualStartTime" not in details)
        public = privacy == "public" and upload == "processed" and not upcoming
        title, channel = snippet.get("title", ""), snippet.get("channelTitle", ch["account"])
        if not isinstance(title, str) or not isinstance(channel, str):
            raise ValueError()
        # Data API has no reliable Shorts/historical-premiere flag. Keep unknowns.
        return Post("youtube", post.source_id, pid, url, title, channel, published,
                    "livestream" if is_broadcast else "unknown", public, None, owner)
    except (KeyError, TypeError, ValueError, AttributeError):
        raise AlertError("YouTube API metadata incomplete or malformed") from None

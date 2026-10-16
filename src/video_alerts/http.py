import json
import socket
import time
import random
import urllib.request
import urllib.error
from dataclasses import dataclass
from .model import AlertError

@dataclass
class Response:
    status: int
    body: bytes
    headers: dict

    def json(self):
        try:
            return json.loads(self.body)
        except (ValueError, UnicodeError):
            raise AlertError("Remote response is not valid JSON") from None

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

def request(method, url, body=None, headers=None, limit=6_000_000):
    h = {"User-Agent": "DiscordVideoAlerts/0.1 (public metadata only)", **(headers or {})}
    req = urllib.request.Request(url, data=body, headers=h, method=method)
    try:
        with urllib.request.build_opener(NoRedirect).open(req, timeout=25) as res:
            data = res.read(limit + 1)
            if len(data) > limit:
                raise AlertError("Remote response exceeds size limit")
            return Response(res.status, data, dict(res.headers))
    except urllib.error.HTTPError as exc:
        return Response(exc.code, exc.read(min(limit, 100_000)), dict(exc.headers))
    except (urllib.error.URLError, OSError, socket.timeout):
        raise AlertError("Network request failed; remote details withheld") from None

def public_get(url, retry, transport=request, sleep=time.sleep):
    for attempt in range(retry["attempts"]):
        try:
            response = transport("GET", url)
        except AlertError:
            if attempt + 1 == retry["attempts"]:
                raise
        else:
            if response.status == 200:
                return response
            if response.status not in {429, 500, 502, 503, 504}:
                raise AlertError(f"Public source HTTP {response.status}")
            if attempt + 1 == retry["attempts"]:
                raise AlertError(f"Source retries exhausted: HTTP {response.status}")
        delay = min(retry["max_seconds"], retry["base_seconds"] * 2**attempt + random.random())
        if 'response' in locals() and response.status == 429:
            try:
                delay = float(response.headers.get("Retry-After", delay))
            except ValueError:
                pass
            if delay > retry["max_seconds"]:
                raise AlertError("Source rate limited beyond retry budget")
        sleep(max(0, delay))
    raise AlertError("Source request failed")

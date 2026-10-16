"""Exact, approved disposable-branch fence around the real GitHubStore transport."""
import copy
import json
import re
from urllib.parse import parse_qs, urlsplit

from .http import request
from .model import AlertError
from .state import GitHubStore

REPOSITORY = "DigitizedInspirations/discord-video-alerts"
APPROVED_BRANCH = "dva-canary-20261016-0f9d3a7c"
BASE = "https://api.github.com/repos/" + REPOSITORY
MARKER = "canary-checkpoint.json"
PREFIX = "DVA CANARY " + APPROVED_BRANCH + ": "


class CanaryTransport:
    def __init__(self, branch, *, initialize=False, transport=None):
        if branch != APPROVED_BRANCH:
            raise AlertError("Canary target does not match the exact approved branch")
        self._branch = APPROVED_BRANCH
        self._initialize = initialize
        self._transport = transport or request
        self._checkpoints = set()
        self._bootstrap = None
        self._created = False
        self.last_commit = None
        self.trace = []
        self.commits = []

    def __call__(self, method, url, body=None, headers=None, **kwargs):
        if self._branch != APPROVED_BRANCH:
            raise AlertError("Canary branch fence changed; all requests refused")
        parsed = urlsplit(url)
        if parsed.scheme != "https" or parsed.netloc != "api.github.com" or not url.startswith(BASE + "/") and url != BASE:
            raise AlertError("Canary repository/host isolation failed")
        path = parsed.path.removeprefix("/repos/"+REPOSITORY)
        if parsed.fragment or parsed.username or parsed.password:
            raise AlertError("Canary URL isolation failed")
        query = parse_qs(parsed.query, keep_blank_values=True)
        data = None
        if body is not None:
            try:
                data = json.loads(body)
            except (ValueError, TypeError):
                raise AlertError("Canary request body invalid") from None
        allowed = False
        if method == "GET" and body is None:
            if path in {"/contents/state.json", "/contents/"+MARKER}:
                refs = query.get("ref")
                allowed = set(query) == {"ref"} and refs is not None and len(refs) == 1 and (refs[0] == self._branch or path.endswith("state.json") and refs[0] in self._checkpoints)
            elif not query:
                allowed = path == "/git/ref/heads/"+self._branch
                if self._initialize and not self._created:
                    allowed = allowed or path in {"", "/git/ref/heads/main"}
                if re.fullmatch(r"/commits/[a-f0-9]{40}", path):
                    allowed = True  # commit metadata only; state reads still require approval below
                if re.fullmatch(r"/compare/[a-f0-9]{40}\.\.\."+re.escape(self._branch), path):
                    allowed = True
        elif method == "POST" and path == "/git/refs" and not query and self._initialize and not self._created:
            allowed = isinstance(data, dict) and set(data) == {"ref", "sha"} and data["ref"] == "refs/heads/"+self._branch and self._bootstrap is not None and data["sha"] == self._bootstrap
        elif method == "PUT" and path in {"/contents/state.json", "/contents/"+MARKER} and not query:
            allowed = isinstance(data, dict) and data.get("branch") == self._branch and set(data) <= {"branch", "message", "sha", "content"} and {"branch", "message", "content"} <= set(data)
            if allowed:
                data = copy.deepcopy(data)
                data["message"] = PREFIX + str(data["message"]) + " [skip ci]"
                body = json.dumps(data).encode("utf-8")
        if not allowed:
            raise AlertError("Canary API request blocked by exact branch/path isolation")
        try:
            response = self._transport(method, url, body, headers or {}, **kwargs)
        except Exception:
            raise AlertError("Canary transport failed; outcome must be reconciled by fresh read") from None
        self.trace.append({"method": method, "path": path, "ref": query.get("ref", [None])[0], "status": response.status})
        if method == "GET" and path == "/git/ref/heads/main" and response.status == 200:
            self._bootstrap = response.json()["object"]["sha"]
        if method == "POST" and response.status == 201:
            self._created = True
        if method == "PUT" and response.status in {200, 201}:
            commit = response.json().get("commit", {}).get("sha")
            if not isinstance(commit, str) or not re.fullmatch(r"[a-f0-9]{40}", commit):
                raise AlertError("Canary write acknowledgement lacks commit SHA; reload before proceeding")
            self.last_commit = commit
            self.commits.append(commit)
        return response

    def store(self, token):
        return GitHubStore(REPOSITORY, token, transport=self, branch=APPROVED_BRANCH)

    def approve_checkpoint(self, store, sha):
        if not isinstance(sha, str) or not re.fullmatch(r"[a-f0-9]{40}", sha):
            raise AlertError("Canary checkpoint must be a full commit SHA")
        commit = store.api("GET", "/commits/"+sha)
        if commit.status != 200 or not commit.json().get("commit", {}).get("message", "").startswith(PREFIX):
            raise AlertError("Canary checkpoint provenance unverified")
        compare = store.api("GET", "/compare/"+sha+"..."+self._branch)
        if compare.status != 200 or compare.json().get("status") not in {"ahead", "identical"}:
            raise AlertError("Canary checkpoint is not on the approved branch history")
        self._checkpoints.add(sha)

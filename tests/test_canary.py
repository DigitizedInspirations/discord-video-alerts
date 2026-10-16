import base64
import copy
import hashlib
import json
import os
import runpy
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

import yaml

from video_alerts.canary import APPROVED_BRANCH, BASE, MARKER, PREFIX, REPOSITORY, CanaryTransport
from video_alerts.http import Response
from video_alerts.model import AlertError
from video_alerts.state import GitHubStore

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = runpy.run_path(str(ROOT/"scripts/durable_canary.py"))


class GitHubFixture:
    """In-memory GitHub API: real store/guard/phase code, no network or secrets."""
    def __init__(self):
        self.counter = 1
        self.root = "0"*39+"1"
        self.branches = {"main": [self.root]}
        self.snapshots = {self.root: {}}
        self.messages = {self.root: "Unrelated main commit"}
        self.calls = []

    def __call__(self, method, url, body=None, headers=None, **kwargs):
        path = urlsplit(url).path.removeprefix("/repos/"+REPOSITORY)
        query = parse_qs(urlsplit(url).query)
        data = json.loads(body) if body else None
        self.calls.append((method, path, query, data))
        status, answer = 200, {}
        if method == "GET" and not path:
            answer = {"default_branch": "main"}
        elif method == "GET" and path.startswith("/git/ref/heads/"):
            branch = path.removeprefix("/git/ref/heads/")
            if branch not in self.branches:
                status = 404
            else:
                answer = {"object": {"sha": self.branches[branch][-1]}}
        elif method == "POST" and path == "/git/refs":
            branch = data["ref"].removeprefix("refs/heads/")
            if branch in self.branches:
                status = 422
            else:
                self.branches[branch] = [data["sha"]]
                status = 201
        elif method == "GET" and path.startswith("/contents/"):
            ref = query["ref"][0]
            commit = self.branches[ref][-1] if ref in self.branches else ref
            raw = self.snapshots.get(commit, {}).get(path.removeprefix("/contents/"))
            if raw is None:
                status = 404
            else:
                answer = {"content": base64.b64encode(raw).decode(), "sha": hashlib.sha1(raw).hexdigest()}
        elif method == "PUT" and path.startswith("/contents/"):
            branch = data["branch"]
            if branch not in self.branches:
                status = 404
            else:
                previous = self.branches[branch][-1]
                files = copy.deepcopy(self.snapshots[previous])
                name = path.removeprefix("/contents/")
                old = files.get(name)
                if old is not None and data.get("sha") != hashlib.sha1(old).hexdigest() or old is None and "sha" in data:
                    status = 409
                else:
                    raw = base64.b64decode(data["content"])
                    files[name] = raw
                    self.counter += 1
                    commit = hashlib.sha1(str(self.counter).encode()).hexdigest()
                    self.snapshots[commit] = files
                    self.messages[commit] = data["message"]
                    self.branches[branch].append(commit)
                    answer = {"content": {"sha": hashlib.sha1(raw).hexdigest()}, "commit": {"sha": commit}}
                    status = 200 if old is not None else 201
        elif method == "GET" and path.startswith("/commits/"):
            sha = path.removeprefix("/commits/")
            if sha not in self.messages:
                status = 404
            else:
                answer = {"commit": {"message": self.messages[sha]}}
        elif method == "GET" and path.startswith("/compare/"):
            sha, branch = path.removeprefix("/compare/").split("...")
            history = self.branches.get(branch, [])
            answer = {"status": "identical" if history and sha == history[-1] else "ahead" if sha in history else "diverged"}
        else:
            raise AssertionError("Unexpected fixture API route")
        return Response(status, json.dumps(answer).encode(), {})


class CanaryTests(unittest.TestCase):
    def setUp(self):
        self.remote = GitHubFixture()
        self.guard = CanaryTransport(APPROVED_BRANCH, initialize=True, transport=self.remote)

    def test_production_default_unchanged_and_alternative_requires_canary_prefix(self):
        self.assertEqual(GitHubStore(REPOSITORY, "synthetic").BRANCH, "notification-state")
        self.assertEqual(self.guard.store("synthetic").BRANCH, APPROVED_BRANCH)
        for branch in ("main", "notification-state", "", "dva-canary-../main", None):
            if branch is None:
                continue
            with self.subTest(branch=branch), self.assertRaises(AlertError):
                GitHubStore(REPOSITORY, "synthetic", branch=branch)

    def test_exact_branch_required_before_any_api(self):
        for branch in ("main", "notification-state", "dva-canary-another-branch", "", None):
            with self.subTest(branch=branch), self.assertRaises(AlertError):
                CanaryTransport(branch, transport=self.remote)
        self.assertEqual(self.remote.calls, [])

    def test_all_wrong_state_read_refs_and_write_targets_blocked(self):
        store = self.guard.store("synthetic")
        for path in ("/contents/state.json?ref=main", "/contents/state.json?ref=notification-state",
                     "/contents/state.json?ref="+"a"*40, "/contents/state.json", "/contents/state.json?ref="+APPROVED_BRANCH+"&ref=main"):
            with self.subTest(path=path), self.assertRaises(AlertError):
                store.api("GET", path)
        for branch in ("main", "notification-state", "dva-canary-other-branch"):
            with self.subTest(branch=branch), self.assertRaises(AlertError):
                store.api("PUT", "/contents/state.json", {"branch": branch, "message": "bad", "content": "e30="})
        self.assertEqual(self.remote.calls, [])

    def test_instance_branch_or_host_mutation_cannot_escape_transport(self):
        store = self.guard.store("synthetic")
        store.BRANCH = "notification-state"
        with self.assertRaises(AlertError):
            store.load()
        store.base = "https://other.invalid/repos/"+REPOSITORY
        with self.assertRaises(AlertError):
            store.api("GET", "/contents/state.json?ref="+APPROVED_BRANCH)
        self.guard._branch = "notification-state"
        with self.assertRaises(AlertError):
            self.guard("GET", BASE)
        self.assertEqual(self.remote.calls, [])

    def test_initialization_only_creates_exact_branch_once(self):
        store = self.guard.store("synthetic")
        store.initialize()
        self.assertEqual(set(self.remote.branches), {"main", APPROVED_BRANCH})
        self.assertEqual(self.remote.snapshots[self.remote.root], {})
        with self.assertRaises(AlertError):
            store.initialize()
        posts = [call for call in self.remote.calls if call[0] == "POST"]
        self.assertEqual(len(posts), 1)
        self.assertEqual(posts[0][3]["ref"], "refs/heads/"+APPROVED_BRANCH)

    def test_verify_cannot_initialize_missing_branch_or_fall_back(self):
        guard = CanaryTransport(APPROVED_BRANCH, transport=self.remote)
        store = guard.store("synthetic")
        with self.assertRaises(AlertError):
            store.load()
        with self.assertRaises(AlertError):
            store.initialize()
        self.assertFalse(any(call[0] in {"PUT", "POST"} for call in self.remote.calls))
        self.assertFalse(any("notification-state" in call[1] for call in self.remote.calls))

    def test_repository_default_branch_drift_fails_before_create(self):
        def drift(method, url, body=None, headers=None, **kwargs):
            if url == BASE:
                return Response(200, b'{"default_branch":"notification-state"}', {})
            return self.remote(method, url, body, headers, **kwargs)
        store = CanaryTransport(APPROVED_BRANCH, initialize=True, transport=drift).store("synthetic")
        with self.assertRaises(AlertError):
            store.initialize()
        self.assertFalse(any(call[0] in {"PUT", "POST"} for call in self.remote.calls))

    def test_delete_force_push_and_unrelated_paths_blocked(self):
        store = self.guard.store("synthetic")
        for method, path in (("DELETE", "/contents/state.json"), ("PATCH", "/git/refs/heads/"+APPROVED_BRANCH),
                             ("PUT", "/contents/other.json"), ("POST", "/git/refs")):
            with self.subTest(method=method, path=path), self.assertRaises(AlertError):
                store.api(method, path, {"branch": APPROVED_BRANCH, "message": "bad", "content": "e30="})
        self.assertEqual(self.remote.calls, [])

    def test_checkpoint_requires_canary_commit_provenance_and_branch_ancestry(self):
        store = self.guard.store("synthetic")
        store.initialize()
        checkpoint = self.guard.last_commit
        self.guard.approve_checkpoint(store, checkpoint)
        self.assertIsInstance(store.load(checkpoint), dict)
        with self.assertRaises(AlertError):
            self.guard.approve_checkpoint(store, self.remote.root)
        unrelated = "f"*40
        self.remote.messages[unrelated] = PREFIX+"forged"
        with self.assertRaises(AlertError):
            self.guard.approve_checkpoint(store, unrelated)
        with self.assertRaises(AlertError):
            store.load(unrelated)

    def test_two_fresh_instances_execute_complete_real_store_protocol(self):
        seed = SCRIPT["execute"]("seed", self.guard, "synthetic", "101", "a"*40)
        self.assertEqual(seed["passed"], 4)
        fresh = CanaryTransport(APPROVED_BRANCH, transport=self.remote)
        verified = SCRIPT["execute"]("verify", fresh, "synthetic", "202", "a"*40, "101")
        self.assertEqual(verified["failed"], 0)
        self.assertGreaterEqual(verified["passed"], 10)
        self.assertTrue(verified["branch_retained"])
        self.assertEqual(verified["phase"], "verify")
        self.assertEqual(self.remote.snapshots[self.remote.root], {})
        writes = [call for call in self.remote.calls if call[0] == "PUT"]
        self.assertTrue(all(call[3]["branch"] == APPROVED_BRANCH for call in writes))
        for call in self.remote.calls:
            if call[1].startswith("/contents/") and call[0] == "GET":
                self.assertNotIn(call[2]["ref"][0], {"main", "notification-state"})

    def test_second_verify_or_same_run_fails_before_writes(self):
        SCRIPT["execute"]("seed", self.guard, "synthetic", "101", "a"*40)
        for run_id, source, seed in (("101", "a"*40, "101"), ("202", "b"*40, "101"), ("202", "a"*40, "999")):
            before = len(self.remote.calls)
            with self.subTest(run_id=run_id, seed=seed), self.assertRaises(AlertError):
                SCRIPT["execute"]("verify", CanaryTransport(APPROVED_BRANCH, transport=self.remote), "synthetic", run_id, source, seed)
            self.assertFalse(any(call[0] in {"PUT", "POST"} for call in self.remote.calls[before:]))
        SCRIPT["execute"]("verify", CanaryTransport(APPROVED_BRANCH, transport=self.remote), "synthetic", "202", "a"*40, "101")
        before = len(self.remote.calls)
        with self.assertRaises(AlertError):
            SCRIPT["execute"]("verify", CanaryTransport(APPROVED_BRANCH, transport=self.remote), "synthetic", "303", "a"*40, "101")
        self.assertFalse(any(call[0] in {"PUT", "POST"} for call in self.remote.calls[before:]))

    def test_workflow_only_manual_single_write_job_and_no_service_secrets(self):
        workflow = yaml.load((ROOT/".github/workflows/durable-canary.yml").read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
        self.assertEqual(set(workflow["on"]), {"workflow_dispatch"})
        self.assertEqual(workflow["permissions"], {"contents": "read"})
        job = workflow["jobs"]["canary"]
        self.assertEqual(job["permissions"], {"contents": "write"})
        self.assertNotIn("secrets.", json.dumps(workflow))
        self.assertIn("github.run_attempt == 1", job["if"])
        keyed = [step for step in job["steps"] if "GITHUB_TOKEN" in step.get("env", {})]
        self.assertEqual(len(keyed), 1)
        self.assertEqual(keyed[0]["run"], "python scripts/durable_canary.py")

    def test_runtime_guards_block_service_secrets_wrong_branch_and_reruns(self):
        env = {"GITHUB_REPOSITORY": REPOSITORY, "GITHUB_REF": "refs/heads/main", "GITHUB_SHA": "a"*40,
               "CANARY_EXPECTED_SHA": "a"*40, "CANARY_BRANCH": APPROVED_BRANCH,
               "GITHUB_RUN_ATTEMPT": "1", "GITHUB_RUN_ID": "101", "GITHUB_TOKEN": "synthetic"}
        with patch.dict(os.environ, env, clear=True):
            SCRIPT["guard_environment"]()
        for change in ({"DISCORD_WEBHOOK_URL": "synthetic"}, {"YOUTUBE_API_KEY": "synthetic"},
                       {"CANARY_BRANCH": "notification-state"}, {"GITHUB_REF": "refs/heads/"+APPROVED_BRANCH},
                       {"GITHUB_RUN_ATTEMPT": "2"}, {"GITHUB_SHA": "b"*40}):
            with self.subTest(keys=list(change)), patch.dict(os.environ, {**env, **change}, clear=True), self.assertRaises(AlertError):
                SCRIPT["guard_environment"]()


if __name__ == "__main__":
    unittest.main()

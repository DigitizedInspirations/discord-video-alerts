import base64
import copy
import hashlib
import importlib.util
import io
import json
import tempfile
import unittest
import urllib.error
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from urllib.parse import urlsplit

import yaml

from video_alerts.http import Response
from video_alerts.model import AlertError
from video_alerts.production_init import (BASE, BRANCH, CONFIRMATION, OPERATION, REPOSITORY,
    InitializationTransport, empty_state, guard_environment, initialize, inspect_failure, verify_initialized)
from video_alerts.state import decode, encode, new_state

ROOT = Path(__file__).resolve().parents[1]
SHA = "a" * 40


class CreationAPI:
    """Mock Git data API; models root tree/commit/ref and Contents retrieval."""
    def __init__(self):
        self.calls, self.trees, self.commits = [], {}, {}
        self.branch = None
        self.main = SHA
        self.repo = {"full_name": REPOSITORY, "default_branch": "main"}
        self.fail = self.lost_ack = None
        self.race = self.corrupt = False
        self.branch_reads = 0

    def __call__(self, method, url, body=None, headers=None, **kwargs):
        path = url.removeprefix(BASE)
        data = json.loads(body) if body else None
        self.calls.append((method, path, copy.deepcopy(data)))
        if self.fail == path:
            return Response(503, b"{}", {})
        status, value = 200, {}
        if method == "GET" and path == "":
            value = self.repo
        elif method == "GET" and path == "/git/ref/heads/main":
            value = {"object": {"sha": self.main}}
        elif method == "GET" and path == "/git/ref/heads/" + BRANCH:
            self.branch_reads += 1
            if self.race and self.branch_reads == 2:
                self.branch = "f" * 40
            status = 200 if self.branch else 404
            value = {"object": {"sha": self.branch}}
        elif method == "GET" and path == "/contents/state.json?ref=" + BRANCH:
            if not self.branch or self.branch not in self.commits:
                status = 404
            else:
                tree = self.trees[self.commits[self.branch]["tree"]["sha"]]
                raw = tree["raw"] + (b"bad" if self.corrupt else b"")
                value = {"content": base64.b64encode(raw).decode(), "sha": tree["tree"][0]["sha"]}
        elif method == "POST" and path == "/git/trees":
            raw = data["tree"][0]["content"].encode()
            blob = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
            sha = hashlib.sha1(b"tree" + raw).hexdigest()
            value = {"sha": sha, "truncated": False, "tree": [{"path": "state.json", "mode": "100644", "type": "blob", "sha": blob}]}
            self.trees[sha] = {**value, "raw": raw}
            status = 201
        elif method == "POST" and path == "/git/commits":
            sha = hashlib.sha1(json.dumps(data).encode()).hexdigest()
            value = {"sha": sha, "parents": data["parents"], "tree": {"sha": data["tree"]}}
            self.commits[sha] = value
            status = 201
        elif method == "POST" and path == "/git/refs":
            status = 422 if self.branch else 201
            if status == 201:
                self.branch = data["sha"]
            value = {"ref": data["ref"], "object": {"sha": self.branch}}
        elif method == "GET" and path.startswith("/git/commits/"):
            value = self.commits[path.rsplit("/", 1)[1]]
        elif method == "GET" and path.startswith("/git/trees/"):
            value = {k: v for k, v in self.trees[path.rsplit("/", 1)[1]].items() if k != "raw"}
        else:
            raise AssertionError("Unexpected route: " + method + " " + path)
        if method == "POST" and self.lost_ack == path:
            raise AlertError("Simulated lost acknowledgement")
        return Response(status, json.dumps(value).encode(), {})


class ProductionInitializationTests(unittest.TestCase):
    def setUp(self):
        self.api = CreationAPI()
        self.state = new_state()
        self.guard = InitializationTransport(SHA, "123", self.state, transport=self.api)

    def posts(self):
        return [call for call in self.api.calls if call[0] == "POST"]

    def test_atomic_state_only_creation_and_new_read_only_store_verification(self):
        result = initialize(self.guard, "synthetic")
        self.assertEqual((result["passed"], result["failed"]), (10, 0))
        self.assertEqual([call[1] for call in self.posts()], ["/git/trees", "/git/commits", "/git/refs"])
        self.assertEqual(self.posts()[1][2]["parents"], [])
        self.assertEqual(result["tree_paths"], ["state.json"])
        self.assertEqual(decode(self.api.trees[result["tree_sha"]]["raw"]), self.state)
        self.assertTrue(result["fresh_store_verified"])
        self.assertEqual((result["source_count"], result["record_count"]), (0, 0))
        self.assertEqual(self.api.branch, result["commit_sha"])
        self.assertEqual(self.api.main, SHA)
        self.assertTrue(all(urlsplit(BASE + path).netloc == "api.github.com" for _, path, _ in self.api.calls))

    def test_existing_branch_even_without_file_refuses_all_writes(self):
        self.api.branch = "b" * 40
        with self.assertRaises(AlertError):
            initialize(self.guard, "synthetic")
        self.assertEqual(self.posts(), [])

    def test_existing_file_with_missing_ref_refuses_all_writes(self):
        original = self.api
        def existing_file(method, url, *args, **kwargs):
            if url.endswith("/contents/state.json?ref=" + BRANCH):
                return Response(200, b"{}", {})
            return original(method, url, *args, **kwargs)
        self.guard.transport = existing_file
        with self.assertRaises(AlertError):
            initialize(self.guard, "synthetic")
        self.assertEqual(self.posts(), [])

    def test_inaccessible_branch_is_not_absence(self):
        self.api.fail = "/git/ref/heads/" + BRANCH
        with self.assertRaises(AlertError):
            initialize(self.guard, "synthetic")
        self.assertEqual(self.posts(), [])

    def test_repository_default_and_main_mismatch_refuse_before_writes(self):
        for change in ({"full_name": "wrong/repo"}, {"default_branch": "other"}, {"main": "b" * 40}):
            with self.subTest(change=change):
                api = CreationAPI()
                if "main" in change:
                    api.main = change["main"]
                else:
                    api.repo.update(change)
                guard = InitializationTransport(SHA, "123", self.state, transport=api)
                with self.assertRaises(AlertError):
                    initialize(guard, "synthetic")
                self.assertFalse(any(m == "POST" for m, _, _ in api.calls))

    def test_no_imports_or_source_baselines_allowed(self):
        for key in ("sources", "records"):
            state = copy.deepcopy(self.state)
            state[key]["synthetic"] = {}
            with self.subTest(key=key), self.assertRaises(AlertError):
                empty_state(state)

    def test_identity_must_be_uuid4(self):
        state = {**self.state, "instance_id": "canary-or-existing-identity"}
        with self.assertRaises(AlertError):
            InitializationTransport(SHA, "123", state, transport=self.api)

    def test_wrong_methods_hosts_branches_paths_and_checkpoint_reads_fenced(self):
        store = self.guard.store("synthetic")
        for method, path, data in (("PUT", "/contents/state.json", {}), ("PATCH", "/git/refs/heads/" + BRANCH, {}),
                                   ("DELETE", "/git/refs/heads/" + BRANCH, None),
                                   ("GET", "/contents/state.json?ref=main", None),
                                   ("GET", "/contents/state.json?ref=dva-canary-test", None),
                                   ("GET", "/contents/state.json?ref=" + BRANCH + "&ref=main", None),
                                   ("POST", "/git/refs", {"ref": "refs/heads/main", "sha": SHA})):
            with self.subTest(path=path), self.assertRaises(AlertError):
                store.api(method, path, data)
        with self.assertRaises(AlertError):
            self.guard("GET", "https://example.com/" + BASE)
        self.assertEqual(self.api.calls, [])

    def test_tree_cannot_include_extra_files_or_copy_base_tree(self):
        store = self.guard.store("synthetic")
        self.guard.preflight(store)
        for data in ({"base_tree": SHA, "tree": []}, {"tree": [{"path": "canary-checkpoint.json", "content": "synthetic"}]}):
            with self.subTest(data=data), self.assertRaises(AlertError):
                store.api("POST", "/git/trees", data)
        self.assertEqual(self.posts(), [])

    def test_failed_creation_stops_without_branch_publication_or_repair(self):
        for path, count in (("/git/trees", 1), ("/git/commits", 2)):
            api = CreationAPI()
            api.fail = path
            guard = InitializationTransport(SHA, "123", self.state, transport=api)
            with self.subTest(path=path), self.assertRaises(AlertError):
                initialize(guard, "synthetic")
            self.assertEqual(sum(m == "POST" for m, _, _ in api.calls), count)
            self.assertIsNone(api.branch)
            self.assertEqual(inspect_failure(guard, "synthetic")["branch_http"], 404)

    def test_lost_tree_ack_cannot_be_retried(self):
        self.api.lost_ack = "/git/trees"
        with self.assertRaises(AlertError):
            initialize(self.guard, "synthetic")
        with self.assertRaises(AlertError):
            initialize(self.guard, "synthetic")
        self.assertEqual(len(self.posts()), 1)
        self.assertIsNone(self.api.branch)

    def test_racing_branch_prevents_publication_without_overwrite(self):
        self.api.race = True
        with self.assertRaises(AlertError):
            initialize(self.guard, "synthetic")
        self.assertEqual([p[1] for p in self.posts()], ["/git/trees", "/git/commits"])
        self.assertEqual(self.api.branch, "f" * 40)

    def test_atomic_ref_creation_conflict_never_overwrites_or_retries(self):
        original = self.api
        def racing_ref(method, url, *args, **kwargs):
            if method == "POST" and url.endswith("/git/refs"):
                original.branch = "c" * 40
            return original(method, url, *args, **kwargs)
        self.guard.transport = racing_ref
        with self.assertRaises(AlertError):
            initialize(self.guard, "synthetic")
        self.assertEqual(self.api.branch, "c" * 40)
        self.assertEqual(sum(p[1] == "/git/refs" for p in self.posts()), 1)

    def test_malformed_tree_acknowledgement_stops_before_commit_or_ref(self):
        original = self.api
        def malformed(method, url, *args, **kwargs):
            response = original(method, url, *args, **kwargs)
            return Response(201, b'{"sha": null}', {}) if method == "POST" else response
        self.guard.transport = malformed
        with self.assertRaises(AlertError):
            initialize(self.guard, "synthetic")
        self.assertEqual(len(self.posts()), 1)
        self.assertIsNone(self.api.branch)

    def test_main_change_is_detected_by_independent_verification(self):
        initialize(self.guard, "synthetic")
        self.api.main = "b" * 40
        count = len(self.posts())
        with self.assertRaises(AlertError):
            verify_initialized(self.guard, "synthetic")
        self.assertEqual(len(self.posts()), count)

    def test_lost_ref_ack_is_inspected_read_only_and_never_republished(self):
        self.api.lost_ack = "/git/refs"
        with self.assertRaises(AlertError):
            initialize(self.guard, "synthetic")
        count = len(self.posts())
        result = inspect_failure(self.guard, "synthetic")
        self.assertTrue(result["empty_state_checksum_valid"])
        self.assertTrue(result["matches_attempted_state"])
        self.assertEqual(len(self.posts()), count)
        self.assertEqual(result["branch_commit"], self.guard.commit_sha)

    def test_repeated_initialization_refuses_after_success(self):
        initialize(self.guard, "synthetic")
        count = len(self.posts())
        repeat = InitializationTransport(SHA, "456", new_state(), transport=self.api)
        with self.assertRaises(AlertError):
            initialize(repeat, "synthetic")
        self.assertEqual(len(self.posts()), count)

    def test_fresh_verification_detects_corruption_without_writing(self):
        initialize(self.guard, "synthetic")
        self.api.corrupt = True
        count = len(self.posts())
        with self.assertRaises(AlertError):
            verify_initialized(self.guard, "synthetic")
        self.assertEqual(len(self.posts()), count)

    def test_fresh_verification_refuses_changed_commit(self):
        initialize(self.guard, "synthetic")
        self.api.branch = "b" * 40
        count = len(self.posts())
        with self.assertRaises(AlertError):
            verify_initialized(self.guard, "synthetic")
        self.assertEqual(len(self.posts()), count)

    def test_read_only_transport_cannot_be_upgraded_to_write(self):
        reader = InitializationTransport(SHA, "123", self.state, transport=self.api, read_only=True)
        reader.preflight(reader.store("synthetic"))
        with self.assertRaises(AlertError):
            initialize(reader, "synthetic")
        self.assertEqual(self.posts(), [])
        with self.assertRaises(AlertError):
            InitializationTransport(SHA, "123", self.state, tree_sha=SHA)

    def test_environment_exact_confirmations_no_secrets_no_reruns(self):
        env = {"GITHUB_REPOSITORY": REPOSITORY, "GITHUB_REF": "refs/heads/main", "GITHUB_EVENT_NAME": "workflow_dispatch",
               "GITHUB_RUN_ATTEMPT": "1", "GITHUB_RUN_ID": "123", "GITHUB_TOKEN": "synthetic",
               "GITHUB_SHA": SHA, "INIT_EXPECTED_SHA": SHA, "INIT_REPOSITORY": REPOSITORY,
               "INIT_BRANCH": BRANCH, "INIT_OPERATION": OPERATION, "INIT_CONFIRMATION": CONFIRMATION}
        with patch("video_alerts.production_init.load_config", return_value=SimpleNamespace(master_enabled=False)):
            self.assertEqual(guard_environment(env, ROOT), SHA)
            for change in ({"DISCORD_WEBHOOK_URL": ""}, {"YOUTUBE_API_KEY": ""}, {"GITHUB_RUN_ATTEMPT": "2"},
                           {"INIT_REPOSITORY": "wrong/repo"}, {"INIT_BRANCH": "main"}, {"INIT_OPERATION": "restore"},
                           {"INIT_CONFIRMATION": "wrong"}, {"GITHUB_REF": "refs/heads/" + BRANCH},
                           {"GITHUB_SHA": "b" * 40}, {"GITHUB_EVENT_NAME": "push"}, {"GITHUB_TOKEN": ""}):
                with self.subTest(change=list(change)), self.assertRaises(AlertError):
                    guard_environment({**env, **change}, ROOT)
            with tempfile.TemporaryDirectory() as folder:
                root = Path(folder)
                workflows = root / ".github/workflows"
                workflows.mkdir(parents=True)
                (workflows / "other.yml").write_text("on:\n  schedule: []\n", encoding="utf-8")
                with self.assertRaises(AlertError):
                    guard_environment(env, root)
        with patch("video_alerts.production_init.load_config", return_value=SimpleNamespace(master_enabled=True)), self.assertRaises(AlertError):
            guard_environment(env, ROOT)

    def test_manual_workflow_token_only_initialization_step_and_no_service_secrets(self):
        flow = yaml.load((ROOT / ".github/workflows/initialize-state.yml").read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
        self.assertEqual(set(flow["on"]), {"workflow_dispatch"})
        self.assertEqual(flow["permissions"], {"contents": "read"})
        self.assertEqual(set(flow["jobs"]), {"initialize"})
        job = flow["jobs"]["initialize"]
        self.assertEqual(job["permissions"], {"contents": "write"})
        self.assertIn("github.run_attempt == 1", job["if"])
        self.assertIn("refs/heads/main", job["if"])
        self.assertNotIn("secrets.", json.dumps(flow))
        self.assertNotIn("operate", json.dumps(flow))
        self.assertNotIn("env", flow)
        self.assertNotIn("env", job)
        steps = [step for step in job["steps"] if "GITHUB_TOKEN" in step.get("env", {})]
        self.assertEqual(len(steps), 1)
        self.assertEqual(steps[0]["run"], "python scripts/initialize_production_state.py")
        self.assertEqual(job["steps"][0]["with"]["persist-credentials"], "false")

    def controller(self, *, prior_runs=False, existing_branch=False):
        spec = importlib.util.spec_from_file_location("initialization_controller_test", ROOT / "scripts/github_control.py")
        controller = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(controller)
        posts = []
        def remote(req):
            path = req.full_url.removeprefix(BASE)
            if req.get_method() == "POST":
                posts.append((path, json.loads(req.data)))
                return io.BytesIO(b"")
            answers = {"/branches/main": {"commit": {"sha": SHA}},
                       "": {"full_name": REPOSITORY, "default_branch": "main"},
                       "/git/ref/heads/main": {"object": {"sha": SHA}},
                       "/actions/workflows/initialize-state.yml/runs?event=workflow_dispatch&per_page=1": {"workflow_runs": [{"id": 1}] if prior_runs else []}}
            if existing_branch:
                answers["/git/ref/heads/" + BRANCH] = {"object": {"sha": "b" * 40}}
            if path not in answers:
                if path in {"/git/ref/heads/" + BRANCH, "/contents/state.json?ref=" + BRANCH}:
                    raise urllib.error.HTTPError(req.full_url, 404, "missing", {}, None)
                raise AssertionError("Unexpected controller route")
            return io.BytesIO(json.dumps(answers[path]).encode())
        args = ["github_control.py", "dispatch", "--workflow", "initialize-state.yml",
                "--expected-sha", SHA, "--confirmation", CONFIRMATION]
        with patch.object(controller, "token", return_value="synthetic"), patch.object(controller, "open_private", side_effect=remote), patch("sys.argv", args), patch("builtins.print"):
            if prior_runs or existing_branch:
                with self.assertRaises(RuntimeError):
                    controller.main()
            else:
                controller.main()
        return posts

    def test_controller_dispatches_only_exact_approved_main_inputs(self):
        self.assertEqual(self.controller(), [("/actions/workflows/initialize-state.yml/dispatches", {
            "ref": "main", "inputs": {"repository": REPOSITORY, "branch": BRANCH,
            "operation": OPERATION, "confirmation": CONFIRMATION, "expected_sha": SHA}})])

    def test_controller_refuses_prior_dispatch_or_existing_branch(self):
        self.assertEqual(self.controller(prior_runs=True), [])
        self.assertEqual(self.controller(existing_branch=True), [])


if __name__ == "__main__":
    unittest.main()

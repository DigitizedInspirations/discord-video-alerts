import base64
import copy
import hashlib
import importlib.util
import io
import os
import shutil
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
from video_alerts.config import load_config
from video_alerts.initialization_authorization import AUTHORIZATION_ID, EXPECTED_RECORD, PREVIOUS_RUN, authorize_dispatch, validate_record

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
        with patch("video_alerts.production_init.load_config", return_value=load_config(ROOT)):
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
        with patch("video_alerts.production_init.load_config", return_value={**load_config(ROOT), "master_enabled": True}), self.assertRaises(AlertError):
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

    def controller(self, *, prior_runs=False, existing_branch=False, expect_failure=False):
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
                       "/actions/workflows/initialize-state.yml/runs?event=workflow_dispatch&per_page=100": {"workflow_runs": [{"id": PREVIOUS_RUN}, {"id": 999}] if prior_runs else [{"id": PREVIOUS_RUN}]},
                       "/actions/runs/" + str(PREVIOUS_RUN): {"id": PREVIOUS_RUN, "head_sha": EXPECTED_RECORD["previous_source_sha"],
                           "head_branch": "main", "status": "completed", "conclusion": "failure", "event": "workflow_dispatch",
                           "run_attempt": 1, "path": ".github/workflows/initialize-state.yml"}}
            if existing_branch:
                answers["/git/ref/heads/" + BRANCH] = {"object": {"sha": "b" * 40}}
            if path not in answers:
                if path in {"/git/ref/heads/" + BRANCH, "/contents/state.json?ref=" + BRANCH}:
                    raise urllib.error.HTTPError(req.full_url, 404, "missing", {}, None)
                raise AssertionError("Unexpected controller route")
            return io.BytesIO(json.dumps(answers[path]).encode())
        args = ["github_control.py", "dispatch", "--workflow", "initialize-state.yml",
                "--expected-sha", SHA, "--confirmation", CONFIRMATION, "--authorization-id", AUTHORIZATION_ID]
        with patch.object(controller, "token", return_value="synthetic"), patch.object(controller, "open_private", side_effect=remote), patch("sys.argv", args), patch("builtins.print"):
            if prior_runs or existing_branch or expect_failure:
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

    def test_controller_rechecks_master_using_actual_dict_contract_before_dispatch(self):
        with patch("video_alerts.production_init.load_config", return_value={**load_config(ROOT), "master_enabled": True}):
            self.assertEqual(self.controller(expect_failure=True), [])

    def environment(self):
        return {"GITHUB_REPOSITORY": REPOSITORY, "GITHUB_REF": "refs/heads/main", "GITHUB_EVENT_NAME": "workflow_dispatch",
                "GITHUB_RUN_ATTEMPT": "1", "GITHUB_RUN_ID": "123", "GITHUB_TOKEN": "synthetic",
                "GITHUB_SHA": SHA, "INIT_EXPECTED_SHA": SHA, "INIT_REPOSITORY": REPOSITORY,
                "INIT_BRANCH": BRANCH, "INIT_OPERATION": OPERATION, "INIT_CONFIRMATION": CONFIRMATION}

    def entrypoint(self):
        spec = importlib.util.spec_from_file_location("init_entrypoint_test", ROOT / "scripts/initialize_production_state.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def assert_local_failure_before_writer(self, root):
        module = self.entrypoint()
        output = io.StringIO()
        with patch.dict(os.environ, self.environment(), clear=True), patch.object(module, "ROOT", root), patch.object(module, "InitializationTransport") as writer, patch("sys.stdout", output):
            result = module.main()
        writer.assert_not_called()
        self.assertEqual(result, 1)
        report = json.loads(output.getvalue().removeprefix("DVA_REPORT "))
        self.assertEqual(report["phase"], "local_preflight")
        self.assertEqual(report["creation_requests_attempted"], 0)
        self.assertEqual(report["failed"], 1)
        self.assertNotIn("synthetic", output.getvalue())
        self.assertNotIn("sensitive-config-value", output.getvalue())
        return report

    def test_real_project_loader_master_off_regression_for_original_attribute_error(self):
        config = load_config(ROOT)
        self.assertIs(type(config), dict)
        self.assertIs(config["master_enabled"], False)
        self.assertEqual(guard_environment(self.environment(), ROOT), SHA)

    def test_entrypoint_real_configuration_and_authorization_with_only_network_mocked(self):
        module = self.entrypoint()
        output = io.StringIO()
        with patch.dict(os.environ, self.environment(), clear=True), patch.object(module, "InitializationTransport", return_value=self.guard), patch("sys.stdout", output):
            self.assertEqual(module.main(), 0)
        report = json.loads(output.getvalue().removeprefix("DVA_REPORT "))
        self.assertEqual(report["phase"], "complete")
        self.assertEqual(report["authorization_id"], AUTHORIZATION_ID)
        self.assertTrue(report["fresh_store_verified"])
        self.assertEqual(len(self.posts()), 3)

    def test_real_loader_master_on_invalid_missing_and_wrong_types_fail_before_writer(self):
        original = load_config(ROOT)
        invalid = [{**original, "master_enabled": value} for value in (True, 0, None, "sensitive-config-value")]
        invalid += [{k: v for k, v in original.items() if k != "master_enabled"}, {}, [], None, "sensitive-config-value", {**original, "unexpected": 1}]
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            shutil.copytree(ROOT / "config", root / "config")
            settings = root / "config/settings.json"
            self.assertIs(load_config(root)["master_enabled"], False)
            for config in invalid:
                with self.subTest(root_type=type(config).__name__, master=config.get("master_enabled") if isinstance(config, dict) else None):
                    settings.write_text(json.dumps(config), encoding="utf-8")
                    self.assert_local_failure_before_writer(root)

    def test_real_loader_missing_malformed_and_nonfinite_json_fail_before_writer(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            shutil.copytree(ROOT / "config", root / "config")
            settings = root / "config/settings.json"
            self.assertIs(load_config(root)["master_enabled"], False)
            settings.unlink()
            self.assert_local_failure_before_writer(root)
            for raw in ("{bad-json", "NaN", '{"master_enabled": NaN}'):
                with self.subTest(raw=raw):
                    settings.write_text(raw, encoding="utf-8")
                    self.assert_local_failure_before_writer(root)

    def test_unexpected_loader_contract_rejected_without_creation_or_attribute_error(self):
        for value in (None, [], False, 0, "sensitive-config-value", SimpleNamespace(master_enabled=False), {}, {"master_enabled": 0}):
            with self.subTest(value_type=type(value).__name__), patch("video_alerts.production_init.load_config", return_value=value):
                self.assert_local_failure_before_writer(ROOT)

    def test_creation_failure_diagnostic_phase_and_no_retry(self):
        module = self.entrypoint()
        self.api.lost_ack = "/git/trees"
        output = io.StringIO()
        with patch.dict(os.environ, self.environment(), clear=True), patch.object(module, "InitializationTransport", return_value=self.guard), patch("sys.stdout", output):
            self.assertEqual(module.main(), 1)
        report = json.loads(output.getvalue().removeprefix("DVA_REPORT "))
        self.assertEqual(report["phase"], "create_tree")
        self.assertEqual(report["creation_requests_attempted"], 1)
        self.assertEqual(len(self.posts()), 1)
        self.assertEqual(report["inspection"]["branch_http"], 404)
        self.assertTrue(report["no_retry_or_repair"])

    def test_retry_record_real_preserved_evidence_and_live_failed_run_required(self):
        previous = {"id": PREVIOUS_RUN, "head_sha": EXPECTED_RECORD["previous_source_sha"], "head_branch": "main",
                    "status": "completed", "conclusion": "failure", "event": "workflow_dispatch", "run_attempt": 1,
                    "path": ".github/workflows/initialize-state.yml"}
        self.assertEqual(authorize_dispatch(ROOT, AUTHORIZATION_ID, [{"id": PREVIOUS_RUN}], previous), EXPECTED_RECORD)
        for history in ([], [{"id": 999}], [{"id": PREVIOUS_RUN}, {"id": 999}]):
            with self.subTest(history=history), self.assertRaises(AlertError):
                authorize_dispatch(ROOT, AUTHORIZATION_ID, history, previous)
        for change in ({"conclusion": "success"}, {"head_sha": SHA}, {"run_attempt": 2}, {"head_branch": BRANCH}, {"status": "in_progress"}):
            with self.subTest(change=change), self.assertRaises(AlertError):
                authorize_dispatch(ROOT, AUTHORIZATION_ID, [{"id": PREVIOUS_RUN}], {**previous, **change})
        with self.assertRaises(AlertError):
            validate_record(ROOT, "unknown-approval")

    def test_retry_record_cannot_expand_scope_or_substitute_prior_evidence(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "docs/cloud").mkdir(parents=True)
            original = ROOT / f"docs/cloud/{PREVIOUS_RUN}-evidence.json"
            evidence = root / f"docs/cloud/{PREVIOUS_RUN}-evidence.json"
            evidence.write_bytes(original.read_bytes())
            record_path = root / "docs/initialization-retry-authorization.json"
            for change in ({"max_new_dispatches": 2}, {"allow_repair_or_overwrite": True}, {"schema_version": True}, {"branch": "main"}):
                with self.subTest(change=change), self.assertRaises(AlertError):
                    record_path.write_text(json.dumps({**EXPECTED_RECORD, **change}), encoding="utf-8")
                    validate_record(root, AUTHORIZATION_ID)
            record_path.write_text(json.dumps(EXPECTED_RECORD), encoding="utf-8")
            evidence.write_text("{}", encoding="utf-8")
            with self.assertRaises(AlertError):
                validate_record(root, AUTHORIZATION_ID)

    def test_retry_evidence_pin_has_identical_meaning_on_windows_and_linux(self):
        source = json.loads((ROOT / f"docs/cloud/{PREVIOUS_RUN}-evidence.json").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "docs/cloud").mkdir(parents=True)
            (root / "docs/initialization-retry-authorization.json").write_text(json.dumps(EXPECTED_RECORD), encoding="utf-8")
            path = root / f"docs/cloud/{PREVIOUS_RUN}-evidence.json"
            for newline in ("\n", "\r\n"):
                with self.subTest(newline=repr(newline)):
                    path.write_bytes(json.dumps(source, indent=2).replace("\n", newline).encode("utf-8"))
                    self.assertEqual(validate_record(root, AUTHORIZATION_ID), EXPECTED_RECORD)


if __name__ == "__main__":
    unittest.main()

import base64
import copy
import importlib.util
import io
import json
import os
import shutil
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import Mock, patch

import yaml

from video_alerts.config import SOURCES, load_config
from video_alerts.engine import Engine
from video_alerts.http import Response
from video_alerts.model import AlertError, Post, stamp
from video_alerts.production_baseline import (AUTHORIZATION, BASE, BRANCH, CONFIRMATION, HISTORY,
    INITIAL_BLOB, INITIAL_COMMIT, INITIAL_HASH, INITIAL_STATE, REPOSITORY, WORKFLOW,
    BaselineTransport, blob_sha, build_proposal, checksum, guard, load_initial, settings,
    validate_proposal, write_once)
from video_alerts.state import MemoryStore, decode, encode

ROOT = Path(__file__).resolve().parents[1]
SHA, RUN = "a" * 40, "54321"
NOW = datetime(2026, 10, 17, 0, 0, tzinfo=timezone.utc)


def environment(phase):
    result = {"GITHUB_REPOSITORY": REPOSITORY, "GITHUB_REF": "refs/heads/main",
        "GITHUB_EVENT_NAME": "workflow_dispatch", "GITHUB_RUN_ATTEMPT": "1", "GITHUB_RUN_ID": RUN,
        "GITHUB_SHA": SHA, "BASELINE_EXPECTED_SHA": SHA, "BASELINE_REPOSITORY": REPOSITORY,
        "BASELINE_BRANCH": BRANCH, "BASELINE_CONFIRMATION": CONFIRMATION, "BASELINE_AUTHORIZATION": AUTHORIZATION}
    result["YOUTUBE_API_KEY" if phase == "metadata" else "GITHUB_TOKEN"] = "mock-only"
    return result


class Adapter:
    def __init__(self, sid, cfg, api):
        ch = cfg["channels"][sid]
        pid = "abcdefghijk" if ch["platform"] == "youtube" else "1234567890123456789"
        url = "https://www.youtube.com/watch?v=" + pid if ch["platform"] == "youtube" else f"https://www.tiktok.com/@{ch['account']}/video/{pid}"
        self.posts = [Post(ch["platform"], sid, pid, url, published_at=stamp(NOW - timedelta(days=1)),
            owner_id=ch["channel_id"] or ch["account"], public=True)]
        self.api = api
        self.error = False

    def discover(self, sid):
        if self.error:
            raise AlertError("Simulated unavailable source")
        return copy.deepcopy(self.posts)

    def enrich(self, post):
        return copy.deepcopy(post)


class StateAPI:
    def __init__(self):
        self.raw = encode(INITIAL_STATE)
        self.head, self.blob = INITIAL_COMMIT, INITIAL_BLOB
        self.calls, self.count = [], 1
        self.fail, self.missing, self.corrupt, self.race, self.lost_ack, self.bad_ack = False, False, False, False, False, False
        self.result = "b" * 40

    def __call__(self, method, url, body=None, headers=None):
        path = url.removeprefix(BASE)
        self.calls.append((method, path))
        status = 200
        if method == "PUT":
            data = json.loads(body)
            if self.race or self.fail:
                return Response(409 if self.race else 503, b"{}", {})
            assert data["sha"] == self.blob and data["branch"] == BRANCH
            self.raw = base64.b64decode(data["content"])
            self.blob, self.head = blob_sha(self.raw), self.result
            if self.lost_ack:
                raise AlertError("Simulated lost acknowledgement")
            value = {"content": {"sha": "c" * 40 if self.bad_ack else self.blob}, "commit": {"sha": self.head}}
        elif path == "":
            value = {"full_name": REPOSITORY, "default_branch": "main"}
        elif path == "/git/ref/heads/main":
            value = {"object": {"sha": SHA}}
        elif path == "/git/ref/heads/" + BRANCH:
            value = {"object": {"sha": self.head}}
            status = 404 if self.missing else 200
        elif path == HISTORY:
            value = {"total_count": self.count, "workflow_runs": [{"id": int(RUN)}]}
        elif path == "/actions/runs/" + RUN:
            value = {"id": int(RUN), "head_sha": SHA, "head_branch": "main", "run_attempt": 1,
                     "event": "workflow_dispatch", "path": ".github/workflows/" + WORKFLOW}
        elif path == "/contents/state.json?ref=" + BRANCH:
            value = {"content": base64.b64encode(self.raw + (b"broken" if self.corrupt else b"")).decode(), "sha": self.blob}
        elif path == "/git/commits/" + self.result:
            value = {"sha": self.result, "parents": [{"sha": INITIAL_COMMIT}], "tree": {"sha": "d" * 40}}
        elif path == "/git/trees/" + "d" * 40:
            value = {"sha": "d" * 40, "truncated": False, "tree": [{"path": "state.json", "type": "blob", "mode": "100644", "sha": self.blob}]}
        else:
            raise AssertionError((method, path))
        return Response(status, json.dumps(value).encode(), {})


class BaselineTests(unittest.TestCase):
    def setUp(self):
        self.cfg = load_config(ROOT)
        self.api = Mock(requests=1)
        self.adapters = {sid: Adapter(sid, self.cfg, self.api) for sid in SOURCES}
        self.report = {}
        self.cloud = StateAPI()

    def proposal(self):
        return build_proposal(self.cfg, self.adapters, RUN, SHA, self.report, clock=lambda: NOW)

    def writer(self, proposal=None):
        return BaselineTransport(SHA, RUN, transport=self.cloud, proposal=proposal or self.proposal())

    def test_real_settings_and_exact_initialized_identity(self):
        self.assertFalse(settings(ROOT)["master_enabled"])
        self.assertEqual(checksum(INITIAL_STATE), INITIAL_HASH)
        self.assertEqual(blob_sha(encode(INITIAL_STATE)), INITIAL_BLOB)
        for phase in ("preflight", "metadata", "write"):
            self.assertEqual(guard(environment(phase), ROOT, phase), self.cfg)

    def test_real_config_master_guard_and_types(self):
        for value in (True, None, 0, "false"):
            with self.subTest(value=value), patch("video_alerts.production_baseline.load_config", return_value={**self.cfg, "master_enabled": value}):
                with self.assertRaises(AlertError):
                    guard(environment("write"), ROOT, "write")
        for value in (None, [], object()):
            with patch("video_alerts.production_baseline.load_config", return_value=value):
                with self.assertRaises(AlertError):
                    settings(ROOT)

    def test_real_config_missing_malformed_invalid_and_schedule_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shutil.copytree(ROOT / "config", root / "config")
            shutil.copytree(ROOT / ".github", root / ".github")
            path = root / "config/settings.json"
            raw = path.read_text(encoding="utf-8")
            self.assertEqual(settings(root), self.cfg)
            for data in ("{", "null", "[]", raw.replace('"master_enabled": false', '"master_enabled": true'),
                         raw.replace('"master_enabled": false', '"master_enabled": 0')):
                path.write_text(data, encoding="utf-8")
                with self.subTest(data=data[:20]), self.assertRaises((AlertError, ValueError, TypeError)):
                    guard(environment("write"), root, "write")
            path.unlink()
            with self.assertRaises((AlertError, OSError)):
                guard(environment("write"), root, "write")
            path.write_text(raw, encoding="utf-8")
            for suffix in (".yml", ".yaml"):
                unexpected = root / (".github/workflows/unexpected" + suffix)
                unexpected.write_text("on:\n  schedule: []\njobs: {}", encoding="utf-8")
                with self.assertRaises(AlertError):
                    guard(environment("write"), root, "write")
                unexpected.unlink()

    def test_secret_branch_review_and_rerun_guards(self):
        for key, value in {"GITHUB_REF": "refs/heads/other", "GITHUB_SHA": "f" * 40,
            "GITHUB_RUN_ATTEMPT": "2", "BASELINE_BRANCH": "main", "BASELINE_AUTHORIZATION": "other",
            "DISCORD_WEBHOOK_URL": "mock", "YOUTUBE_API_KEY": "mock"}.items():
            with self.subTest(key=key), self.assertRaises(AlertError):
                guard({**environment("write"), key: value}, ROOT, "write")
        with self.assertRaises(AlertError):
            guard({**environment("metadata"), "GITHUB_TOKEN": "mock"}, ROOT, "metadata")

    def test_normal_four_source_candidate_no_delivery_history(self):
        value = self.proposal()
        state = decode(encode(value["state"]))
        self.assertEqual(len(state["records"]), 4)
        self.assertEqual(state["instance_id"], INITIAL_STATE["instance_id"])
        self.assertEqual(state["created_at"], INITIAL_STATE["created_at"])
        self.assertEqual({r["status"] for r in state["records"].values()}, {"baseline"})
        self.assertTrue(all(not s["active"] and s["baseline_needed"] for s in state["sources"].values()))
        self.api.prefetch.assert_called_once()
        self.assertEqual(set(self.report["sources"]), set(SOURCES))

    def test_discovery_failure_and_partial_success_never_write(self):
        for sid in SOURCES:
            with self.subTest(sid=sid):
                self.adapters[sid].error = True
                with self.assertRaisesRegex(AlertError, sid):
                    self.proposal()
                self.assertEqual(self.cloud.calls, [])
                self.assertEqual(self.report["sources"][sid]["status"], "FAILED")
                self.adapters[sid].error = False

    def test_empty_incomplete_duplicate_oversized_listing(self):
        adapter = self.adapters["tiktok_milo_mia"]
        post = adapter.posts[0]
        for posts in ([], None, (post,), [post, post], [post] * 31):
            adapter.posts = posts
            with self.subTest(posts=type(posts)), self.assertRaises(AlertError):
                self.proposal()
        self.assertEqual(self.cloud.calls, [])

    def test_every_post_must_have_owner_public_timestamp_and_identity(self):
        for sid in SOURCES:
            original = copy.deepcopy(self.adapters[sid].posts)
            for field, value in (("owner_id", "other"), ("public", False), ("public", None),
                                 ("published_at", None), ("published_at", stamp(NOW + timedelta(seconds=1))),
                                 ("url", "https://example.com/video"), ("source_id", "other")):
                self.adapters[sid].posts = copy.deepcopy(original)
                setattr(self.adapters[sid].posts[0], field, value)
                with self.subTest(sid=sid, field=field), self.assertRaises(AlertError):
                    self.proposal()
            self.adapters[sid].posts = original
        self.assertEqual(self.cloud.calls, [])

    def test_modified_candidate_delivery_state_and_staleness_rejected(self):
        original = self.proposal()
        for status in ("queued", "waiting_metadata", "sending", "sent", "filtered"):
            value = copy.deepcopy(original)
            next(iter(value["state"]["records"].values()))["status"] = status
            with self.subTest(status=status), self.assertRaises(AlertError):
                validate_proposal(value, self.cfg, RUN, SHA, NOW)
        for field in ("instance_id", "created_at"):
            value = copy.deepcopy(original)
            value["state"][field] = "invalid"
            with self.assertRaises(AlertError):
                validate_proposal(value, self.cfg, RUN, SHA, NOW)
        with self.assertRaises(AlertError):
            validate_proposal(original, self.cfg, RUN, SHA, NOW + timedelta(minutes=31))

    def test_exactly_one_optimistic_write_fresh_store_readback(self):
        writer = self.writer()
        result = write_once(writer, "mock", self.cfg, clock=lambda: NOW)
        self.assertEqual(result["production_state_writes"], 1)
        self.assertEqual(result["production_commit"], self.cloud.result)
        self.assertEqual(result["independent_verification"], "PASSED")
        self.assertEqual(result["after_sha256"], checksum(writer.proposal["state"]))
        self.assertEqual(sum(method != "GET" for method, _ in self.cloud.calls), 1)
        self.assertEqual(decode(self.cloud.raw), writer.proposal["state"])
        with self.assertRaises(AlertError):
            write_once(writer, "mock", self.cfg, clock=lambda: NOW)
        self.assertEqual(writer.attempts, 1)

    def test_missing_corrupt_modified_already_baselined_state_no_write(self):
        for fault in ("missing", "corrupt", "modified", "baselined", "blob"):
            self.cloud = StateAPI()
            if fault in {"missing", "corrupt"}:
                setattr(self.cloud, fault, True)
            elif fault == "modified":
                state = copy.deepcopy(INITIAL_STATE)
                state["instance_id"] = "modified"
                self.cloud.raw = encode(state)
            elif fault == "blob":
                self.cloud.blob = "e" * 40
            else:
                self.cloud.head = self.cloud.result
            writer = self.writer()
            with self.subTest(fault=fault), self.assertRaises(AlertError):
                write_once(writer, "mock", self.cfg, clock=lambda: NOW)
            self.assertEqual(writer.attempts, 0)
            self.assertTrue(all(m == "GET" for m, _ in self.cloud.calls))

    def test_concurrent_conflict_failed_write_lost_ack_no_retry(self):
        for fault in ("race", "fail", "lost_ack", "bad_ack"):
            self.cloud = StateAPI()
            setattr(self.cloud, fault, True)
            writer = self.writer()
            with self.subTest(fault=fault), self.assertRaises(AlertError):
                write_once(writer, "mock", self.cfg, clock=lambda: NOW)
            self.assertEqual(writer.attempts, 1)
            self.assertEqual(sum(m == "PUT" for m, _ in self.cloud.calls), 1)
            with self.assertRaises(AlertError):
                writer.store("mock").save(writer.proposal["state"])
            self.assertEqual(sum(m == "PUT" for m, _ in self.cloud.calls), 1)

    def test_request_fence_blocks_all_other_branches_hosts_creation_recovery(self):
        fence = self.writer()
        for method, url in (("POST", BASE + "/git/refs"), ("GET", BASE + "/contents/state.json?ref=main"),
            ("GET", BASE + "/contents/state.json?ref=dva-canary-other"), ("PUT", BASE + "/git/refs/heads/notification-state"),
            ("GET", "https://example.com/"), ("GET", BASE + "-other")):
            with self.subTest(url=url), self.assertRaises(AlertError):
                fence(method, url)
        self.assertEqual(self.cloud.calls, [])

    def test_one_run_history_gate(self):
        self.cloud.count = 2
        writer = self.writer()
        with self.assertRaises(AlertError):
            write_once(writer, "mock", self.cfg, clock=lambda: NOW)
        self.assertEqual(writer.attempts, 0)

    def test_off_to_on_resume_discards_disabled_period_and_history(self):
        state = self.proposal()["state"]
        store = MemoryStore(state)
        cfg = copy.deepcopy(self.cfg)
        cfg["logging"]["level"] = "WARNING"
        client = Mock()
        engine = Engine(ROOT, cfg, store, self.adapters, client=client, clock=lambda: NOW)
        engine.run(deliver=True)
        client.send.assert_not_called()
        cfg["master_enabled"] = True  # mocks only; production config untouched
        for sid, adapter in self.adapters.items():
            new = copy.deepcopy(adapter.posts[0])
            new.post_id = "lmnopqrstuv" if new.platform == "youtube" else "1234567890123456790"
            new.url = "https://www.youtube.com/watch?v=" + new.post_id if new.platform == "youtube" else f"https://www.tiktok.com/@{cfg['channels'][sid]['account']}/video/{new.post_id}"
            new.published_at = stamp(NOW - timedelta(minutes=1))
            adapter.posts.append(new)
        engine = Engine(ROOT, cfg, store, self.adapters, client=client, clock=lambda: NOW)
        engine.run(deliver=True)
        engine.run(deliver=True)
        self.assertEqual(len(engine.state["records"]), 8)
        self.assertEqual({r["status"] for r in engine.state["records"].values()}, {"baseline"})
        client.send.assert_not_called()

    def test_workflow_secrets_permissions_and_exact_execution_surface(self):
        raw = (ROOT / ".github/workflows/baseline-state.yml").read_text(encoding="utf-8")
        data = yaml.load(raw, Loader=yaml.BaseLoader)
        self.assertEqual(set(data["on"]), {"workflow_dispatch"})
        self.assertEqual(data["permissions"], {"contents": "read"})
        job = data["jobs"]["baseline"]
        self.assertEqual(job["permissions"], {"contents": "write", "actions": "read"})
        self.assertNotIn("DISCORD_WEBHOOK_URL", raw)
        self.assertNotIn("operate.yml", raw)
        self.assertEqual([s.get("run") for s in job["steps"] if "YOUTUBE_API_KEY" in s.get("env", {})],
                         ["python scripts/baseline_production_state.py metadata"])
        for step in job["steps"]:
            self.assertFalse({"YOUTUBE_API_KEY", "GITHUB_TOKEN"} <= set(step.get("env", {})))
        self.assertEqual(job["steps"][0]["with"]["persist-credentials"], "false")

    def test_entry_point_real_config_preflight_network_mocked_no_engine_or_discord(self):
        spec = importlib.util.spec_from_file_location("baseline_entry", ROOT / "scripts/baseline_production_state.py")
        entry = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(entry)
        with patch.dict(os.environ, environment("preflight"), clear=True), patch("sys.argv", ["entry", "preflight"]), \
             patch.object(entry, "BaselineTransport", side_effect=lambda sha, run, **kw: BaselineTransport(sha, run, transport=self.cloud, **kw)), \
             patch("video_alerts.engine.Engine", side_effect=AssertionError("Engine reached")), \
             patch("video_alerts.discord.payload", side_effect=AssertionError("Discord payload reached")), \
             patch("video_alerts.discord.DiscordClient.send", side_effect=AssertionError("Discord send reached")), \
             patch("sys.stdout", new_callable=io.StringIO) as output:
            self.assertEqual(entry.main(), 0)
            report = json.loads(output.getvalue().split("DVA_REPORT ")[1])
            self.assertTrue(report["initial_state_verified"])
            self.assertEqual(report["production_state_writes"], 0)

    def test_entry_point_metadata_then_write_real_config_no_discord_reachable(self):
        spec = importlib.util.spec_from_file_location("baseline_entry_transaction", ROOT / "scripts/baseline_production_state.py")
        entry = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(entry)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shutil.copytree(ROOT / "config", root / "config")
            shutil.copytree(ROOT / ".github", root / ".github")
            with patch.object(entry, "ROOT", root), \
                 patch.object(entry, "BaselineTransport", side_effect=lambda sha, run, **kw: BaselineTransport(sha, run, transport=self.cloud, **kw)), \
                 patch("video_alerts.adapters.adapters", return_value=self.adapters), \
                 patch("video_alerts.engine.Engine", side_effect=AssertionError("Engine reached")), \
                 patch("video_alerts.discord.payload", side_effect=AssertionError("Discord payload reached")), \
                 patch("video_alerts.discord.DiscordClient.send", side_effect=AssertionError("Discord send reached")):
                for phase in ("metadata", "write"):
                    with patch.dict(os.environ, environment(phase), clear=True), \
                         patch("sys.argv", ["entry", phase]), patch("sys.stdout", new_callable=io.StringIO) as output:
                        self.assertEqual(entry.main(), 0, output.getvalue())
                        report = json.loads(output.getvalue().split("DVA_REPORT ")[1])
                        self.assertEqual(report["status"], "PASSED")
                        self.assertEqual(report["discord_requests"], 0)
                        self.assertEqual(report["production_state_writes"], int(phase == "write"))
                        self.assertNotIn("mock-only", output.getvalue())


if __name__ == "__main__":
    unittest.main()

import copy
import io
import json
import os
import runpy
import tempfile
import traceback
import unittest
from contextlib import redirect_stdout
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

import yaml

from video_alerts.adapters import YouTubeAdapter, TikTokAdapter, adapters
from video_alerts.config import load_config
from video_alerts.engine import Engine, decision
from video_alerts.http import Response
from video_alerts.model import AlertError, Post
from video_alerts.state import MemoryStore, new_state
from video_alerts.youtube_api import YouTubeAPI, from_api, MAX_REQUESTS_PER_RUN

ROOT = Path(__file__).resolve().parents[1]
KEY = "synthetic-key-for-mock-tests-only"
NOW = datetime(2026, 10, 16, 15, tzinfo=timezone.utc)


def response(body, status=200, headers=None):
    return Response(status, json.dumps(body).encode(), headers or {})


class YouTubeAPITests(unittest.TestCase):
    def setUp(self):
        self.cfg = load_config(ROOT)
        self.ch = self.cfg["channels"]["youtube_dayz"]
        self.retry = {"attempts": 3, "base_seconds": 1, "max_seconds": 5}
        self.post = Post("youtube", "youtube_dayz", "abcdefghijk", "https://www.youtube.com/watch?v=abcdefghijk", "RSS title", "DayZ", "2026-10-16T14:00:00+00:00")

    def item(self, pid="abcdefghijk", sid="youtube_dayz"):
        return {"id": pid, "snippet": {"channelId": self.cfg["channels"][sid]["channel_id"],
                "channelTitle": "Verified channel", "title": "Public title", "publishedAt": "2026-10-16T14:00:00Z",
                "liveBroadcastContent": "none"}, "status": {"privacyStatus": "public", "uploadStatus": "processed"}}

    def client(self, transport):
        return YouTubeAPI(KEY, self.retry, transport=transport, sleep=lambda _: None)

    def test_get_only_key_header_and_bounded_fields(self):
        seen = []
        def transport(method, url, **kwargs):
            seen.append((method, url, kwargs))
            return response({"items": [self.item()]})
        api = self.client(transport)
        self.assertEqual(api.get(self.post.post_id)["id"], self.post.post_id)
        method, url, kwargs = seen[0]
        self.assertEqual(method, "GET")
        parsed = urlsplit(url)
        self.assertEqual((parsed.scheme, parsed.netloc, parsed.path), ("https", "www.googleapis.com", "/youtube/v3/videos"))
        query = parse_qs(parsed.query)
        self.assertNotIn("key", query)
        self.assertNotIn(KEY, url)
        self.assertEqual(kwargs["headers"]["X-Goog-Api-Key"], KEY)
        self.assertEqual(query["part"], ["snippet,status,liveStreamingDetails"])
        self.assertIn("privacyStatus", query["fields"][0])

    def test_batches_at_fifty_and_deduplicates_cache(self):
        ids = [f"{index:011d}" for index in range(101)]
        seen = []
        def transport(method, url, **kwargs):
            requested = parse_qs(urlsplit(url).query)["id"][0].split(",")
            seen.append(requested)
            return response({"items": [self.item(pid) for pid in requested]})
        api = self.client(transport)
        api.prefetch(ids + ids)
        self.assertEqual(list(map(len, seen)), [50, 50, 1])
        for pid in ids:
            self.assertEqual(api.get(pid)["id"], pid)
        self.assertEqual(api.requests, 3)

    def test_cached_response_is_defensive_copy(self):
        api = self.client(lambda *a, **k: response({"items": [self.item()]}))
        api.get(self.post.post_id)["snippet"]["channelId"] = "changed"
        self.assertEqual(api.get(self.post.post_id)["snippet"]["channelId"], self.ch["channel_id"])
        self.assertEqual(api.requests, 1)

    def test_deleted_or_missing_video_negative_cache_no_fallback(self):
        api = self.client(lambda *a, **k: response({"items": []}))
        adapter = YouTubeAdapter(self.ch, self.retry, api=api)
        with patch("video_alerts.adapters.extract", side_effect=AssertionError("No extractor fallback")):
            for _ in range(2):
                with self.assertRaisesRegex(AlertError, "unavailable"):
                    adapter.enrich(self.post)
        self.assertEqual(api.requests, 1)

    def test_bad_ids_rejected_before_network(self):
        for value in ("", "too-short", "x"*12, "abcdefghij/", None):
            api = self.client(lambda *a, **k: self.fail("Network must not run"))
            with self.subTest(value=value), self.assertRaises(AlertError):
                api.prefetch(["abcdefghijk", value])
            self.assertEqual(api.requests, 0)

    def test_missing_key_fails_closed_without_network(self):
        for value in (None, "", "  "):
            api = YouTubeAPI(value, self.retry, transport=lambda *a, **k: self.fail("No request"))
            with self.subTest(value=value), self.assertRaisesRegex(AlertError, "not configured"):
                api.get(self.post.post_id)
            self.assertEqual(api.requests, 0)

    def test_credentials_and_quota_stop_shared_client_without_reflection(self):
        for status, reason, expected in ((400, "keyInvalid", "credentials"), (401, "unauthorized", "credentials"),
                                          (403, "accessNotConfigured", "credentials"), (403, "quotaExceeded", "quota"),
                                          (403, "dailyLimitExceeded", "quota")):
            api = self.client(lambda *a, **k: response({"error": {"message": KEY, "errors": [{"reason": reason}]}}, status))
            for pid in ("abcdefghijk", "12345678901"):
                with self.subTest(status=status, reason=reason, pid=pid), self.assertRaisesRegex(AlertError, expected) as caught:
                    api.get(pid)
                self.assertNotIn(KEY, str(caught.exception))
            self.assertEqual(api.requests, 1)

    def test_transient_errors_retry_and_succeed(self):
        calls, sleeps = [], []
        def transport(*a, **k):
            calls.append(1)
            return response({}, 503) if len(calls) < 3 else response({"items": [self.item()]})
        api = YouTubeAPI(KEY, self.retry, transport=transport, sleep=sleeps.append)
        self.assertEqual(api.get(self.post.post_id)["id"], self.post.post_id)
        self.assertEqual(sleeps, [1, 2])
        self.assertEqual(api.requests, 3)

    def test_network_exception_redacted_and_negative_cached(self):
        def failed(*a, **k):
            raise RuntimeError("Network exception containing " + KEY)
        api = self.client(failed)
        for _ in range(2):
            try:
                api.get(self.post.post_id)
            except AlertError:
                self.assertNotIn(KEY, traceback.format_exc())
            else:
                self.fail("Expected failure")
        self.assertEqual(api.requests, 3)

    def test_rate_limit_retry_after_and_large_delay(self):
        sleeps, calls = [], []
        def limited(*a, **k):
            calls.append(1)
            return response({}, 429, {"Retry-After": "3"}) if len(calls) == 1 else response({"items": [self.item()]})
        api = YouTubeAPI(KEY, self.retry, transport=limited, sleep=sleeps.append)
        api.get(self.post.post_id)
        self.assertEqual(sleeps, [3])
        for delay in ("3600", "nan", "inf"):
            api = self.client(lambda *a, **k: response({}, 429, {"Retry-After": delay}))
            with self.subTest(delay=delay), self.assertRaisesRegex(AlertError, "rate limited"):
                api.get(self.post.post_id)
            self.assertEqual(api.requests, 1)

    def test_total_request_budget_cannot_be_exceeded(self):
        api = self.client(lambda *a, **k: response({}, 503))
        for index in range(8):
            with self.assertRaises(AlertError):
                api.get(f"{index:011d}")
        self.assertEqual(api.requests, MAX_REQUESTS_PER_RUN)

    def test_redirect_never_followed_or_retried(self):
        api = self.client(lambda *a, **k: response({}, 302, {"Location": "https://other.invalid/"+KEY}))
        with self.assertRaisesRegex(AlertError, "redirect") as caught:
            api.get(self.post.post_id)
        self.assertNotIn(KEY, str(caught.exception))
        self.assertEqual(api.requests, 1)

    def test_malformed_success_duplicate_and_extra_ids_rejected(self):
        bodies = [{}, {"items": None}, {"items": [self.item(), self.item()]},
                  {"items": [self.item("12345678901")]}, {"items": [None]},
                  {"items": [], "error": {"message": KEY}}]
        for body in bodies:
            api = self.client(lambda *a, **k: response(body))
            with self.subTest(body=body), self.assertRaisesRegex(AlertError, "invalid metadata"):
                api.get(self.post.post_id)
        api = self.client(lambda *a, **k: Response(200, ("not JSON "+KEY).encode(), {}))
        try:
            api.get(self.post.post_id)
        except AlertError:
            self.assertNotIn(KEY, traceback.format_exc())

    def test_api_identity_and_public_timestamp_verified(self):
        post = from_api(self.item(), self.post, self.ch)
        self.assertEqual(post.owner_id, self.ch["channel_id"])
        self.assertEqual(post.key, self.post.key)
        self.assertTrue(post.public)
        self.assertEqual(post.published_at, "2026-10-16T14:00:00+00:00")
        self.assertEqual(post.title, "Public title")
        self.assertEqual(post.kind, "unknown")
        self.assertIsNone(post.premiere)

    def test_wrong_or_missing_channel_and_video_identity_rejected(self):
        for field, value in (("channelId", "UCg1uoL9TtAaxvyn6dbQ08fA"), ("channelId", None)):
            item = self.item()
            item["snippet"][field] = value
            with self.subTest(value=value), self.assertRaisesRegex(AlertError, "channel identity"):
                from_api(item, self.post, self.ch)
        item = self.item("12345678901")
        with self.assertRaisesRegex(AlertError, "video identity"):
            from_api(item, self.post, self.ch)

    def test_unknown_or_incomplete_metadata_is_never_public(self):
        for section, field, value in (("snippet", "publishedAt", "date-only"),
                                      ("snippet", "publishedAt", "2026-10-16T14:00:00"),
                                      ("snippet", "liveBroadcastContent", "unknown"),
                                      ("status", "privacyStatus", None), ("status", "uploadStatus", None)):
            item = self.item()
            item[section][field] = value
            with self.subTest(field=field, value=value), self.assertRaises(AlertError):
                from_api(item, self.post, self.ch)

    def test_private_unlisted_and_unprocessed_posts_remain_ineligible(self):
        for privacy, upload in (("private", "processed"), ("unlisted", "processed"), ("public", "uploaded"),
                                ("public", "failed"), ("public", "deleted")):
            item = self.item()
            item["status"].update(privacyStatus=privacy, uploadStatus=upload)
            post = from_api(item, self.post, self.ch)
            with self.subTest(privacy=privacy, upload=upload):
                self.assertFalse(post.public)
                self.assertEqual(decision(post, self.ch, self.cfg, NOW)[0], "waiting_metadata")

    def test_upcoming_live_and_completed_broadcasts_preserve_exclusion(self):
        for live, details in (("upcoming", {"scheduledStartTime": "2026-10-17T14:00:00Z"}),
                              ("live", {"actualStartTime": "2026-10-16T14:00:00Z"}),
                              ("none", {"actualStartTime": "2026-10-16T14:00:00Z", "actualEndTime": "2026-10-16T14:30:00Z"})):
            item = self.item()
            item["snippet"]["liveBroadcastContent"] = live
            item["liveStreamingDetails"] = details
            post = from_api(item, self.post, self.ch)
            ch = copy.deepcopy(self.ch)
            ch["filters"].update(enabled=True, exclude_livestreams=True, exclude_premieres=False)
            with self.subTest(live=live):
                self.assertEqual(post.kind, "livestream")
                self.assertEqual(decision(post, ch, self.cfg, NOW)[0], "waiting_metadata" if live == "upcoming" else "filtered")

    def test_premiere_and_short_classification_not_invented(self):
        post = from_api(self.item(), self.post, self.ch)
        ch = copy.deepcopy(self.ch)
        ch["filters"].update(enabled=True, exclude_premieres=True, video_types="both")
        self.assertEqual(decision(post, ch, self.cfg, NOW)[0], "waiting_metadata")
        ch["filters"].update(exclude_premieres=False, video_types="shorts")
        self.assertEqual(decision(post, ch, self.cfg, NOW)[0], "waiting_metadata")

    def test_positive_official_short_tab_proof_still_used(self):
        ch = copy.deepcopy(self.ch)
        ch["filters"].update(enabled=True, video_types="shorts")
        api = self.client(lambda *a, **k: response({"items": [self.item()]}))
        adapter = YouTubeAdapter(ch, self.retry, api=api)
        def listing(url, flat=False):
            self.assertTrue(flat)
            return {"channel_id": ch["channel_id"], "entries": [{"id": self.post.post_id}] if url.endswith("/shorts") else []}
        with patch("video_alerts.adapters.extract", side_effect=listing):
            self.assertEqual(adapter.enrich(self.post).kind, "short")

    def test_two_account_rss_batches_share_client_and_preserve_tiktok(self):
        def rss(sid, ids):
            channel = self.cfg["channels"][sid]["channel_id"]
            entries = "".join(f"<entry><yt:videoId>{pid}</yt:videoId><yt:channelId>{channel}</yt:channelId><published>2026-10-16T14:00:00Z</published></entry>" for pid in ids)
            return Response(200, f'<feed xmlns="http://www.w3.org/2005/Atom" xmlns:yt="http://www.youtube.com/xml/schemas/2015"><yt:channelId>{channel}</yt:channelId>{entries}</feed>'.encode(), {})
        with patch.dict(os.environ, {"YOUTUBE_API_KEY": KEY}, clear=True):
            all_adapters = adapters(self.cfg)
        self.assertIsInstance(all_adapters["tiktok_dayz"], TikTokAdapter)
        self.assertFalse(hasattr(all_adapters["tiktok_dayz"], "api"))
        api = all_adapters["youtube_dayz"].api
        self.assertIs(api, all_adapters["youtube_milo_mia"].api)
        owners = {}
        def transport(method, url, **kwargs):
            ids = parse_qs(urlsplit(url).query)["id"][0].split(",")
            return response({"items": [self.item(pid, owners[pid]) for pid in ids]})
        api.transport = transport
        for index, sid in enumerate(("youtube_dayz", "youtube_milo_mia")):
            ids = [f"{index*30+n:011d}" for n in range(30)]
            owners.update({pid: sid for pid in ids})
            with patch("video_alerts.adapters.public_get", return_value=rss(sid, ids)):
                posts = all_adapters[sid].discover(sid)
            for post in posts:
                self.assertTrue(all_adapters[sid].enrich(post).public)
        self.assertEqual(api.requests, 2)

    def test_no_key_preserves_existing_public_extractor_mode(self):
        with patch.dict(os.environ, {}, clear=True):
            selected = adapters(self.cfg)
        self.assertIsNone(selected["youtube_dayz"].api)
        self.assertEqual(selected["youtube_dayz"].metadata_method, "public_extractor")

    def test_workflow_key_is_only_in_stateless_validation_step(self):
        workflow = yaml.load((ROOT/".github/workflows/youtube-api-validation.yml").read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
        self.assertEqual(set(workflow["on"]), {"workflow_dispatch"})
        self.assertEqual(workflow["permissions"], {"contents": "read"})
        text = json.dumps(workflow)
        self.assertNotIn("DISCORD_WEBHOOK_URL", text)
        self.assertNotIn("contents: write", text)
        steps = workflow["jobs"]["validate"]["steps"]
        keyed = [step for step in steps if "YOUTUBE_API_KEY" in step.get("env", {})]
        self.assertEqual(len(keyed), 1)
        self.assertEqual(keyed[0]["run"], "python scripts/validate_youtube_api.py")
        self.assertFalse(any("YOUTUBE_API_KEY" in json.dumps(step) for step in steps if step is not keyed[0]))

    def test_fresh_run_rechecks_upcoming_and_unavailable_metadata(self):
        upcoming = self.item()
        upcoming["snippet"]["liveBroadcastContent"] = "upcoming"
        api = self.client(lambda *a, **k: response({"items": [upcoming]}))
        self.assertFalse(from_api(api.get(self.post.post_id), self.post, self.ch).public)
        # Next run uses a fresh client, so neither public status nor missing data
        # is frozen in persistent state or a cross-run cache.
        api = self.client(lambda *a, **k: response({"items": []}))
        with self.assertRaises(AlertError):
            api.get(self.post.post_id)
        api = self.client(lambda *a, **k: response({"items": [self.item()]}))
        self.assertTrue(from_api(api.get(self.post.post_id), self.post, self.ch).public)

    def test_header_control_characters_fail_without_request(self):
        for key in (KEY+"\r\nInjected: value", KEY+"\x00", " "+KEY):
            api = YouTubeAPI(key, self.retry, transport=lambda *a, **k: self.fail("No request"))
            with self.subTest(key_suffix=repr(key[-4:])), self.assertRaisesRegex(AlertError, "credentials"):
                api.get(self.post.post_id)
            self.assertEqual(api.requests, 0)

    def test_validation_refuses_missing_key_and_discord_secret(self):
        main = runpy.run_path(str(ROOT/"scripts/validate_youtube_api.py"))["main"]
        for env, expected in (({}, "requires YOUTUBE_API_KEY"), ({"YOUTUBE_API_KEY": KEY, "DISCORD_WEBHOOK_URL": "synthetic"}, "Discord secret")):
            with patch.dict(os.environ, env, clear=True), self.subTest(env=list(env)), self.assertRaisesRegex(AlertError, expected):
                main()

    def test_api_posts_keep_engine_baseline_and_restart_dedup_without_secret_state(self):
        cfg = copy.deepcopy(self.cfg)
        cfg.update(master_enabled=True, queue_delay_seconds=0)
        cfg["logging"]["level"] = "WARNING"
        for sid, ch in cfg["channels"].items():
            ch["enabled"] = sid == "youtube_dayz"
            ch["filters"]["enabled"] = False
            ch["publication_delay_minutes"] = 0
        store, sent = MemoryStore(new_state()), []
        class Sink:
            def send(self, value, media=None):
                sent.append(value)
                return "123456789012345678"
        for phase in range(3):
            posts = [copy.deepcopy(self.post)]
            if phase:
                posts.append(Post("youtube", "youtube_dayz", "12345678901", "https://www.youtube.com/watch?v=12345678901", "New", "DayZ"))
            def transport(method, url, **kwargs):
                ids = parse_qs(urlsplit(url).query)["id"][0].split(",")
                items = [self.item(pid) for pid in ids]
                for item in items:
                    if item["id"] == "12345678901":
                        item["snippet"]["publishedAt"] = "2026-10-16T15:30:00Z"
                return response({"items": items})
            api = self.client(transport)
            adapter = YouTubeAdapter(cfg["channels"]["youtube_dayz"], self.retry, api=api)
            with patch.object(adapter, "discover", return_value=posts):
                Engine(ROOT, cfg, store, {"youtube_dayz": adapter}, Sink(),
                       clock=lambda: NOW+timedelta(hours=phase), sleep=lambda _: None).run(deliver=True)
            self.assertEqual(len(sent), 0 if phase == 0 else 1)
        self.assertNotIn(KEY, json.dumps(store.load()))
        self.assertEqual(store.load()["records"]["youtube:youtube_dayz:12345678901"]["status"], "sent")

    def test_api_quota_failure_does_not_stop_tiktok_source(self):
        cfg = copy.deepcopy(self.cfg)
        cfg["master_enabled"] = True
        cfg["logging"]["level"] = "WARNING"
        for sid, ch in cfg["channels"].items():
            ch["enabled"] = sid in {"youtube_dayz", "tiktok_dayz"}
        api = self.client(lambda *a, **k: response({"error": {"errors": [{"reason": "quotaExceeded"}]}}, 403))
        yt = YouTubeAdapter(self.ch, self.retry, api=api)
        tiktok_post = Post("tiktok", "tiktok_dayz", "1234567890123456789", "https://www.tiktok.com/@infinity.projectrp/video/1234567890123456789", "TikTok", "Infinity", "2026-10-16T14:00:00Z", "regular", True, False, "infinity.projectrp")
        class TikTokFixture:
            def discover(self, sid):
                return [copy.deepcopy(tiktok_post)]
            def enrich(self, post):
                return copy.deepcopy(post)
        store = MemoryStore(new_state())
        with patch.object(yt, "discover", return_value=[self.post]):
            Engine(ROOT, cfg, store, {"youtube_dayz": yt, "tiktok_dayz": TikTokFixture()}, None,
                   clock=lambda: NOW).run()
        sources = store.load()["sources"]
        self.assertIn("quota", sources["youtube_dayz"]["error"])
        self.assertEqual(sources["tiktok_dayz"]["status"], "HEALTHY")
        self.assertNotIn(KEY, json.dumps(store.load()))

    def test_stateless_validation_uses_only_mock_api_and_writes_no_production_state(self):
        main = runpy.run_path(str(ROOT/"scripts/validate_youtube_api.py"))["main"]
        def discover(adapter, sid):
            pid = "abcdefghijk" if sid == "youtube_dayz" else "12345678901"
            return [Post("youtube", sid, pid, "https://www.youtube.com/watch?v="+pid, "", "")]
        def transport(method, url, **kwargs):
            pid = parse_qs(urlsplit(url).query)["id"][0]
            sid = "youtube_dayz" if pid == "abcdefghijk" else "youtube_milo_mia"
            return response({"items": [self.item(pid, sid)]})
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {"YOUTUBE_API_KEY": KEY}, clear=True), \
             patch.dict(main.__globals__, {"ROOT": Path(tmp), "load_config": lambda _: self.cfg}), \
             patch.object(YouTubeAdapter, "discover", discover), patch.object(YouTubeAdapter, "classify", return_value="short"), \
             patch("video_alerts.youtube_api.request", side_effect=transport), redirect_stdout(io.StringIO()) as output:
            self.assertEqual(main(), 0)
            text = (Path(tmp)/".validation/youtube-api-validation.json").read_text(encoding="utf-8")
            self.assertNotIn(KEY, text+output.getvalue())
            report = json.loads(text)
            self.assertEqual(report["api_requests"], 2)
            self.assertTrue(all(s["metadata"] == "VERIFIED" for s in report["sources"].values()))
            self.assertEqual(report["production_state_writes"], 0)
            self.assertFalse((Path(tmp)/"state").exists())


if __name__ == "__main__":
    unittest.main()

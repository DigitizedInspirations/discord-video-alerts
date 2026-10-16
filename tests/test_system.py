import copy
import io
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch
from PIL import Image

from video_alerts.config import load_config, validate, template_fields, relative
from video_alerts.model import AlertError, Post, stamp, sanitize, video_url
from video_alerts.state import LocalStore, MemoryStore, new_state, encode, decode, merge_restore, GitHubStore
from video_alerts.engine import Engine, decision
from video_alerts.discord import DiscordClient, DeliveryError, payload, wire
from video_alerts.http import Response, public_get
from video_alerts.media import attachment, image_info, avatar
from video_alerts.adapters import YouTubeAdapter, TikTokAdapter, from_metadata
from video_alerts.cli import local_lock

ROOT = Path(__file__).resolve().parents[1]
NOW = datetime(2026, 10, 11, 10, tzinfo=timezone.utc)
MID = "123456789012345678"
WEBHOOK = "https://discord.com/api/webhooks/123456789012345678/" + "t"*40

def post(sid="youtube_dayz", pid="abcdefghijk", age=1, kind="regular", public=True):
    ch = load_config(ROOT)["channels"][sid]
    if ch["platform"] == "youtube":
        url = "https://www.youtube.com/watch?v=" + pid
    else:
        pid = pid if pid.isdigit() else "1234567890123456789"
        url = f"https://www.tiktok.com/@{ch['account']}/video/{pid}"
    return Post(ch["platform"], sid, pid, url, "New video", ch["account"], stamp(NOW - timedelta(hours=age)), kind, public, False, ch["channel_id"] or ch["account"])

class FakeAdapter:
    def __init__(self, posts=None, error=False):
        self.posts = posts or []
        self.error = error
    def discover(self, sid):
        if self.error:
            raise AlertError("Simulated source outage")
        return copy.deepcopy(self.posts)
    def enrich(self, item):
        if self.error:
            raise AlertError("Simulated metadata outage")
        return copy.deepcopy(next((p for p in self.posts if p.post_id == item.post_id), item))

class FakeClient:
    def __init__(self, error=None):
        self.calls, self.error = [], error
    def send(self, value, media):
        self.calls.append(value)
        if self.error:
            raise self.error
        return MID
    def edit(self, mid, value, media):
        self.calls.append(("edit", mid, value))
        return mid
    def delete(self, mid):
        self.calls.append(("delete", mid))

class SystemTests(unittest.TestCase):
    def setUp(self):
        self.cfg = load_config(ROOT)
        self.cfg["master_enabled"] = True
        self.cfg["logging"]["level"] = "WARNING"
        self.store = MemoryStore(new_state())
        self.adapters = {sid: FakeAdapter() for sid in self.cfg["channels"]}
        self.client = FakeClient()
        self.sleeps = []
        self.now = NOW
    def engine(self, client=None, store=None):
        return Engine(ROOT, self.cfg, store or self.store, self.adapters, client or self.client, clock=lambda: self.now, sleep=self.sleeps.append)
    def baseline(self):
        self.engine().run()
        self.now += timedelta(hours=2)
    def new(self, sid="youtube_dayz", pid="abcdefghijk", age=1):
        p = post(sid, pid, age)
        p.published_at = stamp(self.now - timedelta(hours=age))
        self.adapters[sid].posts.append(p)
        return p

    def test_config_defaults_and_exact_sources(self):
        cfg = load_config(ROOT)
        self.assertFalse(cfg["master_enabled"])
        self.assertEqual(len(cfg["channels"]), 4)
        self.assertEqual(cfg["queue_delay_seconds"], 10)
    def test_strict_config_types_unknown_keys_and_ranges(self):
        for key, value in [("master_enabled", 1), ("queue_delay_seconds", float("nan")), ("max_video_age_hours", -1), ("max_messages_per_run", 2.2), ("surprise", True)]:
            cfg = copy.deepcopy(self.cfg)
            cfg[key] = value
            with self.assertRaises(AlertError):
                validate(cfg, ROOT)
    def test_template_utf8_matches_original_attachment(self):
        raw = (ROOT / "docs/MASTER_REQUEST.md").read_text(encoding="utf-8")
        for sid in self.cfg["channels"]:
            expected = raw.split(f"## config/messages/{sid}.txt\n\n", 1)[1].split("\n\n", 1)[0]
            actual = (ROOT / f"config/messages/{sid}.txt").read_text(encoding="utf-8").rstrip("\n")
            self.assertEqual(actual, expected)
    def test_invalid_placeholder_attribute_spec_conversion(self):
        for text in ["{OTHER}", "{VIDEO_URL.__class__}", "{VIDEO_URL!r}", "{VIDEO_URL:20}", "{", "plain text"]:
            with self.assertRaises(AlertError):
                template_fields(text)
    def test_dynamic_placeholders_sanitize(self):
        self.assertEqual(template_fields("{VIDEO_URL} {VIDEO_TITLE} {CHANNEL_NAME} {PLATFORM} {PUBLISHED_AT}"), {"VIDEO_URL", "VIDEO_TITLE", "CHANNEL_NAME", "PLATFORM", "PUBLISHED_AT"})
        self.assertNotIn("@everyone", sanitize("@everyone <@&123> **boom**"))
    def test_safe_paths_and_urls(self):
        for path in ["../outside.gif", "C:/temp.gif", "state/../.git/config", "assets\\x.gif"]:
            with self.assertRaises(AlertError):
                relative(ROOT, path)
        for url in ["http://www.youtube.com/watch?v=abcdefghijk", "https://evil.test/watch?v=abcdefghijk", "https://www.youtube.com:8443/watch?v=abcdefghijk", "https://user@www.youtube.com/watch?v=abcdefghijk"]:
            with self.assertRaises(AlertError):
                video_url(url, "youtube")
        with self.assertRaises(AlertError):
            video_url("https://www.tiktok.com/@other/video/1234567890123", "tiktok", "infinity.projectrp")
    def test_initial_baseline_never_sends(self):
        self.adapters["youtube_dayz"].posts = [post()]
        result = self.engine().run(deliver=True)
        self.assertEqual(next(iter(result["records"].values()))["status"], "baseline")
        self.assertEqual(self.client.calls, [])
    def test_master_off_and_individual_independence(self):
        self.baseline()
        self.new()
        self.cfg["master_enabled"] = False
        self.engine().run(deliver=True)
        self.assertEqual(self.client.calls, [])
        self.assertTrue(self.cfg["channels"]["youtube_dayz"]["enabled"])
        self.cfg["master_enabled"] = True
        self.cfg["channels"]["youtube_dayz"]["enabled"] = False
        self.engine().run(deliver=True)
        self.assertEqual(self.store.state["sources"]["youtube_dayz"]["status"], "DISABLED")
    def test_off_on_skips_disabled_period_and_preserves_history(self):
        self.baseline()
        first = self.new()
        self.engine().run(deliver=True)
        self.cfg["channels"]["youtube_dayz"]["enabled"] = False
        self.engine().run()
        self.now += timedelta(hours=1)
        during = self.new(pid="bbbbbbbbbbb", age=0)
        self.engine().run()
        self.cfg["channels"]["youtube_dayz"]["enabled"] = True
        self.engine().run(deliver=True)
        self.assertEqual(self.store.state["records"][first.key]["status"], "sent")
        self.assertEqual(self.store.state["records"][during.key]["status"], "baseline")
        self.assertEqual(len(self.client.calls), 1)
    def test_master_resume_safe_baseline(self):
        self.baseline()
        self.cfg["master_enabled"] = False
        self.engine().run()
        self.new()
        self.cfg["master_enabled"] = True
        self.engine().run(deliver=True)
        self.assertEqual(self.client.calls, [])
    def test_cross_platform_dedup_and_per_source(self):
        self.baseline()
        a = self.new()
        b = self.new("youtube_milo_mia")
        c = self.new("tiktok_dayz")
        self.engine().run(deliver=True)
        self.engine().run(deliver=True)
        self.assertEqual(len(self.client.calls), 3)
        self.assertEqual(len({a.key, b.key, c.key}), 3)
    def test_one_source_failure_does_not_stop_another(self):
        self.baseline()
        self.adapters["tiktok_dayz"].error = True
        self.new()
        self.engine().run(deliver=True)
        self.assertEqual(len(self.client.calls), 1)
        self.assertEqual(self.store.state["sources"]["tiktok_dayz"]["status"], "DEGRADED")
    def test_outage_recent_recovery_is_not_off(self):
        self.baseline()
        self.new()
        self.adapters["youtube_dayz"].error = True
        self.engine().run(deliver=True)
        self.adapters["youtube_dayz"].error = False
        self.engine().run(deliver=True)
        self.assertEqual(len(self.client.calls), 1)
    def test_filters_age_missing_and_future_timestamp(self):
        p = post()
        ch = self.cfg["channels"][p.source_id]
        p.kind = "livestream"
        self.assertEqual(decision(p, ch, self.cfg, NOW)[0], "filtered")
        p.kind = "unknown"
        ch["filters"]["video_types"] = "shorts"
        self.assertEqual(decision(p, ch, self.cfg, NOW)[0], "waiting_metadata")
        ch["filters"]["video_types"] = "both"
        ch["filters"]["exclude_premieres"] = True
        p.premiere = None
        self.assertEqual(decision(p, ch, self.cfg, NOW)[0], "waiting_metadata")
        ch["filters"]["exclude_premieres"] = False
        p.published_at = stamp(NOW-timedelta(hours=25))
        self.assertEqual(decision(p, ch, self.cfg, NOW)[0], "expired")
        p.published_at = None
        self.assertEqual(decision(p, ch, self.cfg, NOW)[0], "waiting_metadata")
        p.published_at = stamp(NOW+timedelta(hours=1))
        self.assertEqual(decision(p, ch, self.cfg, NOW)[0], "waiting_metadata")
    def test_keyword_filters_do_not_backfill_after_change(self):
        self.baseline()
        p = self.new()
        self.cfg["channels"][p.source_id]["filters"]["exclude_keywords"] = ["video"]
        self.engine().run(deliver=True)
        self.cfg["channels"][p.source_id]["filters"]["exclude_keywords"] = []
        self.engine().run(deliver=True)
        self.assertEqual(self.client.calls, [])
    def test_queue_order_delay_limit_and_persistence(self):
        self.baseline()
        newer = self.new(pid="bbbbbbbbbbb", age=0.1)
        older = self.new(pid="aaaaaaaaaaa", age=0.5)
        self.cfg["max_messages_per_run"] = 1
        self.engine().run(deliver=True)
        self.assertIn(older.url, self.client.calls[0]["content"])
        self.assertEqual(self.store.state["records"][newer.key]["status"], "queued")
        self.engine().run(deliver=True)
        self.assertEqual(len(self.client.calls), 2)
    def test_inter_message_delay(self):
        self.baseline()
        self.new()
        self.new(pid="bbbbbbbbbbb")
        self.engine().run(deliver=True)
        self.assertEqual(self.sleeps, [10])
    def test_publication_delay_defers_without_long_sleep(self):
        self.baseline()
        p = self.new(age=0.01)
        self.cfg["channels"][p.source_id]["publication_delay_minutes"] = 15
        self.engine().run(deliver=True)
        self.assertEqual(self.client.calls, [])
        self.assertEqual(self.sleeps, [])
        self.now += timedelta(minutes=16)
        self.engine().run(deliver=True)
        self.assertEqual(len(self.client.calls), 1)
    def test_uncertain_send_quarantined_and_never_retried(self):
        self.baseline()
        p = self.new()
        client = FakeClient(DeliveryError("ambiguous", uncertain=True))
        self.engine(client).run(deliver=True)
        self.engine(client).run(deliver=True)
        self.assertEqual(len(client.calls), 1)
        self.assertEqual(self.store.state["records"][p.key]["status"], "uncertain")
    def test_interrupted_intent_recovered_as_uncertain(self):
        self.baseline()
        p = self.new()
        self.engine().run()
        self.store.state["records"][p.key]["status"] = "sending"
        self.engine().run(deliver=True)
        self.assertEqual(self.store.state["records"][p.key]["status"], "uncertain")
        self.assertEqual(self.client.calls, [])
    def test_no_post_when_write_ahead_checkpoint_fails(self):
        self.baseline()
        self.new()
        self.engine().run()
        class BrokenStore(MemoryStore):
            def save(self, state):
                if any(r["status"] == "sending" for r in state["records"].values()):
                    raise AlertError("checkpoint failed")
                super().save(state)
        with self.assertRaises(AlertError):
            self.engine(store=BrokenStore(self.store.state)).run(deliver=True)
        self.assertEqual(self.client.calls, [])
    def test_dryrun_uses_memory_only(self):
        before = copy.deepcopy(self.store.state)
        self.engine(store=MemoryStore(before)).run()
        self.assertEqual(self.store.state, before)
    def test_allowed_mentions_and_preview_disabled(self):
        ch = self.cfg["channels"]["youtube_dayz"]
        ch["role"] = {"enabled": True, "id": MID}
        ch["preview"] = "disabled"
        value, _ = payload(ROOT, ch, post())
        self.assertEqual(value["allowed_mentions"]["parse"], [])
        self.assertEqual(value["allowed_mentions"]["roles"], [MID])
        self.assertEqual(value["flags"], 4)
        self.assertIn("<https://", value["content"])
    def test_gif_full_animation_and_multipart(self):
        raw = io.BytesIO()
        images = [Image.new("RGB", (4,4), color) for color in ("red", "blue")]
        images[0].save(raw, format="GIF", save_all=True, append_images=images[1:], duration=100, loop=0)
        info = image_info(raw.getvalue(), True)
        self.assertEqual(info["frames"], 2)
        body, mime = wire({"content": "hello"}, {"name": "announcement.gif", "raw": raw.getvalue(), **info})
        self.assertIn(b'name="files[0]"', body)
        self.assertIn(raw.getvalue(), body)
        self.assertTrue(mime.startswith("multipart/form-data"))
    def test_static_media_and_missing_fallback(self):
        raw = io.BytesIO()
        Image.new("RGB", (4,4)).save(raw, format="PNG")
        self.assertEqual(image_info(raw.getvalue())["mime"], "image/png")
        with self.assertRaises(AlertError):
            image_info(raw.getvalue(), True)
        ch = self.cfg["channels"]["youtube_dayz"]
        ch["media"]["enabled"] = True
        self.assertIsNone(attachment(ROOT, ch["media"]))
        ch["media"]["fallback"] = "skip"
        with self.assertRaises(AlertError):
            attachment(ROOT, ch["media"])
    def test_avatar_private_host_fallback(self):
        with patch("video_alerts.media.socket.getaddrinfo", return_value=[(2,1,6,"",("127.0.0.1",443))]):
            self.assertIsNone(avatar("https://example.test/avatar.png", "omit"))
            with self.assertRaises(AlertError):
                avatar("https://example.test/avatar.png", "skip")
    def test_discord_rate_limit_respects_retry_after(self):
        replies = iter([Response(429, b'{"retry_after":2}', {}), Response(200, json.dumps({"id": MID}).encode(), {})])
        client = DiscordClient(WEBHOOK, self.cfg["retry"], transport=lambda *a: next(replies), sleep=self.sleeps.append)
        self.assertEqual(client.send({"content": "test"}), MID)
        self.assertGreaterEqual(self.sleeps[0], 2)
    def test_rate_limit_large_delay_defers(self):
        client = DiscordClient(WEBHOOK, self.cfg["retry"], transport=lambda *a: Response(429, b'{"retry_after":120}', {}), sleep=self.sleeps.append)
        with self.assertRaises(DeliveryError) as result:
            client.send({"content": "test"})
        self.assertTrue(result.exception.retryable)
        self.assertEqual(self.sleeps, [])
    def test_discord_secret_safe_and_ambiguous_http(self):
        for status in (500, 204):
            client = DiscordClient(WEBHOOK, self.cfg["retry"], transport=lambda *a: Response(status, b"", {}))
            with self.assertRaises(DeliveryError) as result:
                client.send({"content": "test"})
            self.assertTrue(result.exception.uncertain)
            self.assertNotIn("t"*40, str(result.exception))
        with self.assertRaises(AlertError):
            DiscordClient(WEBHOOK.replace("discord.com", "evil.test"), self.cfg["retry"])
    def test_discord_permanent_error_not_retried(self):
        calls = []
        def transport(*args):
            calls.append(args)
            return Response(401, b"invalid token", {})
        client = DiscordClient(WEBHOOK, self.cfg["retry"], transport=transport)
        with self.assertRaises(DeliveryError) as result:
            client.send({"content": "test"})
        self.assertFalse(result.exception.uncertain)
        self.assertEqual(len(calls), 1)
    def test_state_checksum_missing_corruption_and_backup(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = LocalStore(Path(tmp)/"state.json")
            with self.assertRaises(AlertError):
                store.load()
            store.initialize()
            original = store.load()
            store.save(original)
            self.assertTrue(store.backup.exists())
            store.path.write_bytes(b"corrupt")
            with self.assertRaises(AlertError):
                store.load()
            store.restore(store.backup.read_bytes(), "RESTORE")
            self.assertEqual(store.load(), original)
    def test_interrupted_atomic_write_preserves_original(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = LocalStore(Path(tmp)/"state.json")
            store.initialize()
            before = store.path.read_bytes()
            with patch("video_alerts.state.os.replace", side_effect=OSError("interrupted")):
                with self.assertRaises(OSError):
                    store.save(store.load())
            self.assertEqual(store.path.read_bytes(), before)
            self.assertEqual(list(Path(tmp).glob(".checkpoint-*")), [])
    def test_restore_merges_newer_delivery_tombstones(self):
        self.baseline()
        checkpoint = self.store.load()
        p = self.new()
        self.engine().run(deliver=True)
        merged = merge_restore(self.store.load(), checkpoint)
        self.assertEqual(merged["records"][p.key]["status"], "sent")
    def test_edit_delete_confirmation_and_tombstone(self):
        self.baseline()
        p = self.new()
        self.engine().run(deliver=True)
        engine = self.engine()
        with self.assertRaises(AlertError):
            engine.manage(p.source_id, p.post_id, "delete")
        engine.manage(p.source_id, p.post_id, "edit", "EDIT")
        engine.manage(p.source_id, p.post_id, "delete", "DELETE")
        self.assertEqual(self.store.state["records"][p.key]["status"], "deleted")
        self.engine().run(deliver=True)
        self.assertEqual(sum(isinstance(v, dict) for v in self.client.calls), 1)
    def test_manual_dryrun_dedup_confirmation_repost_and_master_off(self):
        p = post()
        self.adapters[p.source_id].posts = [p]
        engine = self.engine()
        engine.manual(p.source_id, p.url)
        self.assertEqual(self.client.calls, [])
        with self.assertRaises(AlertError):
            engine.manual(p.source_id, p.url, deliver=True)
        engine.manual(p.source_id, p.url, deliver=True, confirm="SEND")
        with self.assertRaises(AlertError):
            engine.manual(p.source_id, p.url, deliver=True, confirm="SEND")
        engine.manual(p.source_id, p.url, deliver=True, repost=True, confirm="REPOST")
        self.cfg["master_enabled"] = False
        with self.assertRaises(AlertError):
            engine.manual(p.source_id, p.url, deliver=True, repost=True, confirm="REPOST")
        self.assertEqual(len(self.client.calls), 2)
    def test_health_threshold_and_alert_dedup(self):
        self.adapters["youtube_dayz"].error = True
        events = []
        for _ in range(4):
            engine = self.engine()
            engine.run()
            events += engine.events
        self.assertEqual(self.store.state["sources"]["youtube_dayz"]["status"], "FAILED")
        self.assertEqual(sum(e["event"] == "health_alert_summary_only" for e in events), 1)
    def test_local_concurrent_runs_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            with local_lock(Path(tmp)):
                with self.assertRaises(AlertError):
                    with local_lock(Path(tmp)):
                        pass
            self.assertFalse((Path(tmp)/"state/operator.lock").exists())
    def test_official_rss_channel_prefix_identity_and_bad_feed(self):
        adapter = YouTubeAdapter(self.cfg["channels"]["youtube_dayz"], self.cfg["retry"])
        cid = self.cfg["channels"]["youtube_dayz"]["channel_id"]
        raw = f'<feed xmlns="http://www.w3.org/2005/Atom" xmlns:yt="http://www.youtube.com/xml/schemas/2015"><yt:channelId>{cid[2:]}</yt:channelId><entry><yt:videoId>abcdefghijk</yt:videoId><yt:channelId>{cid}</yt:channelId><published>2026-10-11T09:00:00Z</published><title>test</title></entry></feed>'.encode()
        self.assertEqual(adapter.parse_feed(raw, "youtube_dayz")[0].post_id, "abcdefghijk")
        for invalid in (b"<html>error</html>", b"broken", raw.replace(cid.encode(), b"wrong")):
            with self.assertRaises(AlertError):
                adapter.parse_feed(invalid, "youtube_dayz")
    def test_metadata_owner_live_and_classification(self):
        ch = self.cfg["channels"]["youtube_dayz"]
        info = {"id": "abcdefghijk", "webpage_url": post().url, "channel_id": ch["channel_id"], "live_status": "was_live", "availability": "public", "timestamp": NOW.timestamp()}
        self.assertEqual(from_metadata(info, "youtube_dayz", ch).kind, "livestream")
        info["live_status"] = "not_live"
        self.assertEqual(from_metadata(info, "youtube_dayz", ch).kind, "unknown")
        info["channel_id"] = "wrong"
        with self.assertRaises(AlertError):
            from_metadata(info, "youtube_dayz", ch)
    def test_public_request_bounded_retry_and_permanent_failure(self):
        replies = iter([Response(503,b"",{}), Response(200,b"ok",{})])
        self.assertEqual(public_get("https://example.test", self.cfg["retry"], transport=lambda *a: next(replies), sleep=self.sleeps.append).body, b"ok")
        with self.assertRaises(AlertError):
            public_get("https://example.test", self.cfg["retry"], transport=lambda *a: Response(404,b"",{}), sleep=self.sleeps.append)
    def test_github_optimistic_write_conflict(self):
        sha = "a"*40
        encoded = json.dumps({"content": __import__("base64").b64encode(encode(new_state())).decode(), "sha": sha}).encode()
        calls = []
        def transport(method, url, body=None, headers=None):
            calls.append((method, body))
            return Response(200, encoded, {}) if method == "GET" else Response(409,b"",{})
        store = GitHubStore("owner/repo", "not-a-real-token", transport)
        state = store.load()
        with self.assertRaises(AlertError):
            store.save(state)
        self.assertEqual(json.loads(calls[-1][1])["sha"], sha)
    def test_state_validation_rejects_inconsistent_keys(self):
        state = new_state()
        p = post()
        state["records"]["wrong"] = {"post": p.dict(), "status": "baseline", "attempts": 0, "message_id": None, "discovered_at": stamp(NOW)}
        with self.assertRaises(AlertError):
            encode(state)

    def test_tiktok_public_hydration_owner_timestamp_and_privacy(self):
        ch = self.cfg["channels"]["tiktok_dayz"]
        p = post("tiktok_dayz")
        adapter = TikTokAdapter(ch, self.cfg["retry"])
        item = {"id": p.post_id, "author": {"uniqueId": ch["account"]}, "desc": "@everyone test", "createTime": str(int(NOW.timestamp())), "video": {"id": "real-video"}, "privateItem": False, "secret": False, "forFriend": False, "isProhibited": False, "takeDown": 0}
        def raw():
            obj = {"__DEFAULT_SCOPE__": {"webapp.video-detail": {"statusCode": 0, "itemInfo": {"itemStruct": item}}}}
            return ('<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__" type="application/json">' + json.dumps(obj) + '</script>').encode()
        parsed = adapter.parse_detail(raw(), p)
        self.assertTrue(parsed.public)
        self.assertEqual(parsed.owner_id, ch["account"])
        self.assertEqual(parsed.published_at, stamp(NOW))
        item["privateItem"] = True
        self.assertFalse(adapter.parse_detail(raw(), p).public)
        item["privateItem"] = "false"
        with self.assertRaises(AlertError):
            adapter.parse_detail(raw(), p)
        item["privateItem"] = False
        item["author"]["uniqueId"] = "other-account"
        with self.assertRaises(AlertError):
            adapter.parse_detail(raw(), p)
    def test_tiktok_blocked_hydration_is_never_empty_feed(self):
        ch = self.cfg["channels"]["tiktok_dayz"]
        with self.assertRaises(AlertError):
            TikTokAdapter(ch, self.cfg["retry"]).parse_detail(b"<html>captcha</html>", post("tiktok_dayz"))
    def test_manual_can_send_baseline_without_repost(self):
        p = post()
        self.adapters[p.source_id].posts = [p]
        self.engine().run()
        self.engine().manual(p.source_id, p.url, deliver=True, confirm="SEND", test=True)
        self.assertEqual(len(self.client.calls), 1)
        self.assertEqual(self.store.state["records"][p.key]["reason"], "Controlled test")
    def test_source_initial_metadata_failure_not_healthy(self):
        p = post()
        self.adapters[p.source_id].posts = [p]
        with patch.object(self.adapters[p.source_id], "enrich", side_effect=AlertError("metadata missing")):
            self.engine().run()
        self.assertEqual(self.store.state["sources"][p.source_id]["status"], "DEGRADED")
    def test_incomplete_gif_trailer_rejected(self):
        raw = io.BytesIO()
        images = [Image.new("RGB",(4,4),c) for c in ("red","blue")]
        images[0].save(raw, format="GIF", save_all=True, append_images=images[1:])
        with self.assertRaises(AlertError):
            image_info(raw.getvalue()[:-1], True)
    def test_dynamic_render_missing_optional_metadata_and_mention_safety(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root/"message.txt").write_text("{VIDEO_URL}\n{VIDEO_TITLE}\n{CHANNEL_NAME}\n{PLATFORM}\n{PUBLISHED_AT}", encoding="utf-8")
            ch = copy.deepcopy(self.cfg["channels"]["youtube_dayz"])
            ch["template"] = "message.txt"
            p = post()
            p.title, p.channel_name, p.published_at = "@everyone **evil** <@123>", None, None
            value, _ = payload(root, ch, p)
            self.assertNotIn("@everyone", value["content"])
            self.assertIn("YouTube", value["content"])
            self.assertEqual(value["allowed_mentions"]["roles"], [])
    def test_queue_off_cancels_queued_and_age_expires(self):
        self.baseline()
        p = self.new()
        self.engine().run()
        self.cfg["channels"][p.source_id]["enabled"] = False
        self.engine().run(deliver=True)
        self.assertEqual(self.store.state["records"][p.key]["status"], "disabled")
        self.assertEqual(self.client.calls, [])
    def test_rate_limited_queue_blocks_other_sources_until_next_run(self):
        self.baseline()
        p = self.new()
        self.new("youtube_milo_mia")
        client = FakeClient(DeliveryError("rate limited", retryable=True, retry_after=120))
        self.engine(client).run(deliver=True)
        self.assertEqual(len(client.calls), 1)
        rec = self.store.state["records"][p.key]
        self.assertEqual(rec["status"], "queued")
        self.assertGreater(__import__("video_alerts.model", fromlist=["date"]).date(rec["not_before"]), self.now)
    def test_backup_known_good_is_not_overwritten_by_corrupt_current(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = LocalStore(Path(tmp)/"state.json")
            store.initialize()
            state = store.load()
            store.save(state)
            backup = store.backup.read_bytes()
            store.path.write_bytes(b"invalid")
            with self.assertRaises(AlertError):
                store.save(state)
            self.assertEqual(store.backup.read_bytes(), backup)
    def test_official_tab_membership_positive_only_and_cached(self):
        ch = self.cfg["channels"]["youtube_dayz"]
        adapter = YouTubeAdapter(ch, self.cfg["retry"])
        replies = [{"channel_id": ch["channel_id"], "entries": [{"id": "abcdefghijk"}]}, {"channel_id": ch["channel_id"], "entries": [{"id": "bbbbbbbbbbb"}]}]
        with patch("video_alerts.adapters.extract", side_effect=replies) as mock:
            self.assertEqual(adapter.classify(post()), "short")
            self.assertEqual(adapter.classify(post(pid="bbbbbbbbbbb")), "regular")
            self.assertEqual(adapter.classify(post(pid="ccccccccccc")), "unknown")
            self.assertEqual(mock.call_count, 2)
    def test_official_tab_identity_mismatch_never_classifies(self):
        ch = self.cfg["channels"]["youtube_dayz"]
        with patch("video_alerts.adapters.extract", return_value={"channel_id": "wrong", "entries": [{"id": "abcdefghijk"}]}):
            self.assertEqual(YouTubeAdapter(ch, self.cfg["retry"]).classify(post()), "unknown")
    def test_cloud_corrupt_and_missing_state_restore_forces_safe_baseline(self):
        self.baseline()
        p = self.new()
        self.engine().run()
        checkpoint = self.store.load()
        b64 = __import__("base64")
        commit = "a"*40
        blob = "b"*40
        for status in (200, 404):
            calls = []
            def transport(method, url, body=None, headers=None):
                calls.append((method, url, body))
                if method == "PUT":
                    return Response(200, json.dumps({"content": {"sha": "c"*40}}).encode(), {})
                if "/git/ref/" in url:
                    return Response(200, b'{}', {})
                if "ref=" + commit in url:
                    return Response(200, json.dumps({"content": b64.b64encode(encode(checkpoint)).decode(), "sha": blob}).encode(), {})
                return Response(status, json.dumps({"content": b64.b64encode(b"corrupt").decode(), "sha": blob}).encode(), {})
            store = GitHubStore("owner/repo", "not-a-real-token", transport)
            restored = store.restore(commit, "RESTORE")
            self.assertFalse(restored["sources"][p.source_id]["active"])
            self.assertTrue(restored["sources"][p.source_id]["baseline_needed"])
            self.assertEqual(restored["records"][p.key]["status"], "uncertain")
            sent_data = json.loads(calls[-1][2])
            self.assertEqual("sha" in sent_data, status == 200)
    def test_cloud_restore_authentication_failure_never_writes(self):
        calls = []
        def transport(method, url, body=None, headers=None):
            calls.append(method)
            return Response(403, b"", {})
        with self.assertRaises(AlertError):
            GitHubStore("owner/repo", "not-a-real-token", transport).restore("a"*40, "RESTORE")
        self.assertNotIn("PUT", calls)
    def test_cloud_restore_refuses_different_valid_state_identity(self):
        b64 = __import__("base64")
        current, checkpoint = new_state(), new_state()
        commit = "a"*40
        calls = []
        def transport(method, url, body=None, headers=None):
            calls.append(method)
            if "/git/ref/" in url:
                return Response(200, b'{}', {})
            state = checkpoint if "ref=" + commit in url else current
            return Response(200, json.dumps({"sha": "b"*40, "content": b64.b64encode(encode(state)).decode()}).encode(), {})
        with self.assertRaises(AlertError):
            GitHubStore("owner/repo", "not-a-real-token", transport).restore(commit, "RESTORE")
        self.assertNotIn("PUT", calls)
    def test_youtube_rss_404_falls_back_to_verified_public_channel(self):
        ch = self.cfg["channels"]["youtube_dayz"]
        listing = {"channel_id": ch["channel_id"], "entries": [{"id": "abcdefghijk", "url": post().url}]}
        adapter = YouTubeAdapter(ch, self.cfg["retry"])
        with patch("video_alerts.adapters.public_get", side_effect=AlertError("Public source HTTP 404")), patch("video_alerts.adapters.extract", return_value=listing):
            self.assertEqual(adapter.discover("youtube_dayz")[0].post_id, "abcdefghijk")
        self.assertEqual(adapter.discovery_method, "public_channel_fallback_after_rss_404")
    def test_youtube_bad_fallback_identity_and_non404_fail_closed(self):
        ch = self.cfg["channels"]["youtube_dayz"]
        adapter = YouTubeAdapter(ch, self.cfg["retry"])
        with patch("video_alerts.adapters.public_get", side_effect=AlertError("Public source HTTP 404")), patch("video_alerts.adapters.extract", return_value={"channel_id": "wrong", "entries": []}):
            with self.assertRaises(AlertError):
                adapter.discover("youtube_dayz")
        with patch("video_alerts.adapters.public_get", side_effect=AlertError("Public source HTTP 403")), patch("video_alerts.adapters.extract") as mock:
            with self.assertRaises(AlertError):
                adapter.discover("youtube_dayz")
            mock.assert_not_called()
    def test_uncertain_resolve_verifies_existing_message_without_resend(self):
        self.baseline()
        p = self.new()
        self.engine().run()
        self.store.state["records"][p.key]["status"] = "uncertain"
        self.client.lookup = lambda mid: {"id": mid, "content": p.url}
        engine = self.engine()
        with self.assertRaises(AlertError):
            engine.manage(p.source_id, p.post_id, "resolve", message_id=MID)
        engine.manage(p.source_id, p.post_id, "resolve", "RESOLVE", MID)
        self.assertEqual(self.store.state["records"][p.key]["status"], "sent")
        self.assertEqual(self.client.calls, [])
    def test_uncertain_resolve_wrong_message_never_changes_state(self):
        self.baseline()
        p = self.new()
        self.engine().run()
        self.store.state["records"][p.key]["status"] = "uncertain"
        self.client.lookup = lambda mid: {"id": mid, "content": "another video"}
        with self.assertRaises(AlertError):
            self.engine().manage(p.source_id, p.post_id, "resolve", "RESOLVE", MID)
        self.assertEqual(self.store.state["records"][p.key]["status"], "uncertain")
    def test_discord_lookup_verifies_id_and_is_read_only(self):
        calls = []
        def transport(method, url, *args):
            calls.append(method)
            return Response(200, json.dumps({"id": MID, "content": post().url}).encode(), {})
        client = DiscordClient(WEBHOOK, self.cfg["retry"], transport=transport)
        self.assertEqual(client.lookup(MID)["id"], MID)
        self.assertEqual(calls, ["GET"])
    def test_cli_initialize_monitor_off_and_dryrun_are_non_delivery(self):
        import subprocess
        import shutil
        import sys
        import os
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shutil.copytree(ROOT/"config", root/"config")
            env = dict(os.environ, PYTHONPATH=str(ROOT/"src"), PYTHONUTF8="1")
            for args in (("initialize", "--confirmation", "INITIALIZE"), ("monitor",)):
                result = subprocess.run([sys.executable, "-m", "video_alerts.cli", *args, "--root", str(root)], env=env, capture_output=True)
                self.assertEqual(result.returncode, 0, result.stderr)
            raw = (root/"state/state.json").read_bytes()
            state = decode(raw)
            self.assertTrue(all(s["status"] == "DISABLED" for s in state["sources"].values()))
            result = subprocess.run([sys.executable, "-m", "video_alerts.cli", "dryrun", "--root", str(root)], env=env, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual((root/"state/state.json").read_bytes(), raw)

if __name__ == "__main__":
    unittest.main()

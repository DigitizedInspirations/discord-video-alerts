"""Isolated state validation across fresh processes. No GitHub state or Discord API.

All writes are temporary synthetic test data under ignored .validation/. Production
settings are asserted OFF and never modified. Network sockets are disabled in children.
"""
import argparse
import copy
import json
import os
import socket
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"src"))
from video_alerts.cli import local_lock
from video_alerts.config import load_config
from video_alerts.engine import Engine
from video_alerts.model import AlertError, Post, stamp
from video_alerts.state import LocalStore, decode, merge_restore

NOW = datetime(2026, 1, 1, 10, tzinfo=timezone.utc)

class SyntheticAdapter:
    def __init__(self, posts):
        self.posts = posts
    def discover(self, sid):
        return copy.deepcopy(self.posts.get(sid, []))
    def enrich(self, post):
        return copy.deepcopy(post)

class SyntheticSink:
    def __init__(self, path):
        self.path = path
    def send(self, value, media=None):
        data = json.loads(self.path.read_text()) if self.path.exists() else []
        data.append({"content": value["content"], "synthetic": True})
        self.path.write_text(json.dumps(data), encoding="utf-8")
        return str(123456789012345670+len(data))

def fixture(sid, pid, at, cfg):
    ch = cfg["channels"][sid]
    url = "https://www.youtube.com/watch?v="+pid if ch["platform"] == "youtube" else f"https://www.tiktok.com/@{ch['account']}/video/{pid}"
    return Post(ch["platform"], sid, pid, url, "Synthetic fixture", ch["account"], stamp(at), "regular", True, False, ch["channel_id"] or ch["account"])

def child(directory, phase):
    if "DISCORD_WEBHOOK_URL" in os.environ:
        raise AlertError("Validation must not receive a Discord secret")
    def blocked(*args, **kwargs):
        raise AlertError("Network access forbidden in isolated state simulation")
    socket.socket = blocked
    cfg = load_config(ROOT)
    assert cfg["master_enabled"] is False
    # Synthetic controls exercise ON/OFF; the actual file remains OFF throughout.
    cfg["master_enabled"] = True
    cfg["logging"]["level"] = "WARNING"
    cfg["queue_delay_seconds"] = 0
    now = NOW+timedelta(hours=phase*2)
    posts = {sid: [] for sid in cfg["channels"]}
    posts["youtube_dayz"] = [fixture("youtube_dayz", "aaaaaaaaaaa", NOW-timedelta(hours=1), cfg)]
    if phase >= 2:
        posts["youtube_dayz"].append(fixture("youtube_dayz", "bbbbbbbbbbb", NOW+timedelta(hours=3), cfg))
        posts["tiktok_dayz"].append(fixture("tiktok_dayz", "1234567890123456789", NOW+timedelta(hours=3), cfg))
    if phase >= 4:
        posts["youtube_dayz"].append(fixture("youtube_dayz", "ccccccccccc", NOW+timedelta(hours=7), cfg))
    if phase == 4:
        cfg["channels"]["youtube_dayz"]["enabled"] = False
    if phase == 6:
        cfg["master_enabled"] = False
    store = LocalStore(directory/"state.json")
    if phase == 1:
        store.initialize()
    sink = SyntheticSink(directory/"synthetic-outbox.json")
    with local_lock(directory):
        engine = Engine(ROOT, cfg, store, {sid: SyntheticAdapter(posts) for sid in cfg["channels"]}, sink, clock=lambda: now, sleep=lambda _: None)
        engine.run(deliver=True)
    state = store.load()
    emitted = len(json.loads(sink.path.read_text())) if sink.path.exists() else 0
    assert emitted == (0 if phase == 1 else 2)
    if phase == 5:
        assert state["records"]["youtube:youtube_dayz:ccccccccccc"]["status"] == "baseline"
    if phase == 6:
        assert all(s["status"] == "DISABLED" for s in state["sources"].values())

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--child", type=Path)
    p.add_argument("--phase", type=int)
    args = p.parse_args()
    if args.child:
        directory = args.child.resolve()
        if not directory.is_relative_to((ROOT/".validation").resolve()):
            raise AlertError("Simulation writes must stay in isolated .validation/")
        child(directory, args.phase)
        return
    assert "DISCORD_WEBHOOK_URL" not in os.environ
    cfg_before = (ROOT/"config/settings.json").read_bytes()
    parent = ROOT/".validation"
    parent.mkdir(exist_ok=True)
    checks = []
    with tempfile.TemporaryDirectory(prefix="state-simulation-", dir=parent) as tmp:
        directory = Path(tmp).resolve()
        assert directory.is_relative_to(parent.resolve())
        store = LocalStore(directory/"state.json")
        labels = ["initialization/baseline with no historical announcements", "new publications and cross-platform independent notifications", "deduplication after fresh-process restart", "individual source OFF", "safe OFF-to-ON without disabled-period backlog", "MASTER OFF"]
        for phase, label in enumerate(labels, 1):
            result = subprocess.run([sys.executable, __file__, "--child", str(directory), "--phase", str(phase)], capture_output=True, env=dict(os.environ, PYTHONPATH=str(ROOT/"src"), PYTHONUTF8="1"))
            if result.returncode:
                raise AlertError("Synthetic phase failed: "+label)
            checks.append(label)
        state = store.load()
        assert decode(store.path.read_bytes()) == state
        checks.append("state retrieval/schema/checksum serialization")
        backup = store.backup.read_bytes()
        good = store.path.read_bytes()
        with local_lock(directory):
            try:
                with local_lock(directory):
                    raise AssertionError("Concurrent lock accepted")
            except AlertError:
                pass
        checks.append("concurrent local execution guard")
        with patch("video_alerts.state.os.replace", side_effect=OSError("simulated interrupted write")):
            try:
                store.save(state)
                raise AssertionError("Interrupted write accepted")
            except OSError:
                pass
        assert store.path.read_bytes() == good
        checks.append("interrupted write retains known-good state")
        store.path.write_bytes(b"deliberately corrupt isolated test state")
        try:
            store.load()
            raise AssertionError("Corrupt state accepted")
        except AlertError:
            pass
        checks.append("corruption detected without automatic reinitialization")
        try:
            store.save(state)
            raise AssertionError("Corrupt current state overwritten")
        except AlertError:
            pass
        assert store.backup.read_bytes() == backup
        checks.append("known-good backup protected")
        store.restore(backup, "RESTORE")
        restored = store.load()
        assert restored["instance_id"] == state["instance_id"]
        checks.append("explicit backup restoration")
        merged = merge_restore(state, restored)
        assert merged["records"]["youtube:youtube_dayz:bbbbbbbbbbb"]["status"] == "sent"
        checks.append("restore merge preserves delivered-post tombstones")
    assert (ROOT/"config/settings.json").read_bytes() == cfg_before
    assert load_config(ROOT)["master_enabled"] is False
    checks.append("production config unchanged, MASTER remains OFF")
    report = {"mode": "ISOLATED_SIMULATION", "passed": len(checks), "failed": 0, "checks": checks, "separate_child_processes": 6, "discord_requests": 0, "production_state_requests": 0, "github_contents_writes": 0, "actual_github_durability": "NOT TESTED"}
    print("DVA_REPORT "+json.dumps(report))
    if os.getenv("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as file:
            file.write("## Isolated persistence simulation\n\n"+str(len(checks))+" checks passed across six processes. No Discord requests or production state access. Actual GitHub Contents API durability remains unverified.\n")

if __name__ == "__main__":
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    try:
        main()
    except Exception as exc:
        print(str(exc) if isinstance(exc, AlertError) else "Isolated simulation assertion failed", file=sys.stderr)
        raise SystemExit(1)

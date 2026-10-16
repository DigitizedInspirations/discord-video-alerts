import json
import time
from datetime import timedelta
from .discord import DeliveryError, payload
from .model import AlertError, Post, date, stamp, utcnow
from .state import quarantine_sending, validate_state

def decision(post, ch, cfg, now):
    if post.public is not True:
        return "waiting_metadata", "Publication is not verified public"
    if not post.published_at:
        return "waiting_metadata", "Reliable publication timestamp missing"
    published = date(post.published_at)
    if published > now:
        return "waiting_metadata", "Future publication timestamp"
    if now - published > timedelta(hours=cfg["max_video_age_hours"]):
        return "expired", "Publication exceeds age limit"
    f = ch["filters"]
    if f["enabled"]:
        if f["exclude_livestreams"] and post.kind == "livestream":
            return "filtered", "Livestream excluded"
        if f["exclude_livestreams"] and post.kind == "unknown" and post.platform != "youtube":
            return "waiting_metadata", "Livestream classification unavailable"
        if f["video_types"] != "both" and post.kind == "unknown":
            return "waiting_metadata", "Shorts/regular classification unavailable"
        if f["video_types"] == "shorts" and post.kind != "short":
            return "filtered", "Shorts-only filter"
        if f["video_types"] == "regular" and post.kind != "regular":
            return "filtered", "Regular-only filter"
        if f["exclude_premieres"]:
            if post.premiere is None:
                return "waiting_metadata", "Premiere classification unavailable"
            if post.premiere:
                return "filtered", "Premiere excluded"
        title = post.title.casefold()
        if f["include_keywords"] and not any(v.casefold() in title for v in f["include_keywords"]):
            return "filtered", "No include keyword matched"
        if any(v.casefold() in title for v in f["exclude_keywords"]):
            return "filtered", "Exclude keyword matched"
    return "queued", "Eligible publication"

class Engine:
    def __init__(self, root, cfg, store, adapters, client=None, clock=utcnow, sleep=time.sleep):
        self.root, self.cfg, self.store, self.adapters = root, cfg, store, adapters
        self.client, self.clock, self.sleep = client, clock, sleep
        self.state = store.load()
        quarantine_sending(self.state)
        self.events = []

    def log(self, event, sid=None, **details):
        entry = {"at": stamp(self.clock()), "event": event, "source": sid, **details}
        self.events.append(entry)
        if self.cfg["logging"]["level"] == "INFO" or "error" in details:
            print(json.dumps(entry, ensure_ascii=False))

    def save(self):
        self.store.save(self.state)

    def source_state(self, sid):
        if sid not in self.state["sources"]:
            self.state["sources"][sid] = {"active": False, "baseline_needed": True, "cutoff": stamp(self.clock()), "last_attempt": None, "last_success": None, "last_detected": None, "last_announcement": None, "consecutive_failures": 0, "status": "NOT VERIFIED", "error": None, "alerted_error": None}
        return self.state["sources"][sid]

    def enabled(self, sid):
        return self.cfg["master_enabled"] and self.cfg["channels"][sid]["enabled"]

    def switches(self):
        for sid in self.cfg["channels"]:
            source = self.source_state(sid)
            active = self.enabled(sid)
            if not active:
                source.update(active=False, baseline_needed=True, status="DISABLED", error=None)
                for rec in self.state["records"].values():
                    if rec["post"]["source_id"] == sid and rec["status"] in {"queued", "waiting_metadata"}:
                        rec.update(status="disabled", reason="Intentional OFF; pending announcement cancelled")
                self.log("source_disabled", sid)
            elif not source["active"]:
                source.update(active=True, baseline_needed=True, cutoff=stamp(self.clock()), status="NOT VERIFIED")
                self.log("safe_resume_baseline_required", sid)
        self.save()

    def failure(self, sid, error):
        source = self.source_state(sid)
        source["consecutive_failures"] += 1
        source["error"] = error
        threshold = self.cfg["health"]["failure_threshold"]
        source["status"] = "FAILED" if source["consecutive_failures"] >= threshold else "DEGRADED"
        self.log("source_error", sid, error=error)
        if source["consecutive_failures"] >= threshold and source.get("alerted_error") != error:
            source["alerted_error"] = error
            self.log("health_alert_summary_only", sid, error=error)

    def record(self, post, status, reason):
        self.state["records"][post.key] = {"post": post.dict(), "status": status, "reason": reason, "discovered_at": stamp(self.clock()), "attempts": 0, "message_id": None, "not_before": None, "error": None}
        return self.state["records"][post.key]

    def check(self, sid):
        ch, adapter = self.cfg["channels"][sid], self.adapters[sid]
        source = self.source_state(sid)
        source["last_attempt"] = stamp(self.clock())
        try:
            posts = adapter.discover(sid)
            if not isinstance(posts, list):
                raise AlertError("Adapter did not return a complete listing")
            if getattr(adapter, "discovery_method", "official_rss") != "official_rss":
                self.log("source_transport_fallback", sid, method=adapter.discovery_method)
            for post in posts:
                if post.source_id != sid or post.platform != ch["platform"]:
                    raise AlertError("Adapter source identity mismatch")
                # Validate external IDs/URLs before persisting any discovery results.
                candidate = {"schema_version": self.state["schema_version"], "instance_id": self.state["instance_id"], "created_at": self.state["created_at"], "sources": {}, "records": {post.key: {"post": post.dict(), "status": "baseline", "discovered_at": stamp(self.clock()), "attempts": 0, "message_id": None}}}
                validate_state(candidate)
        except AlertError as exc:
            self.failure(sid, str(exc))
            self.save()
            return
        if source["baseline_needed"]:
            for post in posts:
                if post.key not in self.state["records"]:
                    self.record(post, "baseline", "Safe initial/resume baseline; never backfill")
            source["baseline_needed"] = False
            self.log("baseline_established", sid, posts=len(posts))
            if posts:
                try:
                    sample = adapter.enrich(posts[0])
                    if sample.key != posts[0].key or sample.owner_id is None:
                        raise AlertError("Initial source metadata identity could not be verified")
                    source["metadata_verified"] = True
                except AlertError as exc:
                    source["metadata_verified"] = False
                    self.failure(sid, str(exc))
                    self.save()
                    return
        else:
            pending = {p.key: p for p in posts}
            # Upcoming/metadata-delayed publications may fall out of the short RSS window.
            for key, rec in self.state["records"].items():
                if rec["post"]["source_id"] == sid and rec["status"] == "waiting_metadata":
                    pending.setdefault(key, Post(**rec["post"]))
            metadata_errors = []
            for post in pending.values():
                existing = self.state["records"].get(post.key)
                if existing and existing["status"] != "waiting_metadata":
                    continue
                if post.key not in self.state["records"]:
                    source["last_detected"] = stamp(self.clock())
                    self.log("new_post_detected", sid, post_id=post.post_id)
                try:
                    enriched = adapter.enrich(post)
                    if enriched.key != post.key:
                        raise AlertError("Enriched metadata identity mismatch")
                    status, reason = decision(enriched, ch, self.cfg, self.clock())
                    if enriched.published_at and date(enriched.published_at) <= date(source["cutoff"]):
                        status, reason = "baseline", "Published before safe monitoring cutoff"
                    rec = self.record(enriched, status, reason)
                    if status == "queued":
                        rec["not_before"] = stamp(date(enriched.published_at) + timedelta(minutes=ch["publication_delay_minutes"]))
                    self.log("post_decision", sid, post_id=post.post_id, status=status, reason=reason)
                except AlertError as exc:
                    self.record(post, "waiting_metadata", str(exc))
                    metadata_errors.append(str(exc))
            if metadata_errors:
                self.failure(sid, metadata_errors[0])
                self.save()
                return
            if source.get("metadata_verified") is False and posts:
                try:
                    sample = adapter.enrich(posts[0])
                    if sample.key != posts[0].key or sample.owner_id is None:
                        raise AlertError("Source metadata identity could not be verified")
                    source["metadata_verified"] = True
                except AlertError as exc:
                    self.failure(sid, str(exc))
                    self.save()
                    return
        source.update(last_success=stamp(self.clock()), consecutive_failures=0, status="HEALTHY", error=None, alerted_error=None)
        self.log("source_check_success", sid)
        self.save()

    def run(self, deliver=False):
        self.log("workflow_started")
        self.switches()
        for sid in self.cfg["channels"]:
            if self.enabled(sid):
                self.check(sid)
        self.queue(deliver)
        return self.state

    def queue(self, deliver):
        candidates = [(key, rec) for key, rec in self.state["records"].items() if rec["status"] == "queued"]
        candidates.sort(key=lambda pair: (date(pair[1]["post"]["published_at"] or pair[1]["discovered_at"]), pair[0]))
        sent, attempts = 0, 0
        for key, rec in candidates:
            post = Post(**rec["post"])
            sid, ch = post.source_id, self.cfg["channels"][post.source_id]
            if not self.enabled(sid):
                rec["status"] = "disabled"
                self.save()
                continue
            if rec["not_before"] and date(rec["not_before"]) > self.clock():
                continue
            if not post.published_at or self.clock() - date(post.published_at) > timedelta(hours=self.cfg["max_video_age_hours"]):
                rec.update(status="expired", reason="Queue age limit exceeded")
                self.save()
                continue
            if attempts >= self.cfg["max_messages_per_run"]:
                break
            if not deliver:
                self.log("dry_run_queue_preview", sid, post_id=post.post_id)
                continue
            if not self.client:
                raise AlertError("Live sending needs a configured client")
            if sent:
                self.sleep(self.cfg["queue_delay_seconds"])
            try:
                # Recheck switches and public availability immediately before delivery.
                if not self.enabled(sid):
                    continue
                fresh = self.adapters[sid].enrich(post)
                if fresh.key != post.key:
                    raise AlertError("Delivery metadata identity mismatch")
                status, reason = decision(fresh, ch, self.cfg, self.clock())
                if status != "queued":
                    rec.update(status=status, reason=reason)
                    self.save()
                    continue
                value, media = payload(self.root, ch, fresh, rec.get("use_template", True))
            except AlertError as exc:
                self.failure(sid, str(exc))
                self.save()
                continue
            rec.update(status="sending", attempts=rec["attempts"]+1, delivery_started=stamp(self.clock()))
            self.save()  # Durably acknowledged before any external POST.
            attempts += 1
            try:
                mid = self.client.send(value, media)
            except DeliveryError as exc:
                rec["status"] = "uncertain" if exc.uncertain else "queued" if exc.retryable else "failed"
                rec["error"] = str(exc)
                if exc.retryable:
                    rec["not_before"] = stamp(self.clock() + timedelta(seconds=max(60, exc.retry_after)))
                self.log("discord_error", sid, error=str(exc), status=rec["status"])
                self.save()
                if exc.retryable:
                    break  # Shared webhook rate limit applies to the whole queue.
            else:
                rec.update(status="sent", message_id=mid, delivered_at=stamp(self.clock()), error=None)
                self.source_state(sid)["last_announcement"] = stamp(self.clock())
                self.save()
                sent += 1
                self.log("message_sent", sid, post_id=post.post_id, message_id=mid)

    def manual(self, sid, url, deliver=False, repost=False, confirm="", use_template=True, test=False):
        from .model import video_url
        if sid not in self.cfg["channels"]:
            raise AlertError("Unknown source")
        ch = self.cfg["channels"][sid]
        pid, canonical = video_url(url, ch["platform"], ch["account"])
        candidate = Post(ch["platform"], sid, pid, canonical)
        post = self.adapters[sid].enrich(candidate)
        if post.key != candidate.key or post.public is not True:
            raise AlertError("Manual post identity/public availability cannot be verified")
        value, media = payload(self.root, ch, post, use_template)
        if not deliver:
            return {"payload": value, "media": {k: v for k, v in media.items() if k != "raw"} if media else None, "test": test, "would_send": self.enabled(sid), "duplicate": post.key in self.state["records"]}
        required = "REPOST" if repost else "SEND"
        if confirm != required or not self.enabled(sid):
            raise AlertError(f"Live manual operation needs {required} and enabled master/source switches")
        existing = self.state["records"].get(post.key)
        if existing and existing["status"] in {"sent", "deleted", "sending", "uncertain"} and not repost:
            raise AlertError("Already recorded; an explicit REPOST override is required")
        if existing and existing["status"] in {"sending", "uncertain"}:
            raise AlertError("Uncertain delivery must be resolved before reposting")
        history = [] if not existing else existing.get("delivery_history", []) + [{k: v for k, v in existing.items() if k != "delivery_history"}]
        # Controlled manual sends ignore publication-age/filter/delay restrictions explicitly.
        rec = self.record(post, "sending", "Controlled test" if test else "Explicit manual publication")
        rec.update(attempts=1, delivery_history=history, use_template=use_template)
        self.save()
        try:
            mid = self.client.send(value, media)
        except DeliveryError as exc:
            rec.update(status="uncertain" if exc.uncertain else "failed", error=str(exc))
            self.save()
            raise
        rec.update(status="sent", message_id=mid, delivered_at=stamp(self.clock()))
        self.source_state(sid)["last_announcement"] = stamp(self.clock())
        self.save()
        return {"message_id": mid, "status": "sent"}

    def manage(self, sid, pid, action, confirm="", message_id=""):
        ch = self.cfg["channels"].get(sid)
        if not ch:
            raise AlertError("Unknown source")
        key = f"{ch['platform']}:{sid}:{pid}"
        rec = self.state["records"].get(key)
        if not rec:
            raise AlertError("No recorded announcement")
        if action == "show":
            return rec
        if confirm != action.upper() or not self.client:
            raise AlertError("Explicit action confirmation and webhook required")
        if action == "resolve":
            if rec["status"] not in {"uncertain", "sending"}:
                raise AlertError("Only uncertain/interrupted delivery can be resolved")
            found = self.client.lookup(message_id)
            if rec["post"]["url"] not in found["content"]:
                raise AlertError("Existing Discord message does not contain this post URL")
            rec.update(status="sent", message_id=message_id, resolved_at=stamp(self.clock()), error=None)
            self.save()
            return rec
        if rec["status"] not in {"sent", "deleted"} or not rec["message_id"]:
            raise AlertError("Record has no confirmed Discord message")
        if action == "delete":
            self.client.delete(rec["message_id"])
            rec["status"] = "deleted"  # Retain deduplication tombstone.
        elif action == "edit":
            value, media = payload(self.root, ch, Post(**rec["post"]))
            value.setdefault("attachments", [])  # Explicitly replace old attachments.
            self.client.edit(rec["message_id"], value, media)
            rec["edited_at"] = stamp(self.clock())
        else:
            raise AlertError("Unsupported management action")
        self.save()
        return rec

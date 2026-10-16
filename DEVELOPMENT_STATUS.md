# Πίνακας λειτουργιών — 2026-10-16

Το audited code push και το εγκεκριμένο cloud validation ολοκληρώθηκαν.
**Δεν υπάρχει production readiness:** YouTube Linux metadata BLOCKED, Discord
και πραγματικό GitHub durable state NOT TESTED. MASTER/media OFF, schedule disabled.
VERIFIED αφορά μόνο το περιβάλλον και την απόδειξη της γραμμής· πολλά tests είναι mocks.

62 unittest tests PASS σε Windows και σε κάθε καταγεγραμμένο Linux CI, 0 failed/skipped.
14 isolated filesystem checks PASS ανά περιβάλλον, σε έξι fresh processes. Τα tests
δεν αποδεικνύουν GitHub persistence μεταξύ jobs. TikTok metadata πέρασε σε 3 Linux jobs.
YouTube metadata απέτυχε και στα 3· Node+EJS0.8.0 αφαίρεσαν μόνο το runtime warning,
όχι τα bot/authentication warnings. Δεν προστέθηκαν cookies ή bypasses.

Αποδεικτικά/links: [deployment validation](docs/DEPLOYMENT_VALIDATION.md),
docs/cloud, docs/test-results.txt, docs/local_verification.json, docs/adapter_probe.json.

| Λειτουργία | Status | Απόδειξη / περιορισμός |
|---|---|---|
| Repository origin / workspace | VERIFIED | git status / remote URL |
| Ακριβώς 4 ανεξάρτητες πηγές | VERIFIED | Strict config και source-isolation tests |
| Αυθεντικά UTF-8 TXT templates | VERIFIED | Σύγκριση με το αρχικό master request |
| Config / defaults / ασφαλή paths | VERIFIED | Type/range/unknown-key/traversal tests |
| Master και source ON/OFF | VERIFIED | Mock tests, master αρχικά OFF |
| Initial και OFF→ON χωρίς backlog | VERIFIED | Baseline/history/pending-cancellation tests |
| YouTube IDs / official RSS | PARTIAL | Owner IDs verified· RSS404 και επαναφορά παρατηρήθηκαν Windows/Linux |
| YouTube discovery / public metadata | PARTIAL | Windows VERIFIED, Linux discovery 5/13 VERIFIED αλλά metadata BLOCKED |
| RSS 404 fallback | VERIFIED | Πραγματικό verified public-channel fallback Windows και Linux· enrichment παραμένει ξεχωριστό |
| YouTube Linux συμβατότητα | BLOCKED | 3 cloud audits: λείπουν channel/time/public/live, bot/authentication warnings |
| Standard + Shorts default both | PARTIAL | Public non-live eligible, άγνωστο subtype δεν επινοείται |
| Livestream exclusion | VERIFIED | live_status/was_live mapping tests· real live transition NOT TESTED |
| Shorts-only / regular-only | PARTIAL | Official-tab membership verified στα δύο newest Shorts· unknown εκτός finite window αναβάλλεται |
| Premiere exclusion | PARTIAL | Unknown identity defers, reliable provider classification λείπει |
| Scheduled→public | PARTIAL | Metadata recheck implemented· actual transition NOT TESTED |
| TikTok profile listing | VERIFIED | Windows και 3 Linux jobs: 30 Infinity / 16 Milo & Mia posts |
| TikTok public metadata | VERIFIED | Windows/Linux: newest id/owner/time/privacy και των δύο, 3 cloud samples |
| TikTok production reliability | PARTIAL | Experimental HTML/IP behavior· επιτυχείς Linux στιγμιαίοι έλεγχοι, χωρίς uptime guarantee |
| Platform/source dedup | VERIFIED | Independent cross-platform και repeated-run tests |
| Variables / sanitized metadata | VERIFIED | Dynamic render, missing optional fields και mention safety tests |
| Keywords / filter-change no backfill | VERIFIED | Persisted filter-decision tests |
| Queue / stable order / 10s / ceiling | VERIFIED | Mock timing/order/persistence tests |
| Max age / missing-future time / delays | VERIFIED | 24h expiry, deferred jobs χωρίς long sleeps |
| Discord payload / roles | VERIFIED | Explicit allowed_mentions tests· real role permission NOT TESTED |
| Username / avatar overrides | PARTIAL | Config/public image validation· real client NOT TESTED |
| GIF/static multipart + validation | VERIFIED | Synthetic animation/PNG/multipart/type/MIME/limit tests |
| Authentic branding assets | BLOCKED | Δεν έχουν δοθεί· media OFF, κανένα substitute |
| Media omit/skip fallback | VERIFIED | Missing/invalid-media tests |
| Native / disabled preview | PARTIAL | Original URL / flags=4 payload· client playback NOT TESTED |
| External TikTok embed service | NOT TESTED | Archived vxtiktok researched, provider δεν επιλέχθηκε |
| Webhook acknowledgement / IDs | VERIFIED | Mock wait=true/ID validation· actual POST NOT TESTED |
| Rate limits / bounded retries | VERIFIED | 429 Retry-After, queue deferral, permanent/ambiguous-error tests |
| Local durable state / lock | VERIFIED | Unit tests + 14 isolated checks σε Windows/Linux, έξι fresh processes |
| GitHub durable branch / SHA | PARTIAL | Mock conflict tests· real Contents API writes NOT TESTED |
| Write-ahead / uncertain quarantine | VERIFIED | Save-before-send failure / interrupted-delivery tests |
| Resolve uncertain από υπάρχον ID | VERIFIED | Confirmation + GET/URL match tests χωρίς POST· real API pending |
| Local backup/recovery | VERIFIED | Protected backup, validated restore, tombstone merge |
| Cloud backup/recovery | PARTIAL | Commit-history design and merge restore· real cloud test pending |
| Corrupt/missing cloud state file | PARTIAL | Explicit restore/quarantine/fresh baseline mock-tested· real API pending |
| Missing cloud state branch | BLOCKED | Reviewed Git branch repair required, no auto initialization |
| Find / edit / delete | VERIFIED | Confirmation/ID/tombstone mocks· real operations NOT TESTED |
| Manual / repost / test fixture | VERIFIED | SEND/REPOST/owner/master/dedup tests; actual sends pending |
| Dry run | VERIFIED | No-send / memory-only tests |
| Logs / per-source health | VERIFIED | Structured events, metadata failure, threshold-alert dedup tests |
| Health alert destination | PARTIAL | Logs/Greek summary only· no separate destination supplied |
| Workflow files | VERIFIED | 5 YAML αρχεία, pinned actions, dormant schedule, read-only validation |
| GitHub Actions execution | VERIFIED | CI και isolated workflow PASS· source audits FAIL λόγω YouTube, πραγματικά logs στο docs/cloud |
| €0 operation / offline Windows | PARTIAL | Public standard runners εκτέλεσαν validation· production με 4 πηγές BLOCKED |
| Scoped security audit / scan | VERIFIED | Exact staged audits χωρίς findings, MASTER OFF, validation χωρίς Discord secret |
| Dependencies | PARTIAL | Exact tested versions + pip check· hashes/CVE audit pending |
| Greek README/setup/operations | VERIFIED | Written against current CLI/config |
| AGENTS/context/handoff/changelog | VERIFIED | Accurate local checkpoints |
| Production deployment / schedule | NOT TESTED | Μόνο code push/validation· MASTER OFF, schedule disabled, Discord untested |

Επόμενα: επιτρεπτή λύση YouTube metadata, ξεχωριστή έγκριση για production
initialize/baseline/persistence, πραγματικό Discord/client/media test με αυθεντικά
assets, και τελική νέα έγκριση MASTER/schedule. Το push έχει ήδη εγκριθεί/γίνει.

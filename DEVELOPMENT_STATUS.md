# Πίνακας λειτουργιών — durable canary αποτέλεσμα 2026-10-16

Ο isolated GitHub canary ολοκληρώθηκε στο `dva-canary-20261016-0f9d3a7c`:
δύο fresh hosted runners,4 seed +10 verify checks PASS,0 FAIL. Windows104 mocked
tests/14 filesystem checks PASS· Linux CI/δύο canary jobs104 tests PASS ανά job.
[Report, hashes και commits](docs/DURABLE_CANARY_RESULTS.md). Η branch διατηρείται.
Η άδεια εξαντλήθηκε· όχι νέα runs/state writes/cleanup χωρίς νέα έγκριση.

Production notification-state ανέγγιχτο,0 production/Discord/YouTube requests στον
canary και χωρίς service secrets. MASTER/media OFF, schedule disabled. Production
initialize/baseline/restore, Discord και activation απαιτούν ξεχωριστή έγκριση.
Δεν υπάρχει συνολική production readiness. Το lost ack ήταν τεχνητή έγχυση μετά
από actual write· genuine runner kill/outage, sustained concurrency και production
branch rules παραμένουν NOT TESTED. VERIFIED αφορά μόνο το αναφερόμενο scope.

Το προηγούμενο μοναδικό API run38907646290 πέρασε για τις δύο πηγές: owner/public/
time και official Shorts proof,2 requests/~2 units. Δεν επαναλήφθηκε.
[API report](docs/YOUTUBE_API_CLOUD_VALIDATION.md). Premiere μπορεί να μένει unknown,
live transitions/client/media NOT TESTED. TikTok experimental. OSV exact-lock0
advisories με όρια κάλυψης. Αυθεντικά branding assets δεν έχουν δοθεί.

| Λειτουργία | Status | Απόδειξη / περιορισμός |
|---|---|---|
| Repository origin / workspace | VERIFIED | git status / remote URL |
| Ακριβώς 4 ανεξάρτητες πηγές | VERIFIED | Strict config και source-isolation tests |
| Αυθεντικά UTF-8 TXT templates | VERIFIED | Σύγκριση με το αρχικό master request |
| Config / defaults / ασφαλή paths | VERIFIED | Type/range/unknown-key/traversal tests |
| Master και source ON/OFF | VERIFIED | Mock tests, master αρχικά OFF |
| Initial και OFF→ON χωρίς backlog | VERIFIED | Baseline/history/pending-cancellation tests |
| YouTube IDs / official RSS | PARTIAL | Owner IDs verified· RSS404 και επαναφορά παρατηρήθηκαν Windows/Linux |
| YouTube discovery / public metadata | VERIFIED | Windows public metadata· Linux official API2 newest samples owner/time/public verified |
| RSS 404 fallback | VERIFIED | Πραγματικό verified public-channel fallback Windows και Linux· enrichment παραμένει ξεχωριστό |
| YouTube Linux συμβατότητα | VERIFIED | Official API run38907646290 PASS και91 tests· legacy extractor bot block παραμένει |
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
| GitHub durable branch / SHA | VERIFIED | Synthetic actual Contents API, fresh runner durability και stale-SHA409· production NOT TESTED |
| Write-ahead / uncertain quarantine | VERIFIED | Save-before-send failure / interrupted-delivery tests |
| Resolve uncertain από υπάρχον ID | VERIFIED | Confirmation + GET/URL match tests χωρίς POST· real API pending |
| Local backup/recovery | VERIFIED | Protected backup, validated restore, tombstone merge |
| Cloud backup/recovery | VERIFIED | Synthetic checkpoints/conservative restore/merge PASS· production NOT TESTED |
| Corrupt/missing cloud state file | PARTIAL | Actual synthetic checksum corruption/recovery PASS· missing-state mocked, production NOT TESTED |
| Missing cloud state branch | BLOCKED | Reviewed Git branch repair required, no auto initialization |
| Find / edit / delete | VERIFIED | Confirmation/ID/tombstone mocks· real operations NOT TESTED |
| Manual / repost / test fixture | VERIFIED | SEND/REPOST/owner/master/dedup tests; actual sends pending |
| Dry run | VERIFIED | No-send / memory-only tests |
| Logs / per-source health | VERIFIED | Structured events, metadata failure, threshold-alert dedup tests |
| Health alert destination | PARTIAL | Logs/Greek summary only· no separate destination supplied |
| Workflow files | VERIFIED | Manual-only canary, exact request fence, dedicated write job χωρίς service secrets· άλλα permissions ίδια, schedule disabled |
| GitHub Actions execution | VERIFIED | Canary38915919832/38916699753 και CI38914460856 PASS,104 tests ανά job |
| €0 operation / offline Windows | PARTIAL | Standard public Linux runner/API2 units verified· actual production operation/cost NOT TESTED |
| Scoped security audit / scan | VERIFIED | Exact staged audits χωρίς findings, MASTER OFF, validation χωρίς Discord secret |
| Dependencies | PARTIAL | Exact versions/pip check/OSV0 advisories· hashes/build-tool/Actions coverage εκκρεμούν |
| Greek README/setup/operations | VERIFIED | Written against current CLI/config |
| AGENTS/context/handoff/changelog | VERIFIED | Accurate local checkpoints |
| Production deployment / schedule | NOT TESTED | Μόνο code push/validation· MASTER OFF, schedule disabled, Discord untested |

Επόμενο βήμα με ξεχωριστή έγκριση: state-only production initialization χωρίς
service secrets, άρνηση overwrite, κενό checksum state και ανεξάρτητη retrieval
validation. MASTER/schedule OFF. Baseline, Discord, activation και cleanup θέλουν
ξεχωριστό scope.

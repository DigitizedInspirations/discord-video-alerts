# Πίνακας λειτουργιών — API cloud αποτέλεσμα 2026-10-16

## Νέο isolated durable canary — προετοιμασία

Εγκρίθηκε μόνο το dva-canary-20261016-0f9d3a7c με synthetic data και έως ΔΥΟ manual
fresh-runner workflows. Local104 tests PASS· actual cloud persistence εκκρεμεί.
Production default/notification-state ανέγγιχτο, χωρίς service secrets ή activation.
Ο έλεγχος γίνεται σε actual API requests, όχι μόνο σε πρόθεμα ονόματος branch.

Το official YouTube API validation ολοκληρώθηκε επιτυχώς ΜΙΑ φορά από trusted main
f25153002b4dba8da65beb5af61dee9718f04623. API run[38907646290](https://github.com/DigitizedInspirations/discord-video-alerts/actions/runs/38907646290), CI[38905370126](https://github.com/DigitizedInspirations/discord-video-alerts/actions/runs/38905370126) PASS.
Και οι δύο πηγές: strict API channel/video/public/time VERIFIED, RSS5/13 entries,
official Shorts tab proof.2 requests, estimated2 quota units. Windows91 tests/14
isolated checks PASS· Linux CI/API job91 tests PASS το καθένα. OSV0 known advisories.
VERIFIED αφορά το αναφερόμενο scope, όχι συνολική production readiness.

Δεν έγινε Discord request, secret access στο webhook, production state write ή
activation. MASTER/media OFF, schedule disabled. Κάθε πραγματικό GitHub durable
state write (ακόμη και disposable canary), Discord test ή activation απαιτεί νέα
ξεχωριστή έγκριση. Δεν έγινε αυτόματη επανάληψη API run.

Shorts proof υπάρχει για τα δύο samples, premiere παραμένει unknown και restrictive
filters defer. Live transitions δεν δοκιμάστηκαν πραγματικά. Actual cloud durability,
Discord/client/media και αυθεντικά branding assets παραμένουν blockers.
Αναλυτικό [API cloud report](docs/YOUTUBE_API_CLOUD_VALIDATION.md).

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
| Workflow files | VERIFIED |6 YAML files, pinned actions, API secret μόνο σε dedicated manual step, schedule disabled |
| GitHub Actions execution | VERIFIED | API run38907646290 και CI38905370126 PASS,91 tests ανά job |
| €0 operation / offline Windows | PARTIAL | Standard public Linux runner/API2 units verified· actual production operation/cost NOT TESTED |
| Scoped security audit / scan | VERIFIED | Exact staged audits χωρίς findings, MASTER OFF, validation χωρίς Discord secret |
| Dependencies | PARTIAL | Exact versions/pip check/OSV0 advisories· hashes/build-tool/Actions coverage εκκρεμούν |
| Greek README/setup/operations | VERIFIED | Written against current CLI/config |
| AGENTS/context/handoff/changelog | VERIFIED | Accurate local checkpoints |
| Production deployment / schedule | NOT TESTED | Μόνο code push/validation· MASTER OFF, schedule disabled, Discord untested |

Επόμενο βήμα μόνο μετά από ξεχωριστή έγκριση: περιορισμένο disposable durable-state
canary, μετά ανεξάρτητη έγκριση Discord/client acceptance. MASTER/schedule παραμένουν
OFF έως επιτυχή acceptance και νέα ρητή έγκριση. Δεν υπάρχει production readiness.

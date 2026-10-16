# Πίνακας λειτουργιών — 2026-10-11

Cloud checkpoint 2026-10-16: cfc4b96 pushed, Linux CI 62 PASS, isolated state
14 PASS. TikTok Linux metadata: VERIFIED και για τα δύο προφίλ. YouTube Linux:
discovery VERIFIED μέσω RSS404 fallback, metadata BLOCKED (channel identity).
Ακολουθεί περιορισμένο diagnostic χωρίς cookies ή παράκαμψη ελέγχων.

Συνέχεια 2026-10-16: διορθώθηκε το release audit ώστε το MASTER να ελέγχεται
από το staged config. Το αρχικό Git identity χρησιμοποιείται ανά commit.

Εγκρίθηκε audited push και read-only Linux validation. Επαληθεύτηκε πρόσβαση
στο public repository. Επιπλέον 14 isolated persistence checks πέρασαν σε έξι
νέα processes, χωρίς Discord/production-state requests ή GitHub Contents writes.
Πραγματικό GitHub durable state: NOT TESTED. MASTER/schedule: OFF.

VERIFIED αφορά το αναφερόμενο περιβάλλον. PARTIAL έχει τεκμηριωμένο περιορισμό,
BLOCKED συγκεκριμένο εμπόδιο, NOT TESTED εκκρεμή δοκιμή. Το σύνολο του συστήματος
δεν έχει production verification.

**62 unittest tests PASS**, compileall PASS, config/templates PASS, τέσσερα workflow
YAML PASS, static security scan 0 findings, pip check PASS. Αποδεικτικά:
docs/test-results.txt, docs/local_verification.json, docs/security-scan.json.
Discord tests: mocks. Πραγματικά read-only probes: docs/adapter_probe.json,
docs/source_probe.json.

| Λειτουργία | Status | Απόδειξη / περιορισμός |
|---|---|---|
| Repository origin / workspace | VERIFIED | git status / remote URL |
| Ακριβώς 4 ανεξάρτητες πηγές | VERIFIED | Strict config και source-isolation tests |
| Αυθεντικά UTF-8 TXT templates | VERIFIED | Σύγκριση με το αρχικό master request |
| Config / defaults / ασφαλή paths | VERIFIED | Type/range/unknown-key/traversal tests |
| Master και source ON/OFF | VERIFIED | Mock tests, master αρχικά OFF |
| Initial και OFF→ON χωρίς backlog | VERIFIED | Baseline/history/pending-cancellation tests |
| YouTube IDs / official RSS | VERIFIED | Δύο public profiles + feeds στα Windows |
| YouTube discovery / public metadata | VERIFIED | 1 DayZ / 14 Milo & Mia entries, newest owner/time/public |
| RSS 404 fallback | PARTIAL | Verified public-channel fallback mock-tested· RSS επανήλθε στο επόμενο live probe |
| YouTube Linux συμβατότητα | NOT TESTED | Εκκρεμεί source-audit workflow |
| Standard + Shorts default both | PARTIAL | Public non-live eligible, άγνωστο subtype δεν επινοείται |
| Livestream exclusion | VERIFIED | live_status/was_live mapping tests· real live transition NOT TESTED |
| Shorts-only / regular-only | PARTIAL | Official-tab membership verified στα δύο newest Shorts· unknown εκτός finite window αναβάλλεται |
| Premiere exclusion | PARTIAL | Unknown identity defers, reliable provider classification λείπει |
| Scheduled→public | PARTIAL | Metadata recheck implemented· actual transition NOT TESTED |
| TikTok profile listing | VERIFIED | Windows: 30 DayZ / 11 Milo & Mia posts |
| TikTok public metadata | VERIFIED | Windows: newest id/owner/time/privacy και των δύο |
| TikTok production reliability | PARTIAL | Experimental HTML/IP behavior· Linux NOT TESTED |
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
| Local durable state / lock | VERIFIED | Atomic/checksum/schema/interruption/concurrency tests |
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
| Workflow files | VERIFIED | Four structural YAML checks, pinned actions, dormant schedule |
| GitHub Actions execution | NOT TESTED | No runner dispatched |
| €0 operation / offline Windows | PARTIAL | Public free standard-runner design· deployed evidence pending |
| Scoped security audit / scan | VERIFIED | Regression controls + 0 static findings; not pentest/CVE scan |
| Dependencies | PARTIAL | Exact tested versions + pip check· hashes/CVE audit pending |
| Greek README/setup/operations | VERIFIED | Written against current CLI/config |
| AGENTS/context/handoff/changelog | VERIFIED | Accurate local checkpoints |
| Production deployment / schedule | NOT TESTED | Approval and controlled acceptance required |

Πριν από production: approved push + CI/Linux audit, approved cloud initialization
και δύο persistence runs, approved Discord/client/media test, επίλυση ή ρητή απόφαση
για PARTIAL απαιτήσεις, και νέα έγκριση schedule. Δεν έγινε push, POST ή activation.

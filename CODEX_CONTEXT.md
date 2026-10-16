# Project context — official API cloud acceptance, 2026-10-16

Repo https://github.com/DigitizedInspirations/discord-video-alerts, public main.
Reviewed API implementation f25153002b4dba8da65beb5af61dee9718f04623 pushed and remote SHA verified. Exactly ONE
approved manual API workflow 38907646290 succeeded; automatic CI 38905370126 also passed.
Actual evidence: docs/YOUTUBE_API_CLOUD_VALIDATION.md and docs/cloud/38907646290-evidence.json.
Both configured YouTube newest videos verified channel/public/time via official
API; RSS discovery5/13, official Shorts membership for both,2 API requests~2 units.
Windows91 tests/14 isolated checks PASS; Linux CI/API job each91 tests PASS.

AUTHORIZATION CONSUMED: no further automatic secret-backed API run. Stop for
separate explicit authorization before any actual GitHub durable-state write,
including disposable canaries, Discord tests or production activation. No Discord
request/secret, production state initialize/restore, notification-state change,
MASTER/schedule activation or paid service occurred. MASTER/media OFF; dormant
scheduled.yml.disabled remains unchanged as an inactive file. Main source/report
publication was approved, not notification-state writes. Conversation English;
Greek README/operator guides and exact original UTF-8 templates preserved.

Sources: YouTube @DayZMomentsTV / @milo-and-mia-world and TikTok @infinity.projectrp /
@milo.and.mia.world. Independent adapters → verified metadata → filters → queue →
Discord. Dedup platform+source_id+post_id, never cross-platform. Safe initial/resume
baselines, write-ahead delivery checkpoint, uncertain quarantine/no auto resend.
Local atomic JSON/checksum/protected backup/lock; GitHub Contents API optimistic SHA/
concurrency design unchanged. Actual durable cloud-state writes/recovery remain NOT
TESTED. Missing/corrupt state fails closed, tombstones never discarded automatically.

youtube_api.py: fixed videos.list GET endpoint, header-only environment key, selected
fields, batch50, run-only positive/negative cache, shared cap6 HTTP attempts including
retries. API independently verifies video/channel identity, aware publishedAt,
public+processed and broadcast readiness. Missing/error metadata fails closed with
fixed redacted errors; no API-error fallback. Absence of key retains legacy public
extractor path (still subject to historical Linux bot blocking). API key remains
GitHub-only; it was never retrieved locally or placed in URL/config/log/state.

RSS identity and verified RSS404 fallback preserved. Shorts require official-tab
proof, not duration guesses; API historical premiere identity remains unknown and
restrictive filters defer. Live/upcoming/completed mapping mocked; no actual live
transition was tested. Public API privacy is not proof of every playback restriction.
TikTok implementation and engine/state/config/templates unchanged; all regression
tests pass, including independent TikTok health after API quota failure. Earlier
TikTok Linux public metadata passed3 samples; no extra live TikTok call was made here.

API workflow: manual-only contents:read, pinned Actions, checkout credentials not
persisted; key only in final stateless step. Tests/install/audit have no key and
validation never receives Discord secret or state token. Local controller requires
expected main SHA for API dispatch and refuses auth redirects for log storage.
Two API requests consumed about2 quota units; normal0–2/run or up to96/day at
30-minute cadence, hard cap6/run or288/day plus extra invocations. No billing changes.

Pre-push exact27file staged audit:0 findings, MASTER false, no active schedule.
OSV exact Pillow12.3.0/PyYAML6.0.3/yt-dlp2026.8.19 lookup:0 known advisories; wheel
hashes/build-tool/Actions audit coverage remain limitations. No new runtime deps.
Branding assets absent. Actual Discord/client/media/roles/playback and production
readiness remain unverified. See HANDOFF for precise next approvals and safe resume.

# Project context — YouTube API review, 2026-10-16

LATEST CLOUD AUTHORIZATION: the user reviewed this implementation and approved
an audited commit/push and ONE manual read-only API validation from trusted main.
Real API secret remains GitHub-only and step-scoped. No Discord secret/effects,
actual durable-state writes, MASTER/schedule or paid services. Do not automatically
repeat a real API run; retain outcome. Older review-stage approval gates below
describe the prior checkpoint and are superseded for this single controlled test.
Pre-push repeat:91 tests/14 isolated checks PASS. OSV exact-lock lookup:0 findings;
wheel hashes and build-tool/Actions advisory coverage remain unresolved limitations.

Repo: https://github.com/DigitizedInspirations/discord-video-alerts, public main.
Current committed HEAD eb15885. This API update is local/uncommitted/unpushed.
User reports YouTube Data API v3 enabled and a dedicated API-restricted key stored
in GitHub YOUTUBE_API_KEY. Existing DISCORD_WEBHOOK_URL unchanged; never retrieve,
print or save either secret. New API path has been exercised ONLY with mocked data.

LATEST authorization allows local development/tests and preparing a restricted
workflow. Separate approval is required before pushing new changes or secret-backed
cloud validation. Earlier push authorization is superseded for this update. No
production state writes, Discord effects, MASTER/schedule or paid Google services.
Conversation English; Greek README/operator guides; original templates untouched.

Four sources: YouTube @DayZMomentsTV / @milo-and-mia-world, TikTok @infinity.projectrp
and @milo.and.mia.world. Independent adapters; dedup platform+source_id+post_id.
State: notification-state Contents API/SHA/concurrency, local atomic checksum JSON,
protected backup/lock, write-ahead checkpoint, uncertain quarantine, safe baseline
and OFF-to-ON no backlog. Engine, state schema, TikTok implementation unchanged.

New youtube_api.py uses fixed videos.list GET endpoint, X-Goog-Api-Key header,
selected fields, batch50 and shared per-run cache/six-attempt budget. Key never
appears in URLs/CLI/config/state/logs. API ID and channel must independently match;
public+processed, aware publishedAt and broadcast metadata required. Missing/invalid
data fails closed. No fallback after API errors; legacy extractor remains available
only when no key variable is provided. Factory shares one client across YouTube
sources; TikTok receives no API client/header. No new dependencies or config fields.

RSS identity and verified RSS404 channel fallback remain intact. Shorts rely on
positive official-tab membership; no duration guess. API cannot prove historical
premiere identity; unknown stays unknown and restrictive filters defer. Live and
completed broadcasts conservatively retain livestream exclusion. Client playback
and every possible access restriction are not proven by API privacy metadata.

Prepared workflow youtube-api-validation.yml is workflow_dispatch-only, contents:
read, pinned Actions, no persisted checkout credential. Mock tests/install/audit
receive no API key. Only final stateless validator step gets YOUTUBE_API_KEY; no
Discord secret, production CLI/state or write token. It asserts MASTER OFF/schedule
disabled and refuses a Discord-secret env. Operator/dormant schedule API wiring is
prepared but never run. Local controller allowlist remains unchanged.

Local evidence: 91 tests PASS, 0 failed/skipped; compile/config/six YAML/static scan/
pip check PASS; isolated state simulation14 checks PASS. Initial NaN retry test
failure fixed. API tests use synthetic credentials/responses and prove batching,
caps/redaction/identity/privacy/broadcast/filter guards/dedup/source isolation.
Expected normal0–2 quota units/run, up to96/day at30-minute polling; cap6/run,
up to288/day including retries at that cadence. Real project quota is unverified.

Historical cloud evidence: prior code62 unit tests PASS, filesystem14 PASS; TikTok
public metadata worked in three Linux jobs. YouTube public extraction blocked by
bot/auth warnings; RSS discovery/fallback worked. API/Linux key validation has NOT
been executed, so that blocker is not yet demonstrated resolved. Actual GitHub
durability/restore across jobs, real Discord/client/media, authentic assets and
production scheduling remain unverified. MASTER/media OFF, schedule disabled.

Read HANDOFF.md and docs/YOUTUBE_API_INTEGRATION.md for review, next approvals,
quota/security details and exact files. MASTER request and prior deployment report
remain historical evidence; follow the most recent user authorization.

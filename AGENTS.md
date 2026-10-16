# Discord Video Alerts — project instructions

Build a zero-recurring-cost Python monitor for the four approved accounts. Preserve
the approved message templates exactly. Never merge cross-platform announcements.
Global instructions remain authoritative, including Windows PowerShell restrictions.

Read CODEX_CONTEXT.md, HANDOFF.md, DEVELOPMENT_STATUS.md and recent changes before
work. Inspect the actual Git working tree. Do not restart completed investigations.
Use independent adapters, strict configuration validation, explicit allowed_mentions,
atomic state writes, conservative uncertain-delivery recovery, and bounded retries.
Never log, save or request the Discord webhook token. No paid APIs, CAPTCHA bypasses,
credential harvesting, unrelated modifications, or substitute branding assets.
Do not push, send real Discord messages, enable production schedules, edit or delete
Discord messages without explicit user authorization. Read-only research is permitted.
Use mocks for Discord tests. Keep network compatibility distinct from unit-test results.
After each meaningful milestone run relevant tests and update HANDOFF.md,
DEVELOPMENT_STATUS.md, CHANGELOG.md and CODEX_CONTEXT.md when architecture changes.
Never label an untested feature VERIFIED. Operator instructions must be in Greek.
Conversation updates must be in English; Greek user-facing guides remain Greek.

LATEST CANARY AUTHORIZATION: prepare/audit/push isolated tooling and use at most
TWO manual runs on fresh runners against exactly dva-canary-20261016-0f9d3a7c.
Only synthetic state on that one branch may be read/written/recovered. Do not
delete it. Production default remains notification-state. Fail closed at actual
API requests for any wrong repo/branch/path/checkpoint; no fallback or force push.
Only the dedicated manual canary workflow gets its required write token. It must
receive no Discord/YouTube secret, keep MASTER/schedule OFF, and never alter any
production state. Production initialization/Discord/activation remain unauthorized.
The older stop boundary below is superseded only for this exact isolated canary.

Latest approved API publication and ONE cloud metadata run have completed.
Tested commit f25153002b4dba8da65beb5af61dee9718f04623; successful API run 38907646290,91 Linux tests and2 verified sources.
The single-run authorization is consumed: do not automatically dispatch another
secret-backed API run. Read docs/YOUTUBE_API_CLOUD_VALIDATION.md and HANDOFF.md.
Only the specific stateless validation step may receive YOUTUBE_API_KEY from GitHub
Secrets. Never retrieve/log/save/request its value or give validation the Discord
secret. Keep strict RSS/API video+channel identity, privacy/time, Shorts/premiere
unknown handling, deduplication and source independence. TikTok is unchanged.
Missing/corrupt state fails closed; no auto backfill or retry of uncertain sends.

STOP for separate authorization before ANY actual GitHub durable-state write,
including a disposable canary, Discord integration test, production initialize/
restore, or activation. Never touch notification-state under this completed API
authorization. MASTER/media OFF, schedule disabled. No paid services or billing
changes. Main code/report publication was authorized; production state was not.
91 Windows tests and14 isolated checks pass. OSV exact-lock lookup found0 advisories,
but hashes and build-tool/Actions coverage remain limited. Real API success is one
sample per channel, not proof of live transitions, client playback or production readiness.

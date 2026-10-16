# Discord Video Alerts — project instructions

Build a zero-recurring-cost Python monitor for the four approved accounts. Preserve
approved message templates exactly. Never merge cross-platform announcements.
Global instructions remain authoritative, including Windows PowerShell restrictions.
Read CODEX_CONTEXT.md, HANDOFF.md, DEVELOPMENT_STATUS.md and recent changes before
work. Inspect the actual Git working tree. Do not restart completed investigations.
Use independent adapters, strict configuration validation, explicit allowed_mentions,
atomic state writes, conservative uncertain-delivery recovery and bounded retries.
Never log, save or request webhook tokens or API keys. No paid APIs, CAPTCHA
bypasses, credential harvesting, unrelated changes or substitute branding assets.
Use mocks for Discord tests. Keep network evidence distinct from unit-test results.
After meaningful milestones run relevant tests and update HANDOFF.md,
DEVELOPMENT_STATUS.md, CHANGELOG.md and CODEX_CONTEXT.md for architecture changes.
Never label an untested feature VERIFIED. Operator guides remain Greek; conversation
remains English. Preserve sandbox and approval restrictions.

## Active approval — ONE empty production initialization

Latest user approval supersedes the prior initialization stop ONLY for ONE empty
notification-state creation and independent verification through the dedicated
manual initialize-state.yml workflow. Prepare/test/audit/commit/push is authorized.
Exact repository DigitizedInspirations/discord-video-alerts, trusted main/full SHA,
operation initialize_empty_state, confirmation INITIALIZE_EMPTY_NOTIFICATION_STATE_ONCE.
Refuse if branch/file exists or is inaccessible. No overwrite/reset/repair/restore.
Publish one state-only root commit by creating its ref last, at most three creation
POSTs; no retry or destructive repair after failed/uncertain acknowledgement.
Only dedicated job gets contents:write; token explicitly in initialization step.
Never use operate.yml; never receive Discord/YouTube secrets or run engine/adapters.
Initialize new UUID4/schema/checksum with sources={} and records={}; no canary,
history, queue or baselines. New read-only GitHubStore must independently verify.
MASTER/media OFF, production schedule disabled. Stop on any mandatory failure;
report partial/unacknowledged writes with read-only diagnosis, never repair/retry.
After success publish evidence/continuity and STOP. Baseline/source queries,
monitoring, real Discord, recovery, cleanup and activation need separate approval.

Earlier API run38907646290 and canary runs38915919832/38916699753 are consumed.
Retain dva-canary-20261016-0f9d3a7c unchanged; no new canary operations. See
docs/PRODUCTION_INITIALIZATION.md and HANDOFF.md for current progress.
128 mocked local tests and14 isolated filesystem checks PASS; production cloud
initialization pending. Fresh OSV exact lock0 findings, with hash/build-tool/Actions
coverage limits. Do not label pending production behavior VERIFIED.

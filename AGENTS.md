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

## Completed authorization and current stop boundary

ONE approved API cloud run38907646290 succeeded; its permission is consumed.
TWO approved canary runs38915919832/38916699753 succeeded on exactly
dva-canary-20261016-0f9d3a7c. Their permission is consumed. Keep branch available;
no more dispatches/state writes/cleanup. See docs/DURABLE_CANARY_RESULTS.md.
Audited source/report publication remains authorized. Production GitHubStore default
remains notification-state. Preserve exact request isolation and checkpoint
provenance/ancestry. No canary fallback to production. Missing/corrupt state fails
closed; never auto-retry uncertain sends or backfill initial/disabled periods.

STOP for separate approval before additional durable-state writes, production
initialize/baseline/restore, real Discord tests/messages/edit/delete, canary cleanup
or activation. Never touch notification-state under the completed canary grant.
No Discord/YouTube secrets in state validation. MASTER/media OFF, production
schedule disabled. No production history/queue/baseline/record changes. Do not push
unrelated work or enable paid services. Any separately authorized API key use must
remain environment/Actions Secrets only, without exposing values.

104 mocked tests and14 filesystem checks passed locally; both canary Linux runs
passed104 tests and collectively14 real persistence checks. Exact-lock OSV0 known
advisories has hash/build-tool/Actions coverage limits. API success remains one
sample/channel; live transitions/client playback/production readiness unverified.

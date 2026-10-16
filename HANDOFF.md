# Working checkpoint — YouTube API local review, 2026-10-16

Latest checkpoint: user now approves an audited commit/push and ONE manual secret-
backed read-only API workflow from trusted main. No automatic repeat. Stop afterward
for separate approval before any actual durable-state writes, Discord or activation.
91 tests/14 state checks passed again. OSV scan of three exact locked versions found
zero known vulnerabilities; hashes/build-tool/Actions coverage remain limited.
Controller is being scoped to API workflow with mandatory expected-main SHA.
The review-stage restrictions below describe the earlier checkpoint.

Current task: official YouTube Data API metadata integration after user-provided
Cloud setup. User reports API v3 enabled, a restricted dedicated key stored only
in GitHub YOUTUBE_API_KEY, and the Discord secret unchanged. Never retrieve its value.

## Authorization — latest message supersedes earlier push permission

Local implementation, mocked tests and restricted workflow preparation ONLY.
Do not push new changes or execute secret-backed cloud validation until separate
approval of this reviewed implementation. No real Discord effects, production state
writes, MASTER activation, schedule or paid Google Cloud services. Conversation
English; operator guides Greek. No global settings changes.

## Completed locally

- src/video_alerts/youtube_api.py: fixed Google endpoint, header-only key, selected
  public fields, batch50, per-run positive/negative cache, shared six-attempt cap,
  bounded retries and safe fixed errors. API independently verifies video/channel,
  timestamp, privacy, upload readiness and broadcast details.
- adapters.py: API selected by environment-variable presence, shared across both
  YouTube sources. RSS/channel identity and RSS404 fallback preserved. Missing env
  retains legacy public extraction; API errors never silently fall back.
- Shorts use official-tab proof; premiere unknown remains deferred when excluded.
  No duration heuristic, privacy assumption or weakened identity check.
- .github/workflows/youtube-api-validation.yml: manual-only, contents:read, mock
  tests/install/audit without secrets; only final stateless step gets API key.
  No Discord secret/state access. Script guards MASTER/schedule and Discord env.
- Prepared key wiring in manual operations and dormant scheduled workflow only;
  neither was executed. Existing controller does not dispatch the new workflow.
- Google-key literal detection added to static/proposed/staged scans; local test
  runner refuses real service-secret environments. No new dependency/config schema.
- All 91 tests PASS (62 existing + 29 new), 0 failed/skipped; compile/config/
  six YAML/static scan/pip check PASS. Existing isolated simulation14 PASS across
  six processes; zero Discord/production-state/GitHub Contents requests.
- New engine tests prove API-post baseline/dedup and TikTok independence during quota
  failure, with no key in state. Stateless validation tested end-to-end with mocks.
- First test run caught Retry-After:NaN handling; fixed and regression passes.

## Review state and evidence

HEAD remains eb15885a7d9e4b3e83dd8d90019c2c96d1e48e87; no new commit/push or cloud
run occurred. Changes are local for review, including new untracked module/tests/
workflow/script/report. docs/YOUTUBE_API_INTEGRATION.md is the full technical report.
Evidence: docs/test-results.txt, docs/local_verification.json, docs/security-scan.json,
docs/prepush-audit.json. No actual API secret or API response exists locally.

Estimated normal quota0–2 units/run; at a hypothetical30-minute cadence up to96/day.
Shared hard cap6 HTTP attempts/run includes retries, up to288/day at that cadence,
plus extra manual invocations. No paid services or quota increases were enabled.

## Existing architecture / historical evidence

Independent adapters → verified metadata → filters → persistent sequential queue.
Dedup key platform+source_id+post_id, safe initialization/OFF-to-ON baselines, write-
ahead Discord checkpoints, uncertain quarantine/no auto resend. Local atomic/checksum/
backup/lock and GitHub notification-state Contents API/SHA design unchanged.
Do not discard tombstones or auto-initialize missing/corrupt production state.

Previous deployed code eb15885 had62 passing Linux tests and14 filesystem checks.
Both TikTok profiles passed three actual Linux source audits. YouTube RSS/fallback
discovery worked, but public per-video extraction failed with bot/authentication
warnings despite Node+EJS. Those are historical results, not API verification.
Links/evidence remain in docs/DEPLOYMENT_VALIDATION.md and docs/cloud.

## Precise next steps

1. Review local diff and docs/YOUTUBE_API_INTEGRATION.md; wait for separate approval
   before pushing or using the real API secret. Do not reuse old approval.
2. After approval, run a fresh exact staged audit, publish only reviewed files,
   observe mock CI, then dispatch ONLY the restricted API validation workflow.
   The controller currently lacks this secret-backed workflow in its allowlist;
   use the approved GitHub workflow UI or explicitly scope a controller update then.
3. Record actual Linux/API identity/time/privacy, quota counts and safe failures.
   Do not claim the historical cloud blocker resolved from mocks.
4. Real GitHub durability across jobs remains NOT TESTED; production initialization
   and all Discord/client/media tests need their own authorization.
5. Shorts/premiere identity limits, finite discovery windows, TikTok HTML/IP stability,
   absent authentic assets, client playback and dependency hashes/CVE scan remain.
6. MASTER/media stay OFF and scheduled.yml.disabled stays dormant throughout.

Safe local verification (no real service-secret env):
`.\.venv\Scripts\python.exe scripts/check_local.py`
and `.\.venv\Scripts\python.exe scripts/cloud_state_simulation.py`.

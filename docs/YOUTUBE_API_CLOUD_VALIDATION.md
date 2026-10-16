# Approved YouTube API cloud validation — 2026-10-16

## 1. Deployment Summary

Audited, committed and pushed the reviewed integration as
[f25153002b4dba8da65beb5af61dee9718f04623](https://github.com/DigitizedInspirations/discord-video-alerts/commit/f25153002b4dba8da65beb5af61dee9718f04623).
Public main matched this SHA before dispatch; the controller requires expected-main
SHA and refuses branch drift. Exactly ONE secret-backed API run was dispatched.
This report/evidence publication follows that tested implementation without another
real API run. MASTER/media remain OFF; scheduled.yml.disabled remains inactive.

## 2. GitHub Actions Results

| Workflow | Result | Evidence |
|---|---|---|
| Restricted YouTube API metadata validation | SUCCESS | [38907646290](https://github.com/DigitizedInspirations/discord-video-alerts/actions/runs/38907646290) |
| Automatic local-quality CI on integration commit | SUCCESS | [38905370126](https://github.com/DigitizedInspirations/discord-video-alerts/actions/runs/38905370126) |

The API job used workflow_dispatch from trusted main, contents:read and Python3.12
on a standard Ubuntu runner. Checkout/setup-python are pinned; checkout credentials
are not persisted. Dependency installation, mock tests and safeguard checks had no
API key. Only the stateless final API step received YOUTUBE_API_KEY. No Discord
secret, production CLI or state access was supplied. Subsequent report-only CI
uses mocked tests and does not cause an additional API execution.

## 3. Source Compatibility

Both sources independently passed official API video/channel identity, aware
publication timestamp, public privacy, processed upload and ready-public checks.
RSS discovery succeeded with5 DayZ and13 Milo & Mia entries; API requests used
batched discovered IDs. Full per-post validation sampled the newest video per source.

| Source | Verified channel ID | Video ID | Published (UTC offset) | Availability | Official tab |
|---|---|---|---|---|---|
| @DayZMomentsTV | UCz5ka9rKYsdaeaxmN_7nHbg | bkSyrLsRuS4 | 2026-10-15T14:04:58+00:00 | public | short |
| @milo-and-mia-world | UCg1uoL9TtAaxvyn6dbQ08fA | KwmMj-mCuKg | 2026-10-15T14:00:31+00:00 | public | short |

Both metadata_method values were youtube_data_api_v3; discovery_method official_rss.
Windows previously verified public extractor metadata for the same samples; current
Windows API tests are mocked only. Actual secret-backed API verification happened
only in the one approved Linux run. Earlier yt-dlp bot blocking remains a limitation
of the legacy no-key path, not a failure of this API test.

## 4. Test Results

| Check | Executed | Passed | Failed | Skipped |
|---|---:|---:|---:|---:|
| Windows unit suite before push |91|91|0|0|
| Windows isolated state simulation |14|14|0|0|
| Linux automatic CI unit suite |91|91|0|0|
| Linux API workflow unit suite (no secrets) |91|91|0|0|
| Actual API source validations |2|2|0|0|

Compilation, config/templates, six YAML files, scoped static scan, pip dependency
compatibility and exact staged whitespace checks passed. Original62 plus29 API/
security/engine tests include TikTok independence during a YouTube quota failure.
No regression was observed. TikTok code, templates, config schema, engine/state and
dedup design remained unchanged; no extra live TikTok test was performed here.

## 5. Cloud Persistence

Still PARTIAL / actual GitHub durability NOT TESTED. Fourteen isolated filesystem
checks passed across six fresh child processes. They do not establish Contents API
durability across jobs. No notification-state branch was created/read/modified by
this validation, no production initialization or restore occurred, and no actual
durable-state canary was run. Separate authorization is required before any such test.

## 6. Security Audit

Exact staged audit covered27 changed/new files before implementation push, with
zero findings. Reviewed all modified/new workflows and the full implementation diff.
No API key, webhook URL, cookies, credential files, .env, local environment or raw
sensitive output was committed. Validation has only manual dispatch and contents:read;
push triggers mock CI only. MASTER false and inactive schedule were verified.
The Google key was read by the dedicated step only, never retrieved locally, logged,
stored in state/config, placed in URL or passed as a CLI argument. API errors are
fixed/redacted and authenticated redirects are refused. Full downloaded logs stay
under ignored .validation; committed evidence contains selected public fields only.

OSV querybatch/advisory audit of Pillow12.3.0, PyYAML6.0.3 and yt-dlp2026.8.19 found
zero known advisories (docs/dependency-audit.json, recorded timestamp retained).
Unresolved limitations: lock has no wheel hashes; GitHub Actions/build-only
setuptools/pip advisory coverage is outside that lookup; no independent pentest.
No known critical issue was found in the reviewed scope. No paid service, quota
increase or billing change was introduced.

## 7. Known Issues and Classification Limits

- Both sample videos had positive official /shorts tab membership. API kind remains
  unknown for Shorts-vs-regular until official-tab classification is needed; API
  duration/URL shape never fabricates a type. Unknown restrictive filters defer.
- Premiere is null/unknown for both samples. The API does not provide reliable
  historical premiere identity; exclude_premieres continues to defer unknowns.
- Current/upcoming/completed broadcast mapping and exclusion are mock-tested.
  Neither real sample exercises an actual live/premiere transition. Public metadata
  is not proof of every regional/client playback or access restriction.
- RSS can intermittently404 and listings are finite; verified channel fallback is
  retained. TikTok remains experimental despite earlier Linux successes.
- Real GitHub durable state, Discord/client/roles/avatar/media/playback, uncertain
  delivery recovery with real services and production scheduling remain untested.
  Authentic branding assets remain absent.

## 8. Feature Verification Matrix

| Feature | Status | Scope |
|---|---|---|
| Official API metadata on Linux | VERIFIED | Two configured channels, one actual run |
| Video/channel identity, public/time readiness | VERIFIED | Both newest API samples plus negative mocked tests |
| RSS discovery and source separation | VERIFIED | Actual RSS; original independent engine tests |
| Shorts classification | PARTIAL | Positive tab proof for both samples; unknown outside finite listing |
| Premiere classification | PARTIAL | Unknown is deferred, not guessed |
| Livestream exclusion/transitions | PARTIAL | Mapping mocked; real transition NOT TESTED |
| Queue/dedup/switches/TikTok isolation | VERIFIED |91 regression tests with stated mock scope |
| Actual GitHub durable state | NOT TESTED | No actual state writes authorized |
| Real Discord/client/media | NOT TESTED | No webhook effects authorized |
| Production activation | NOT TESTED | MASTER OFF / schedule disabled |

## 9. Documentation & Handoff

AGENTS.md, CODEX_CONTEXT.md, HANDOFF.md, DEVELOPMENT_STATUS.md and CHANGELOG.md
updated to record the single completed run and next authorization boundary. Greek
README/deployment/operations guides preserved and updated. Public API/CI results
and sanitized reports are under docs/cloud. The earlier local implementation report
remains as historical design/test evidence, with a link to this actual acceptance.

## 10. Quota and Next Steps

Actual HTTP request counter: 2 videos.list calls, estimated
quota units: 2. No retries were needed (two batches
for two source lists). This is request-based estimation, not a Cloud Console quota
or billing measurement. Normal0–2 units/run implies up to96/day at a hypothetical
30-minute cadence; shared six-attempt cap implies up to288/day at that cadence,
plus extra manual invocations. Scheduling remains disabled.

The one approved secret-backed run is complete; no automatic rerun occurred.
STOP for separate explicit authorization before any actual GitHub durable state
write (including disposable canaries), Discord integration test, production-state
initialize/baseline/restore or MASTER/schedule activation. A next proposal should
scope disposable state tests independently from Discord tests and activation.
No production-readiness claim is made by this metadata-only acceptance.

# Four-source production baseline — FAILED SAFELY, 2026-10-17

The ONE approved attempt failed strict TikTok metadata validation. The production
write step was skipped. **Zero production write attempts, zero committed baseline
records, zero queued/sent notifications.** The existing empty state is unchanged.
Authorization `four-source-baseline-87757f44` is consumed. No rerun, retry, repair,
new source probe, production write or activation is authorized.

## Source and cloud evidence

- Implementation: [`4b6a1598f78e12f4d95cec2d304b0e068bdd40ac`](https://github.com/DigitizedInspirations/discord-video-alerts/commit/4b6a1598f78e12f4d95cec2d304b0e068bdd40ac).
- Source CI [38983356531](https://github.com/DigitizedInspirations/discord-video-alerts/actions/runs/38983356531): SUCCESS.
- Single baseline run [38984066072](https://github.com/DigitizedInspirations/discord-video-alerts/actions/runs/38984066072): FAILURE during metadata.
- Windows:156 regression tests PASS,0 FAIL;14 isolated filesystem persistence
  checks PASS. Compile/config/YAML/security/pip consistency checks PASS.
- Linux source CI:156 tests PASS,0 FAIL. Baseline job:156 tests PASS,0 FAIL;
  hosted safeguard audit and initial production preflight PASS. Metadata FAIL;
  optimistic state update and baseline readback step SKIPPED.

Baseline attempt timestamp: `2026-10-16T23:57:37.783544+00:00`
(2026-10-17,02:57:37 Europe/Athens). No baseline timestamp was committed.

| Source / approved account | Discovered finite window | Metadata result | Committed baseline records |
|---|---:|---|---:|
| youtube_dayz / @DayZMomentsTV | 6 | All6 verified public/owner/time/URL | 0 |
| youtube_milo_mia / @milo-and-mia-world | 14 | All14 verified public/owner/time/URL | 0 |
| tiktok_dayz / @infinity.projectrp | 30 | FAILED strict public HTML metadata validation | 0 |
| tiktok_milo_mia / @milo.and.mia.world | 17 | Discovery only; enrichment not reached | 0 |

The6/14 `baseline_records` counters in the metadata diagnostic represent verified
in-memory proposals only. No complete candidate was emitted, no state write step
ran, and none of these20 proposed identities reached production.

YouTube used the existing verified public-channel fallback after RSS404 for both
accounts. API ownership matched `UCz5ka9rKYsdaeaxmN_7nHbg` and
`UCg1uoL9TtAaxvyn6dbQ08fA`, respectively. Public publication ranges:

- DayZ: `2026-10-10T19:04:29+00:00` through `2026-10-16T14:00:29+00:00`.
- Milo & Mia: `2026-10-01T12:23:10+00:00` through `2026-10-16T14:00:21+00:00`.

One shared official videos.list request verified all20 YouTube videos: estimated
**1 quota unit** (maximum configured request budget6). No paid service was added.

Exact failure: `tiktok_dayz: TikTok public HTML metadata missing, private,
incomplete or identity mismatch`. The existing parser intentionally combines these
failure categories. Retained diagnostics do not identify the failed post/field or
prove which category caused rejection. Do not call this confirmed privacy or owner
mismatch. No additional public probes, alternative parser, skip, weaker validation,
cookie/authentication workaround or automatic retry was attempted. Discovery of
the second TikTok account succeeded, but its metadata remains NOT TESTED in this run.

## Independent production-state verification after failure

A NEW read-only BaselineTransport and NEW GitHubStore made three fenced GETs at
`2026-10-17T00:00:18.316021+00:00`. They validated schema/checksum/raw Git blob,
exact initial identity/content and the same branch head before/after retrieval.

| Evidence | Before | After |
|---|---|---|
| Production commit | dffc5833c9c69d69acde3180e1b760255d116250 | dffc5833c9c69d69acde3180e1b760255d116250 |
| Git blob SHA | 6cb68f2eefbadf5ffc2d8efe611eaed29bffc055 | 6cb68f2eefbadf5ffc2d8efe611eaed29bffc055 |
| Canonical SHA256 | ab2350425c1426621905f314f12ea723eb33ebb20fb816bf7bcd68e8e7a48b1c | ab2350425c1426621905f314f12ea723eb33ebb20fb816bf7bcd68e8e7a48b1c |

Schema1, instance `e0dae2af-a0a5-424d-aa2e-216ca84c287a`, creation time
`2026-10-16T19:42:22.688305+00:00`, `sources={}`, `records={}`. No production
baseline, history, queue, backup, initialization, restoration or repair occurred.
No new production commit exists. The retained canary branch was untouched.

## Security and regression outcome

Full runtime/workflow diff reviewed; exact20-file staged source audit:0 findings.
Fresh OSV audit:0 known advisories for the unchanged exact dependency lock. Wheel
hashes are absent; build tools/Actions lie outside that lock advisory audit, and
advisory coverage is not a guarantee of no vulnerabilities. Hosted safeguard audit
PASS. No credential values, cookies, environment files or sensitive output committed.

Manual-only workflow; trusted main/reviewed SHA/run attempt1; exact repo/branch/
confirmation/authorization and live single-run history checks. Default contents:read;
only the baseline job has contents:write/actions:read. Checkout does not persist
credentials. YouTube key was available only to metadata; GitHub token only to
fenced state steps. No workflow received DISCORD_WEBHOOK_URL. Zero Discord requests,
payloads, announcements or service-secret mixing in the baseline operation.

MASTER/media remain OFF; production scheduling disabled. Sources remain uninitialized
and inactive. Normal engine/config/adapters/templates/TikTok behavior unchanged;
no implementation regression was observed by the suites. TikTok live reliability
remains an external compatibility blocker, not a passing unit-test claim. Strict
window-wide metadata validation exposed a failure that newest-video samples did not
establish coverage for. No security/identity/privacy rules were relaxed.

## What remains unverified and next approval

The intended production atomic update, production stale-SHA conflict behavior and
independent committed-baseline readback were NOT EXERCISED. Their mocks passed,
but the real operation correctly stopped before writing. Future OFF-to-ON safe
resume/no historical backfill passed mocked regression tests; no activation occurred.

Finite RSS/profile/extractor windows never imply complete account history. Shorts
and historical premiere identity may remain unknown, real livestream/premiere
transitions remain untested, and TikTok public HTML/IP reliability is experimental.
No Discord/client/media acceptance, monitoring or production readiness is claimed.
Smart Monitoring Schedule remains future final-stage scope, unimplemented/disabled.

Next approval must explicitly scope targeted TikTok diagnostics and any reviewed
fix. A further baseline attempt requires a NEW single-attempt authorization and
fresh unchanged-state preflight; this grant must not be reused. Monitoring,
Discord delivery, further production writes, recovery/cleanup, MASTER/schedule
activation and paid services remain unauthorized. STOP for review.

Evidence: [job results](cloud/38984066072-result.json),
[metadata evidence](cloud/38984066072-evidence.json),
[phase reports](cloud/38984066072-phases.json),
[independent state inspection](cloud/38984066072-state-inspection.json),
[Linux CI evidence](cloud/38983356531-evidence.json).

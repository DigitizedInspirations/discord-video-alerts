# Deployment validation — 2026-10-16

> Historical checkpoint. The two-run synthetic GitHub canary is now complete;
> see [actual results](DURABLE_CANARY_RESULTS.md). Both runs are consumed.
> Production state remains untouched; all activation gates remain closed.


## 1. Deployment Summary

Pushed the audited implementation cfc4b968f2d3123302a2750a477276a7c9273a0b to public
main in DigitizedInspirations/discord-video-alerts. Follow-ups 623ad56 and 95de8cf
record evidence and diagnostics. The final report/docs commit follows these revisions.
This is code publication and controlled validation, not live announcement deployment.
MASTER/media OFF; schedule disabled; no production state or Discord effects.

## 2. GitHub Actions Results

| Run | Workflow | Outcome | Commit |
|---|---|---|---|
| [38834116442](https://github.com/DigitizedInspirations/discord-video-alerts/actions/runs/38834116442) | CI | PASS | cfc4b96 |
| [38834738641](https://github.com/DigitizedInspirations/discord-video-alerts/actions/runs/38834738641) | Isolated state | PASS: 14 checks | cfc4b96 |
| [38834735917](https://github.com/DigitizedInspirations/discord-video-alerts/actions/runs/38834735917) | Source audit | FAIL: YouTube metadata | cfc4b96 |
| [38836796267](https://github.com/DigitizedInspirations/discord-video-alerts/actions/runs/38836796267) | CI | PASS | 623ad56 |
| [38836896270](https://github.com/DigitizedInspirations/discord-video-alerts/actions/runs/38836896270) | Source audit + diagnostic | FAIL: YouTube metadata | 623ad56 |
| [38837567165](https://github.com/DigitizedInspirations/discord-video-alerts/actions/runs/38837567165) | CI | PASS | 95de8cf |
| [38837567703](https://github.com/DigitizedInspirations/discord-video-alerts/actions/runs/38837567703) | Source audit + runtime comparison | FAIL: YouTube metadata | 95de8cf |

All jobs used standard ubuntu-latest runners and Python3.12. Dependency installation
worked. CI checks config and workflow structure in addition to unit tests; state
validation checks pip compatibility and production safeguards. Failed source audits
are retained as failures; no continue-on-error or requirement removal hid the blocker.
The Node comparison was a one-off diagnostic installation, now removed from the
workflow; its public report remains in 38837567703-evidence.json.

## 3. Source Compatibility

| Source | Windows October16 | Linux, 3 jobs | Limitation |
|---|---|---|---|
| YouTube @DayZMomentsTV | VERIFIED newest owner/public/time, Short | BLOCKED metadata; discovery VERIFIED, 5 posts | bot/authentication warning; channel/time/public fields absent |
| YouTube @milo-and-mia-world | VERIFIED newest owner/public/time, Short | BLOCKED metadata; discovery VERIFIED, 13 posts | same cloud restriction |
| TikTok @infinity.projectrp | VERIFIED, 30 listed | VERIFIED newest public owner/time, 30 listed | experimental, sample success is not uptime proof |
| TikTok @milo.and.mia.world | VERIFIED, 16 listed | VERIFIED newest public owner/time, 16 listed | experimental HTML/IP behavior |

YouTube newest IDs: bkSyrLsRuS4 / KwmMj-mCuKg. Windows publication times:
2026-10-15T14:04:58+00:00 / 2026-10-15T14:00:31+00:00. First Linux discovery
used verified public-channel fallback after RSS404; later jobs recovered official RSS.
TikTok newest IDs: 7694665449945959702 / 7696819705918622998; times
2026-10-09T13:51:56+00:00 / 2026-10-15T14:00:00+00:00, verified on Linux.
YouTube failures do not prevent evaluation of TikTok or other sources.

## 4. Test Results

| Verification | Executed | Passed | Failed | Skipped |
|---|---:|---:|---:|---:|
| Windows unit suite | 62 | 62 | 0 | 0 |
| Linux unit suite per recorded CI run (3 runs above) | 62 | 62 | 0 | 0 |
| Windows isolated filesystem simulation (October11) | 14 | 14 | 0 | 0 |
| Linux isolated filesystem simulation | 14 | 14 | 0 | 0 |
| Linux source checks per audit (3 audits) | 4 | 2 | 2 blocked | 0 |

Compile/config/YAML/static scan/pip check passed locally; CI validated Linux packages,
config/YAML/tests. These counts distinguish unit tests, simulation checks and real
source checks; they are not a combined unique-test count. Subsequent report-only CI
runs also execute the same 62-test suite and can be found in Actions.

## 5. Cloud Persistence

PARTIAL. Linux temporary filesystem survived six fresh child processes. Fourteen
checks cover initialization/baseline, new posts, cross-platform separation, restart
dedup, source OFF, OFF-to-ON no backlog, MASTER OFF, serialization/retrieval, lock,
interrupted write, corruption, protected backup, explicit restore and tombstones.
The report groups related assertions into 14 checks. Production config was unchanged.
No Discord, production-state or GitHub Contents requests were made by simulations.
The notification-state Contents API architecture, optimistic SHA, permissions and
commit-history recovery are mock-tested but actual cloud durability across jobs is
NOT TESTED. The next live persistence test must be explicitly scoped to disposable
resources (never production history); production initialize requires separate approval.

## 6. Security Audit

Exact staged audits passed before every push with no findings. No webhook URL/token,
cookies, .env, virtual environment, keys or private local logs were staged. No real
Discord secret was read, exposed or passed to validation. Minimal read permissions,
pinned Actions, inactive schedule and MASTER false were verified. Fixed staged
config inspection. Credentials from the existing Git helper remain in memory only;
no authenticated redirects to log storage. This is a scoped audit, not a pentest or
live CVE audit. Dependency hashes remain a documented limitation.

## 7. Known Issues

- YouTube cloud enrichment BLOCKED: public extractor returns missing identity/time
  fields with authentication/bot warnings. Existing Node+official EJS0.8.0 eliminated
  runtime warnings but did not fix access. No cookies/proxy/CAPTCHA workaround used.
- Candidate zero-cost alternative: evaluate official YouTube Data API within free
  quota, requiring a restricted key and a new tested adapter/config path. This is
  not enabled or verified; see https://developers.google.com/youtube/v3/getting-started.
  Windows metadata works, but an always-on Windows host does not meet the desired
  PC-off architecture and is not an adopted solution.
- TikTok remains experimental despite three Linux successes; public HTML/IP changes
  or finite windows can fail later. No alternative provider is needed/selected yet.
- Premiere identity, finite subtype windows, scheduled-to-public transitions and
  external embed-provider behavior remain partial. Unknown restrictive filters defer.
- Actual Discord/client formatting/roles/avatars/media/playback, real delivery IDs,
  edit/delete and cloud production recovery are NOT TESTED. Authentic assets absent.

## 8. Feature Verification Matrix

| Feature | Status | Scope |
|---|---|---|
| Config/templates/queue/dedup/switches/recovery | VERIFIED | unit/mocked and isolated filesystem tests |
| Linux runtime/dependency compatibility | VERIFIED | successful CI and pip checks |
| TikTok public newest metadata on Linux | VERIFIED | three independent samples, not reliability guarantee |
| TikTok long-term monitoring | PARTIAL | experimental public HTML/IP behavior |
| YouTube cloud discovery/RSS404 fallback | VERIFIED | actual runner evidence |
| YouTube cloud per-video metadata | BLOCKED | bot/auth warning and missing channel/time fields |
| GitHub durable state across separate jobs | PARTIAL | architecture/mocks; actual writes NOT TESTED |
| Real Discord effects/client/media | NOT TESTED | no live test authorized |
| Authentic branding assets | BLOCKED | absent |
| Production MASTER/schedule | NOT TESTED | intentionally OFF/disabled |

Full requirement matrix: ../DEVELOPMENT_STATUS.md; VERIFIED always has the stated scope.

## 9. Documentation & Handoff

Updated AGENTS.md, CODEX_CONTEXT.md, HANDOFF.md, DEVELOPMENT_STATUS.md and CHANGELOG.md.
Updated Greek README and deployment guide; operations guide remains applicable.
Security audit and public Windows/Linux result/evidence JSON files are retained.
No credentials or full downloaded runner logs are committed. Handoff identifies the
safe next steps, failed approaches, exact commits, actual evidence and authorization.

## 10. Next Steps

Choose a permitted YouTube metadata solution before all-four-source acceptance.
If adopting an official API, configure a restricted key through the approved secret
store and authorize the necessary design/config change; never paste keys in chat.
Any actual durable cloud canary must have a reviewed disposable branch scope.
Production initialization/baselines, real Discord tests and MASTER/schedule activation
require their own explicit approvals. Supply authentic branding files for media tests.
No production-readiness claim is supported by the current provider/state/client gaps.

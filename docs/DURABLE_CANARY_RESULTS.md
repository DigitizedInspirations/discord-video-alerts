# GitHub durable persistence canary results — 2026-10-16

Completed within scope: ONE disposable branch, TWO manual runs, synthetic data
only. **14 actual cloud checks passed,0 failed.** Both run permissions are consumed.
No more dispatches, state writes or cleanup are authorized. The branch is retained:
[dva-canary-20261016-0f9d3a7c](https://github.com/DigitizedInspirations/discord-video-alerts/tree/dva-canary-20261016-0f9d3a7c).

## Reviewed source, runs and independent runners

Tested implementation: [`b0541e2d6a9e0f039818396c03edc6c464e79e1c`](https://github.com/DigitizedInspirations/discord-video-alerts/commit/b0541e2d6a9e0f039818396c03edc6c464e79e1c). Evidence publication is a
later source/report commit; cloud results apply to the implementation above.

| Purpose | Run | Result | Mocked tests | Job / runner identity |
|---|---|---|---:|---|
| Source CI | [38914460856](https://github.com/DigitizedInspirations/discord-video-alerts/actions/runs/38914460856) | SUCCESS | 104 | Hosted Linux CI |
| Seed | [38915919832](https://github.com/DigitizedInspirations/discord-video-alerts/actions/runs/38915919832) | SUCCESS,4 cloud checks | 104 | Job 117023242549; runner 1000000012 / GitHub Actions 1000000012 |
| Verify | [38916699753](https://github.com/DigitizedInspirations/discord-video-alerts/actions/runs/38916699753) | SUCCESS,10 cloud checks | 104 | Job 117025888776; runner 1000000013 / GitHub Actions 1000000013 |

Seed completed before verify was dispatched. A separate fresh GitHub-hosted runner
loaded the identical instance, canonical hash and Git blob SHA **before its first
write**. Runner identities come from GitHub job metadata in `*-result.json`;
empty runner-name arrays in log evidence are not used as runner proof. Both jobs
used ubuntu-latest/Python3.12. Windows pre-push:104 mocked tests (91 existing +13
canary) and14 isolated filesystem simulation checks passed. The14 simulations are
separate from the14 actual GitHub canary checks, not extra real cloud evidence.

## Actual persistence checks

| Phase | Check | Result |
|---|---|---|
| Seed | real canary branch and checksum state initialization | PASS |
| Seed | real Contents API synthetic write and exact retrieval | PASS |
| Seed | recoverable commit checkpoint and cross-run fingerprint stored | PASS |
| Seed | all actual API operations fenced to exact disposable branch; no production requests | PASS |
| Verify | exact state/blob/hash durability from independent completed run | PASS |
| Verify | synthetic dedup records and tombstones survive fresh runner | PASS |
| Verify | real optimistic stale-SHA conflict rejects overwrite | PASS |
| Verify | lost acknowledgement after actual write reconciled without resend; intent quarantined | PASS |
| Verify | recoverable canary checkpoint preserved before destructive fault | PASS |
| Verify | actual corrupt GitHub state detected and never auto-initialized | PASS |
| Verify | failed-load write blocked before network | PASS |
| Verify | real checkpoint recovery quarantines queue and requires safe baseline | PASS |
| Verify | older-checkpoint merge preserves newer dedup/tombstones and final retrieval | PASS |
| Verify | all actual API operations fenced to exact disposable branch; no production requests | PASS |

Real Contents API reads/writes and commit-history recovery were exercised. Stale
SHA PUT returned HTTP409 without overwriting the winning state. Lost acknowledgement
was injected **after a successful real GitHub write**. A fresh read reconciled it
and quarantined the sending intent without resending. This was client-side fault
injection, not a genuine GitHub outage or runner termination.

A recoverable checkpoint was committed before checksum corruption. Corrupt load
failed closed and save after failed load was blocked before network. Explicit
recovery quarantined queued work and required a fresh safe baseline. An older
checkpoint merge preserved newer delivered records/tombstones. Final state was
retrieved and validated again.

## State fingerprints

| Item | Value |
|---|---|
| Instance | `98194f7c-db9d-427b-8d02-2ebc20f5648f` |
| Initial canonical SHA256, unchanged across runs | `baeea4beee643e4987c446517c6c81b2cea7d65607bfb9fb736994f7022f9e07` |
| Initial Git blob SHA | `68403437966c68240f94c4dd677462bf0572ab33` |
| Pre-corruption recovery canonical SHA256 | `bb242acc3648f594d3e07e800e4c6e74596dff7d24667229b822849b012d24e0` |
| Final canonical SHA256 | `d3f72142544af0a4571d986359d56ea77a01ca19ccea3cd2614a834a8e050444` |
| Final Git blob SHA | `4082ab2fe43b682c8717a2fa539bcc28260f0631` |
| Final state commit | `5642550cd2eb12f28adacbe4752f213810face6d` |
| Retained branch head / final marker | `82a87957bb18f7473d54860f2acc82d698c5dfb3` |

Canonical hashes identify validated serialized state; Git blob SHAs identify stored
bytes. They are different hash types and are not interchangeable.

## Actual disposable-branch commit inventory

| Phase | Purpose | Commit |
|---|---|---|
| Seed | Initialize synthetic state | [`2c17020f427c0d73c2a3feee7152e34249370ad2`](https://github.com/DigitizedInspirations/discord-video-alerts/commit/2c17020f427c0d73c2a3feee7152e34249370ad2) |
| Seed | Seed records/checkpoint | [`dfa0f53c9f7a550e08054a661d43e97f29d6831c`](https://github.com/DigitizedInspirations/discord-video-alerts/commit/dfa0f53c9f7a550e08054a661d43e97f29d6831c) |
| Seed | Seed fingerprint marker | [`fa262e603cb3003bffbe93f174b0a42210a6f727`](https://github.com/DigitizedInspirations/discord-video-alerts/commit/fa262e603cb3003bffbe93f174b0a42210a6f727) |
| Verify | Winning optimistic write | [`c542036a87e8435645ab49f456da1ab7ca80bba1`](https://github.com/DigitizedInspirations/discord-video-alerts/commit/c542036a87e8435645ab49f456da1ab7ca80bba1) |
| Verify | Write then lost-ack injection | [`d211c5368f4b0841586cb6605b00c6bb4d8bc0df`](https://github.com/DigitizedInspirations/discord-video-alerts/commit/d211c5368f4b0841586cb6605b00c6bb4d8bc0df) |
| Verify | Quarantined recovery checkpoint | [`f460335f563600c88d79991ea02d76974b5258f2`](https://github.com/DigitizedInspirations/discord-video-alerts/commit/f460335f563600c88d79991ea02d76974b5258f2) |
| Verify | Pre-corruption marker | [`83efbe8656eeaf91fd7f52f9af0c7e01f6a8e77c`](https://github.com/DigitizedInspirations/discord-video-alerts/commit/83efbe8656eeaf91fd7f52f9af0c7e01f6a8e77c) |
| Verify | Inject checksum corruption | [`079101ac204373a2c3eae66fd94b5fff2b294604`](https://github.com/DigitizedInspirations/discord-video-alerts/commit/079101ac204373a2c3eae66fd94b5fff2b294604) |
| Verify | Explicit conservative recovery | [`8f2073948b7895461f5c0756e5dddd84cd091df9`](https://github.com/DigitizedInspirations/discord-video-alerts/commit/8f2073948b7895461f5c0756e5dddd84cd091df9) |
| Verify | Final merged state | [`5642550cd2eb12f28adacbe4752f213810face6d`](https://github.com/DigitizedInspirations/discord-video-alerts/commit/5642550cd2eb12f28adacbe4752f213810face6d) |
| Verify | Final verification marker | [`82a87957bb18f7473d54860f2acc82d698c5dfb3`](https://github.com/DigitizedInspirations/discord-video-alerts/commit/82a87957bb18f7473d54860f2acc82d698c5dfb3) |

## Security, isolation and regressions

- Production GitHubStore default remains `notification-state`; no production CLI
  branch switch was added. Canary uses an explicitly supplied alternative branch.
- CanaryTransport fences actual requests to the exact repository, branch and
  allowed paths. Wrong targets, main/production state refs, unapproved checkpoint
  refs, DELETE and PATCH/force updates are rejected. Missing/inaccessible canary
  never falls back to production. Recovery validates canary-tagged commit
  provenance and ancestry in the approved branch history.
- Bootstrap read main Git-ref metadata to create the branch from source; it did
  not read notification state on main or on notification-state.
- Both reports record0 production-state requests,0 Discord requests and0 YouTube
  requests. Production history, queues, baselines and records were untouched by
  this canary. Isolation is supported by the transport fence, tests and API trace;
  no production read was used to establish it.
- Manual-only workflow, trusted main, no reruns, default contents:read; only the
  dedicated canary job gets contents:write. Token explicitly supplied only to the
  canary step. No Discord/YouTube secret references or access. Checkout does not
  persist credentials; Actions are pinned. Other workflow permissions unchanged.
- Push CI runs mocks/static/config checks only; it cannot dispatch canary operations
  or write notification state. Synthetic IDs/titles/times/message records contain
  no real user or Discord data. Published evidence is sanitized; full logs ignored.
- MASTER/media OFF, production schedule disabled. No force push, deletion, paid
  service, billing change, production operation or real Discord effect occurred.
- No dependencies added. Existing exact-lock OSV lookup found0 known advisories;
  wheel hashes/build-tool/Actions advisory coverage remain unresolved limits.
- All existing regressions passed, including TikTok/source-isolation tests. TikTok,
  approved templates and YouTube discovery/identity/privacy safeguards unchanged.
  No extra live TikTok or YouTube call was made by this canary.

## Technical fixes and limitations

Load-ref validation was safely generalized for an explicitly supplied canary branch
while preserving the production default. The actual request fence covers reads,
initialization, writes and recovery. Checkpoints require provenance and ancestry.
Post-run diagnostic changes correct the canary dispatch label and retain GitHub
job runner identities; they do not change the cloud-tested state algorithm.
No unexpected cloud failures occurred. Expected stale-SHA/corruption failures were
successful safety checks, not test failures.

Untested: genuine runner kill/GitHub or network outage, sustained simultaneous load,
production branch policies/permissions, production initialization/recovery, real
delivery and Discord/client/media acceptance. Fault handling was tested only with
the described controlled injections. Historical Shorts/premiere/live-transition
limits, experimental TikTok reliability and missing authentic branding remain.
This result does not establish overall production readiness.

## Proposed next stage — separate approval required

Prepare/review a state-only production initialization workflow without Discord or
YouTube secrets. After explicit approval, check whether notification-state exists
and refuse overwrite if present. Initialize empty checksum state only, then
independently retrieve/validate it. Keep MASTER/scheduling OFF. Production source
baselines, Discord tests, activation and canary cleanup require separately scoped
approval. Do not perform those actions under this completed grant.

Evidence: docs/cloud/38915919832-{result,evidence}.json,
docs/cloud/38916699753-{result,evidence}.json and source CI
docs/cloud/38914460856-{result,evidence}.json. They preserve results, API traces,
runner metadata, commits and hashes without credentials.

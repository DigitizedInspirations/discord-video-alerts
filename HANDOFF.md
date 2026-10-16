# Handoff — durable persistence canary complete, 2026-10-16

## Outcome and exact evidence

ONE branch `dva-canary-20261016-0f9d3a7c`, TWO manual runs: **14 real cloud checks PASS,0 FAIL**.
Tested source [`b0541e2d6a9e0f039818396c03edc6c464e79e1c`](https://github.com/DigitizedInspirations/discord-video-alerts/commit/b0541e2d6a9e0f039818396c03edc6c464e79e1c).
Seed [38915919832](https://github.com/DigitizedInspirations/discord-video-alerts/actions/runs/38915919832) PASS (4 checks),
verify [38916699753](https://github.com/DigitizedInspirations/discord-video-alerts/actions/runs/38916699753) PASS (10 checks).
Distinct hosted runners 1000000012 and 1000000013.
Source CI [38914460856](https://github.com/DigitizedInspirations/discord-video-alerts/actions/runs/38914460856) PASS.
Each Linux job104 mocked tests PASS; Windows104 tests/14 filesystem checks PASS.
Full14-check list,11 commits, state hashes and limitations:
[DURABLE_CANARY_RESULTS](docs/DURABLE_CANARY_RESULTS.md), sanitized cloud JSON.

Initial hash `baeea4beee643e4987c446517c6c81b2cea7d65607bfb9fb736994f7022f9e07` recovered unchanged before verify writes.
Final hash `d3f72142544af0a4571d986359d56ea77a01ca19ccea3cd2614a834a8e050444`; retained branch head
`82a87957bb18f7473d54860f2acc82d698c5dfb3`. Do not delete branch.
Real initialization/read/write, cross-run dedup, stale-SHA409, lost-ack reconciliation,
checkpoint, checksum rejection/no-save-after-failed-load, quarantine/baseline
recovery and older-checkpoint merge passed. Lost ack was injected after an actual
successful write, not a genuine GitHub outage. No unexpected cloud failures.

## Authorization boundary — STOP for review

Both canary runs and earlier single API run are consumed. No further dispatch,
rerun, state write or cleanup. Audited source/report publication and automatic
unkeyed mock CI only remain authorized. Production notification-state untouched;
no production/Discord/YouTube requests or service-secret access by this canary.
MASTER/media OFF; schedule disabled. Production initialize/baseline/restore,
real Discord, activation and cleanup require separate approval. Never auto-retry
uncertain sends, weaken identity/privacy checks or backfill history.

## Implementation and fixes

src/video_alerts/state.py: optional explicit branch and safe load-ref validation,
production default unchanged, no production CLI override. canary.py: exact actual
request fence and checkpoint provenance/ancestry. scripts/durable_canary.py:
seed/verify synthetic state and bounded faults. Dedicated manual-only workflow:
contents:read default, contents:write canary job, token explicitly only in canary
step, no service secrets, pinned Actions, credentials not persisted. Other workflow
permissions unchanged. tests/test_canary.py adds13 tests. Controller enforces
reviewed SHA/order/max two dispatches. Post-run diagnostics fix dispatch label and
capture runner metadata without changing cloud-tested state logic. No dependency
added. Plan preserved in docs/DURABLE_CANARY_PLAN.md.

## Existing evidence and remaining limits

ONE API run38907646290 on f25153002b4dba8da65beb5af61dee9718f04623 passed both
YouTube owner/public/time samples and official Shorts proof,2 requests/~2 units.
See docs/YOUTUBE_API_CLOUD_VALIDATION.md. RSS/identity/privacy and TikTok preserved.
Premiere/live transitions, finite subtype windows, TikTok reliability and playback
remain partial. Exact-lock OSV0 advisories with hash/build-tool/Actions coverage
limits. Full logs ignored under .validation; no credentials published.
Genuine runner kill/network outage, sustained concurrency, production branch rules,
production recovery and Discord/client/media/roles/delivery/edit/delete untested.
Authentic branding assets still missing; no production readiness claim.

## Proposed next stage — separately approved production initialization

Prepare/review state-only workflow without Discord/YouTube secrets. After explicit
approval, check notification-state existence and refuse overwrite. Initialize only
empty checksum state, then retrieve/validate independently. MASTER/schedule OFF.
Production baseline, Discord acceptance, activation and cleanup require separate
scope. Do not perform them under this grant; stop after publication for review.

Local verification: .venv Python scripts/check_local.py,
scripts/cloud_state_simulation.py and scripts/release_audit.py --staged. Do not
rerun real API/canary tests. Use Git author per commit, not global settings.
Five mandatory continuity files and Greek guides updated for completed canary.

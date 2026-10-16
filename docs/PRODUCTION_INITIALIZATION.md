# One-time production initialization — reviewed plan, 2026-10-16

> Historical reviewed plan. Actual attempt failed in the config guard BEFORE any
> writer/API creation. Do not rerun. See [failed result](PRODUCTION_INITIALIZATION_RESULTS.md).
> The creation protocol remains cloud-untested; a NEW approval is required.


Status: local implementation/validation; production initialization is NOT YET
TESTED. Latest user approval permits ONE empty initialization after all preflights,
an audited source push and one dedicated manual workflow dispatch. No baseline,
engine, source query, service-secret access, delivery, recovery, cleanup or activation.

## Scope and preflight

Exact repository `DigitizedInspirations/discord-video-alerts`, trusted `main`, target
`notification-state`, operation `initialize_empty_state`, confirmation
`INITIALIZE_EMPTY_NOTIFICATION_STATE_ONCE`. Reviewed full main SHA is required.
Initial read-only inspection saw main `5a5961f74fc80b05b0b3ad0f6211497b551b5386`
and no notification-state ref. The workflow repeats authoritative API checks.
MASTER/media OFF, schedule disabled. Wrong repository/ref/event/SHA/inputs,
service-secret variables, reruns and existing/inaccessible branch/file fail closed.
Controller refuses any second initialization dispatch, even after a failed run.

## Creation-only protocol

The actual-request fence in `production_init.py` permits only these creation POSTs:

1. A Git tree with exactly `state.json`, no base tree. It contains new_state():
   schema1, fresh UUID4/time, sources={}, records={} and validated SHA256 envelope.
2. An independent root commit with parents=[] pointing at that tree. No main or
   canary history/source files are copied.
3. After repeating main/absence preflight, creation of the exact new branch ref.
   Publication is atomic and last; an existing ref is never updated.

Three creation POSTs maximum, each consumed before I/O. No PUT/PATCH/DELETE, force,
retry, import or repair. Failure before publication can leave immutable unpublished
objects. Any uncertain acknowledgement stops; bounded read-only diagnosis records
known SHAs/branch status for manual review, without retrying or repairing anything.
The existing production GitHubStore initialization/recovery implementation is unchanged.

## Workflow and independent verification

`initialize-state.yml`: workflow_dispatch only, trusted exact repository/main,
run_attempt1, serialized without cancellation. Default contents:read; its dedicated
job contents:write. Pinned Actions, checkout credentials not persisted. Mocked tests
and safeguard audit run before the only step with explicit GITHUB_TOKEN env. No
service secrets, operate.yml, engine or adapter operation. Other permissions unchanged.

A new read-only transport and new GitHubStore retrieve via Contents API, validate
schema/checksum and compare exact generated identity/state/blob SHA. Independent
reads verify root commit, empty parents, state-only tree, stable branch commit and
trusted main. Local immutable source/config is rechecked for MASTER/schedule OFF.
Logs contain safe hashes, object/run IDs and request paths/statuses, never credentials.

## Validation and boundaries

Tests cover creation order/empty state, existing/inaccessible state, wrong targets,
imports, failed/lost acknowledgements, races, malformed responses, corruption,
branch/main drift, repeat refusal, read-only verification, environment/workflow
contracts and exact one-time controller dispatch. See test-results.txt and
local_verification.json for complete local results. Fourteen filesystem checks
also pass; these are separate from actual production evidence.
Fresh exact-lock OSV found0 advisories. Wheel hashes, build-tool and Actions audit
coverage remain limits. No dependency added. Full diff and exact staged credential/
private-path/workflow audit must pass before source publication or dispatch.

After ONE initialization and verification, publish evidence/continuity and stop.
Next approval must explicitly scope production baselining/source validation.
Discord acceptance, monitoring, activation, recovery and cleanup remain separate.

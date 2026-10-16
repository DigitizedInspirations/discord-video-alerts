# Isolated durable canary — approved plan

> Historical checkpoint. The two-run synthetic GitHub canary is now complete;
> see [actual results](DURABLE_CANARY_RESULTS.md). Both runs are consumed.
> Production state remains untouched; all activation gates remain closed.


Only branch: `dva-canary-20261016-0f9d3a7c`, retained afterward. At most TWO manual
`durable-canary.yml` runs from the same reviewed main commit, with no reruns.
Production GitHubStore default remains `notification-state`; production CLI has
no alternative branch switch. Only the dedicated canary step receives GITHUB_TOKEN
from its contents:write job. No Discord/YouTube secrets or public-source queries.
Other workflow permissions, MASTER=false and dormant schedule remain unchanged.

GitHubStore supports an explicit canary-only alternative. CanaryTransport enforces
the EXACT approved repository and branch on every actual request. It denies wrong
state refs, unapproved checkpoint SHAs, other paths/hosts, DELETE, PATCH/force-update
and branch drift. Historical state reads require canary-tagged commits proven to
be ancestors of the canary branch. Reads of repository metadata/main Git ref are
allowed only to bootstrap the single branch; state on main/production is forbidden.
Missing/inaccessible canary never falls back to production or automatically resets.

Run1 seeds new checksum state, synthetic sent/deleted/queued records and a marker
with canonical state hash, blob SHA, instance ID, seed run ID and checkpoint commit.
No real user/Discord data is used. Existing internal source IDs exercise the real
state schema; video IDs, channel/title, timestamps and message IDs are fabricated.
Branch starts from main source-code tree; production notification-state is never read.

Run2 starts only after run1 succeeds and terminates. A fresh runner checks identical
state/hash/blob/instance and dedup records BEFORE any write. It tests a real stale-SHA
rejection, successful GitHub write followed by injected lost acknowledgement, fresh
read reconciliation and uncertain quarantine. It stores a recoverable checkpoint,
then corrupts only synthetic state checksum, verifies failed-load/no-write behavior,
restores from an approved canary commit and tests older-checkpoint merge preserving
newer delivered/tombstone truth. Final state and reports remain inspectable.

Lost acknowledgement is client-side fault injection after a real GitHub write;
this is not a claim of an actual GitHub outage. No production delivery is attempted.
Controller caps two dispatches; workflow rejects reruns/other refs; marker prevents
repeating completed phases. Local104 tests cover positive protocol and hostile scope.
Actual API outcomes/commits/hashes will be recorded after the two authorized runs.

Stop afterward. Any canary cleanup, production initialization, Discord integration
or activation needs separate authorization. No paid service or force push is allowed.

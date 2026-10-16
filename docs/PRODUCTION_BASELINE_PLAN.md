# Four-source baseline-only authorization — 2026-10-17

Authorization `four-source-baseline-87757f44` permits ONE manual attempt and at
most ONE state-file update. It does not authorize monitoring or activation.

The existing production state must match commit
`dffc5833c9c69d69acde3180e1b760255d116250`, blob
`6cb68f2eefbadf5ffc2d8efe611eaed29bffc055`, canonical SHA256
`ab2350425c1426621905f314f12ea723eb33ebb20fb816bf7bcd68e8e7a48b1c`, schema 1,
UUID `e0dae2af-a0a5-424d-aa2e-216ca84c287a`, creation time
`2026-10-16T19:42:22.688305+00:00`, and empty sources/records. No initialization,
repair, reset, recovery, backup write or branch cleanup is permitted.

## Dedicated execution path

`baseline-state.yml` is manual-only, trusted main/run_attempt=1, reviewed full SHA,
exact repository/branch/authorization/confirmation. Default token is contents:read;
only its baseline job has contents:write and actions:read. Other workflows are
unchanged. Checkout credentials are not persisted. Tests/audit have no credentials.
The preflight and write steps receive only the GitHub token. Only the metadata
step receives YOUTUBE_API_KEY; it receives no GitHub token. No step receives the
Discord secret or invokes operate.yml, the engine, or Discord code.

The controller refuses dispatch unless there are zero previous baseline runs.
Both remote preflights require exactly this single run in workflow history,
matching main/source/event/path/run attempt. Any failed attempt also consumes the
grant. Neither dispatch nor PUT is automatically repeated after any uncertain
acknowledgement. On failure stop for review.

1. Read and independently validate the exact initialized production state and live
   main/run identity before any metadata work. Reads are fenced to exact GitHub
   repository, branch and paths. Actual raw Contents bytes must match their blob.
2. Discover all four existing finite public windows with unchanged adapters: RSS
   and existing verified 404 fallback for YouTube; public TikTok profile listings.
   Require nonempty list windows, at most 30 entries/source, canonical URLs,
   unique video IDs and correct source identities. Empty, malformed, unavailable,
   oversized or duplicate windows fail. No claim of complete historical coverage.
3. Batch both YouTube lists through one cached official API client, normally
   1–2 videos.list calls (1 quota unit each); maximum 6 attempts across the shared
   client. Public adapters retain existing bounded retry settings (3 attempts;
   yt-dlp retries/extractor retries 1, 30-entry listing cap). At most 60 TikTok
   detail requests before retries. Job timeout 25 minutes; candidate age <=30 min.
4. Enrich EVERY listed video. Require canonical identity, exact verified account,
   explicit public availability and reliable publication timestamp no later than
   the captured baseline timestamp. Unknown privacy/time fails the whole operation.
   Unknown Shorts/premiere classifications remain unknown; baseline records cannot
   send and do not bypass future eligibility filters. No filters are relaxed.
5. Build the entire four-source state in memory, preserving original instance ID,
   schema and creation time. Only baseline records, attempts=0/message_id=None,
   no queues, sends, delivery history, pending metadata or announcements. Sources
   inactive, DISABLED, baseline_needed=True, metadata_verified=True. This deliberately
   preserves Engine.switches() OFF-to-ON fresh resume-baseline behavior. Production
   engine/config/settings/templates/TikTok behavior are unchanged.
6. Without any service secret, validate the proposal and repeat remote preflight.
   Make exactly one PUT through GitHubStore.save, fenced to state.json,
   notification-state, initial blob SHA and exact encoded candidate. Reject stale
   SHA/concurrent change. The attempt is consumed before network execution. No
   POST/PATCH/DELETE, alternate branch, initialization or recovery API is allowed.
7. New read-only transport and NEW GitHubStore reload schema/checksum/identity,
   exact state/blob, commit parent, state-only tree, stable production/main refs.
   Report before/after hashes, actual commit, counts and API trace without headers,
   credentials, response bodies or raw service errors.

## Validation and limits

156 Windows mocked regression tests PASS (18 new), 14 isolated persistence checks
PASS. Real configuration and entry-point tests included. Compilation, CLI config,
YAML, security scan and pip dependency consistency PASS. Proposed-file audit has
zero findings. Fresh OSV advisory check: zero known advisories for the unchanged
locked dependencies. Final staged audit, live CI and actual baseline are pending here;
the final results document will distinguish executed checks from design.

TikTok profile/HTML reliability remains experimental. Finite RSS/profile/extractor
windows cannot prove complete account history or guarantee future availability.
No historical backfill is authorized. Shorts and historical premiere identity may
stay unknown; livestream/premiere transitions and real Discord delivery remain
untested. Smart Monitoring Schedule is future final-stage scope, not implemented.
No new dependencies. Existing lock lacks wheel hashes; build tools/Actions are
outside the runtime/dev OSV lock advisory coverage.

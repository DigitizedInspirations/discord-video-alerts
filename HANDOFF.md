# Working checkpoint — 2026-10-16

Approved deployment validation completed with a documented provider blocker.
Implementation cfc4b968f2d3123302a2750a477276a7c9273a0b was audited and pushed
to public main. Follow-up commits 623ad56 and 95de8cf contain actual Linux evidence
and bounded diagnostics. A final documentation commit follows these revisions.
No Discord secret was read or passed to validation jobs. No Discord effects or
production notification-state writes occurred. MASTER/media remain OFF and
scheduled.yml.disabled is still inactive. Do not claim production readiness.

## Current evidence

- Windows: all four public sources verified on October 16; latest YouTube owners,
  timestamps and official Shorts membership verified. RSS404 fallback worked live.
- Linux: 62 unit tests passed in each of three recorded CI runs, zero failures/skips.
- Linux: 14 isolated state checks passed across six fresh processes. No network in
  child simulations, no GitHub Contents writes, no production state access.
- TikTok: both sources returned public id/owner/time in three separate Linux jobs.
  Listing counts: 30 Infinity / 16 Milo & Mia. Still experimental, no uptime guarantee.
- YouTube: discovery verified in all three Linux audits (5 DayZ / 13 Milo & Mia).
  First run used verified public-channel RSS404 fallback; later RSS recovered.
  Per-video metadata was BLOCKED: channel_id, timestamp, availability and live_status
  were missing. Diagnostic categories included authentication_requested and bot_check.
- Installed the official optional yt-dlp-ejs==0.8.0 in a disposable runner and enabled
  its existing Node runtime. Both dependencies were present; the runtime warning
  disappeared, but bot/authentication warnings and missing identities persisted.
  This package was not added to production dependencies; the one-off install step
  was removed after the comparison. Optional probe_youtube.py --node remains.
- Actual GitHub durable branch/retrieval/conflicts/restore remain NOT TESTED;
  filesystem simulations do not establish persistence across separate cloud jobs.

| Run | Workflow | Outcome | Commit |
|---|---|---|---|
| [38834116442](https://github.com/DigitizedInspirations/discord-video-alerts/actions/runs/38834116442) | CI | PASS | cfc4b96 |
| [38834738641](https://github.com/DigitizedInspirations/discord-video-alerts/actions/runs/38834738641) | Isolated state | PASS: 14 checks | cfc4b96 |
| [38834735917](https://github.com/DigitizedInspirations/discord-video-alerts/actions/runs/38834735917) | Source audit | FAIL: YouTube metadata | cfc4b96 |
| [38836796267](https://github.com/DigitizedInspirations/discord-video-alerts/actions/runs/38836796267) | CI | PASS | 623ad56 |
| [38836896270](https://github.com/DigitizedInspirations/discord-video-alerts/actions/runs/38836896270) | Source audit + diagnostic | FAIL: YouTube metadata | 623ad56 |
| [38837567165](https://github.com/DigitizedInspirations/discord-video-alerts/actions/runs/38837567165) | CI | PASS | 95de8cf |
| [38837567703](https://github.com/DigitizedInspirations/discord-video-alerts/actions/runs/38837567703) | Source audit + runtime comparison | FAIL: YouTube metadata | 95de8cf |

## Files and architecture

src/video_alerts: strict config, independent adapters, filters, sequential queue,
safe baselines, Discord client, media validation, CLI/manual/recovery/health.
State architecture: notification-state branch through Contents API, optimistic SHA,
common Actions concurrency, durable write-ahead checkpoint before Discord POST.
Local store: atomic replace/fsync, schema/checksum, protected backup, CLI lock.
Ambiguous deliveries become uncertain and are never automatically resent.
Initial and OFF-to-ON runs exclude historical/disabled-period backlog.
Unknown YouTube subtype/premiere identity is not invented; restrictive filters defer.
Explicit corrupt/missing-file restore quarantines old queues and establishes safe
baselines; valid state merges preserve delivered records/tombstones. Missing branch
needs reviewed repair. RESOLVE verifies an existing message by GET without resending.

Evidence: docs/cloud/*-result.json and *-evidence.json, docs/adapter_probe.json,
docs/probes/adapters-20261016T012929Z.json, docs/test-results.txt,
docs/local_verification.json, docs/DEPLOYMENT_VALIDATION.md. Full downloaded logs
stay under ignored .validation/. Public GitHub run links above retain source logs.

## Security and failed approaches

- Exact staged secret/private-path audits passed before every push. Validation uses
  contents:read, no Discord secret, no active schedule, no posting trigger on push.
- Fixed release_audit.py to read MASTER from the actual staged config.
- Missing Git author identity blocked the first commit. Reused the initial commit's
  existing author through git -c user.name/user.email, without global settings changes.
- Credential helper requires the narrowly approved non-sandbox controller invocation.
  It never prints/saves credentials. Authenticated log requests refuse redirects;
  signed storage downloads are separate unauthenticated requests with host checks.
- Earlier RSS ID normalization, YAML quoting, UTF-8 output, TikTok public hydration,
  platform labels, and queue time ordering are resolved; do not repeat development.
- No cookies, authentication workarounds, CAPTCHA handling, proxies, paid services,
  or unverified identity fallback were introduced to work around YouTube blocking.

## Remaining limits and precise next steps

1. Resolve YouTube metadata access before considering all-four-source deployment.
   A candidate is official YouTube Data API metadata within its free quota; this
   needs a separately supplied restricted API key, design/config changes and tests.
   It has not been implemented or tested. Never request secrets in the conversation.
2. Separate explicit authorization is required for production state initialize,
   baseline and a second durable run. Use a reviewed disposable branch for any
   canary instead of notification-state; do not silently write production history.
3. Separate authorization is required for a real Discord test, and later activation
   of MASTER/schedule. No approval is needed again for the already authorized pushes.
4. Authentic branding assets are absent. Client formatting/role/avatar/GIF/playback,
   real delivery IDs and edit/delete remain NOT TESTED. Do not substitute branding.
5. Premiere detection, finite listing windows, scheduled-to-public transitions,
   TikTok HTML/IP stability, dependency hashes and live CVE audit remain limitations.
6. Consult docs/DEPLOYMENT_VALIDATION.md and DEVELOPMENT_STATUS.md before resuming.
   Current source failure is an external access restriction, not a failing unit suite.

Safe local checks: .\.venv\Scripts\python.exe scripts/check_local.py and
scripts/cloud_state_simulation.py. Network audits require the approved scoped prefix.
Use PowerShell directly; trusted .ps1 files must use RemoteSigned child execution.

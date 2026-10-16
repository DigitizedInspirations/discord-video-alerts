# YouTube Data API integration — local review, 2026-10-16

Implemented locally against official API documentation. The user reports YouTube
Data API v3 enabled, a dedicated YouTube-restricted key stored as YOUTUBE_API_KEY
in the existing repository, and DISCORD_WEBHOOK_URL unchanged. No secret was read,
retrieved, printed or used in local tests. No push/commit or cloud dispatch was made
for this update. Current HEAD remains eb15885. MASTER/media OFF; schedule disabled.

## Implementation

RSS discovery and its strict channel/entry identity checks remain intact. The
previous verified public-channel RSS404 fallback remains unchanged. When the
YOUTUBE_API_KEY environment variable is present, both YouTube adapters share one
YouTubeAPI client. It uses only GET https://www.googleapis.com/youtube/v3/videos,
with the key in X-Goog-Api-Key, never in URLs, command arguments, config or state.
No SDK or dependency changes were required.

The request selects snippet,status,liveStreamingDetails and a bounded fields mask.
Each source's discovered IDs are fetched in batches of at most50 on first enrichment.
Positive and missing/error results are cached only for the current invocation;
repeat enrichments do not consume another request. Both sources share an overall
six-HTTP-attempt budget, including retries. Previously deferred IDs outside the
current RSS window may consume extra bounded requests. Fresh invocations recheck
public/scheduled/unavailable metadata instead of persisting an API response cache.

Independent API proof must match the video ID and configured channel ID; a matching
RSS entry alone is insufficient. PublishedAt must parse as a timezone-aware instant.
Privacy must explicitly be public and uploadStatus processed. Private/unlisted/
unprocessed or upcoming videos remain ineligible. Missing/malformed metadata fails
closed. There is no extractor fallback after an API credential/quota/metadata error.
When the variable is absent, the existing public-extractor mode is preserved; the
restricted validation script requires a nonempty key so it cannot silently use it.

Current/upcoming and completed broadcasts are classified using liveBroadcastContent
and liveStreamingDetails. Existing livestream filters remain effective. API metadata
does not prove Shorts or historical-premiere identity: Shorts retain positive
official /shorts or /videos membership checks; unknown subtype is deferred by
restrictive filters. Premiere remains unknown, so exclude_premieres defers it.
Duration/URL shape is not treated as subtype proof. Public API privacy metadata is
not a guarantee of region/client playback or every access restriction.

TikTok implementation, config schema/defaults, four original templates, engine,
state format, queue and dedup keys are unchanged. API Posts flow through the existing
engine. Tests verify baseline/no backfill, restart dedup and no key in persisted
state. A YouTube quota failure leaves the TikTok source independently healthy.

## Failure handling

- Missing/invalid header credentials fail before a request where possible.
- HTTP400/401/403 are terminal for the shared client for that run. Known quota/rate
  reasons produce a fixed quota error; all other credential/access failures use a
  fixed redacted error. No response error message is echoed.
- HTTP429 and transient500/502/503/504/network errors have bounded configured retries.
  Retry-After is bounded; negative/nonfinite/oversized values cannot cause an
  unbounded wait. NaN handling was caught by the new regression suite and corrected.
- Redirects are refused by the existing HTTP transport, so the key is not forwarded
  to another host. Raw response bodies, network exceptions and exception chains are
  not exposed. Duplicate/unrequested result IDs and malformed JSON are rejected.
- Missing/deleted/unavailable videos have a per-run negative cache and are deferred
  through existing error/queue handling; no reset, resend or production write occurs
  during validation. Subsequent invocations may recover normally.

## Local tests and security verification

91 unittest tests passed: existing62 plus 29 new API/security/integration
tests; 0 failed, 0 skipped. All API responses, network failures and credentials were
synthetic. Compileall, config/templates, six workflow YAML files, static scan and
pip check passed. The existing isolated-state simulation passed14 checks across six
fresh processes, with zero Discord/production/GitHub Contents requests.

Tests cover batching50/50/1, per-source batching (60 items in two requests), shared
quota/error/cache behavior, six-attempt cap, missing/invalid keys, transient failures,
429/NaN delays, redirects, malformed/duplicate IDs, strict channel/video identity,
privacy/upload readiness, broadcasts, unknown subtype/premiere, fresh-run recovery,
engine dedup/source isolation, secret-free state/logs and the stateless validator.
Mock validation returned two verified sources and wrote only a temporary report.

Local check_local.py now refuses service-secret environment variables. Static and
proposed/staged scans detect Google API key literals as well as existing secret
patterns, reporting paths/categories only. No actual key is stored in evidence.
Dependency hashes/live CVE audit remain outside this scoped verification.

## Quota estimate

Official videos.list costs1 quota unit per request. No API search or API discovery
calls are used. RSS and public official-tab checks consume no YouTube Data API quota.

| Scenario | Estimated units |
|---|---:|
| No metadata enrichment needed | 0 per run |
| Up to50 requested IDs per YouTube source, normal successful run | up to2 per run |
| Hypothetical30-minute cadence,48 such runs/day, both sources | up to96/day normally |
| Hard shared cap including retries/deferred IDs | 6 per invocation; up to288/day at that cadence |
| Dedicated API validation | normally2; capped6 |
| Additional manual runs | additional actual request count, same per-invocation cap |

These are estimates, not measured project quota or billing verification. Invalid
requests may also consume quota. Production cadence remains disabled; no quota
increase, billing setting or paid Google service was enabled. Actual project limits
and secret restrictions await separately approved cloud validation.

Sources checked on2026-10-16:
- https://developers.google.com/youtube/v3/docs/videos/list — method, parts, filters and quota.
- https://developers.google.com/youtube/v3/docs/videos — publishedAt, identity, privacy and broadcast fields.
- https://docs.cloud.google.com/docs/authentication/api-keys-use — API-key header usage.
- https://cloud.google.com/docs/authentication/api-keys-best-practices — key management.

## Restricted workflow prepared, not executed

.github/workflows/youtube-api-validation.yml is workflow_dispatch only, with
contents:read, pinned checkout/setup-python and checkout persist-credentials:false.
Dependency installation, mock unit tests and safeguard auditing run WITHOUT the key.
Only the final stateless scripts/validate_youtube_api.py step receives YOUTUBE_API_KEY
from GitHub Secrets. No Discord secret, write token, production CLI, notification-state
API or artifact upload is used. The script refuses any Discord-secret environment,
MASTER ON or an active scheduled workflow. Its report includes selected public
metadata, safe error categories and actual request count, never request headers.

The existing manual operations workflow and still-disabled schedule have prepared
step-level YOUTUBE_API_KEY wiring for later approved operations. They were not run.
The existing source-audit workflow remains a no-secret legacy extractor check; use
the new dedicated workflow for API acceptance after approval. The scoped local
GitHub controller has not been expanded to dispatch this secret-backed workflow.

## Remaining blockers and next approved action

Real key validity/restrictions, API availability/quota and this revision on Linux
remain NOT TESTED. Historical Linux public-extractor bot blocking is not evidence
that the API path works; it must be checked separately. Shorts/premiere limitations,
real cloud persistence and Discord/client/media acceptance remain unresolved.
Authentic branding assets remain absent.

Review this local implementation and diff. Separate explicit approval is required
before pushing the update and executing the restricted secret-backed
workflow. Even after that approval, do not run operations, send Discord messages,
write production state, enable MASTER/schedule or change Google billing/services.

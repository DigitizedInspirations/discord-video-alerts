# Security audit — 2026-10-16

Scope: manual code review, mock regression tests, input/media/state failure tests,
structural workflow validation and a project-only static secret/dynamic-code scan.
This is not an independent penetration test or a dependency CVE database scan.
Public repository/push access and read-only validation workflows were exercised.
Production state permissions and all real Discord effects remain NOT TESTED.

## Implemented controls

| Area | Control and evidence |
|---|---|
| Secrets | Webhook only from env, no stored URL, controlled network errors without exception repr; static scanner reports filenames only |
| Mentions | parse=[], users=[], explicit role allowlist; untrusted metadata escapes Markdown/@/angle brackets |
| URL inputs | HTTPS, host allowlists, no credentials/ports/fragments, canonical IDs and source owner checks |
| Code execution | Formatter plain-placeholder allowlist, no eval/exec, workflow inputs passed via env/argparse, no shell interpolation |
| Attachments | resolved project paths, actual format/MIME/extension, size/pixel/frame budgets, full animation decoding, GIF trailer check |
| Avatars | public DNS addresses, HTTPS, redirect refused, bounded fetch, real image/MIME check, omit/skip fallback |
| Discord retry | only explicit 429 reject retried; ambiguous network/5xx/invalid ack quarantined; no automatic duplicate POST |
| State | schema/checksum, atomic writes, retained backup, lock, optimistic GitHub SHA, acknowledgement before POST |
| Resume/recovery | missing/corrupt state fails closed, no startup backlog, disabled-period baseline, tombstones retained during restore |
| Permissions | CI/source audit contents:read, only operator/schedule job contents:write; GITHUB_TOKEN restricted to repository |
| Actions | checkout/setup-python pinned commit SHA, Linux standard runners, bounded timeout, common concurrency group |
| Dependencies | exact tested versions in requirements.lock, binary wheels only, pip check; updates require repeat verification |

## Residual risks / honest limits

- Exactly-once cannot be guaranteed by a webhook after ambiguous network delivery;
  quarantining favors avoiding duplicates and may leave a missed announcement.
- Public repo state includes public metadata, source health and Discord message IDs.
  These are not secrets, but operator should be aware of their public visibility.
- State commit history grows; no automatic history rewrite/pruning is authorized.
- GitHub workflow concurrency can replace an older pending run when multiple triggers
  arrive; finite RSS/TikTok listings can therefore miss publications during outages.
- TikTok public HTML is an undocumented shape and can change/block datacenter IPs.
  No authentication/CAPTCHA bypass is provided. Both TikTok sources passed three Linux samples; long-term reliability remains unverified.
- Unknown YouTube subtype/premiere identity defers restrictive filters. Default live
  classification depends on yt-dlp metadata and real premiere transition is untested.
- Avatar validation resolves DNS before fetching; arbitrary configured hosts remain
  trusted operator inputs. DNS rebinding is not fully prevented by urllib. Keep
  avatar URLs on known public static-image hosts. HTTP redirects are refused.
- TLS uses platform trust store. Dependency packages are pinned but wheel hashes
  are not yet locked and a live vulnerability database audit has not been run.
- Local crash can leave operator.lock; manual inspection is required before removal.
- Explicit known-checkpoint corrupt/missing cloud-file recovery quarantines old
  queues and forces safe baselines. Missing branch needs reviewed Git repair.
  Actual cloud recovery is NOT TESTED; no background auto reset is provided.
- RESOLVE changes an uncertain record only after confirmation and verified existing
  Discord GET/post-URL match. Missing messages never trigger an automatic resend.
- No actual secret has been read or tested. Webhook validity, role permission,
  media ceiling and native playback need controlled real tests after approval.

Evidence: docs/test-results.txt, docs/local_verification.json,
docs/security-scan.json, docs/source_probe.json and docs/adapter_probe.json.


## Deployment validation audit

Every push passed exact staged-file credential/private-path and whitespace checks.
No credential findings were reported. .gitignore excludes environments, cookies,
credential/key files, local configuration and .validation logs. MASTER is read from
the staged config; scheduling is inactive. Only mock CI starts automatically on push.
The source and isolated-state workflows use contents:read, never receive the Discord
secret and do not call Discord or production state APIs. Real operator workflows
remain manual and were not dispatched. Existing GitHub credential-helper material
was used only in memory for the approved controller; it was never printed or saved.
Authenticated requests refuse redirects; signed log downloads carry no Authorization.

Linux YouTube bot/authentication restrictions remain BLOCKED. Missing ownership is
never replaced by an assumption based on discovery. A disposable optional EJS/Node
comparison did not resolve access and was not added to production dependencies.
Dependency wheel hashes and a live vulnerability-database audit remain unperformed.
Public workflow results and sanitized reports are under docs/cloud; full downloaded
logs remain local and ignored. See DEPLOYMENT_VALIDATION.md for exact run links.

# Project context — 2026-10-16

Specifications: docs/MASTER_REQUEST.md; deployment authorization:
docs/DEPLOYMENT_REQUEST.md. Conversation in English; Greek README/operations guides.
Repository: https://github.com/DigitizedInspirations/discord-video-alerts, public main.
Audited push/read-only Linux validation/disposable simulations are already approved.
No real Discord effects, secret access during validation, production-state changes,
MASTER activation, scheduling or paid services are authorized. No global config edits.

Four sources: YouTube @DayZMomentsTV / @milo-and-mia-world and TikTok
@infinity.projectrp / @milo.and.mia.world. Exact original UTF-8 templates preserved.
Adapters are independent; dedup key is platform+source_id+post_id, never cross-platform.
Pipeline: discovery → verified metadata → filters → persistent queue → Discord.
State uses notification-state + Contents API optimistic SHA and Actions concurrency.
Atomic local JSON/checksum/backup + lock; write-ahead delivery checkpoints, conservative
uncertain quarantine, explicit GET-based resolution, safe restore/tombstone merging.
No automatic backfill after initialization or OFF-to-ON. Corrupt/missing state fails
closed. Missing branch needs reviewed repair. Never discard delivery tombstones.

Files: src/video_alerts/{config,model,http,adapters,media,discord,state,engine,cli}.py;
tests/test_system.py; scripts; config; Greek guides and public evidence under docs.
Pinned Python 3.12 runtime dependencies: Pillow12.3.0, yt-dlp2026.8.19; PyYAML6.0.3
for workflow checks. Full animation decoding/MIME/path/budget checks protect media.
Authentic branding assets absent, media OFF. No substitute art or paid services.

Deployment evidence: implementation cfc4b96 pushed; 623ad56 / 95de8cf add Linux logs
and diagnostics. Three recorded Linux CI runs passed 62 tests each. Local suite also
has 62 tests. Isolated state simulation passed 14 checks locally and on Linux, across
six fresh processes. This tests filesystem persistence, not durable GitHub state.
Actual GitHub Contents writes/recovery/permissions across jobs remain NOT TESTED.

Windows October16: four sources verified, newest owner/time/public checked, both
YouTube newest Shorts positively classified in official tabs; RSS404 fallback verified.
Linux: TikTok metadata/public/owner/time verified in three separate source audits.
YouTube discovery works (RSS404 fallback then recovered RSS); metadata is BLOCKED:
missing channel/time/public/live fields, bot/authentication warnings. Official optional
EJS0.8.0+existing Node removed only the JS warning, not the block. Runtime production
dependencies were kept unchanged. Source audits correctly remain failed, independently
evaluating all four sources. TikTok remains experimental despite successful samples.
Do not weaken channel identity/public checks to force a green audit.

YouTube restrictive type filters use positive /shorts or /videos membership with strict
channel checks; absence stays unknown. Premiere identity and live transitions remain
partial. Finite listings can miss content during outages. RSS is intermittently404.
Discord tests are mocks; client previews/playback/roles/media are not verified.
Unknown/ambiguous delivery never retries automatically. External embed providers unset.

Validation jobs have contents:read and never receive DISCORD_WEBHOOK_URL. Controller
uses existing credential helper without displaying/persisting credentials and avoids
authenticated redirects. Staged scanner reads staged MASTER; all pushes audited.
Commit identity comes from initial repository author via per-command -c options.
MASTER=false and scheduled.yml.disabled stay unchanged. Full next steps and public
workflow links: HANDOFF.md / docs/DEPLOYMENT_VALIDATION.md. Future work needs a permitted
YouTube metadata alternative, scoped cloud-state testing and separately approved real
Discord acceptance before any production activation. Do not repeat push permission.

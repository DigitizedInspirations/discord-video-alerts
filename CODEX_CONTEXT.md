# Project context
Resume 2026-10-16: initial commit author provides the existing repository identity;
use git -c user.name/user.email for commits, without global settings changes.
Staged release audit now reads staged configuration for its MASTER safeguard.
Deployment authorization: docs/DEPLOYMENT_REQUEST.md approves audited push,
read-only Linux checks and disposable state simulations. Public main and push
access are verified. Local simulation passed 14 checks in six fresh processes,
with zero Discord/production-state requests or GitHub Contents writes. Actual
GitHub durability remains NOT TESTED. MASTER and scheduling remain OFF.

Approved specification: docs/MASTER_REQUEST.md (verbatim user attachment).
Four sources: YouTube @DayZMomentsTV and @milo-and-mia-world; TikTok
@infinity.projectrp and @milo.and.mia.world. Existing repository:
https://github.com/DigitizedInspirations/discord-video-alerts.
Only secret: DISCORD_WEBHOOK_URL, already stored on GitHub; never copy locally.

Architecture selected: independent source adapters → filter → persistent sequential
queue → Discord webhook. State uses a dedicated `notification-state` branch through
GitHub Contents API optimistic SHA updates; serialized Actions runs and per-delivery
write-ahead checkpoints. Local state is atomic JSON with checksums and backups.
Do not use expiring caches as authoritative state. Ambiguous sends are quarantined.
Settings and UTF-8 templates are user editable. No automatic schedule is activated
until controlled production testing and approval. Scheduled runs target :7 and :37.
Optional authentic media is absent. Discord client playback and GitHub Linux are
unverified. Windows public discovery/newest metadata is verified for all four sources;
TikTok remains experimental and uses public hydration HTML for per-post metadata.

Implementation layout: src/video_alerts/{config,model,http,adapters,media,discord,
state,engine,cli}.py; tests/test_system.py; scripts for read-only source evidence,
environment bootstrap and workflow checks. Pillow decodes full attachment animation;
yt-dlp extracts only public metadata with no login/cookies/downloads; PyYAML is used
only for development workflow checks. requirements.lock pins tested versions:
Pillow 12.3.0, yt-dlp 2026.8.19, PyYAML 6.0.3; pyproject pins runtime dependencies.
Verified YouTube IDs are stored in config/settings.json. Public RSS snapshots are
finite (currently 1 and 14 entries); outages longer than that window can miss posts.
Unknown Shorts/regular or premiere identity is never invented: restrictive requested
filters defer until supported metadata exists. External TikTok embed services have
not been tested and are not enabled; archived vxtiktok was researched but not selected.

Restrictive YouTube subtype filters use positive official /shorts or /videos tab
membership, with strict channel ID checks and per-run bounded listing cache.
Newest Shorts membership verified for both accounts; absent membership stays unknown.
RSS404 may fall back to verified public channel listing; transport fallback logged.
An RSS404 outage was observed and feeds recovered. Fallback live path not exercised,
only mock-tested. Metadata verification still gates every public announcement.
Cloud restore handles corrupt/missing state file on existing branch via explicit
checkpoint, queued-entry quarantine and safe baseline/cutoff. Missing branch not
auto repaired. Valid current state preserves newer delivery records and tombstones.
Resolve confirms existing Discord message ID/canonical URL via GET, never resend.

Final local evidence: 62 unit tests, compileall/config/YAML/static scan/pip check pass.
Every external live operation still requires approval. Current feature evidence lives
in DEVELOPMENT_STATUS.md; exact next steps and failed approaches live in HANDOFF.md.

Implementation plan: research → core → advanced/manual/recovery → TikTok probes →
tests/security audit → Greek deployment preparation → approval-controlled live tests.

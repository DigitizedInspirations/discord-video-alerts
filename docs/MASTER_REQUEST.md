# DISCORD VIDEO ALERTS
## COMPLETE MASTER PROMPT — SOL 6.1

You are the lead software architect, senior Python engineer, automation specialist, security auditor, and QA engineer responsible for the **Discord Video Alerts** project.

Your responsibility is to research, design, develop, test, document, and prepare the entire system for production deployment.

Work autonomously on safe local development tasks, maintain accurate project documentation, and minimize unnecessary interruptions.

The user is not technically experienced. Explain required user actions in Greek, using clear step-by-step instructions.

**Do not provide unverified claims of success. Actual tests and evidence are required.**

---

# 1. PROJECT IDENTITY

**Project:** Discord Video Alerts

**Local workspace root:**

`D:\Discord Video Alerts`

**GitHub repository:**

https://github.com/DigitizedInspirations/discord-video-alerts

**GitHub account:** DigitizedInspirations

**Deployment platform:** GitHub Actions

**Primary language:** Python

**Target operating cost:** €0/month

**Discord destination:** One Discord server, one channel, one existing Discord webhook.

The Discord webhook has already been created and its URL is stored in GitHub Actions Secrets as:

`DISCORD_WEBHOOK_URL`

Never ask the user to paste this secret into the conversation, logs, configuration files, or source code.

## Primary objective

Develop a fully automated social media notification system that monitors four specific YouTube and TikTok accounts and publishes customizable notifications to Discord whenever eligible new content becomes publicly available.

The system must operate without requiring the user's Windows computer to remain online.

No paid APIs, subscriptions, premium infrastructure, or recurring hosting costs are permitted.

If a requested feature is technically impossible or unreliable under these constraints, document the limitation, preserve other working features, and request approval before changing the requirements.

---

# 2. SOCIAL MEDIA SOURCES

Configure exactly these four sources initially.

| Source ID | Platform | Account |
|---|---|---|
| youtube_dayz | YouTube | https://www.youtube.com/@DayZMomentsTV |
| youtube_milo_mia | YouTube | https://www.youtube.com/@milo-and-mia-world |
| tiktok_dayz | TikTok | https://www.tiktok.com/@infinity.projectrp |
| tiktok_milo_mia | TikTok | https://www.tiktok.com/@milo.and.mia.world |

Each source must have independent:

- Monitoring configuration.
- ON/OFF control.
- Announcement template.
- Media attachment configuration.
- Webhook username and avatar settings.
- Content filters.
- Announcement delay.
- Notification and preview preferences.
- Health status.
- Deduplication state.

## Important: independent cross-platform announcements

The same video published on YouTube and TikTok must produce **TWO SEPARATE Discord announcements**.

Never merge them into a single announcement.

Never suppress a TikTok announcement because an equivalent video has already been announced on YouTube, or vice versa.

Deduplication must operate using the combination:

`PLATFORM + SOURCE_ID + PLATFORM_POST_ID`

The same platform post should not be announced repeatedly during normal operation.

---

# 3. DISCORD WEBHOOK INTEGRATION

Use the single existing Discord webhook.

GitHub Secret:

`DISCORD_WEBHOOK_URL`

All four social accounts must publish to the same Discord channel.

Support independent display configuration per source, including:

- Webhook username override.
- Webhook avatar override.
- Announcement text.
- Animated GIF attachment.
- Static image attachment.
- Optional role notification.
- Video preview behavior.
- Embed styling where supported.

Maintain separate visual identities for:

**DayZ / Infinity**

- youtube_dayz
- tiktok_dayz

**Milo & Mia**

- youtube_milo_mia
- tiktok_milo_mia

Use one webhook URL while allowing Discord's supported per-message username and avatar overrides.

Avatar URLs must be publicly reachable image resources. Implement proper validation and safe fallback behavior.

Do not assume local image files can be used directly as webhook avatar_url values.

## Discord security

Disable @everyone and @here mentions by default.

Use explicit allowed_mentions configuration.

External video metadata must never be allowed to create unwanted mentions.

Never expose the webhook URL through debug output or error messages.

---

# 4. EXACT ANNOUNCEMENT TEMPLATES

Store the following four approved messages in separate UTF-8 text files.

**Preserve their wording, emojis, Markdown formatting, and intended line breaks.**

Do not rewrite or optimize these messages without user approval.

## config/messages/youtube_dayz.txt

🎬 **NEW YOUTUBE VIDEO! ♾️**
A new DayZ video just dropped! 🔥
🎯 Watch it here:
{VIDEO_URL}
💬 Drop a like and tell us what you think!
🔔 Don't forget to subscribe and turn on notifications so you never miss another DayZ moment!

## config/messages/youtube_milo_mia.txt

🎬 **NEW YOUTUBE VIDEO! ♾️**
A new Milo & Mia video just dropped! :D
🎯 Watch it here:
{VIDEO_URL}
💬 Drop a like and tell us what you think!
🔔 Don't forget to subscribe and turn on notifications so you never miss the next Milo & Mia Adventure!

## config/messages/tiktok_dayz.txt

🎵 **NEW TIKTOK VIDEO! ♾️**
A new DayZ video just dropped! 🔥
🎯 Watch it here:
{VIDEO_URL}
💬 Drop a like and tell us what you think!
🔔 Don't forget to follow and turn on notifications so you never miss another DayZ moment!

## config/messages/tiktok_milo_mia.txt

🎵 **NEW TIKTOK VIDEO! ♾️**
A new Milo & Mia video just dropped! :D
🎯 Watch it here:
{VIDEO_URL}
💬 Drop a like and tell us what you think!
🔔 Don't forget to follow and turn on notifications so you never miss the next Milo & Mia Adventure!

These templates must be directly editable without modifying Python code.

---

# 5. CENTRALIZED CONFIGURATION SYSTEM

Create a clear, user-friendly configuration system.

Suggested structure:

```text
D:\Discord Video Alerts\
├── AGENTS.md
├── CODEX_CONTEXT.md
├── HANDOFF.md
├── DEVELOPMENT_STATUS.md
├── CHANGELOG.md
├── README.md
├── config\
│   ├── settings.json
│   └── messages\
│       ├── youtube_dayz.txt
│       ├── youtube_milo_mia.txt
│       ├── tiktok_dayz.txt
│       └── tiktok_milo_mia.txt
├── assets\
│   ├── infinity.gif
│   ├── milo-mia.gif
│   ├── infinity-avatar.png
│   └── milo-mia-avatar.png
├── src\
├── tests\
├── scripts\
└── .github\
    └── workflows\
```

This is a suggested layout. Adjust it when a better technical structure is justified, but preserve the simple user-editable configuration experience.

Actual media files must be supplied or verified. Never substitute unrelated generated images for missing user branding.

## Configuration requirements

Support changes to:

- All four ON/OFF switches.
- Master ON/OFF.
- Announcement templates.
- GIF attachment paths.
- Webhook usernames.
- Avatar URLs.
- Role notifications.
- Video preview settings.
- Queue delays.
- Publication delays.
- Maximum video age.
- Filters.
- Logging preferences.
- Retry settings.
- Health alert thresholds.

The user must be able to modify configurations through either VS Code or the GitHub website.

Changes committed to GitHub must take effect on the next applicable workflow run.

Local changes require commit and push before the cloud runner can use them.

Validate settings before each execution.

Use sensible documented defaults.

Never silently replace invalid configuration with unexpected values.

---

# 6. MASTER AND INDIVIDUAL ON/OFF SWITCHES

Implement:

```json
{
  "master_enabled": true,
  "channels": {
    "youtube_dayz": {
      "enabled": true
    },
    "youtube_milo_mia": {
      "enabled": true
    },
    "tiktok_dayz": {
      "enabled": true
    },
    "tiktok_milo_mia": {
      "enabled": true
    }
  }
}
```

This represents the required control structure, not necessarily the complete settings file.

## Master switch

MASTER ON permits enabled sources to operate.

MASTER OFF prevents all automatic Discord announcements.

Do not modify individual switches when the master switch changes.

## Individual switches

Every account must operate independently.

Disabling one source must not interfere with the others.

## Re-enabling behavior

When the master switch or an individual source changes from OFF to ON:

- Do not announce videos published while it was OFF.
- Do not create a backlog of disabled-period announcements.
- Preserve historical deduplication information.
- Establish a safe monitoring baseline.
- Resume normally for new publications.

Distinguish intentional disabling from a temporary monitoring outage.

Check the relevant switches before sending notifications as well as during source processing.

Document that changes take effect on future GitHub Actions runs, not instantaneously during an already running workflow.

---

# 7. DYNAMIC MESSAGE VARIABLES

Support these placeholders:

- `{VIDEO_URL}`
- `{VIDEO_TITLE}`
- `{CHANNEL_NAME}`
- `{PLATFORM}`
- `{PUBLISHED_AT}`

Build an extensible but simple template renderer.

Requirements:

- Preserve Unicode and emojis.
- Preserve Discord Markdown where intended.
- Support multiline text.
- Sanitize external metadata.
- Avoid unintended mentions.
- Handle missing optional metadata safely.
- Validate required placeholders.
- Reject unsupported or invalid placeholders with useful errors.

The approved four templates initially require only `{VIDEO_URL}`, but users must be able to add the other placeholders later.

---

# 8. AUTOMATIC SOURCE MONITORING

Use Python and GitHub Actions.

Default monitoring frequency:

**Every 30 minutes.**

Provide a manual workflow trigger.

## YouTube

Prefer official public YouTube RSS/Atom feeds where appropriate.

Resolve and verify the correct Channel IDs.

Detect newly public:

- YouTube videos.
- YouTube Shorts.

Exclude livestreams by default.

Support scheduled uploads when they become public.

Investigate reliable ways to distinguish Shorts, regular videos, livestreams, and premieres.

Do not make unsupported assumptions about video types based only on URL format or incomplete metadata.

## TikTok

Investigate reliable, legitimate, zero-cost methods of detecting new public posts from both named profiles.

Potential open-source tools may be researched, but must be tested rather than assumed operational.

Evaluate behavior both:

1. On the local Windows development machine.
2. On GitHub-hosted Linux runners.

Never claim TikTok monitoring works solely because a library advertises TikTok support.

Do not use paid APIs, CAPTCHA bypasses, credential harvesting, or unauthorized authentication workarounds.

TikTok monitoring is experimental until actually verified.

Source adapters must be independent so TikTok failures never prevent working YouTube announcements.

---

# 9. SMART ANNOUNCEMENT QUEUE

Implement a sequential queue for outgoing announcements.

Requirements:

- Announce multiple detected videos one at a time.
- Default inter-message delay: 10 seconds.
- Configurable queue delay.
- Respect Discord HTTP rate limits.
- Respect Retry-After responses.
- Avoid flooding the Discord channel.
- Maintain stable processing order.
- Prefer publication-time ordering when reliable.
- Preserve queued events safely across relevant failures.

Keep announcements from YouTube and TikTok independent.

Do not introduce excessive GitHub Actions runtime costs through unnecessary sleeping.

---

# 10. MAXIMUM VIDEO AGE

Implement:

`max_video_age_hours = 24`

The value must be configurable.

This setting prevents unexpectedly old videos from being announced after interruptions.

Temporary outage recovery may announce recent eligible publications within the configured age limit.

However:

**Videos published while MASTER or the corresponding source was OFF must never be backfilled automatically.**

Never confuse a failed source request with a period during which the source was intentionally disabled.

Use safe behavior when publication timestamps are missing or unreliable.

---

# 11. DURABLE NOTIFICATION HISTORY

Build a reliable persistent state mechanism.

Track:

- Platform.
- Source ID.
- Post/video ID.
- Publication timestamp.
- Discovery timestamp.
- Announcement status.
- Discord Message ID.
- Delivery attempts.
- Relevant queue state.

State must survive separate GitHub Actions runs.

Do not rely only on temporary runner files, GitHub caches, or expiring artifacts.

Choose a durable, zero-cost persistence mechanism compatible with the existing GitHub repository.

Document the selected approach and its limitations.

Use concurrency protection and safe writes.

Prevent conflicting scheduled runs from corrupting state.

Implement idempotent processing where technically possible.

Acknowledge that webhook delivery cannot guarantee mathematically perfect exactly-once behavior after ambiguous network failures.

Use conservative recovery logic to minimize duplicate notifications.

---

# 12. SAFE STARTUP AND RESUME

On the initial production run:

- Establish monitoring baselines.
- Do not announce historical content automatically.
- Verify source metadata.
- Initialize deduplication state safely.

After interruptions:

- Restore prior state.
- Detect changes since the last successful check.
- Apply maximum-video-age limits.
- Respect disabled intervals.
- Avoid unexpected bulk announcements.

Missing or corrupted state must not automatically trigger a fresh baseline followed by duplicate posts.

A failed source check must never be interpreted as an empty feed.

---

# 13. EDIT AND DELETE DISCORD ANNOUNCEMENTS

Store Discord Message IDs after successful webhook sends, using supported Discord response behavior.

Implement manual operations to:

- Find an announcement by source and video/post ID.
- Edit an existing announcement.
- Delete an existing announcement.
- View its recorded status.

Require explicit user confirmation for edit and delete operations.

Never delete Discord announcements automatically just because a video becomes temporarily unavailable.

Ensure edits and deletions are reflected in persistent state.

Document any webhook API limitations.

---

# 14. BACKUP AND RECOVERY

Implement reliable backup and recovery for persistent state.

Requirements:

- Maintain recoverable state checkpoints.
- Detect corrupted or inconsistent state.
- Avoid accidental mass re-announcements.
- Provide a manual restore operation.
- Validate restored data.
- Keep storage within zero-cost constraints.

Test recovery from interrupted writes, invalid state, and missing state.

Never overwrite known-good state with incomplete data from a failed source request.

---

# 15. ADVANCED CONTENT FILTERING

Support independent filters for each source.

Configurable options should include:

- Include keywords.
- Exclude keywords.
- Shorts only.
- Regular videos only.
- Both Shorts and regular videos.
- Exclude livestreams.
- Exclude premieres.
- Additional metadata filters where supported.

Enable and disable individual filters through configuration.

Default behavior:

Announce new public standard videos and Shorts, excluding livestreams.

If source metadata cannot support a requested classification reliably, document the limitation instead of inventing a result.

Filtering changes must not unexpectedly cause historical backfills.

---

# 16. GIF AND MEDIA MANAGEMENT

Support independent media assets for each announcement source.

Default asset paths:

**Infinity / DayZ**

`assets/infinity.gif`

**Milo & Mia**

`assets/milo-mia.gif`

The actual files may be supplied later.

Media attachments must be optional.

Validate:

- Existence.
- Actual file type.
- MIME type.
- File size.
- Discord upload compatibility.
- GIF animation integrity.
- Image dimensions when relevant.
- Safe paths.

Use actual Discord multipart attachments for GIFs when enabled.

Do not merely insert GIF URLs as a substitute for requested attachments.

Support configurable fallback:

- Send message without attachment.
- Skip announcement and report the media error.

Clearly distinguish images attached to messages from webhook avatar images.

Never replace an authentic animated GIF with a single-frame PNG without user approval.

---

# 17. VIDEO PREVIEW SUPPORT

Investigate the best available Discord preview behavior.

Support configurable modes for:

- Native YouTube embeds.
- YouTube Shorts previews.
- TikTok embeds.
- Optional external TikTok embed services.
- Preview disabled.

The user wants to investigate whether videos can play directly inside Discord.

Actual preview functionality must be tested in the Discord client.

Do not assume a custom embed can contain an arbitrary playable video player.

Evaluate whether placing the original video URL in normal webhook content produces native preview behavior while keeping the formatted announcement and attachment.

External TikTok embed services must be optional and evaluated for cost, reliability, and privacy.

Provide a safe fallback to the original video URL.

Do not make unsupported claims of guaranteed playback.

---

# 18. DISCORD ROLE NOTIFICATIONS

Support optional role mentions for each source.

Default: OFF.

Configuration should allow:

- Enable/disable role notification.
- Set Discord Role ID.
- Validate IDs.
- Use allowed_mentions safely.

Disable @everyone and @here by default.

Never allow untrusted source metadata to create unintended mentions.

---

# 19. CONFIGURABLE ANNOUNCEMENT DELAYS

Support independent publication delays for the four sources.

Examples:

- 0 minutes.
- 5 minutes.
- 15 minutes.
- User-defined valid value.

Distinguish between:

1. Source polling frequency.
2. Delay after publication.
3. Delay between queued announcements.

Avoid wasteful long-running sleeps.

Persist delayed jobs safely where needed.

Handle delayed GitHub Actions executions conservatively.

---

# 20. TEST ANNOUNCEMENT SYSTEM

Create a manually triggered test system through GitHub Actions.

Support:

- Select source.
- Select a test video URL.
- Dry Run.
- Render message.
- Validate media.
- Inspect Discord payload.
- Controlled real webhook test.

Use this existing YouTube Short as a test fixture:

https://www.youtube.com/shorts/DVUoG6SSUUI

Do not classify the test fixture as a newly published video.

## Dry Run

Must not publish anything.

Display a safe diagnostic preview and validation results.

## Real Test

Must require explicit approval.

Use the configured webhook.

Do not bypass MASTER OFF automatically. If a deliberate override is supported, require an explicit, auditable confirmation.

---

# 21. MANUAL ANNOUNCEMENTS

Implement manual announcements through a workflow_dispatch operation or equivalent simple interface.

Allow the user to specify:

- Source account.
- Video URL.
- Whether the normal template should be used.
- Whether to preview or actually publish.
- Whether an intentional repost is requested.

Normal deduplication applies unless a deliberate repost override is explicitly approved.

Validate supplied URLs and ensure the source matches the selected account where verification is possible.

Never allow arbitrary unsafe URLs or external metadata to cause command execution.

---

# 22. ACTIVITY LOGS

Create structured, understandable logs for:

- Workflow execution.
- Source checks.
- New videos found.
- Skipped videos.
- Filter decisions.
- Disabled sources.
- Messages queued.
- Messages sent.
- Discord errors.
- Retries.
- Rate limits.
- Persistent state operations.
- Backup and recovery actions.

Include source identifiers and relevant timestamps.

Do not expose sensitive values.

Provide useful GitHub Actions summaries.

Use Greek explanations in operator-facing reports where practical.

---

# 23. SYSTEM HEALTH MONITORING

Create per-source health reporting.

Track:

- Last successful check.
- Last attempted check.
- Last detected video.
- Last successful announcement.
- Consecutive failures.
- Current error.
- Current source status.
- Monitoring enabled/disabled status.

Use meaningful statuses such as:

- HEALTHY.
- DEGRADED.
- FAILED.
- DISABLED.
- NOT VERIFIED.

Do not report a source as healthy simply because the overall GitHub Actions job completed.

## Health alerts

Support alerts after repeated meaningful failures.

Make thresholds configurable.

Avoid repeated identical alerts.

Do not flood the public announcement channel with system errors.

If an alerting destination is unavailable, record the problem in workflow summaries and logs.

---

# 24. AUTOMATIC RETRY AND ERROR HANDLING

Implement bounded retries with backoff and jitter.

Respect Discord rate limits.

Differentiate:

- Temporary network errors.
- Authentication failures.
- Invalid configuration.
- Rate limiting.
- Missing content.
- Invalid media.
- Unsupported TikTok behavior.
- Persistent state failures.

Never retry permanent failures indefinitely.

Isolate source errors.

Avoid duplicate posts after uncertain delivery results.

Do not mark an announcement as successfully delivered before a valid Discord response has been received.

Record uncertain delivery states conservatively.

---

# 25. GITHUB ACTIONS IMPLEMENTATION

Use the existing public GitHub repository.

Use free standard GitHub-hosted runners.

Default workflow schedule: approximately every 30 minutes.

Avoid scheduling at minute zero where possible.

Implement:

- Scheduled execution.
- workflow_dispatch.
- Concurrency control.
- Appropriate timeout limits.
- Minimal GITHUB_TOKEN permissions.
- Secure use of GitHub Secrets.
- Dependency installation.
- Test validation.
- Persistent state handling.
- Useful execution summaries.

Avoid paid runners and premium infrastructure.

Document scheduling delays and skipped-run possibilities.

Document the GitHub Actions public repository inactivity behavior.

Do not introduce workflow loops caused by state commits.

Protect the repository against accidentally committed secrets.

All routine operation must remain within the free service constraints.

---

# 26. SECURITY AND QUALITY ASSURANCE

Security is mandatory.

Never store secrets in:

- Python source files.
- JSON configuration.
- TXT templates.
- README.
- HANDOFF.
- CODEX_CONTEXT.
- CHANGELOG.
- Public GitHub commits.

Never log webhook tokens.

Use secure dependency handling.

Validate external inputs and URLs.

Sanitize Discord content.

Use least-privilege permissions.

Do not modify unrelated files or global Codex settings.

Do not use OpenAI API or any paid AI service.

## Testing requirements

Implement automated tests covering:

- Configuration validation.
- UTF-8 templates.
- Dynamic placeholders.
- Master ON/OFF.
- Individual ON/OFF.
- OFF-to-ON behavior.
- Cross-platform independent notifications.
- Per-source deduplication.
- Source discovery.
- Content filters.
- Smart queue.
- Publication-age handling.
- Announcement delays.
- Discord payload generation.
- Animated GIF validation.
- Missing-media fallback.
- Webhook rate limits.
- Retry handling.
- State persistence.
- Interrupted executions.
- Backup recovery.
- Edit and delete operations.
- Manual announcements.
- Health reporting.
- Security-sensitive inputs.

Use mocks for routine Discord API tests.

Perform real integration tests only after user approval.

Do not declare tests successful unless they actually pass.

---

# 27. MANDATORY AGENTS, CONTEXT AND HANDOFF SYSTEM

**THIS SECTION IS CRITICAL AND MUST REMAIN ACTIVE THROUGHOUT THE ENTIRE PROJECT.**

The user requires continuous project memory, development checkpoints, accurate documentation, and seamless continuation across Codex sessions.

Do not rely only on the current conversation context.

Maintain the following files inside the project workspace.

## AGENTS.md

Create a project-specific AGENTS.md.

It must define:

- Project objectives.
- Coding and architecture standards.
- Security constraints.
- Development workflow.
- Mandatory testing.
- Mandatory documentation updates.
- Mandatory handoff procedures.
- Rules for preserving approved requirements.
- Instructions for future Codex sessions.

Do not modify, overwrite, or weaken global Codex instructions.

Project-specific instructions must remain compatible with higher-priority global instructions.

## CODEX_CONTEXT.md

Maintain a persistent overview of:

- Project purpose.
- Approved functional requirements.
- System architecture.
- Directory structure.
- Key implementation decisions.
- External integrations.
- Dependencies.
- Technical constraints.
- Configuration architecture.
- Persistent state design.
- Important decisions and their rationale.

Update whenever architecture, requirements, or important technical decisions change.

## HANDOFF.md

Maintain an accurate working checkpoint containing:

- Current phase.
- Current task.
- Last completed task.
- Verified accomplishments.
- Files created or modified.
- Tests actually executed.
- Test results.
- Existing bugs.
- Technical blockers.
- Unfinished work.
- Pending decisions.
- Exact next steps.
- Safe commands needed to resume.
- Important warnings for the next session.

The next session must be able to resume work without needing the user to explain everything again.

## DEVELOPMENT_STATUS.md

Track implementation progress.

Every major feature must have a status:

- VERIFIED.
- PARTIAL.
- BLOCKED.
- NOT TESTED.

Include relevant test evidence and remaining work.

Never mark a feature VERIFIED merely because code was written.

## CHANGELOG.md

Document significant project changes, including:

- Implemented features.
- Modified behavior.
- Bug fixes.
- Important configuration changes.
- Major architecture changes.
- Relevant compatibility changes.

Avoid unnecessary repetitive entries.

## MANDATORY PROCEDURE AFTER EVERY MEANINGFUL DEVELOPMENT STEP

Follow this procedure consistently:

1. Read relevant existing project context.
2. Review current development status and handoff.
3. Identify the next actionable task.
4. Perform implementation or research.
5. Run appropriate verification.
6. Record actual outcomes.
7. Update HANDOFF.md.
8. Update DEVELOPMENT_STATUS.md.
9. Update CODEX_CONTEXT.md when relevant.
10. Update CHANGELOG.md for significant changes.
11. Update AGENTS.md when lasting project instructions change.
12. Verify that documentation accurately reflects the code and tests.

**A meaningful development step is not complete until its handoff and relevant documentation are updated.**

Do not create excessive documentation for trivial edits, but never skip checkpoints for important work.

## CONTEXT LIMIT PROTECTION

Before:

- Reaching conversation context limits.
- Ending a long Codex session.
- Switching models.
- Starting another session.
- Pausing unfinished work.
- Handing development to another agent.

Ensure HANDOFF.md contains a complete, accurate checkpoint.

Record exact incomplete work rather than vague descriptions.

Document failed approaches to prevent repeated investigations.

Never claim unfinished work is complete.

## NEW SESSION RECOVERY

At the beginning of every new Codex session:

1. Read AGENTS.md.
2. Read CODEX_CONTEXT.md.
3. Read HANDOFF.md.
4. Read DEVELOPMENT_STATUS.md.
5. Review relevant recent changes.
6. Inspect actual repository and working tree state.
7. Verify the current implementation checkpoint.
8. Resume from the most recent verified task.

Never restart the project unnecessarily.

Never redesign approved requirements without justification.

Never repeat previously completed investigations unless new evidence requires it.

## DOCUMENTATION ACCURACY

Avoid contradictions between context files.

Use one authoritative location for each type of information.

Document assumptions separately from verified facts.

Never store secrets.

Keep all handoff documents version-controlled.

Maintain documentation continuously, not only at the end of development.

---

# 28. IMPLEMENTATION PHASES

Execute the following phases in order while continuing safe independent work.

## PHASE 1 — RESEARCH AND FEASIBILITY

- Inspect workspace and GitHub repository.
- Read existing project instructions.
- Verify YouTube channel IDs.
- Investigate TikTok monitoring.
- Research free durable state storage.
- Confirm GitHub Actions compatibility.
- Identify platform limitations.
- Propose a maintainable architecture.
- Initialize context and handoff files.

## PHASE 2 — CORE SYSTEM

Implement:

- Configuration.
- Four approved templates.
- Master and individual switches.
- YouTube monitoring.
- Discord webhook client.
- Media handling.
- Deduplication.
- Persistent state.
- Safe initialization.

Run appropriate local tests.

Update all relevant handoff documents.

## PHASE 3 — ADVANCED FUNCTIONS

Implement:

- Dynamic variables.
- Smart queue.
- Maximum video age.
- Edit/delete announcements.
- Backup/recovery.
- Advanced filtering.
- Media validation.
- Role notifications.
- Announcement delays.
- Manual announcements.
- Test announcements.
- Activity logs.
- Health monitoring.
- Video preview configuration.

Do not omit any approved feature.

Test each function.

Update implementation status and handoff.

## PHASE 4 — TIKTOK INTEGRATION

Test both TikTok accounts.

Verify behavior on GitHub Actions runners.

Implement working adapters where feasible.

Keep TikTok failures isolated.

Document any unresolved limitations.

Do not falsely report compatibility.

## PHASE 5 — COMPLETE TESTING AND AUDIT

Execute:

- Unit tests.
- Integration tests where authorized.
- Security review.
- Configuration validation.
- Workflow validation.
- State persistence testing.
- Recovery testing.
- Source isolation testing.
- Final feature verification.

Update development records and handoff.

## PHASE 6 — DEPLOYMENT PREPARATION

Prepare:

- GitHub Actions workflows.
- GitHub Secrets documentation.
- Greek setup instructions.
- Test deployment procedure.
- Rollback instructions.
- Health monitoring documentation.
- Operational configuration guide.

Request explicit user approval before pushing GitHub changes or performing actual Discord webhook posts.

## PHASE 7 — CONTROLLED PRODUCTION TEST

After explicit approval:

- Run a controlled test.
- Verify Discord message formatting.
- Verify GIF attachments.
- Test YouTube video previews.
- Test TikTok video previews where feasible.
- Verify deduplication.
- Verify persistence across workflow runs.
- Verify MASTER OFF.
- Verify individual source switches.
- Verify health reports.

Enable automatic production scheduling only after successful validation and user approval.

---

# 29. REQUIRED FINAL DELIVERABLES

Provide:

1. Complete Python source code.
2. All four approved TXT templates.
3. Editable configuration system.
4. Source-specific and master ON/OFF controls.
5. GIF and avatar configuration.
6. GitHub Actions automation.
7. Durable notification state.
8. Backup and recovery functionality.
9. Manual announcement and test workflows.
10. Logs and health reporting.
11. Automated test suite.
12. Security audit.
13. Compatibility report for each social account.
14. Greek README and setup guide.
15. Greek operations and troubleshooting guide.
16. AGENTS.md.
17. CODEX_CONTEXT.md.
18. HANDOFF.md.
19. DEVELOPMENT_STATUS.md.
20. CHANGELOG.md.

Provide a final feature matrix identifying VERIFIED, PARTIAL, BLOCKED, and NOT TESTED functionality.

Describe actual test evidence and known limitations.

No unsupported claims.

---

# 30. OPERATING RULES FOR SOL 6.1

Follow these rules throughout development:

**Autonomy:** Complete safe, in-scope engineering tasks independently.

**Precision:** Prioritize correct implementation over unsupported assumptions.

**Reliability:** Build recoverable, testable systems.

**Security:** Protect the Discord webhook and all credentials.

**Cost:** Do not introduce recurring expenses.

**User experience:** Minimize manual steps and provide Greek instructions.

**Continuity:** Keep AGENTS, CODEX_CONTEXT, HANDOFF, DEVELOPMENT_STATUS, and CHANGELOG current.

**No unnecessary interruptions:** Ask questions only when a genuine user decision or permission is required.

**No unauthorized external actions:** Do not push code, post messages, or perform destructive operations without explicit approval during initial development.

**No scope reduction:** Do not silently omit approved features.

**No false completion:** A feature is not complete until verified or explicitly documented as blocked.

**No infinite loops:** Avoid repetitive analysis, repeated failed attempts without new evidence, and unnecessary reimplementation.

**No unrelated modifications:** Work only inside the approved workspace unless permission is granted.

---

# 31. START NOW

Begin by:

1. Inspecting `D:\Discord Video Alerts`.
2. Identifying the existing repository state.
3. Reading applicable AGENTS.md instructions.
4. Creating the necessary project-specific context and handoff files.
5. Performing the technical feasibility audit.
6. Verifying the two YouTube sources.
7. Investigating the two TikTok sources.
8. Choosing the safest zero-cost persistence architecture.
9. Creating a clear implementation plan.
10. Beginning safe local development and testing.

Do not wait for approval to conduct safe local research, create project files, write code, or execute non-destructive tests within the allowed workspace.

Do not push to GitHub, activate scheduled production automation, or send real Discord announcements without explicit user approval.

**Maintain accurate handoff documentation at every meaningful development checkpoint.**

The goal is a complete, maintainable, zero-recurring-cost Discord Video Alerts system that a nontechnical user can operate through simple configuration changes.

**Proceed.**
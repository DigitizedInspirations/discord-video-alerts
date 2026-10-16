# DISCORD VIDEO ALERTS — GITHUB DEPLOYMENT & VALIDATION

## 1. COMMUNICATION LANGUAGE — IMPORTANT

**From this point forward, respond exclusively in English throughout this Codex conversation.**

This applies to:
- Progress updates and development reports.
- Technical explanations and research findings.
- Test results and verification reports.
- Error messages, troubleshooting explanations, and blockers.
- Approval requests and questions.
- Security audits and deployment reports.
- Final summaries, recommendations, and next steps.

Preserve original technical terminology, filenames, commands, and error messages.

Do not translate technical terminology unnecessarily.

**Important:** This language preference applies to our current Codex conversation. Do not modify global Codex settings or instructions.

Existing requirements for Greek README files and Greek user-facing operational documentation remain unchanged.

All previously approved project requirements remain in effect.

---

## 2. CURRENT PROJECT STATUS

Project: Discord Video Alerts

Workspace:
`D:\Discord Video Alerts`

GitHub repository:
https://github.com/DigitizedInspirations/discord-video-alerts

According to your latest report:

- The local implementation is complete and ready for controlled deployment validation.
- 62 local tests passed.
- All four social media sources were successfully checked on Windows.
- Configuration, announcement templates, persistent state, queue management, recovery mechanisms, and documentation have been implemented.
- GitHub Linux compatibility remains unverified.
- Cloud persistence remains unverified.
- Real Discord integration remains untested.
- TikTok monitoring remains experimental.
- Original GIF assets have not yet been provided.
- MASTER remains OFF.
- Production scheduling remains disabled.

Treat these as reported results, not independently verified evidence. Review the actual test records and repository state before proceeding.

Do not restart the project or repeat completed development unnecessarily.

---

## 3. AUTHORIZATION

**APPROVED:**

You are authorized to:

1. Perform a final local security and deployment readiness audit.
2. Commit and push the existing project to the authorized GitHub repository, provided all security checks pass.
3. Execute controlled read-only GitHub Actions validation.
4. Test dependencies and runtime compatibility on GitHub-hosted Linux runners.
5. Perform public, read-only source discovery tests for all four accounts.
6. Perform safe, isolated simulations of state persistence and recovery.
7. Fix issues discovered during validation and repeat safe tests.
8. Update all required project documentation and handoff files.

**NOT APPROVED:**

- Sending real Discord announcements.
- Executing Discord webhook POST, PATCH, or DELETE requests.
- Publishing test messages to Discord.
- Enabling MASTER.
- Enabling production scheduling.
- Changing GitHub billing or enabling paid features.
- Purchasing or activating external services.
- Destructively altering production notification state.
- Deploying a live announcement system.
- Modifying unrelated repositories or files.

Request separate explicit approval before any prohibited action.

---

## 4. MANDATORY PRE-PUSH SECURITY AUDIT

Before pushing, verify that no sensitive information will be committed.

Check for:

- Discord webhook URLs.
- API tokens and access credentials.
- Passwords.
- Session cookies.
- Authentication files.
- Local `.env` files.
- Python virtual environments.
- Temporary credentials.
- Sensitive debugging output.
- Accidentally generated secrets.
- Private or irrelevant local files.

Verify that `.gitignore` is correctly configured.

Review the exact Git diff and staged changes.

Confirm that no live production operation will be triggered accidentally by the push.

If any security concern exists, stop and explain the issue before proceeding.

---

## 5. GITHUB ACTIONS VALIDATION

After the security audit passes, push the project and execute controlled GitHub Actions validation.

All cloud tests must operate in safe DRY_RUN / READ_ONLY mode.

### Critical requirements

1. Keep MASTER OFF.
2. Keep production scheduling disabled.
3. Do not send Discord messages.
4. Do not access or expose `DISCORD_WEBHOOK_URL` in validation jobs.
5. Use minimal GitHub Actions token permissions.
6. Use public-source GET requests only where appropriate.
7. Prevent test workflows from changing production announcement history.
8. Prevent automatic production posting on push.
9. Do not run destructive tests against production state.
10. Record actual workflow logs and results.

Any persistence tests requiring writes must use isolated disposable test data or temporary branches/resources, never production state, and must stay within the approved authorization.

---

## 6. VERIFY ALL FOUR SOCIAL ACCOUNTS

Perform actual GitHub-hosted Linux compatibility tests for:

**YouTube**
- https://www.youtube.com/@DayZMomentsTV
- https://www.youtube.com/@milo-and-mia-world

**TikTok**
- https://www.tiktok.com/@infinity.projectrp
- https://www.tiktok.com/@milo.and.mia.world

For every source, verify:

- Network accessibility.
- Successful metadata retrieval.
- Video/post identification.
- Publication timestamps where available.
- Compatibility with Linux runners.
- Source-specific error handling.
- Relevant dependency compatibility.
- Differences compared with the Windows test results.

Do not mark a source VERIFIED based solely on its Windows results.

For TikTok, specifically determine whether public profile monitoring works reliably from GitHub-hosted infrastructure.

If TikTok fails, document the actual error, likely cause, and reasonable zero-cost alternatives.

Do not allow TikTok failures to break YouTube functionality.

---

## 7. CLOUD STATE AND DEDUPLICATION VALIDATION

Verify the selected persistence architecture.

Test:

- State initialization.
- State retrieval.
- State serialization.
- State restoration.
- Deduplication across separate simulated runs.
- Concurrent execution safeguards.
- Corrupted state handling.
- Backup and recovery.
- MASTER OFF behavior.
- Individual source OFF behavior.
- Safe restart and resumption.
- No historical posting after re-enabling a source.

Actual production persistence must remain unchanged during these validation tests.

If complete cloud persistence cannot be safely verified under read-only authorization, mark it PARTIAL or NOT TESTED and explain the next test requiring separate approval.

---

## 8. DOCUMENTATION & HANDOFF — MANDATORY

Continue following the project's mandatory continuity protocol.

Maintain:

- `AGENTS.md`
- `CODEX_CONTEXT.md`
- `HANDOFF.md`
- `DEVELOPMENT_STATUS.md`
- `CHANGELOG.md`

After every meaningful development step:

1. Record the changes made.
2. Record the actual tests executed.
3. Record successful and failed results.
4. Document discovered limitations.
5. Record unresolved blockers.
6. Update current implementation status.
7. Record precise next steps.

Before ending this session, ensure HANDOFF.md is complete and up to date.

Future Codex sessions must be able to resume without losing project context.

Do not modify global AGENTS.md or global Codex configuration.

---

## 9. REQUIRED FINAL REPORT

After completing the approved work, provide your report entirely in English.

Use these exact sections:

### 1. Deployment Summary
Explain what was pushed and which GitHub commit contains the changes.

### 2. GitHub Actions Results
List the executed workflows, their actual outcomes, and relevant links.

### 3. Source Compatibility
Provide a table for all four sources, including Windows status, Linux status, and remaining limitations.

### 4. Test Results
Show the number of tests executed, passed, failed, and skipped.

### 5. Cloud Persistence
Explain what has been verified and what remains unverified.

### 6. Security Audit
Report the security checks and any findings.

### 7. Known Issues
List unresolved problems and their impact.

### 8. Feature Verification Matrix
Use VERIFIED, PARTIAL, BLOCKED, or NOT TESTED.

### 9. Documentation & Handoff
Confirm which project context files were updated.

### 10. Next Steps
Explain exactly what user approval or action is needed before the next development or deployment stage.

Never claim production readiness without supporting evidence.

---

## 10. EXECUTION INSTRUCTIONS

Proceed autonomously through all approved safe tasks.

Do not interrupt for routine development decisions.

Do not repeat previously completed work unless required by actual new evidence.

Keep progress and handoff documentation accurate.

If a task would exceed the authorization above, stop that action and request explicit approval.

**Remember: communicate with me exclusively in English throughout this Codex chat, while preserving all existing project requirements.**

Begin the security audit, then proceed with the approved GitHub push and controlled cloud validation.
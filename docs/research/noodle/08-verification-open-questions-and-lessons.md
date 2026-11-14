# 08. Verification status, open questions, and lessons for our build

## 1. What was verified and how

| Area | Method | Result |
|---|---|---|
| Repository structure and counts | `git clone` (full history), `find`, `wc` | verified |
| Versions and changelog | `VERSION`, `CHANGELOG.md`, `Shared/` | verified |
| Licences | `LICENSE`, `Enterprise/LICENSE`, `Incubator/*/LICENSE.md`, `ENTERPRISE.md` | verified |
| Feature descriptions | docs and component READMEs (full reads of `docs/security.md`, `docs/harness-setup.md`, `docs/privacy.md`, `docs/usage.md`, `docs/mcp-connections.md`, `Hub/README.md`, `Server/README.md`, `Applet/README.md`, `Browser/README.md`, `Computer/README.md`) | verified as the project's documentation |
| Feature behaviour | not run | **not verified** |
| Swift code | read by name and size; not built; not read in full | **not verified** |
| Enterprise profile keys | JSON schema read | verified as written |
| Competitor claims in the README | not checked | **not verified** |

## 2. Not done (and why)

- **Building or running Noodle:** requires macOS 26 on Apple silicon and Xcode 27. This sandbox is Linux.
- **Reading every Swift source file:** 1,411 files; only module names and tests were surveyed.
- **Reading Noodle Mobile, Push, Embed and the website in depth:** surveyed through their READMEs.
- **Running `noodled` (Server):** Linux only, needs systemd and bubblewrap; not attempted.

## 3. Open questions

1. How exactly is the restricted sandbox implemented on macOS (`Sources/NoodleAgentHost`, `claude-sandbox-probe.py`)? The security claims depend on it.
2. What is `NoodleAppleRuntime` doing for Apple Intelligence, and what data leaves the Mac in that mode?
3. Is `AllowCustomMCP` (in the schema) absent from the published key list by design or by omission?
4. Several changelog versions (0.81.0, 0.82.1) were not read in detail.
5. Who maintains the project? Commit history (all branches): `pdparchitect` 1,885 commits, a `noodle-theo[bot]` account 245, and four other contributors with 1 to 3 commits each. The project is effectively one maintainer. Confirm bus-factor and support expectations before a team deployment.
6. What is Rook's status and red-team scope, and who authorises its use? Its design says it is for "authorized offensive engagements"; its licence is non-commercial.

## 4. Lessons for our build

These come from Noodle's documents and code, not its marketing.

1. **Keep the harness as an external process.** Noodle runs each agent program under its own account and supervises it. Our Temporal activities do the same job for model calls.
2. **A restricted default with an explicit, confirmed escalation.** Noodle asks for confirmation before turning on unrestricted access and records the change. Our approval gates should do the same for wider tool access.
3. **Separate the sign-in from the bot.** Noodle keeps a private copy of each sign-in per bot and says plainly that copies share the account's billing and revocation. Our worker-only secrets are the same idea; copy the honesty of the documentation.
4. **Name the limits in the product docs.** Noodle's security page has a limitations section that states writable files, shared data, open internet access and no resource limits. We should publish the same list for our bots.
5. **Per-bot budgets and suspension.** Token budgets per hour, day, week and month, and a suspend-for-a-period control, are simple and useful. Our schedules can carry the same budget check.
6. **Heartbeats and assignment files.** Bots keep an assignments file and advance it on each heartbeat, and they schedule their own wake-ups with a cap (three at once). Temporal timers can implement a cap per bot.
7. **Installer-level choices.** A Suite installer that lets people choose components, and an MDM profile with per-key restrictions (`AllowedHarnesses`, `AllowCustomMCP`, and so on), is a good model for a configurable deployment.
8. **Documented licence boundaries.** The three-licence split (Apache, PolyForm Small Business, PolyForm Noncommercial) is stated per folder. We should do the same if we ever mix licences.
9. **Engineering rules for concurrent agents.** `AGENTS.md` assumes several agents edit the repo, forbids commits unless asked, and requires changelog updates in the same change. Our repo has no equivalent yet.

## 5. Suggested follow-ups

1. Build Noodle on a Mac with Xcode 27 and run its tests, to verify the feature claims that depend on runtime behaviour.
2. Read `Sources/NoodleAgentHost` and `Sources/NoodleAgentBridge` in full, and the sandbox code, to verify the restricted-access claims.
3. Compare Noodle's restricted sandbox with Temporal activity isolation for our `michel/` tools.

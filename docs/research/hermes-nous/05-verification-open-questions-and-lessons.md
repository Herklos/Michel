# 05. Verification, open questions, and lessons for our build

## 1. What was verified

| Area | Method | Result |
|---|---|---|
| Site, docs index, full docs | `llms.txt`, `docs/llms.txt`, `llms-full.txt` fetched; sections read by heading | verified as the project's documentation |
| Source counts | shallow clone `NousResearch/hermes-agent` (HEAD 2026-11-13); `find`, `ls` | verified (file 01 §4) |
| Release tags | `git ls-remote --tags` | 250 tags; latest `v2026.9.24` |
| Licence | `LICENSE` (MIT), `pyproject.toml` | verified |
| Migration commands | `grep` in `hermes_cli/` | verified that the code references them; not executed |
| X Chat plugin | `grep` in `plugins/` | not found in this repository |
| Feature behaviour | not run | **not verified** |
| Vendor comparisons | comparison pages read; cited sources not fetched | **not verified** |
| Hermes Cloud, Nous Portal | not in the repository | **not verified** |

## 2. Access limits

- The release page `nousresearch.com/releases` is an HTML catalogue of models and papers, not an agent changelog.
- The agent's own changelog is not in the docs dump. The GitHub release notes were not fetched (no API), so the content of each tag is unread.
- `pyproject.toml` version `0.0.0` means the tag is the only version identifier.

## 3. Open questions

1. What changed between the tags (for example `v2026.9.7` and `v2026.9.24`)? Read the tag messages or commit log.
2. The docs say "70+ tools, 28 toolsets". Which exact count is right (the source's toolset registry should answer this)?
3. The memory page says two processes on one home "compound" writes. Is the single-writer rule enforced at runtime, or only documented?
4. How does `smart` approval classify commands? The classifier was not read.
5. What exactly is in the Nous Portal plans (the Tool Gateway's web search, image and TTS quotas)?
6. Which of the 35 messaging platforms are production-ready? The docs list statuses per platform (for example "Labs" or "catalogue"); not read.

## 4. Lessons for our build

These come from Hermes's documents and source. Several overlap with Noodle's.

1. **One writer for session state.** Hermes makes the profile's gateway the single writer of sessions and forces every client through it. Our Temporal workflow is already the single writer for a bot's conversation; keep clients on signals and queries, never direct database writes.
2. **Frozen memory snapshots.** Injecting memory once per session preserves the prompt cache and makes behaviour predictable. We should inject per-run snapshots the same way.
3. **Bounded memory with explicit errors.** A hard character limit that returns an error (rather than silently dropping entries) forces the agent to curate. Our per-bot memory could use the same limit and error.
4. **Cron admission recovery.** An agent-backed run keeps its fire identity until delivery is recorded; a known result is delivered without re-running; an uncertain delivery is not retried automatically. Temporal's activity history gives us most of this; the "don't auto-resume after an unknown interruption" rule is worth copying as an explicit policy.
5. **Loop guards.** Cron runs cannot create cron jobs; the supervised gateway cannot restart itself. Our Schedules should refuse to create schedules from inside a scheduled run.
6. **Separate defaults for unattended contexts.** Hermes sets cron, single-query, and webhook sessions to deny dangerous commands by default, separately from interactive sessions. Our schedule and webhook paths should default to deny for approval-gated tools.
7. **A curator for self-written skills.** Skills the agent creates should be pruned by use, not kept forever; pinned and scheduled ones stay. We have no skill store yet; if we add one, copy the rule.
8. **Name what YOLO still asks for.** Hermes lists the prompts that survive its bypass mode (spend limits, elicitation, card fills, subscriptions). Our approval design should list its non-bypassable checks the same way.
9. **Profiles as isolated homes.** Named profiles with their own config, sessions and cron, and a documented clone that excludes channel credentials, is a clean model for multi-tenant bots.
10. **Be explicit about competitor claims.** Hermes's comparison pages are marketing. Our own comparisons should cite the competitor's primary source or say they are unverified.

## 5. Suggested follow-ups

1. Read the git tag messages between `v2026.9.7` and `v2026.9.24` to build a real changelog.
2. Count the toolsets from `toolsets.py` properly and reconcile with the docs' figure.
3. Read `tools/approval.py` and the `smart` classifier, to know what the default actually blocks.
4. Test `hermes migrate grok-bot` and `hermes migrate openclaw` on sample data, to verify the import claims.

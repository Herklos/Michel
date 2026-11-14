# 04. Product features: what Robin does, as the code and docs describe it

Sources: `README.md` ("What Robin does", "Control and safety"), `docs/reference/human-review.md`, `docs/reference/expedited-slack-review.md`, `docs/reference/auto-approve-rules.md`, `docs/reference/review-approval-threat-model.md`, `docs/MERGE_QUEUE.md`, `docs/PLUGINS.md`, `docs/reference/audit-logs.md`, `docs/TRACE_ACCESS.md`, `docs/CUSTOMIZATION.md`, backend module docstrings, `swagger.json`. Read 2026-11-14. Features are listed as the repo states them; "not verified" marks claims I did not check against running code.

## 1. Entry points

- **Dashboard** (`ui/`, React): start and continue work, see threads, change settings.
- **GitHub:** issues and PR conversations; the reviewer and review-scout run on pull requests.
- **Slack:** @mentions, DMs ("concierge" threads), incident channels, review requests. Typed and slash commands are optional shortcuts; buttons are preferred for explicit actions (`AGENTS.md`).
- **Linear:** mention or delegate an issue to the Robin app to open an agent session.
- **Schedules:** recurring tasks (declared in MDA or created at runtime).
- **CLI `robin`:** run an agent on a local checkout (file 08).
- **Desktop app:** "This Mac" as the sandbox for a thread (file 08).
- **Claude Code plugin:** mirror Claude Code sessions into Robin threads and use Robin's MCP tools (file 08).
- **Public API:** 309 operations (file 07 §4).

## 2. Build

- Investigate repositories, edit code, run focused validation, open or update pull requests.
- Parallelize: subagents for research and independent work (`task`; background workers via `start_async_task`).
- `open_pull_request`, `propose_pr_review`, `publish_review`, `merge_expedited_pr`, `request_human_review`, `expedite_pr_approval` (tools in `openswe/tools/`).

## 3. Review

**Reviewer run** (`reviewer` kind): a read-only review of one PR, with findings (`add_finding`, `list_findings`, `update_finding`, `resolve_finding_thread`, `reply_to_finding_thread`), a diff helper (`fetch_review_diff`), and publication (`publish_review`).
- Reviewers are instructed "not to commit or push"; PR chat excludes mutation tools (README).
- Reviewer code mode may call a fixed list of tools from its JavaScript (`_REVIEWER_PTC_TOOLS` in `mda/agent.py`): `read_file`, `write_file`, `web_search`, `fetch_url`, `http_request`, the finding tools, and `publish_review`.
- Evaluation: an offline LangSmith eval over 50 PRs and 173 categorized golden comments from `withmartian/code-review-benchmark` (`evals/reviewer/README.md`). The judge is `claude-opus-4-5` via the gateway.

**Approval modes** (`docs/reference/auto-approve-rules.md`): each repository's approval mode is `off` (skip), `dry_run` (default: post the assessment as a comment), or `approve` (submit a GitHub approval).

**Auto-approve rules** live in the repository's `.open-swe/auto-approve-rules/*.md`, read from the **default branch**, so a PR cannot rewrite the rules that judge it. Frontmatter scopes a rule with `match-all-files` and/or `match-any-files` (glob lists, `fnmatch`). If any rule fails to parse, no rule applies. The repo ships seven example rules (`default-off-experiments`, `documentation`, `human-review-required`, `langchain-dependency-refreshes`, `small-low-risk-changes`, `stricter-approval-policy`, `tests-only`).

**Stale-approval threat model** (`docs/reference/review-approval-threat-model.md`): a GitHub approval can satisfy required reviews even after new commits. Robin tries to dismiss superseded approvals on `pull_request.synchronize`, and after publishing a review it withdraws older approvals from the same bot login. The document states limits: turning automatic review off does not revoke an existing approval.

**Supplementary reviews** (`docs/reference/human-review.md`): per-repository specialist reviews (for example design or security) configured in `.open-swe/settings.json` with `paths`, `exclude`, and `criteria`, each assigned to a GitHub team.

## 4. Human review in Slack

Two request kinds, stored in one `human_review_request` table (`docs/reference/human-review.md`):

- **Standard:** any open PR posted to the repository's review channel. People sign up and review on GitHub; the PR merges once they approve. One open request per PR.
- **Expedited:** a tiny PR whose full diff is shown on a Slack card; one person other than the author approves from the card (see §5).

Routing: `.open-swe/settings.json` sets `reviewChannel`, and `reviewChannelRules` route changed files to channels by path. The channel with the most changed files wins; ties are broken at random. `reviewAllowedAuthors` lists GitHub logins outside Robin accounts allowed to request review. Human-review events are kept 14 days in the admin-only `event_log`.

## 5. Expedited Slack review (experimental, off by default)

From `docs/reference/expedited-slack-review.md`:
- The agent calls `expedite_pr_approval` whenever it decides to. The backend decides eligibility and posts the card. Nothing posts in the background.
- Gate: 1–20 changed lines (the agent is told 20; **25 is enforced**). Binary diffs are refused.
- Tests, generated declarative files (`swagger.*`, `openapi.*`, snapshots) sit outside the gate. Hunks that qualify under the repository's auto-approve rules can be excluded from the card; CI workflows, migrations, dependency manifests, lockfiles, env files, and auth/credential paths can never be excluded.
- The approval survives a later commit only if it leaves the drawn diff unchanged.
- Conditional approval: a review may approve once a person approves one named condition ("Remove the legacy `foo` exporter").

## 6. Merge queue (`docs/MERGE_QUEUE.md`)

Two modes, documented as separate integration steps:
- **Native observation:** reads GitHub's merge queue through the App (Contents, Metadata, Pull requests: read) and stores a snapshot. It "never builds commits, dispatches tests, posts checks, or merges PRs." Limit: merge-commit queues, at most 100 entries. Webhooks schedule wakeups; a minute job recovers missed deliveries.
- **Custom mode** (default): a candidate and smoke-validation controller. Configured per workspace in `merge_queue_config` with a dispatch URL, a reviewed workflow digest, operator emails, `max_batch_size`, `collection_seconds` (example 900), and per-check App IDs. Validation requires a dispatcher and an independent check-reporting authority. "A custom smoke pass is not permission to merge."

Native validation is **not** implemented; the doc lists it as a later integration step.

## 7. Operate: baby-sit, monitors, incidents, schedules

- **`/baby-sit`** (`openswe/baby_sit.py`): "durable, opt-in PR CI watches." Diagnoses failures and reruns only "evidence-backed flaky jobs" (README). Managed by the `manage_baby_sit` tool; bundled skill `baby-sit`.
- **Monitors** (`openswe/monitors/`): long-running sandbox commands whose filtered output is delivered to the thread as events (`monitor` tool).
- **Incidents** (`openswe/incidents/`): Slack incident channels investigated on system-owned agent threads (`incident_policy` table).
- **Schedules:** recurring prompts, declared in `schedules/` (MDA) or created by the backend's schedule store (`openswe/schedules/`). The schedule store references `pull_request.opened` as an event trigger (`openswe/schedules/store.py`).
- **Event subscriptions:** `listen_events` lets an admin thread subscribe to sources (for example `human_review`); tables `event_subscription` and `event_match`.
- **Background callbacks** (`openswe/background_tasks.py`): finished sandbox commands call back, or a per-thread cron polls each minute.

## 8. Build products: projects, artifacts, plugins, page commands

- **Projects** (`openswe/projects/`): "named, shareable folders of threads" (`project`, `project_member` tables).
- **Artifacts:** `publish_artifact` and `output_iframe` tools; the `html-artifacts` bundled skill; sandbox HTML previews can be attached to Slack threads (`slack_attach_html`).
- **Web apps / plugins** (`docs/PLUGINS.md`, `openswe/plugins/`, `plugins/`): an app is one self-contained HTML file in a sandboxed frame with an opaque origin, `default-src 'none'` CSP (no network), no navigation, and a MessageChannel to the dashboard using Cap'n Web. It reaches the backend only through `/plugins/{id}/...` and acts as the person using it, within the grants the installer approved. Starter (`plugins/starter`) and a Markdown-docs app that publishes pull requests (`plugins/docs`) are included. Tables: `plugin`, `plugin_version`, `plugin_installation`, `plugin_repository_grant`, `plugin_document`, `plugin_chat`, and others.
- **Page commands** (`openswe/page_commands/`): a dashboard tab that is "a page session" queues commands for the browser to carry out, in order, and reports results back (`page_command` table).

## 9. Settings, instructions, skills, MCP, models

- **Settings:** instance, workspace, thread and personal scopes (the `settings_record` table; workspace and personal settings modules). Every setting has a matching agent tool with the same validation (`AGENTS.md`).
- **Instructions:** agent instructions (instance/workspace) and user instructions (`agent_instructions`, `user_instructions`).
- **Skills:** bundled skills (`openswe/bundled_skills/`, five), organization skills (`organization_skills` tool), repository `AGENTS.md`.
- **MCP:** connections layer instance-wide, workspace and personal tools (`mcp_connection`, `mcp_oauth_entry`, `user_oauth_credential`). Managed tools cards (`managed_tools_card`, `discover_managed_tools`, `connect_managed_tools`).
- **Models:** choose model and reasoning effort per instance, workspace, thread or person; "Auto" routing; a model named in the opening Slack request (file 06).
- **Workspaces:** a grouping of repositories with routing, base snapshot, Slack channels, settings, merge-queue config (`workspace`, `workspace_repository`, `workspace_slack_channel`).
- **Feature flags:** `manage_feature_flags`; experiments including classify, model routing, and expedited review.

## 10. Governance and observability

- **Audit logs** (`docs/reference/audit-logs.md`): metadata-only, insert-only records in `audit_logs`, covering authenticated dashboard writes, settings tools, and workspace lifecycle. Request and tool bodies are never stored.
- **Analytics:** `analytics/` package with PostHog and Segment senders, an outbox, and usage observations (migration `0009_usage_observations`); usage and cost summaries.
- **Traces:** self-only LangSmith trace access via `root_run_metadata.owner_ls_user_id` under LangSmith ABAC (`docs/TRACE_ACCESS.md`). Service keys remain privileged.
- **API keys** (`api_keys/`) and **federation** (`federation/`, GitHub Actions tokens) for non-browser callers.
- **Announcements** (`announcements/`) and **notifications** (`app_notification`).
- **Encryption** (`encryption.py`, `encryption/` config): in the Agent Server config (file 06).

## 11. Not verified in this pass

- Behavior of every route in the 253-path API (only names and tags were read).
- The `trace_flight_season` and `trace_flight_best` tables (names only; purpose not read).
- The `openwiki/` directory (53 files; a generated docs tree updated by the `openwiki-update.yml` workflow; contents not read).

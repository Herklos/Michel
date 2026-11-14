# 05. Integrations and channels: GitHub, Slack, Linear, MCP, web tools

Sources: `openswe/github/`, `openswe/slack/`, `openswe/linear/`, `openswe/mda_channels/__init__.py`, `openswe/bridge/`, `openswe/claude_code/`, `openswe/mcp/`, `mda/channels/*.py`, `mda/identity.py`, `swagger.json` (webhook paths), `pyproject.toml` (dependencies), `AGENTS.md`, `docs/INSTALLATION.md` (partly), `docs/CUSTOMIZATION.md` §4 and §3. Read 2026-11-14. Setup steps in `docs/INSTALLATION.md` were not read in full.

## 1. Who receives what

| Channel | Receives events | Delivered to | Replies |
|---|---|---|---|
| GitHub | App webhooks | MDA's GitHub channel (`mda/channels/github.py`) → backend `/mda/github/deliveries` and the MDA channel API | PR comments, reviews, labels; the run acts as the App or as a linked user |
| Slack | Slack Events and interactivity | Backend `/webhooks/slack` and `/webhooks/slack/interactivity`; MDA's Slack channel (Trigger-backed) → `/mda/slack/channel-events` | threads, DMs, ephemeral replies, Block Kit cards |
| Linear | Linear app webhooks | MDA's Linear channel (`mda/channels/linear.py`) | agent-session replies and comments |
| HTTP | custom webhooks for other providers | an MDA HTTP channel, if declared | the channel's `post` callback |

Only the MDA deployment, holding Robin's shared secret, may call the backend's channel endpoints (`openswe/mda_channels/__init__.py`, which names `.auth` as the check). A channel thread belongs to that channel's conversation and runs on a thread the backend owns.

## 2. GitHub

- **Client:** `githubkit` 0.17.1 with `githubkit-schemas` and App auth (`pyproject.toml`). `AGENTS.md`: call GitHub only through named `RepoClient` and `PullRequestClient` methods; raw REST paths only in `openswe/github/http.py`.
- **Acting identity:** `GitHubClient.as_user(login)` or `GitHubClient.as_app(owner, repo)`. `connect(token=...)` only for a token a run was handed.
- **Sandbox access:** coding sandboxes "normally receive installation-wide GitHub App access; selected workflows use narrower repository scopes" (README). The proxy is configured for `github.com` (Basic, token) and `api.github.com` (Bearer) (`docs/CUSTOMIZATION.md`). Workspace repository bindings control routing and checkouts, not a separate credential boundary.
- **Webhooks:** `/mda/github/deliveries` (MDA-forwarded) and `/webhooks/rollout`, which the rollout checklist uses. `pull_request.synchronize` schedules withdrawal of stale Robin approvals (threat model).
- **Merge queue:** native observation via the App's `merge_group` subscription; custom mode dispatches to a configured dispatcher (file 04 §6).
- **Repository settings in the repo:** `.open-swe/settings.json` and `.open-swe/auto-approve-rules/` (read from the default branch).
- **Reviewer bot identity:** the bot's login matters: approvals are withdrawn "from the same bot login as the posted review" (threat model).

## 3. Slack

- **Client:** `slack-sdk` 3.44.1 (`pyproject.toml`); `openswe/slack/client.py`, routes in `openswe/slack/routes.py`, tools `slack_reply`, `slack_attach_html`.
- **Trigger modes** (MDA channel): `mention`, `thread`, `all` (`docs/` and `mda/channels/slack.py`; file 03 of the managed research has the semantics).
- **Concierge DM:** a person's DM with the bot is a thread that "must see everything in their DM with the bot" (`AGENTS.md`).
- **Thread coherence rule:** "An agent thread's view of its Slack thread never diverges from the Slack thread." Commands another thread took (`/btw`, `/breakout`) and anything Robin posts that the thread's agent did not write are posted as notices (`SlackNotice`).
- **Single owner rule:** "Only the agent that owns a Slack channel thread posts in it." Background work sends events via `wake_thread_owner` or `note_for_thread_owner`.
- **Interaction design:** prefer @mentions with plain-language requests and buttons for explicit actions; typed and slash commands are optional shortcuts. Block Kit: update the clicked message before slow GitHub or Slack calls.
- **Cards:** human review (standard and expedited), incident channels, model selection, approvals, and walkthroughs. Button clicks come back as `"interaction"` events.
- **Incidents:** Slack incident channels are investigated on system-owned agent threads (`openswe/incidents/`, `incident_policy` table).
- **Files:** Slack attachments are saved to `/workspace/attachments/` in the sandbox; thread history is scanned for files (up to 5 pages of 100 messages) when the history scope is granted (`docs/CUSTOMIZATION.md` in managed research file 02).
- **Search grants:** a `slack_search_grant` table exists; its purpose is inferred from the name only.

## 4. Linear

- **Channel:** `mda/channels/linear.py` declares `channels.linear(...)`; `openswe/linear/` is the backend side.
- **Routing:** `docs/CUSTOMIZATION.md` §4 has "Customizing Linear routing". Mentions and delegations open an agent session on the issue.
- **Tools:** `linear-tickets` bundled skill; `mda/rt/linear_automations.py` handles Linear automation events.
- **Prompts:** `linear-issue.md.jinja`, `linear-automation-event.md.jinja`.

## 5. Model Context Protocol (MCP)

- **Client:** `langchain[mcp]` (`pyproject.toml`); code in `openswe/mcp/` and `mda/rt/mcp.py`.
- **Scopes:** instance-wide, workspace-specific, and personal servers (README: "MCP connections layer..."). Managed-tools cards for LangSmith-hosted kits (`managed_tools_card` table).
- **Credentials:** `mcp_connection`, `mcp_oauth_entry`, `user_oauth_credential`; `mda/CONNECTIONS.md` describes how MDA resolves connections for runs.
- **Exposure:** `mcp_exposure` tool, and the Claude Code plugin exposes Robin's MCP tools to Claude Code.
- **Customization:** add servers through `docs/CUSTOMIZATION.md` "Workspace MCP servers" and "MCP servers on an MDA connection".

## 6. Web and HTTP tools

- `fetch_url` (`openswe/tools/fetch_url.py`): fetches web pages as Markdown. Uses `markdownify` and `markdown-it-py`.
- `http_request` (`openswe/tools/http_request.py`): HTTP API calls.
- `web_search` (`openswe/tools/web_search.py`, and `mda/rt/local_tools.py`): search via the `exa-py` client.
- Reviewer code mode may call `web_search`, `fetch_url`, `http_request` (file 04 §3).

The `mda/rt/public_http.py` module is used for fetching attachments and images that channel messages reference.

## 7. Bridge: a thread whose sandbox is a person's machine

- **Backend side:** `openswe/bridge/` ("a cloud thread whose sandbox is the user's own machine"): routes, store, protocol, worktree branch and handoff logic.
- **Machine side:** `bridge-client/` (TypeScript, `open-swe-bridge-client`), shared by the CLI and the desktop app. Long-polls the backend for `execute`, `upload_files`, and `download_files` requests, runs them locally, and posts results. Files: `executor.ts`, `bridge.ts`, `github-remote.ts`, `api.ts`.
- **Safety:** commands run **unsandboxed** as the user (CLI README). Auto mode reviews calls that leave the checkout, touch credentials or reach beyond the project (file 03). Desktop runs commands with the login shell's environment, minus secret-shaped variables except `GITHUB_TOKEN` and `GH_TOKEN`.
- **Continuity:** a bridged thread "runs only while the app that started it is open" (desktop README).

## 8. Claude Code

- `openswe/claude_code/`: reads what Claude Code writes on a person's machine (transcripts, hooks, sync tokens). Table `claude_code_sync_token`; five `claude-code` operations appear in `swagger.json`.
- `claude-code-plugin/`: plugin named "robin" that mirrors Claude Code sessions into Robin threads and exposes Robin's MCP tools; skills `connect` (with `connect.py`) and `thread`.

## 9. Webhook endpoints (from `swagger.json`)

`/webhooks/slack`, `/webhooks/slack/interactivity`, `/webhooks/run-complete`, `/webhooks/rollout`, `/mda/resolve-user`, `/mda/github/deliveries`, `/mda/slack/channel-events`, `/mda/slack/reactions`, `/mda/channel-api/{endpoint}`, and `/health`. The Makefile `tunnel` target exposes only `/webhooks/*` through ngrok, with `examples/ngrok/webhooks-only.yml`.

## 10. Not verified in this pass

- Exact Slack scopes and GitHub App permissions required for each feature (see `docs/INSTALLATION.md`, not read in full).
- Linear app setup details.
- The Slack, GitHub, and Linear channel SDK behavior beyond their declarations.

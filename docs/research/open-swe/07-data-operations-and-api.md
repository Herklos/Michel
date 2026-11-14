# 07. Data model, operations, deployment, and the public API

Sources: `openswe/database/migrations/versions/` (161 migration files), table names from `__tablename__` and `create_table` calls (80 distinct names), `swagger.json` (OpenAPI 3.1.0, 253 paths, 309 operations, 288 schemas), `langgraph.json`, `Dockerfile`, `compose.yaml`, `Makefile`, `.github/workflows/*.yml`, `docs/DEVELOPMENT.md`, `docs/INSTALLATION.md` (partly), `pyproject.toml`, `scripts/`. Read 2026-11-14.

## 1. Database

- **PostgreSQL** with **SQLAlchemy 2.1.8 (async)**, **asyncpg 0.32.0**, and **Alembic 1.20.1** (`pyproject.toml`). Migrations are created with `make migration m="..."`.
- **161 migrations** (`0001_analytics.py` through `0103_...`; the numbering is not contiguous per file name alone).
- **80 distinct tables.** Grouped by area (names from the code):

| Area | Tables |
|---|---|
| Identity and access | `users`, `user_identity`, `user_record`, `api_key`, `user_oauth_credential`, `allowed_slack_bot` |
| Workspaces and repositories | `workspace`, `workspace_repository`, `workspace_slack_channel`, `repository`, `settings_record`, `skill`, `agent_instructions`, `task` family |
| Threads and runs | `task`, `task_membership`, `task_message`, `task_delegation`, `thread_plan`, `thread_plan_comment`, `thread_queued_message`, `thread_feedback`, `thread_blob`, `run_tool_sets` |
| Slack | `slack_channel`, `slack_thread`, `slack_message`, `slack_run`, `slack_pull_request_link`, `slack_search_grant` |
| Pull requests and reviews | `pull_request`, `pull_request_review`, `pull_request_thread`, `pull_request_finding`, `pull_request_finding_state`, `pull_request_finding_interaction`, `pull_request_requester`, `pull_request_walkthrough`, `completed_review`, `review_assessment`, `review_shadow`, `review_style`, `reviewer_eval_run` |
| Human review | `human_review_request`, `human_review_participant`, `event_subscription`, `event_match` |
| Merge queue | `merge_queue`, `merge_queue_request`, `merge_queue_attempt`, `merge_queue_batch`, `merge_queue_decision`, `merge_queue_evidence`, `merge_queue_member` |
| Plugins | `plugin`, `plugin_version`, `plugin_bundle`, `plugin_installation`, `plugin_repository_grant`, `plugin_document`, `plugin_document_attachment`, `plugin_chat`, `plugin_chat_call`, `plugin_room_update` |
| Projects and page | `project`, `project_member`, `page_command` |
| MCP and tools | `mcp_connection`, `mcp_oauth_entry`, `managed_tools_card` |
| Notifications and announcements | `app_notification`, `announcement`, `announcement_delivery`, `incident_policy` |
| Governance and analytics | `audit_logs`, `event_log`, `trace_flight_season`, `trace_flight_best`, `short_link`, `agent_report_receipt` |

Modeling rules (`AGENTS.md`, `openswe/database/migrations/AGENTS.md`): UUIDv7 primary keys set in Python; `created_at`, `updated_at` with `clock_timestamp()`; `created_by`/`updated_by` foreign keys to `users`; natural keys as unique indexes; JSON columns named after their content.

Migration notes worth knowing:
- `0050_..._join_screenshot_evidence_and_modal_base_` (the name mentions "modal base", a UI concept, not a sandbox provider).
- `0052_..._index_event_log_by_source_and_event_type`.
- `0103_..._add_thread_last_activity_timestamp`, `0103_..._let_a_managed_tools_card_name_no_kit`: two migrations share the `0103` prefix.

## 2. The thread store and the Agent Server

- Thread metadata and state are in PostgreSQL (`openswe/threads/store.py`). The Agent Server holds checkpoints (with TTL) and runs.
- The **store** is not used for state (`AGENTS.md`).
- A **thread index** is kept in PostgreSQL and served through `openswe/threads/router.py`.

## 3. Operations and runtime configuration

**`langgraph.json`** (`python_version` 3.14, `api_version` `>~=0.15.0rc1`): graphs `agent`, `reviewer`, `review-scout`; HTTP app `openswe.webapp:app`; auth `openswe.api.agent_server_auth:auth` with Studio auth disabled; checkpointer TTL (delete after 12 h, sweep hourly); env from `.env`; Dockerfile lines that build the dashboard into `/opt/open-swe-dashboard`, with `DASHBOARD_STATIC_DIR` set. The dashboard build is "best effort": a failed UI build still deploys the backend.

**Dependency pins of note** (`pyproject.toml`): `deepagents==0.7.35`; `managed-deepagents>=0.10.1` (vendored); `langgraph>=1.2.20`; `langgraph-sdk>=0.4.14`; `langchain[mcp]>=1.4.10`; `langchain-quickjs==0.3.12`; `langchain-typesafe==0.0.2`; `githubkit==0.17.1`; `standardwebhooks>=1.1.0`; `httpx2>=2.12.0`; `slack-sdk>=3.44.1`; `croniter>=6.0.0`. `[tool.uv] constraint-dependencies` pins `langgraph-api==0.19.0.dev3` and `langgraph-runtime-inmem==0.39.0.dev5`, which are **pre-release** builds. The PyPI versions read in the managed research were 0.18.0 and 0.38.0.

**Toolchain:** Python **3.14+** with uv; Node **26+** and pnpm **11.22.0** (Dockerfile) for the dashboard and TypeScript packages; Turbo for the JS workspace (`turbo.json`, `pnpm-workspace.yaml`).

**Local development** (`Makefile`, `docs/DEVELOPMENT.md`):

| Target | What it does |
|---|---|
| `make dev` | starts Postgres 16 in Docker (port 5433) if no `POSTGRES_URI`, then `langgraph dev --port 2024` |
| `make dev-mda` | runs the MDA runtime locally on port 2025 from the vendored `mda` CLI |
| `make dev-ui` | Vite dashboard on port 3000, backend on 2024, and MDA on 2025, in parallel |
| `make tunnel` | ngrok, exposing only `/webhooks/*` (`examples/ngrok/webhooks-only.yml`) |
| `make migration m="..."` | new Alembic migration |
| `make swagger` | regenerates `swagger.json` from the FastAPI app |
| `make run` | `uvicorn openswe.webapp:app` on port 8000 (no LangGraph server) |
| `make mda-cli` | builds the vendored Rust `mda` CLI |
| `make mda-test`, `make mda-typecheck` | tests and types for `mda/` |
| `make desktop`, `make cli`, `make install-desktop` | desktop and CLI builds |
| `make lint`, `make format`, `make typecheck`, `make test` | project checks |

**Containers:**
- `compose.yaml` starts **only Postgres 16** (loopback port 5433, volume `open-swe-postgres`).
- The root `Dockerfile` builds the **LangGraph API server image** (the backend; not the sandbox image). `docs/INSTALLATION.md` shows an example with Redis: `REDIS_URI`. **Redis is not referenced in any code** (0 matches in `openswe/` or `mda/rt/`), so the example is stale.

**CI** (`.github/workflows/`): `ci.yml` ("Agent CI") runs lint, format check, typecheck, swagger check, a check that no new `langgraph_client` uses appear in the backend, and a check that owned HTTP clients use `httpx2` (`scripts/check_httpx.py`, `scripts/check_langgraph_client.py`). Other workflows: `precommit.yml`, `pr_lint.yml`, `check-pr-source.yml`, `close_old_prs.yml`, `clear_pending_deletion.yml`, `keep_open_on_comment.yml`, `openwiki-update.yml`.

**Scripts** (`scripts/`): `deploy_preview.py`, `build_preview_branch.py` (preview deployments), `create_sandbox_snapshot.py`, `list_snapshots.py`, `new_migration.py`, `rebuild_transcript_projections.py`, `purge_wakeup_crons.py`, `seed_local_author_guidance.py`, `scrape_pr_context.py`, `sync_pull_request_descriptions.py`, `stamp_build_info.py`, `vendor.py`, `install_desktop.sh`, `dotenv_value.sh`.

## 4. Public API

`swagger.json` is generated from the FastAPI app (`make swagger`) and committed. It declares **253 paths**, **309 operations**, **288 schemas**.

| Path prefix | Paths | Notes |
|---|---|---|
| `/dashboard/*` | 243 | the web UI API; tags include `dashboard` (284 ops), `threads` (48), `review` (44), `plugins` (44), `slack` (17), `auth` (10), `workspaces` (9), `projects` (8), `pull-requests` (7), `analytics` (6), `merge-queue` (6), `plan` (6), and about 25 more |
| `/mda/*` | 5 | channel callbacks from the MDA runtime (`resolve-user`, `github/deliveries`, `slack/channel-events`, `slack/reactions`, `channel-api/{endpoint}`) |
| `/webhooks/*` | 4 | `slack`, `slack/interactivity`, `run-complete`, `rollout` |
| `/health` | 1 | liveness |

Tags of note: `sandbox-bridge` (5), `sandbox-tools` (3), `workflow-approval` (3), `trace-flight` (4), `transcript` (5), `api-keys` (3), `claude-code` (5), `announcements` (2), `event-log` (2), `incidents` (2), `notifications` (2), `profiles` (3), `user-preferences` (2).

Auth (`openswe/api/agent_server_auth.py`): the Agent Server's own API is reachable only with the deployment's LangSmith key by the backend; a signed-in dashboard user can read threads they own; everything else goes through the dashboard API, which applies Robin's thread rules first. API keys (`api_keys/`) and federation tokens cover non-browser callers.

Request hygiene: a body size limit (`openswe/api/body_limit.py`), request ids (`request_ids.py`), public origin handling (`public_origin.py`), and GitHub error mapping (`github_errors.py`).

## 5. Analytics and telemetry

- `openswe/analytics/`: events, identity, directory, measurements, outbox, PostHog and Segment senders, retention, revisions, summaries, usage, a worker, and routes.
- Telemetry toggles and tracing: `openswe/api/tracing.py`; LangSmith tracing via `langsmith`; Datadog browser RUM and PostHog in the dashboard (`ui/package.json`).
- Frontend tracing and analytics are in the dashboard, not in the backend's API responses.

## 6. Background work

- **Job queue** (`openswe/jobs/queue.py`) runs "work due at a time, once or on a cron schedule", via `JobWorker`. Handlers in `openswe/jobs/kinds.py`. One registered kind was found by the grep (`event_subscription_timeout`), so the registry is larger than the grep showed.
- **Background tasks, monitors, schedules, wakeups:** see file 02 §8 and file 04 §7.
- **Concurrency:** `openswe/webapp.py` wires the worker before startup (kinds imported first, per the module docstring).

## 7. What this shows about scale

- 161 migrations and 80 tables for one product: the schema is the product's largest, most stateful surface.
- The public API is a dashboard API first; the `/mda` and `/webhooks` routes are a small set of callbacks.
- Operationally the stack has three moving parts beyond the code: Postgres, the Agent Server (LangGraph), and MDA with LangSmith sandboxes and gateway.

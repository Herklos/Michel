# 08. How open-swe (Robin) uses LangSmith: the preview and every other surface

Source: `langchain-ai/open-swe` at `42db6cc` (clone at `/home/user/langchain-ai/open-swe`), read 2026-11-14. Each row names the feature from files 02 to 07 and the open-swe file that uses it. Verified by reading the file or by a targeted search of the repository.

## 1. The preview (the question's "preview")

open-swe's preview is a **LangSmith preview deployment**: a preview branch is built and deployed as a revision of an Agent Server, and the script waits for it.

| Step | Mechanism | Where |
|---|---|---|
| Assemble a preview branch | from `main`, a `preview-manual` branch, and labelled pull requests; or reset it | `scripts/build_preview_branch.py` (docstring) |
| Resolve conflicts and fix type errors automatically | uses prompts in `.github/prompts/` and a Node 26 container for typecheck | `scripts/build_preview_branch.py` (constants `TYPECHECK_IMAGE`, prompt paths) |
| Read the preview branch's commit | `git ls-remote` on the `preview` branch, 40-hex SHA check | `scripts/deploy_preview.py` `preview_sha()` |
| Read revision status | `GET /v2/deployments/{deployment_id}/revisions` (the Deployments API, base URL `LANGSMITH_HOST_URL` or `https://api.host.langchain.com`) | `scripts/deploy_preview.py` lines 114 to 147 |
| Wait for the revision | polls every 15 s for up to an hour; statuses `CREATING`, `QUEUED`, `AWAITING_BUILD`, `BUILDING`, `AWAITING_DEPLOY`, `DEPLOYING`, then `DEPLOYED`, or `CREATE_FAILED`, `BUILD_FAILED`, `DEPLOY_FAILED`, `SKIPPED`, `INTERRUPTED` | `scripts/deploy_preview.py` (`RevisionStatus`, `IN_PROGRESS`) |
| Fetch build and deploy logs | `GET …/revisions/{id}/logs` | `scripts/deploy_preview.py` line 168 |
| Detect a superseded deploy | raises `SupersededDeploy` if the preview branch moved on | `scripts/deploy_preview.py` |
| Platform feature used | Agent Server **revisions** (file 02 §3), and the **preview build** concept (public beta) | docs `deployment-revisions`, `preview-builds` |

So the preview is the revision flow of file 02, driven from GitHub Actions, with the revision status as the gate.

## 2. Runtime: the agent is a LangSmith deployment

| Feature | How open-swe uses it | Where |
|---|---|---|
| Agent Server graphs | `langgraph.json` declares graphs `agent`, `reviewer` and `review-scout`; the HTTP app is `openswe.webapp:app`; Studio auth is disabled | `langgraph.json` |
| Checkpointer TTL | `delete` strategy, sweep hourly, 12-hour default TTL | `langgraph.json` `checkpointer.ttl` (docs `configure-ttl`) |
| Multitask strategy | runs start with `multitask_strategy="interrupt"` by default, so a follow-up halts the active run and resumes with the new message. Background follow-ups can use `enqueue`. This is the Agent Server's **Interrupt** double-texting mode | `openswe/dispatch.py` lines 6, 486, 512 (docs `double-texting`, `interrupt-concurrent`) |
| Run completion webhook | every dispatched run carries a `webhook` to `/webhooks/run-complete`, so every run ends with a signal | `openswe/completion.py` (docs "run `webhook` parameter") |
| Auth on the Agent Server | `openswe.api.agent_server_auth:auth` controls who can call the server; the backend is the only caller allowed to change things | `langgraph.json` `auth`; `openswe/api/agent_server_auth.py` |
| Deployment metadata | the runtime reads `LANGSMITH_DEPLOYMENT_NAME`, `LANGSMITH_REVISION_ID`, `LANGSMITH_LANGGRAPH_API_VARIANT`, `LANGSMITH_AGENT_VERSION`, `LANGSMITH_HOST_PROJECT_ID` | `openswe/`, `mda/` (grep counts 2 to 5 each) |
| Thread index | a PostgreSQL thread index serves the Agent Server's thread API; new threads are created there | `openswe/threads/router.py` (AGENTS.md) |
| Cron and timers | **not** Agent Server crons: background work runs on open-swe's own job queue, "instead of in Agent Server runs and crons" | `openswe/jobs/queue.py` docstring; `openswe/schedules/` |
| Dynamic per-run configuration | a factory runs per run and builds the graph from a catalog sent in the run context; "a compiled graph is scoped to one execution" | `mda/agent.py` (docs `agent-definition`, `runtime`) |

## 3. The sandbox

| Feature | How open-swe uses it | Where |
|---|---|---|
| Sandbox SDK | `langsmith.sandbox.SandboxClient`, `AsyncSandboxClient`, and errors `SandboxRetryableConnectionError`, `ResourceNotFoundError`, `SandboxNotReadyError`, `SandboxProxyConfig` | `openswe/sandboxes/providers/langsmith.py` (imports) |
| Backend integration | imports deepagents' `LangSmithSandbox` and the sandbox backend protocol types (`ReadResult`, `WriteResult`, `ExecuteResponse`, `LsResult`, and others), so the file operations speak the Deep Agents backend interface | `openswe/sandboxes/providers/langsmith.py` (imports from `deepagents.backends`) |
| Defaults | 4 vCPU, 16 GiB memory, 128 GiB filesystem, idle TTL 2 h, delete after stop 7 d | `openswe/sandboxes/providers/langsmith.py` constants (docs `sandboxes`, Managed Deep Agents' sandbox page) |
| Snapshot | `snapshot_id` or name per workspace (`base_snapshot_id`, `snapshot_name`, `snapshot_id` columns); must be a UUID server-side | `openswe/sandboxes/providers/langsmith.py`; migration `0013_workspaces.py` (docs `sandbox-snapshots`) |
| GitHub credentials through the auth proxy | `GITHUB_PROXY_RULES`: Basic auth for `github.com`, Bearer for `api.github.com`, injected by the proxy, never stored in the sandbox | `packages/runtime-api/src/runtime_api/sandbox_proxy.py`; `openswe/sandboxes/providers/langsmith.py` `get_sandbox_proxy_config()` (docs `sandbox-auth-proxy`) |
| Egress allow-list | `access_control` per sandbox (docs say per-connection enforcement) | `runtime_api/sandbox_proxy.py` (per the docs' model) |
| Reconnect and loss | `SandboxGoneError` distinguishes a deleted sandbox (hand back to MDA) from an unreachable one (not replaced silently) | `openswe/sandboxes/providers/registry.py` (AGENTS.md, CUSTOMIZATION) |
| Creation retries | create retries on 408, 409, 425, 429, 500, 502, 503, 504, 529; boot wait 90 s | `openswe/sandboxes/providers/langsmith.py` constants |
| Access delegation | not verified in the files read | — |
| Who creates it | MDA creates the sandbox when the run starts; the backend only connects to it (docs and `CUSTOMIZATION.md`) | `openswe/sandboxes/providers/registry.py` docstring |

## 4. The LLM gateway

| Feature | How open-swe uses it | Where |
|---|---|---|
| Gateway base URL | `LANGSMITH_GATEWAY_BASE_URL`, default `https://gateway.smith.langchain.com` | `packages/runtime-api/src/runtime_api/models.py` line 366 and `gateway_base_url()` |
| Gateway key | `LANGSMITH_GATEWAY_API_KEY`, falling back to `LANGSMITH_API_KEY` (needs `gateway:invoke`) | `runtime_api/models.py` `gateway_api_key()` (docs `llm-gateway-authentication`) |
| Opt-in | `LANGSMITH_GATEWAY_ENABLED` deployment default, per-workspace override | `openswe/dashboard/workspace_settings.py`; `runtime_api/models.py` |
| Model routes | `auto` and `default` routes per model | `runtime_api/models.py` `GatewayModelRoute` |
| Responses API | `LANGSMITH_GATEWAY_OPENAI_USE_RESPONSES` chooses OpenAI's Responses format for the gateway | `runtime_api/models.py` line 441 (docs `llm-gateway-api-formats`) |
| Model calls from the runtime | `mda/rt/gateway.py` sends each run's calls through the gateway as the person the run acts for, or the deployment's key for other runs | `mda/rt/gateway.py` (docs "Gateway: two credentials") |
| Decision models | Jev (TypeSafe System One) classifies routing and "use Opus" requests, with a three-second deadline and a 0.6 confidence cut-off | `openswe/model_routing.py`, `packages/runtime-api` classifier, `docs/CUSTOMIZATION.md` §2 (docs `llm-gateway-decision-models`) |
| Spend and rate policies | not configured in the repository; policies are set in LangSmith | — |

## 5. Tracing and identity

| Feature | How open-swe uses it | Where |
|---|---|---|
| Run tree API | `RunTree`, `tracing_context`, `get_current_run_tree` | imports across `openswe/` (docs `access-current-span`, `distributed-tracing`) |
| Owner metadata | every run stamps `owner_ls_user_id` (the stored owner's LangSmith user ID) into run metadata and context, so ABAC can restrict personal trace access | `openswe/threads/runtimes.py` lines 508 to 613; `mda/rt/middleware.py` line 1007; `docs/TRACE_ACCESS.md` |
| ABAC rollout | a LangSmith ABAC condition on `root_run_metadata.owner_ls_user_id` restricts non-admin users to their own traces | `docs/TRACE_ACCESS.md` (docs ABAC for trace access) |
| Service identity for MDA | `auth.langsmith_api_key()` on the MDA identity; the backend calls MDA with its LangSmith service key | `mda/identity.py` line 17 (docs `identity`) |
| Dashboard login | LangSmith OAuth client with `LANGSMITH_OAUTH_CLIENT_ID` and secret, and `LANGSMITH_AUTH_ENDPOINT` | `openswe/dashboard/langsmith_oauth.py` (docs `auth`, `add-auth-server`) |

## 6. Managed tools and MCP

| Feature | How open-swe uses it | Where |
|---|---|---|
| Managed tools | `/v1/managed-tools/servers` and `/v1/managed-tools/kits` list LangSmith-hosted MCP servers and kits; a personal kit loads per user | `openswe/mcp/managed.py` lines 54 to 55 |
| Consent | `/v1/agent-auth/oauth-authorization-sessions` starts OAuth consent | `openswe/mcp/managed.py` line 57 (docs `agent-auth`) |
| MCP connections for runs | connections offered to each run as MCP servers | `openswe/mcp/managed.py` `connections()`; `mda/rt/mcp.py` |
| Agent-side MCP | the MDA runtime can declare MCP servers in `tools/mcp.py` (managed research file 02) | `mda/` (docs `managed-deep-agents-mcp-endpoint`) |

## 7. Channels, triggers and automation

- **Trigger Server** receives Slack, GitHub and Linear events for the MDA deployment. The MDA reads `LANGSMITH_MDA_TRIGGER_SERVER_URL` (`mda/README.md`, the `*_ENV` form). This is the managed channel path described in the managed research files.
- **Automation webhooks:** not verified in the repository.
- **Linear automations** have their own runtime module (`mda/rt/linear_automations.py`). Delayed and periodic work generally goes through open-swe's job queue (AGENTS.md). The repository does not show Linear rules being implemented as LangSmith automation rules.

## 8. Evaluation

- `evals/reviewer/` uses `langsmith.Client` and `aevaluate` to run the reviewer over 50 pull requests and 173 golden comments; the judge uses `claude-opus-4-5` through the gateway (`evals/reviewer/README.md`).
- `evals/ask_messages/run_eval.py` uses the same pattern for message handling.

## 9. Things open-swe does not use, or uses differently

- **Context Hub:** no references in the repository. Managed Deep Agents' memory layers are described as stored in Context Hub by the managed docs (`docs/research/managed-deep-agents/01`), but open-swe's own memory lives in its PostgreSQL tables.
- **LangGraph Store and Agent Server crons:** avoided on purpose. AGENTS.md says "Don't use the LangGraph Store (`client.store`) for state," and the job queue is preferred for timers.
- **Legacy LangGraph SDK client:** AGENTS.md says new uses are forbidden and CI enforces it (`scripts/check_langgraph_client.py`).
- **Insights, Engine, online evaluators, alerts:** not referenced in the repository. Open-swe has its own analytics stack (`openswe/analytics/`: PostHog and Segment senders).
- **Fleet:** not used. Open-swe is a code-first Managed Deep Agents project.

## 10. Summary of the dependency

open-swe depends on LangSmith for six things: the **Agent Server** (deployment, revisions, threads, runs and the Interrupt double-texting mode), the **Sandbox** (SDK and auth proxy for GitHub credentials), the **LLM Gateway** (every model call), **tracing** (run trees and the owner metadata for ABAC), **Managed Deep Agents** (the runtime that runs the loop and the Trigger server for channels), and **Agent Auth and managed tools** (per-user MCP consent). The evaluation client and OAuth login are smaller uses.

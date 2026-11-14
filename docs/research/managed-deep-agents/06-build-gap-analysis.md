# 06. Gap analysis: what a "managed Deep Agent runtime" needs, mapped to our build

Purpose: decide what to build ourselves, what to reuse (MIT), and what the managed product provides that we do not yet have. Based on files 01–05 and our existing backend in `grokbot/` (on branch `claude/serene-pasteur-gu7bbs`). Read and written 2026-11-14.

## 1. Feature matrix

Legend: **Have** = implemented and offline-tested in `grokbot/`. **Partial** = a piece exists. **Missing** = not started. Each row names its managed-product reference from files 01–05.

| # | Capability | Managed product (reference) | Our status | Notes |
|---|---|---|---|---|
| 1 | Durable agent loop | LangGraph Agent Server with checkpointer | **Have** (Temporal workflow + `temporalio-deepagents`) | Temporal replaces the Agent Server's queue and checkpoints. Not executed end to end yet. |
| 2 | Declarative agent project (`agent.py`, `instructions.md`) | `define_deep_agent` (file 01 §2) | **Missing** | We build agents in code (`grokbot/agent.py`). A config-file or Python-factory layer is needed. |
| 3 | Per-run dynamic configuration (factory) | `agent(runtime)` factory (file 01 §2) | **Partial** | `BotConfig` is fixed per bot at creation. Per-run model/tool selection is missing. |
| 4 | Human-in-the-loop approvals | `interrupt_on`, Slack/HTTP approval routing (files 01, 03) | **Have** (tool-level). Routing to a channel: **Missing** | Approve/reject via query + update. Route the prompt into the originating channel. |
| 5 | Correlated interrupts | `INTERRUPT_CORRELATION_KEY` (file 02 §3) | **Missing** | Needed when several approvals can be pending. |
| 6 | Long-term memory, layered | agent / assistant / user layers, hot memory loaded once per run (file 01 §4) | **Missing** | Our per-bot workspace is closest to the agent layer. No user or assistant layer. |
| 7 | Memory write policy | per-layer `allow` callbacks, deprecated for root (file 01 §4) | **Missing** | Would be a policy function in the worker. |
| 8 | Sub-agents, blocking and background | `task` and `start_async_task`, async subagent as its own graph (file 01 §6) | **Partial** | We have one blocking `researcher`. No background subagents, no shared sandbox. |
| 9 | Skills | `skills/<name>/SKILL.md` (file 01 §7) | **Missing** | Deep Agents' skills middleware exists in the library (file 02). Not wired. |
| 10 | Sandbox (managed code execution) | LangSmith sandbox, `setup.sh` baked into a snapshot (file 02 §6) | **Missing** | Our `FilesystemBackend` is a directory on the worker, not isolation. Options in §3. |
| 11 | MCP tools | `define_mcp`, agent vs user connections, `jit_auth` (file 02 §7) | **Missing** | Deep Agents supports MCP via LangChain; needs a connection vault. |
| 12 | Per-user credentials (OAuth) | user connections, interrupt for grants (file 02 §7–8) | **Missing** | Needs an identity provider and token store. |
| 13 | Schedules, declared | `define_schedule` cron files reconciled on deploy (file 02 §5) | **Have** (gateway creates Temporal Schedules) | Declared-in-repo reconciliation is missing; we create schedules via API. |
| 14 | Schedules, runtime (agent creates them) | `runtime.schedules.create/list/update/delete`, limits 20 per owner (file 02 §5) | **Missing** | A tool that calls the gateway. |
| 15 | Channels: Slack | Trigger-hosted, modes, multitask strategy (file 03 §2) | **Missing** | We have a generic message endpoint only. |
| 16 | Channels: GitHub / Linear | App webhooks with signed deliveries (file 03 §3–4) | **Missing** | |
| 17 | Channels: custom HTTP adapter | `verify`/`parse`/`post` plus lifecycle hooks (file 03 §5) | **Partial** | Our gateway is effectively a custom HTTP channel without signature verification. |
| 18 | Webhook signing | Standard Webhooks, `whsec_` secrets, 5-min replay window (file 03 §6) | **Missing** | Straightforward; use the `standardwebhooks` library. |
| 19 | Sender→user identity mapping | `resolve_user` returning user, identity, reply, ignore (file 03 §7) | **Missing** | Our `ALLOWED_SENDERS` is a flat allowlist. |
| 20 | Thread model: origin, participants | `runtime.thread.origin`, `participants` (file 02 §2) | **Missing** | Our bot = one thread. Multi-person threads need this. |
| 21 | Posting replies to a channel | `channel.post`, `[quiet]`, fallback error notice (file 02 §4) | **Missing** | Requires channel adapters first. |
| 22 | Declarative deploy | `mda deploy`, `.mda/build`, Hub directory reconcile (file 05) | **Missing** | We have no deploy tool. Docker compose or a Helm chart would be our equivalent. |
| 23 | Control-plane API for agents | `/v1/deepagents/agents` CRUD and health (file 05 §1) | **Partial** | Our gateway creates bots and sends messages; no agent definition store. |
| 24 | Streaming output | stream modes `messages`, `updates`, `values`, v2 events (file 04 §3) | **Missing** | `temporalio-deepagents` `streaming_topic` supports token streaming. Not wired. |
| 25 | Observability | LangSmith tracing; OTEL metrics (files 02, 04) | **Missing** | Temporal's OpenTelemetry plugin and `temporalio.langsmith` plugin compose with ours. |
| 26 | Auth on the API | LangSmith API keys, custom `auth.path` (file 04 §6) | **Partial** | Single shared `X-API-Key`. |
| 27 | Encryption at rest | `encryption.path` AES-JSON (file 04 §4) | **Missing** | |
| 28 | Webhook URL SSRF policy | `webhooks.url` policy (file 04 §4) | **Missing** | Our `fetch_url` checks hosts but not resolved IPs. Add this. |
| 29 | Eval harness | `mda evals` on Harbor (file 01 §Evaluate) | **Missing** | |
| 30 | Multi-tenant workspaces | workspace IDs, per-workspace secrets (files 04, 05) | **Missing** | |
| 31 | Context and memory isolation per tenant | assistant and user memory keys (file 01 §4) | **Missing** | |
| 32 | A2A agent interop | `/a2a/{assistant_id}` (file 04 §2) | **Missing** | Low priority. |
| 33 | MCP server of our own | `/mcp` on the Agent Server (file 04 §2) | **Missing** | Low priority. |

## 2. Licensing decision

- Reuse freely (MIT): `deepagents`, `langgraph`, `langgraph-sdk`, `langgraph-cli`, `managed-deepagents` (the authoring package; its runtime code is MIT, but it targets the managed platform).
- Do not copy: `langgraph-api` and `langgraph-runtime-inmem` (Elastic-2.0). These restrict offering a managed service. Our Temporal-based server avoids the dependency.
- Our design replaces the Agent Server with Temporal (durable execution, schedules, signals, updates). We keep the same *client-facing concepts* (threads, runs, interrupts, channels, schedules) but not the code.

## 3. Sandbox options (row 10)

| Option | Isolation | Cost to build | Notes |
|---|---|---|---|
| Our `FilesystemBackend` on the worker | none | done | Acceptable only for trusted code |
| Docker container per thread, via Temporal activities | container | medium | Matches `TemporalBackend` factory pattern (`temporalio-deepagents` README). Recommended first step. |
| Firecracker or gVisor microVM | strong | high | Only if running untrusted code at scale |
| Third-party sandbox (for example a managed provider) | varies | low | Deep Agents has a `backends/sandbox.py` interface (file 02) |

## 4. Priorities

**P0 (correctness and safety of what exists):**
1. Run the grokbot workflows end to end on a Temporal server (blocked here; file 07 §1).
2. Add Standard Webhooks signing to the gateway (row 18).
3. Resolve IPs before fetch, or block private ranges (row 28).

**P1 (the managed-runtime core):**
4. Declarative agent definition: a repo format (`agent.py` or `agent.json` plus `instructions.md`) and a deploy command that writes a Temporal worker build (rows 2, 3, 22).
5. Layered memory with per-layer policy (rows 6, 7).
6. Channels: Slack and one HTTP channel, with `channel.post` and approval routing (rows 15, 17, 21).
7. Thread origin and participants (row 20), needed by channels.
8. Streaming via `streaming_topic` (row 24).

**P2 (scale and product):**
9. Sandbox with Docker per thread (row 10).
10. MCP with a connection vault and `jit_auth` (rows 11, 12).
11. Skills and background subagents (rows 8, 9).
12. Runtime schedules for the agent (row 14).
13. Multi-tenant workspaces and encryption (rows 27, 30, 31).
14. Evals (row 29), observability (row 25).

## 5. Architecture sketch (mapping to our stack)

```text
 channels (Slack, GitHub, Linear, HTTP)  ──►  gateway (signed webhooks, resolve_user)
                                                 │  start / signal / update / query / schedule
                                                 ▼
                               Temporal: BotWorkflow (one per thread)  ──  ScheduledTurnWorkflow
                                                 │  Deep Agent (durable loop)
                                                 ▼  activities
                    worker: model provider · MCP tools · sandbox (Docker) · memory store · channel post
```

Our current `grokbot/` covers the center. The gaps are the edges: channels, identity, memory layers, sandbox, MCP, and the declarative deploy.

## 6. What still needs deciding (for the user)

1. Do we need a managed multi-tenant SaaS, or a self-hosted runtime for one team? The answer changes row 30 and the sandbox choice.
2. Which channels come first? Slack is the most-referenced in the README; HTTP is the most flexible.
3. Is an agent definition in a repo (managed-style) or in the API (our current style) the source of truth?
4. Is the Elastic-2.0 constraint acceptable for any dependency? (Assumed no.)

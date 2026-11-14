# grokbot: target architecture

Status: **design**, written 2026-11-14. The code in `grokbot/` implements a subset (marked in each page). The project goal document (the Claude artifact the request referred to) could not be opened from this session; this set was written from the research in `docs/research/`. Reconcile it with that goal document when it is available.

## Stack decision

| Layer | Choice | Why |
|---|---|---|
| Durable execution | **Temporal** (self-hosted or Temporal Cloud) | Survives crashes and long waits; timers, signals, updates, schedules, child workflows, retries built in |
| Agent harness | **LangChain Deep Agents** (`deepagents` 0.7.x) | Planning, filesystem, subagents, human-in-the-loop, skills, memory, summarisation, all open source (MIT) |
| Temporal integration | **`temporalio-deepagents`** (0.0.x, pre-release) | Makes model calls, I/O tools and file operations into activities; the agent loop replays deterministically |
| Gateway | FastAPI (ASGI) | Thin HTTP and webhook edge; no state |
| System of record | **PostgreSQL** | Transcripts, memory, approvals, audit, bindings; Temporal's own persistence can share the server |
| Large objects | S3-compatible object store | Files and attachments referenced from workflow history by key |
| Sandboxes | Container runtime behind a provider interface (Docker first); LangSmith Sandboxes as one provider | Isolated code execution, outside the workflow |
| Observability | OpenTelemetry (Temporal interceptor) and the LangSmith tracing plugin | Traces across workflow, activity and model call |
| Identity | OIDC at the gateway; channel signatures (Standard Webhooks) | Authenticates people and external events |

**Not in the stack, and why:** no Redis (nothing needs it; Temporal holds the queues), no Kafka (Temporal is the event log), no LangGraph Agent Server (replaced by Temporal; its server packages are Elastic-2.0, see `docs/research/managed-deep-agents/04`), no separate cron service (Temporal Schedules), no vector database until memory retrieval is needed (start with files and Postgres full-text search).

## Pages

| Page | Content |
|---|---|
| [01-goals-and-scope.md](01-goals-and-scope.md) | What the system is, what it is not, the requirements it must meet |
| [02-system-context.md](02-system-context.md) | External actors, channels and components; the deployment picture |
| [03-domain-model.md](03-domain-model.md) | Tenants, bots, threads, runs, turns, subagents, sandboxes, memory, schedules, bindings, approvals |
| [04-temporal-topology.md](04-temporal-topology.md) | Workflows, activities, task queues, signals, updates, queries, schedules, child workflows |
| [05-deepagents-integration.md](05-deepagents-integration.md) | How the agent loop, tools, subagents, memory and approvals map onto Temporal |
| [06-thread-lifecycle.md](06-thread-lifecycle.md) | Message intake, double-texting policies, stop, approvals, continue-as-new, close |
| [07-sandboxes.md](07-sandboxes.md) | Sandbox lifecycle, provider interface, egress, credentials, failure handling |
| [08-memory-and-state.md](08-memory-and-state.md) | What lives in workflow state, in Postgres and in object storage; memory layers; transcript |
| [09-channels-and-identity.md](09-channels-and-identity.md) | Ingress, signature verification, identity mapping, bindings, outbound posts |
| [10-scheduling-and-automation.md](10-scheduling-and-automation.md) | Temporal Schedules, runtime schedules created by agents, limits, loop guards |
| [11-security.md](11-security.md) | Trust boundaries, secrets, approvals, sandboxes, prompt injection, audit, budgets |
| [12-observability-and-operations.md](12-observability-and-operations.md) | Tracing, metrics, search attributes, dashboards, deployment, rollout and versioning |
| [13-testing-and-quality.md](13-testing-and-quality.md) | Test levels, determinism checks, replay tests, evaluation |
| [14-decisions.md](14-decisions.md) | Architecture decision records (ADR-001 to ADR-013) |
| [15-roadmap-and-gaps.md](15-roadmap-and-gaps.md) | Phases, what the current code has, what is missing, risks, open questions |
| [16-procedures.md](16-procedures.md) | Procedures as the core unit: versioned step graphs, triggers, per-step approval policy, conditions, bounded loops, MCP-bound tools, enforcement in the workflow |

## Labels used in the pages

- **[implemented]**: present in `grokbot/` and tested offline.
- **[designed]**: decided here, not yet in code.
- **[verify]**: depends on a Temporal or deepagents behaviour not yet tested against a running server.

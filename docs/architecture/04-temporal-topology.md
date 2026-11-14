# 04. Temporal topology

## Workflows

| Workflow | Id | One per | Lifetime | Purpose | Status |
|---|---|---|---|---|---|
| `ThreadWorkflow` | `thread:{tenant}:{thread}` (design) | conversation | weeks; continues-as-new | owns the inbox, turns, approvals, budget counters, stop state, sandbox reference | **[implemented]** as `BotWorkflow`, id `bot-{name}-{hex}` in code (one bot = one thread for now; the id scheme changes when channels bind threads, see `09`) |
| `SubagentWorkflow` | `{thread}:task:{n}` | delegated background task | minutes to hours | runs one async subagent with its own history | **[designed]** |
| `ScheduleTurnWorkflow` | Temporal Schedule action id | schedule firing | seconds | delivers a scheduled prompt to a thread | **[implemented]** |
| `MaintenanceWorkflow` | per tenant | periodic | forever | sandbox reaper, memory curation, budget resets, audit export | **[designed]** |
| `ProcedureWorkflow` | `run:{tenant}:{procedure}:{business_key}` for correlated triggers, else `run:{tenant}:{procedure}:{run_id}` (rule in `16`) | procedure run | minutes to weeks; continues-as-new | interprets one pinned procedure version: walks steps, waits on approvals and events, enforces loop bounds and output schemas (see `16`) | **[designed]** |
| `AgentStepWorkflow` | `{run}:step:{step_id}:{attempt}` | agent step attempt | minutes | runs one deepagents agent with a step's tool grant and output schema, returns validated output | **[designed]** |

Deterministic code only in workflows: no clock reads (use `workflow.now()`), no network, no randomness outside `workflow.uuid4()`-style helpers, no reads of environment or files. Model and tool calls are activities.

## Thread workflow interface

| Kind | Name | Input / output | Notes |
|---|---|---|---|
| Update | `submit_turn` | `{text, sender, idempotency_key, policy}` → `{run_id, status}` | Validator checks size, status, budget and idempotency key before accepting. Returns when the turn is accepted, not when it finishes. **[designed]** (current code uses a signal `enqueue_message`) |
| Update | `decide_approval` | `{approval_id, decision}` → `{decision}` | Validator rejects an unknown decision value or no pending approval. **[implemented]** in `BotWorkflow` with `decision` only (no `approval_id` yet). The first-decision-wins rule is **[designed]** with approval ids |
| Signal | `stop` | `{run_id?}` | Cancels the in-flight turn (see `06`) |
| Signal | `close` | — | Rejects pending approvals, finishes the current turn, exits |
| Query | `status` | `{state, current_run, budget_used, budget_limit}` | Read-only |
| Query | `pending_approval` | the pending action, with arguments hash and size-bounded preview | **[implemented]** |
| Query | `transcript_page` | — | Returns a pointer to Postgres; **not** the transcript itself. **[designed]**. The current code has a query named `transcript` that returns a bounded list kept in the workflow **[implemented, to be replaced]** |

Why an update for submission: callers need an acknowledgement that the message is durably accepted, and a validator can reject it without writing history.

## Activities and task queues

| Queue | Runs | Typical activity | Concurrency control |
|---|---|---|---|
| `thread` | workflows only | — | workflow task limits |
| `llm` | model calls (`deepagents.invoke_model`, streaming variant) | one provider call | max concurrent activities per worker; provider rate limits; gateway budget |
| `io` | tools that touch the outside world (`fetch_url`, `http_request`, `deliver_channel_message`, MCP calls) | one external request | per-host concurrency; egress allowlist |
| `sandbox` | sandbox create, attach, exec, read/write, snapshot, destroy | one sandbox operation | per-host capacity; heartbeat on long exec |
| `persist` | Postgres writes (transcript, memory, audit, usage) | one write batch | connection pool |
| `maintenance` | sweeps and curation | — | single active worker |

A worker process joins one or more queues. Capacity is added per queue, so model calls cannot starve sandbox work. **[designed]**; the current code runs one worker on one queue.

Activity timeouts and retries (the policy each type uses):

| Activity | Start-to-close | Retry | Non-retryable errors |
|---|---|---|---|
| model call | 5 min (per-agent override via `activity_options`) | exponential, up to a small count, with jitter | auth failure, invalid request, content refused, budget exceeded |
| read-only tool (`fetch_url`) | 30 s | 3 attempts | policy violation (not on allowlist), HTTP 4xx |
| side-effect tool (`deliver_channel_message`) | 30 s | at most once unless the target honours an idempotency key | any error after the request left the worker |
| sandbox create | 2 min | 3 attempts | quota exceeded |
| sandbox exec | per command timeout + margin, heartbeats every 10 s | none (the agent decides to retry) | — |
| Postgres write | 10 s | 5 attempts | constraint violation |

## Signals, updates, queries: rules

- Handlers never block; they change state and return.
- Update validators reject without side effects. Updates that pass validation are recorded in history.
- Queries must not change state and must not depend on in-progress activities.

## Timers

- Approval timeout: `workflow.wait_condition(predicate, timeout=…)` (default 24 h, configurable per bot). The `timeout` parameter exists in 1.36.0 (checked in the installed SDK); its behaviour on expiry **[verify]** on a server. On timeout the approval is rejected and the turn ends with a visible notice.
- Budget windows: a timer per window reset, or computed from `workflow.now()` at the next turn.
- Schedules do not use timers in the workflow; they use Temporal Schedules.

## Child workflows

Subagents started with `start_child_workflow`. Parent close policy: `REQUEST_CANCEL` for subagents of a stopped thread (their work stops, their history stays), `ABANDON` for detached tasks the user asked to continue. Child results are read by the parent when it waits, and queried otherwise. **[designed]**

## Schedules

Temporal Schedules created by the gateway (`/v1/bots/{id}/schedules`). Overlap policy `SKIP` by default, so a slow run never stacks. Each fire starts `ScheduleTurnWorkflow`, which signals the thread (creating it if absent). Schedule configuration is versioned with the bot. **[implemented]** for creation; overlap and misfire settings **[designed]**.

## Starting threads from channels

Signal-with-start: one call starts the thread if it does not exist and delivers the message. The 1.36.0 client exposes it as the `start_signal` argument of `start_workflow` (checked in the installed SDK). Its behaviour with a running workflow **[verify]** on a server. The workflow id is derived from the binding, so retried deliveries reach the same thread.

## Namespaces and environments

One Temporal namespace per environment (dev, staging, prod). Workers and clients carry the namespace. Tenants share a namespace in v1 and are separated by task queue and by workflow id prefix. Separate namespaces per tenant are the upgrade path. **[designed]**

## Limits to design around

- Workflow history size: keep inputs and per-step results small; use continue-as-new (see `06`).
- Payload size: the SDK warns at 512 KiB by default (`payloads_warn_size` in `temporalio/service.py`); keep payloads far smaller and store large content in the object store with a key (claim-check).
- Number of pending signals and updates per workflow: throttle at the gateway.

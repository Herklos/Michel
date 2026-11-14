# 03. Domain model

Each entity lists its identity, its owner, where it lives, and its lifecycle. "Live in" names the single source of truth. Copies in workflow state are caches of that truth.

## Entities

| Entity | Identity | Owner | Lives in | Lifecycle |
|---|---|---|---|---|
| **Tenant** | `tenant_id` | operator | Postgres | created by operator |
| **User** | `user_id` (internal), linked external identities | tenant | Postgres | invited, linked, suspended |
| **Bot** | `bot_id` | tenant | Postgres (versioned definition) | created, edited (new version), archived |
| **Bot version** | `bot_id` + `version` | bot | Postgres | immutable once used by a thread |
| **Thread** | `thread_id` = Temporal workflow id | bot + owner | Postgres index; history in Temporal | open, suspended, stopped, closed |
| **Turn** (run) | `run_id` | thread | Postgres row + workflow history | queued, running, waiting_approval, done, failed, cancelled |
| **Message** | `(thread_id, seq)` | thread | Postgres (transcript) | append-only |
| **Subagent task** | `task_id` = child workflow id | thread | child workflow history + Postgres row | running, done, failed, cancelled |
| **Sandbox** | `sandbox_id` (provider id) | thread | Postgres row + provider | provisioned, attached, idle, removed |
| **Memory item** | `(scope, key)` + version | tenant, user or thread | Postgres | written, superseded, deleted |
| **Skill** | name + version | bot | object store + Postgres row | created by agent, curated, archived |
| **Schedule** | Temporal schedule id | bot, owner | Temporal schedule + Postgres row | active, paused, deleted |
| **Channel binding** | `(provider, external_conversation_id)` | tenant | Postgres | created on first message, unbound on request |
| **Procedure** | `procedure_id` | tenant | Postgres | drafted, published, archived |
| **Procedure version** | `procedure_id` + `version` | procedure | Postgres (validated JSON) | immutable once published; pinned by runs |
| **Procedure trigger** | `trigger_id` | procedure | Postgres row; Temporal Schedule for time triggers | enabled, paused, deleted |
| **Procedure run** | `run_id`; workflow id from the business key when correlated | procedure version | `ProcedureWorkflow` history + Postgres index | running, waiting_approval, completed, rejected, failed, budget_exceeded |
| **Step run** | `(run_id, step_id, attempt)` | procedure run | run history + Postgres row | pending, running, waiting_approval, succeeded, failed, skipped, timed_out |
| **Connection** | `connection_id` | tenant | Postgres (secret reference) | configured, tools pinned per version, revoked |
| **Approval** | `approval_id` | turn or step run | Postgres row + workflow state | pending, approved, rejected, expired |
| **Tool grant** | `(user_id, connection)` | user | Postgres (secret reference) | granted, revoked |
| **Budget** | `(scope, window)` | tenant, bot, thread | Postgres (ledger) + workflow counters | per window |
| **Audit record** | `event_id` | any | Postgres, append-only | never updated |

## Relationships

```text
Tenant 1──* User
Tenant 1──* Bot 1──* BotVersion
Bot 1──* Thread *──1 BotVersion          (a thread pins the version it started with)
Thread 1──* Message
Thread 1──* Turn 1──* Approval
Thread 1──* SubagentTask
Thread 1──0..1 Sandbox
Thread *──* ChannelBinding               (a conversation may map to one thread at a time)
Bot 1──* Schedule  ──starts──▶ Thread
Procedure 1──* ProcedureVersion 1──* ProcedureRun ──pins──▶ ProcedureVersion
ProcedureRun 1──* StepRun 1──0..1 Approval
ProcedureVersion 1──* ProcedureTrigger ──starts──▶ ProcedureRun
ProcedureVersion *──* Connection         (each step's tools are granted from these)
ProcedureRun 0..1──* Thread              (a person may talk to the agent of the running step)
User 1──* ToolGrant
Memory (tenant | user | thread) is scoped; Thread reads tenant and user memory per turn
```

## Invariants

- A thread has **one** workflow. Its id is derived deterministically from the binding (`thread:{tenant}:{channel}:{conversation}` or a generated id for web threads) so that retries of the same inbound event reach the same workflow.
- A thread pins a bot **version**. Editing a bot creates a new version; only new threads use it unless the owner migrates a thread explicitly.
- An approval belongs to exactly one turn and is decided once. Re-deciding returns the first decision.
- A sandbox belongs to exactly one thread. It is never shared between threads.
- Memory writes go to Postgres through an activity; the workflow keeps no memory content, only the version it read.
- Every entity that a person can change has `created_by`, `updated_by` and timestamps. Records that drive side effects also have an idempotency key.

## Current code **[implemented]**

`michel/models.py` defines `BotConfig`, `BotState`, `InboundMessage`, `ScheduledPrompt`. The bot is one workflow (one bot = one thread for now). Tenants, versions, sandboxes, memory layers, bindings and budgets are **[designed]**.

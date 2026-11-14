# Code structure of Open SWE (now "Robin") and T3 Code

Read 2026-11-14 from shallow clones (`--depth 1`):
- `langchain-ai/open-swe` at `42db6cc` (`/home/user/langchain-ai/open-swe`). The README now calls the product **Robin**. The repo is under active development and is not accepting outside contributions.
- `pingdotgg/t3code` at `75c544a9` (`/home/user/pingdotgg/t3code`).

Every claim names its file. Paths are relative to each repo root. Where a claim is an inference rather than a quote, it says so.

## 1. What each product is

| | Open SWE / Robin (`langchain-ai/open-swe`) | T3 Code (`pingdotgg/t3code`) |
|---|---|---|
| Purpose | Engineering work as a service: investigate, implement in a sandbox, open a PR, review PRs, monitor CI (`README.md`) | Control plane for coding agents that already run on the user's machine: Claude Code, Codex, Cursor, OpenCode, and others (`README.md`) |
| Who runs the loop | A LangChain Managed Deep Agents runtime (`mda/`, `vendor/managed-deepagents-sdk`). The Open SWE backend (`openswe/`) plans the run (`openswe/graphs/agent.py` docstring) | The external agent process (CLI or ACP). T3 starts, drives and observes it. T3 has no agent loop of its own (`docs/internals/providers.md`) |
| Runtime language | Python backend and runtime, plus a TypeScript dashboard (`ui/`) | TypeScript on Effect (`effect/Schema`, `effect/Layer` in `apps/server/src`) |
| Clients | Dashboard (`ui/`), GitHub, Slack, Linear, a desktop app and a mobile app (`desktop/`, `mobile/`) | Web, desktop (Electron) and mobile (`apps/web`, `apps/desktop`, `apps/mobile`) |
| Scale of the repo | About 2,300 tracked files; 761 under `ui/src`; `openswe/` has 53 subdirectories; 162 database migrations | About 2,000 files in `apps/server`, `apps/web`, `apps/mobile` and `apps/desktop` combined; `packages/` has 33 subdirectories; a driver for each named agent in the README (eleven named agents, plus any ACP agent) |

## 2. Open SWE / Robin: structure

### 2.1 Two halves with a contract between them

The central design choice is a split between a **backend that owns credentials and state** and a **runtime that runs the loop**.

- The backend is `openswe/`. It holds the GitHub App, the sandbox credentials and the model keys. For each run it builds a **catalog**: the operations the run may call, its subagents, its models and their routes, its sandbox, and the rules of its middleware (`packages/runtime-api/src/runtime_api/catalog.py`, module docstring).
- The runtime is `mda/rt/`. It builds the agent from the catalog and calls the backend only for what needs data or credentials: one named call each (`mda/rt/loop.py` docstring, which cites `runtime_api.loop`).
- The catalog is typed. `RunModels`, `ToolSpec`, `ModelSpec` and `LoopRules` are Pydantic models shared by both halves through the `packages/runtime-api` package.
- The graph is built once per process from inputs that are the same for every run on those models (`GraphInputs`, `mda/agent.py` docstring). The per-run state is read from the run in progress through `rt.backend.current_run`.

The same agent also runs as the async `general-purpose` subagent. A worker is a full Open SWE thread with its own run token (`mda/agent.py` docstring).

Inference: the catalog is what makes the runtime replaceable. The runtime only knows what the catalog tells it. Most policy, including what a tool may do, lives on the backend side.

### 2.2 Entrypoints and deployment

- `langgraph.json` declares three graphs (`agent`, `reviewer`, `review-scout`), an HTTP app (`openswe.webapp:app`), an auth hook (`openswe.api.agent_server_auth:auth`), and a checkpointer TTL: `strategy: delete`, sweep every 60 minutes, default TTL 43,200 s (12 h).
- `Dockerfile` builds the dashboard into the image and stamps build information (`langgraph.json` `dockerfile_lines`).

### 2.3 Storage

- **PostgreSQL only**, through SQLAlchemy async with `asyncpg` (`openswe/database/postgres.py`). Everything lives in one schema, `open_swe`. Migrations are Alembic, guarded by a Postgres advisory lock (`MIGRATION_LOCK`).
- The connection pool is sized from environment variables, and every query is timed through an event listener (`postgres.py`, `engine()`).
- Tables are declared per domain module (`__tablename__` in `openswe/*/`). Examples: `pull_request_thread`, `pull_request_finding`, `merge_queue_request`, `plugin`, `workspace` rows, `human_review_request`, `audit_logs`, `api_key`, `mcp_connection`, `settings_record`, `agent_instructions`. Roughly 60 or more tables in total (inference from the grep count).
- **Audit log** (`docs/reference/audit-logs.md`): metadata only, in `open_swe.audit_logs`. The envelope follows LangSmith's audit schema. Writes are insert-only, duplicate event IDs are ignored, and there are **no cascading foreign keys**, so deleting an account, key or workspace does not erase its history.
- **Task graph** (`openswe/tasks/store.py`): a `Task` is the work a person hands over. It has a coordinating thread and zero or more worker threads, with `TaskRole` `coordinator` or `worker`. `WorkerAlreadyLaunchedError` makes a launch idempotent.
- Thread state is the LangGraph checkpointer. The `checkpointer.ttl` in `langgraph.json` bounds it.

### 2.4 Configuration

- **One declared registry.** `openswe/config.py` says it declares "every environment variable Open SWE reads, declared once". Each variable is an `EnvVar` with a name, description, default, aliases, a secret flag, and a deprecation note. The rest of the code reads them as `ENV.<NAME>.get()`. Nothing else reads `os.environ` for configuration.
- **Three tiers of settings** (`docs/reference/workspaces.md`, "Settings tiers"):
  1. **Instance**: the settings record that existed before workspaces, kept under its original key so an upgrade needs no migration.
  2. **Workspace**: a sparse record of overrides per workspace slug. A field that is unset inherits the instance value. `PUT` replaces the overrides, and `null` means "inherit".
  3. **User**: profile preferences. Model, reasoning effort and routing defaults come from the workspace tier, not from personal profiles.
- **Instance-level configuration stays out of the workspace**: the GitHub App, the Slack app, model provider keys, the sandbox provider, the admin list and the sign-in allowlist (`docs/reference/workspaces.md`, "The workspace record").
- **Repository access is not the same as preference.** A workspace lists "preferred" repositories, which decide where events run and what the sandbox image preloads. "Preferring a repository is not what grants access to it." (`docs/reference/workspaces.md`, Summary.)

### 2.5 Harness (the agent loop)

- Dispatch is one function, `openswe/dispatch.py`, for every run trigger. It sets `multitask_strategy="interrupt"` by default. A follow-up halts the active run, progress is kept through checkpoints, and the agent resumes with the full history plus the new message. Background follow-ups such as `/baby-sit` can ask for `enqueue` instead.
- It sets `durability="async"`: each step is checkpointed while the next step runs. The docstring says that synchronous checkpoints cost about 0.3 s per model or tool step in production.
- It sets a **completion webhook**, so every run ends with a signal "even if the agent died".
- It sets `stream_resumable=False`: nothing replays these runs' streams, because the dashboard reads a thread from its transcript.
- The middleware stack order in `openswe/server.py` is "significant" (`openswe/middleware/AGENTS.md`). The middleware modules are split by responsibility: `prepare_run`, `model_selection`, `require_user_reply`, `require_cli_result`, `pr_creation_guard`, `workflow_push_guard`, `sandbox_circuit_breaker`, `stale_workspace`, `task_coordination`, `record_run_usage`, and others (`openswe/middleware/`).
- The loop itself is `mda/rt/loop.py`. Before each model call it can end the run where a rule says to, add task context, pick the route and the model, and assemble the system prompt and the tool list. After an answer with no tool call, it asks again for the reply or CLI result the run owes (`mda/rt/loop.py` docstring).
- Models are routed by name. `RunModels.routes` maps a route name to a `ModelSpec`. A text-only model is sent to a vision model when the conversation holds an image (`runtime_api/catalog.py`).

### 2.6 Sandboxes

- `openswe/sandboxes/AGENTS.md`: the managed runtime creates and replaces every thread's sandbox. The backend only connects to one by its id and **must never create one**. An unreachable sandbox raises rather than being abandoned, because a fresh one would lose the thread's work. Only the read-only reviewer may abandon one.
- The one provider implementation is LangSmith (`openswe/sandboxes/providers/langsmith.py`). The README says other providers are configurable. The earlier research note found no second implementation (`docs/research/open-swe/06-models-sandboxes-and-safety.md`, "Providers").

### 2.7 Memory

- The runtime's memory is `mda/memory.py`: `define_memory(user=MemoryLayer())`. Only a **user** layer is declared. The docstring says "caller-scoped memory with MDA's default private-conversation policy".
- There is no bot-wide or thread-wide memory layer in this code. Shared knowledge goes elsewhere: per-workspace instructions (`agent_instructions` table, `openswe/dashboard/agent_instructions.py`), a repository's `AGENTS.md` (`openswe/utils/agents_md.py`), and skills (below).
- **Skills** are read-only files. `mda/rt/skills.py` lists them in each call's system prompt through deepagents' skills middleware. "A thread's checkpoint keeps the skills it listed, so each run lists them again: a public thread never keeps the skills of a person a previous run acted for." Skills come from `openswe/skill_store/` (stored per workspace) and from `openswe/bundled_skills/` (`baby-sit`, `html-artifacts`, `linear-tickets`, `web-apps`, `workspaces`).
- **Repository-owned rules.** `docs/reference/auto-approve-rules.md`: rules are Markdown files in `.open-swe/auto-approve-rules/` on the **default branch**. "A pull request cannot rewrite the rules it is judged by." An invalid rule disables all auto-approval rather than applying a partial set.

### 2.8 Approvals, safety and review

- Human review is a separate domain: `openswe/human_review/`, `openswe/expedited_review/`, `openswe/merge_queue/`. Review state is in Postgres tables (`human_review_request`, `merge_queue_decision`, `merge_queue_evidence`).
- `docs/reference/review-approval-threat-model.md` exists and is the place to read the threat model.
- The README is explicit about the limit: "Workflow-file approval prompts guard detected Git pushes, not every possible shell or API write." Reviewers are told not to commit or push, and PR chat excludes mutation tools.

### 2.9 Testing

- `tests/` has about 41 directories (`e2e`, `agent`, `slack`, `github`, `sandbox`, `reviewer`, `threads`, `dashboard`, and others). `evals/` holds reviewer evaluations.
- `docs/tla/SteerRace.tla` with `check.sh`: a TLA+ model of the race between steering a run and a new message. This is the only formal model in the repo, and it is directly relevant to our double-texting design (`docs/architecture/06`).

## 3. T3 Code: structure

### 3.1 The boundary

`docs/internals/overview.md` states the rule: "T3 Code keeps execution in the environment that owns the workspace. Web, desktop, and mobile clients control it over authenticated RPC. A remote client must never substitute its own filesystem, provider credentials, or machine state for the environment's."

- An **environment** is one running server with the machine, credentials, workspace access and state it owns (`docs/internals/glossary.md`).
- `packages/contracts` holds the RPC contract (`rpc.ts` is the boundary). Subscriptions send the state a client needs, so a client looking at one thread does not receive every thread's history.
- `packages/client-runtime` holds the connection logic shared by web, desktop and mobile: one connection owner per environment, one retry owner, one registry (`docs/internals/connection-runtime.md`).

### 3.2 Storage: event log and projections in SQLite

- The database is SQLite, opened through `apps/server/src/persistence/Sqlite.ts`. Migrations are in `persistence/Migrations/`. Runtime state lives in a `userdata` directory under the T3 home directory (`apps/server/src/config.ts`, line 149).
- **Orchestration v2** (`apps/server/src/orchestration-v2/`, documented in `docs/orchestration-v2/core-graph-and-data-model.md`) is event-sourced. Its entities are `Project`, `AppThread`, `Run`, `ExecutionNode` (a tree of work inside a run), `ProviderThread`, `ProviderSession`, `ContextTransfer`, `ContextHandoff`, `ProviderTurn`, `RuntimeRequest`, `Checkpoint`.
- Every committed event has a store-assigned, monotonically increasing `sequence`. A client reads a snapshot at sequence N and then streams events with sequence greater than N (`core-graph-and-data-model.md`, Overview).
- **Commit path** (`docs/internals/overview.md`, "Durable intent and side effects"):
  - `Orchestrator.ts` serializes commands and decides events. It performs **no provider or filesystem work**.
  - `EventSink.ts` commits, in one database transaction: the events, the persisted projections, the accepted command receipt, and the outbox effects.
  - Subscribers receive events only after that commit.
  - `EffectWorker.ts` runs the outbox effects after commit and feeds results back as commands.
  - A command acknowledgement therefore means "the intent committed", not "the provider finished".
- **Retention.** The event log keeps about a day of history for reconnect replay and command-id retries. `ProjectionMaintenance.ts` deletes older events that the projections cover. A client whose cursor falls below the pruned-through sequence resumes from a snapshot. Projections cannot be rebuilt from the log after pruning, and command receipts are kept longer so retries stay idempotent.

### 3.3 Providers: adapter boundary and capability flags

- `packages/provider-core/src/server/ProviderAdapter.ts` defines `ProviderAdapterV2`. Orchestration works with normalized commands and events. "Adding a provider should not require branches throughout the domain or clients" (`docs/internals/overview.md`).
- A **driver kind** names an integration. A **provider instance** names one configuration and account lifecycle. Work is routed by instance, "so two accounts using the same driver do not share mutable session or catalog state" (`docs/internals/providers.md`).
- **Capability flags** (`OrchestrationV2ProviderCapabilities`) must describe what the provider really does. A capability that is on but fails at runtime is a bug. Fork, rollback, steering and subagent support can each be turned off, and orchestration falls back (for example to a portable context handoff) (`docs/internals/adding-a-provider.md`).
- **Permission modes** are offered only where the provider enforces them natively. "Do not imitate a missing mode by answering approvals in T3: T3's check is weaker than the agent's own enforcement." An unoffered stored mode runs as Supervised (`RuntimePolicy.ts`, cited in `adding-a-provider.md`).
- **Protocol traps** are documented per provider (`docs/internals/providers.md`, "Protocol traps"). For example, Codex asks questions as notifications answered by a new user message, and the adapter stores them as pending runtime requests that survive a server restart.
- **Checkpoints** use hidden Git refs, so the user's branch does not get extra commits (`docs/internals/overview.md`, "Turn completion and checkpoints"). A revert must coordinate the workspace with the provider conversation, and an adapter that cannot roll back its conversation must reject the revert before it touches files.

### 3.4 Auth and trust

- The environment issues its own **scoped sessions** (`docs/internals/environment-auth.md`). A pairing grant can be **narrowed** by the bootstrap exchange but **never widened**.
- The default pairing grant includes terminal and orchestration operate scopes, because "either can mint a session with every scope", so withholding them "would not be a boundary".
- A **relay token is never an environment login.** Cloud identity (T3 Connect) is a separate trust boundary.
- **Guest links** are HMACs of the thread and share id under a server key, so nothing secret is stored. Replacing, closing or archiving the share revokes every token. Guest tokens never enter the session store, so no RPC, WebSocket or MCP path can accept one.
- Browser cookies, bearer tokens and DPoP tokens adapt "the same scoped session model". An invalid DPoP proof must fail, not fall back to bearer.

### 3.5 Identity and routing

- An environment **keeps its ID across restarts and endpoint changes** (`docs/internals/remote.md`). The ID file is initialized atomically, and a recovery file keeps concurrent initializers on the same winner.
- A saved environment holds an ordered list of **routes**. The driver tries them in order. "Only an incompatible server stops the walk, because it is the same server on every route." Advertised endpoints are only hints. A loopback address "refers to a different machine when another device opens it".
- A repository identity correlates clones across environments but **never routes work between environments**.

### 3.6 Config

- `.env.example` holds only **public identifiers** for T3 Connect builds, and says "Do not add server-side secrets to this file."
- `t3.json` declares per-project scripts (`Dev`, `Setup Worktree`), so the project's own dev workflow is data.
- Per-user keybindings are a file (`apps/server/src/keybindings.ts`). Settings are split: "client preferences stay in the current client; environment defaults and project overrides stay on their owning server" (`docs/internals/overview.md`, "Settings ownership").

### 3.7 Memory

- T3 has **no memory layer of its own**. Memory is the provider's: Claude's and Codex's own sessions and context files. Cross-provider continuity uses **portable context handoffs**, generated summaries stored as `ContextHandoff` records (`core-graph-and-data-model.md`, "ContextHandoff").
- Text generation for titles and commit messages uses a separate model role ("text generator"), which agent surfaces never list (`docs/internals/glossary.md`).

### 3.8 Testing

- `apps/server/src/**/*.test.ts` and `*.integration.test.ts` sit beside the code. `docs/orchestration-v2/testing-strategy.md` describes the approach.
- Tests use "drainable workers" that wait until both the queue and its current item have finished. "An empty queue alone does not prove the worker is idle" (`docs/internals/overview.md`, "Waiting for asynchronous work").

## 4. Comparison with michel's design

| Topic | Open SWE / Robin | T3 Code | What michel does today (`docs/architecture`) | Implication for michel |
|---|---|---|---|---|
| Control plane vs runtime split | Backend builds a typed catalog per run; runtime only calls back for data or credentials (`runtime_api`) | Server owns all state; clients and agents are adapters | Workflow runs the agent; activities hold I/O (`04`, `05`) | Adopt a **typed run catalog** written when a procedure run starts. A procedure version already pins what a run may do (`16`); make the catalog its schema. |
| Command vs effect | Dispatch has a completion webhook so every run ends | Orchestrator decides events with no I/O; `EventSink` commits events, projections, receipt and outbox in one transaction; `EffectWorker` runs effects after commit (`overview.md`) | Update validator, then workflow activities (`04`, `06`) | Strong candidate for **ADR-014**: commands decided without I/O, effects committed as outbox intents. Maps onto Temporal as "decide in workflow, activity performs I/O, result returns as a signal". |
| Retention and replay | Checkpointer TTL 12 h with sweep; stream not resumable | About one day of events; projections pruned; snapshot resume | Continue-as-new and a Postgres transcript (`06`, `08`) | Write a retention rule per store, as both do: Temporal history bounded by continue-as-new, transcript kept in Postgres, receipts kept longer than events. |
| Idempotent commands | Dispatch keys; "duplicate event IDs are ignored" in audit | Command receipts stored with the event, retries return the receipt | Idempotency key on `submit_turn` (`04`) | Keep receipts as their own table, retained longer than events. |
| Audit | Insert-only metadata table; no cascading FKs; LangSmith-shaped envelope | Event log is the audit trail for state changes | Append-only `audit_log`, "never contains message bodies" (`11`) | Adopt **no cascading foreign keys** from `audit_log`, and the rule "audit records never contain message bodies". Use an envelope shaped like the LangSmith schema, as Robin does. |
| Tiered settings | Instance, workspace (sparse overrides with `null` = inherit), user | Client prefs stay on client; environment defaults and project overrides on the server | One bot version, pinned per thread (`03`) | Add a sparse **override tier** per bot, so a bot inherits tenant defaults until changed. Keep the pin: a thread still runs the version it started with. |
| Config declaration | One `EnvVar` registry; no other code reads `os.environ` | Environment file holds public identifiers only | `michel/config.py` with `from_env`; secrets read on the worker (`michel/config.py`) | Keep one registry, as in Robin. Make it reject unknown names at startup. |
| Policy that a repository or agent could edit | Auto-approve rules read from the default branch, so a PR cannot change the rules that judge it | Scopes can be narrowed, never widened | Tool grants pinned per version; agents cannot change policy (`16`) | State the rule in `11`: **policy is read from a pinned or default source, never from the content it judges.** |
| Memory | User-only memory layer, per-workspace instructions, skills per workspace; a run lists skills again each time so a thread keeps nothing a person did not get | None; uses provider sessions and handoff summaries | Three layers: bot, user, thread (`08`) | Robin's "list skills again every run" is a useful rule for our skills: a thread must not keep skills of a person a previous run acted for. Robin's single user layer is a smaller start than our three layers. |
| Routing and identity | Workspace routing by thread, then tag, then channel, then repository preference, then user default, then `default` (`workspaces.md`) | Environment ID persists across endpoint changes; routes tried in order | Channel binding to one thread (`09`) | Write the **routing order** in `09` explicitly, as Robin does. |
| Connection retry | Not in scope of the research | One retry owner; jittered exponential backoff capped at 5 minutes; reset only after a stable connection | Not designed | Add to `09`/`12`: one retry owner per gateway client, jittered, capped. |
| Provider or driver boundary | Model routes chosen by name | Driver kind vs provider instance; per-instance isolation | One model string per bot (`BOT_MODEL`) | Separate "driver" (kind of model provider) from "instance" (account), so two accounts never share mutable state. |
| Formal model | `docs/tla/SteerRace.tla` for the steer race | Not found | Not designed | Candidate spike: model the double-texting race in TLA+ or as a property test (`13`). |
| Documentation habit | `AGENTS.md` per directory with rules, e.g. `openswe/sandboxes/AGENTS.md` | `docs/internals/` with "constraints" pages, glossary | Architecture pages with labels, no per-directory rules | Adopt per-directory `AGENTS.md`-style rule files for `michel/` (see `CLAUDE.md`). |

## 5. Things that are not clear from the code

- Whether Robin's runtime is open source. `vendor/managed-deepagents-sdk` is vendored. Its license and status were already noted in `docs/research/managed-deep-agents/04` (Elastic-2.0 for the server packages).
- The formal threat model in `docs/reference/review-approval-threat-model.md` was not read in full in this pass.
- T3 Connect (relay) internals in `infra/relay` were not read.
- How the T3 event log behaves under load was not measured.

## 6. Sources read

Open SWE: `README.md`, `langgraph.json`, `AGENTS.md` (headings only), `openswe/config.py` (header), `openswe/database/postgres.py`, `openswe/database/` listing, `openswe/dispatch.py` (header), `openswe/graphs/agent.py`, `openswe/middleware/AGENTS.md`, `openswe/sandboxes/AGENTS.md`, `openswe/tasks/store.py` (header), `openswe/workspaces` (via docs), `mda/agent.py` (header), `mda/memory.py`, `mda/rt/loop.py` (header), `mda/rt/skills.py` (header), `packages/runtime-api/src/runtime_api/catalog.py` (header and models), `docs/reference/workspaces.md`, `docs/reference/audit-logs.md`, `docs/reference/auto-approve-rules.md`, `docs/CUSTOMIZATION.md` (headings).

T3 Code: `README.md`, `docs/internals/overview.md`, `docs/internals/providers.md`, `docs/internals/environment-auth.md`, `docs/internals/remote.md`, `docs/internals/connection-runtime.md`, `docs/internals/glossary.md`, `docs/internals/adding-a-provider.md`, `docs/orchestration-v2/core-graph-and-data-model.md` (overview and entity summary), `packages/provider-core/src/server/ProviderAdapter.ts` (header), `apps/server/src/persistence/Sqlite.ts` (header), `apps/server/src/config.ts` (line 149), `.env.example`, `t3.json`.

Not read in full: most `apps/server` implementation files, the `ui/` and `apps/web` trees, and the test suites.

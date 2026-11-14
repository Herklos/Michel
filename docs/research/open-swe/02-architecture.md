# 02. Architecture: the backend, the managed runtime, and the contract between them

Sources: `AGENTS.md` ("Constant gardening" and "Conventions"), `README.md` ("How it works"), `langgraph.json`, `packages/runtime-api/src/runtime_api/*.py`, `openswe/agent_api/run_kinds.py`, `openswe/dispatch.py`, `openswe/completion.py`, `mda/agent.py` module docstring, `docs/CUSTOMIZATION.md`. Read 2026-11-14.

## 1. Two processes, one run

Every `agent`, `reviewer` and `review-scout` thread runs on **Managed Deep Agents** as one graph, `open-swe`, built from `mda/`. The backend refuses to start without `MDA_RUNTIME_URL` and `REMOTE_RUNTIME_TOKEN_SECRET` (`AGENTS.md`).

| Side | Holds | Does |
|---|---|---|
| **MDA runtime** (`mda/`, runs on the Agent Server) | the model loop, checkpoints, thread sandbox, every tool call, all middleware and hooks | runs the agent |
| **Backend** (`openswe/`, FastAPI, Postgres) | every credential (GitHub App, Slack, Linear, LangSmith keys), thread settings, workspace defaults, the sender's access | plans each run and answers its calls |

MDA "owns the run"; the backend is "a set of stateless APIs MDA calls" (`AGENTS.md`).

## 2. The contract: typed endpoints under `/agent-api/{endpoint}`

`packages/runtime-api` is imported by **both** sides. It defines typed endpoints (class `Endpoint`). The names found in the package:

`worker_launched`, `adopt`, `prepare`, `inbox`, `model_result`, `tool_started`, `tool_result`, `sandbox_replaced`, `sandbox_unreachable`, `browser`, `reply_on_behalf`, `run_started`, `run_ended`, `model_failed`, `step_limit_reached`, `settle_review_check`, `finish_scout_plan`, `operation`, `check_shell`, `slack_moved`

Other modules in the same package (names only, from the file list): `model_errors`, `sandbox_setup`, `loop`, `files`, `operations`, `gateway_auth`, `slack`, `sandbox_proxy`, `provenance`, `linear`, `reports`, `catalog`, `route_questions`, `models`, `skills`, `tool_search`, `github`, `mcp_secrets`, `classifier`, `connections`, `workers`, `endpoint`.

Rules stated in `AGENTS.md`:
- Each call is answered "from the run token the router signs and the request alone, on whichever replica it lands". No replica-local state.
- Work needing backend credentials or data is a **named endpoint** for that work (for example `model_choice`, `refresh_github_proxy`), never a generic phase call or an untyped body.
- Facts fixed for a run are computed **once**, at run start, and sent in the run context (`Catalog`). A later call derives what it needs from the token.
- State between calls lives in MDA's run state or PostgreSQL, never backend memory.

## 3. Run kinds and the catalog

`openswe/agent_api/run_kinds.py` defines `RunKind`. Three kinds exist, each with its own reporters and shell guards:

| Kind | Graph name | What it does | Subagent it delegates to (`mda/agent.py`) |
|---|---|---|---|
| `agent` | `agent` | Coding work: investigate, change code, validate, open or update PRs | `general-purpose` |
| `reviewer` | `reviewer` | Reviews a pull request; read-only on that repo | `reviewer` |
| `review-scout` | `review-scout` | Plans a PR walkthrough (`plan_walkthrough` tool, `openswe/walkthrough/planner.py`) | `general-purpose` |

As a run starts, its kind resolves a **catalog** from data only the backend holds: `agent_catalog`, `reviewer_catalog`, `review_scout_catalog` (`openswe/agent_api/run_catalog.py`). The catalog names the run's operations, subagents, models, sandbox and loop rules. Customization docs point to `agent_catalog()` in `openswe/server.py` and the `ToolSurface` in `openswe/sandboxes/tool_runtime.py` as the place to swap tools and models.

MDA "plays all of them with its one graph" (`mda/agent.py`). `GraphInputs` builds each graph **once per process** and shares it across runs, threads and people. Per-run variation is passed in the catalog, not the graph.

## 4. Subagents and async workers

- The graph exposes one blocking subagent per kind (table above).
- Background **task workers** are an extra graph, `open-swe--general-purpose`, started by a coordinator with `start_async_task`. A worker "is an Open SWE thread of its own: it starts with a worker grant, adopts its own run token, and runs this agent's middleware as it" (`mda/agent.py`).
- Endpoints `worker_launched` and `adopt` implement the handoff; `GraphInputs.worker_webhook` tells the Agent Server where to report a worker's end.

## 5. Dispatch, follow-ups, and completion

`openswe/dispatch.py` is the **single durable dispatch contract** for every reviewer and openswe run trigger. From its docstring:
- Default `multitask_strategy="interrupt"`: a follow-up halts the active run (progress kept by its checkpoints) and resumes with full history plus the new message. On an idle thread it simply starts.
- Background follow-ups such as `/baby-sit` can opt into `enqueue`.
- Every dispatched run carries a `webhook` to `/webhooks/run-complete` (`openswe/completion.py`). The handler guarantees "every run ends with a signal": a failed run (`error`/`timeout`) posts a short reply so the user is never silent.

Mid-run messages: the MDA run takes follow-ups from the thread's inbox (`openswe/threads/inbox.py`, read by the `inbox` endpoint) **before each model call** (`docs/CUSTOMIZATION.md` §6).

## 6. Reporting back: the outbox

`mda/rt/outbox.py`: the runtime tells the backend what happened (replies, tool calls, inbox receipts, notices). Reports are batched into one `reports` call. The run is only "done" once the backend has taken all of them, because the backend's completion closes the transcript turn. This is the mechanism that keeps the backend's transcript consistent with what the model did.

## 7. Thread storage

- **Threads:** Agent Server threads, but a PostgreSQL thread index is the source of truth. `openswe/threads/router.py` serves the Agent Server's thread API from that index and routes runs to MDA. Threads created before the switch are read-only (`openswe/graphs/read_only.py`).
- **Checkpoints:** the Agent Server checkpointer with TTL: strategy `delete`, sweep every 60 minutes, default TTL 43,200 s (12 h) (`langgraph.json`).
- **Store:** `AGENTS.md`: "Don't use the LangGraph Store (`client.store`) for state; keep it in PostgreSQL tables."
- **Legacy SDK use:** "Don't add new uses of the LangGraph SDK client in the backend... Existing uses are legacy."

## 8. Other backend pieces (from docstrings or file names)

- **Job queue** (`openswe/jobs/queue.py`): "work due at a time, once or on a cron schedule, run by `JobWorker`". Handlers registered in `openswe/jobs/kinds.py`. `AGENTS.md`: never hand-roll due-time columns or polling sweeps.
- **Schedules** (`openswe/schedules/`): the backend side of schedules declared by MDA.
- **Background tasks** (`openswe/background_tasks.py`): model-free completion delivery for sandbox background commands, reconciled by a per-thread cron every minute or a callback.
- **Monitors** (`openswe/monitors/`): sandbox commands whose filtered output reaches the thread as events.
- **Bridge** (`openswe/bridge/`): "a cloud thread whose sandbox is the user's own machine" (see file 05).
- **Federation** (`openswe/federation/`): callers that authenticate with a token issued elsewhere (for example GitHub Actions).
- **Analytics, audit logs, announcements, API keys, encryption:** each a subpackage (see file 06).

## 9. Conventions that shape the code (from `AGENTS.md`)

- **"Constant gardening":** before a change, refactor surrounding code so the change "reads as if it had always been designed that way".
- **"Every new function is a method."** Module-level functions only for framework entrypoints (routes, graph nodes, tools, job handlers). Private helpers are methods on the class that owns the data. "A new class must own real state, never be a bag of arguments."
- **Identity by `users.id` everywhere**; provider handles (GitHub login, Slack id, email) resolve to a `User` on entry and are turned back into handles only to call that provider.
- **GitHub calls go through named clients** (`RepoClient`, `PullRequestClient`); no raw REST paths outside `openswe/github/http.py`.
- **Async only;** sync methods only where an interface needs them and then raise `NotImplementedError`.
- **Strong types; never `Any`/`any`.**
- **Prompts live in files** (`openswe/resources/prompts/*.md.jinja`), never inline in Python. Exception: prompts only MDA channel handlers render, in `mda/prompts/`.
- **Exceptions, not `(value, error)` returns.** "Never discard an error: every `except` re-raises or logs what it swallowed."
- **Tables:** `uuid7` primary key, `created_at`/`updated_at`, `created_by`/`updated_by` foreign keys to `users`. Natural keys are unique indexes.
- **Agent tools are fine-grained Unix-style primitives**; no batch tools. Code mode composes them.
- **Settings have agent tools too:** "Whenever adding or changing a setting, add or update its authorized agent tool alongside the UI."

These rules are an unusually explicit engineering standard. They are worth copying in our own repo, independent of the product.

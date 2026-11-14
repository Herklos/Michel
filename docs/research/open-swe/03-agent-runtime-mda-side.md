# 03. The agent runtime (`mda/`): what runs inside Managed Deep Agents

Sources: `mda/agent.py` (module docstring and code), `mda/identity.py`, `mda/memory.py`, `mda/rt/*.py` module docstrings (54 modules), `mda/pyproject.toml`, `mda/README.md`, `mda/CONNECTIONS.md`, `vendor/README.md`, `docs/CUSTOMIZATION.md` §3 and §6. Read 2026-11-14. Docstrings that use Python 3.14 syntax (bare-comma `except`) could not be parsed by the sandbox's 3.13 `ast`; those modules were read as text.

## 1. Shape

`mda/` is a standalone project. Its `agent.py` defines one `define_deep_agent(...)`-based graph and a factory that the Agent Server calls per run. The graph's behavior comes from **what the backend sends in the run context**, not from code in `mda/`:

> "The graph declares one sandbox (`sandbox`) for every run; each run's catalog says which sandbox it uses and the options MDA creates it with (`SandboxSpec`), or that it has none." (`mda/rt/managed_sandbox.py`)

Consequences:
- The same graph serves `agent`, `reviewer` and `review-scout`.
- A thread's state reads the same through any graph.
- Code changes to loop rules usually mean changing `LoopRules` in the backend's catalog, then `mda/rt/loop.py` to carry them out.

## 2. Files that define the project

| File | Role |
|---|---|
| `agent.py` | The graph and factory: subagents per kind, tool lists, middleware order, sandbox declaration, model build |
| `identity.py` | `define_identity(auth=auth.langsmith_api_key(), resolve_user=backend_endpoint("/mda/resolve-user"))`. Channel senders are mapped to Robin users by the backend |
| `memory.py` | `define_memory(user=MemoryLayer())`: user-scoped memory with MDA's default private-conversation policy. No agent or assistant memory layer |
| `instructions.md` | System prompt for the agent; workers start with it, runs follow it |
| `channels/slack.py`, `channels/github.py`, `channels/linear.py` | Channel declarations (`channels.slack(...)` etc.) |
| `bundled_skills/` | Five skills shipped with the project: `baby-sit`, `html-artifacts`, `linear-tickets`, `web-apps`, `workspaces` |
| `prompts/` | Model-facing prompts that only MDA channel handlers render (Slack, GitHub, Linear messages; auto-review; model selection) |
| `pyproject.toml` | Pins: `managed-deepagents` from the vendored SDK (editable), `open-swe-runtime-api` from `packages/runtime-api` |

Channel prompts include `slack-concierge`, `slack-kitchen`, `slack-review-request`, `github-issue`, `github-automation-event`, `linear-issue`, `linear-automation-event`, and an `auto-review/` family (authorization, hard-denied, refused-repeatedly, and risk categories: `credential_access`, `destructive`, `exfiltration`, `persistence`, `routine`, `scope_escalation`, `security_bypass`).

## 3. The `rt/` package (54 modules)

Grouped by responsibility, from module docstrings:

**Loop control** (`rt/loop.py`): "Open SWE's middleware around each model call, run here as the catalog's `LoopRules` say." Before each call it ends the run where a rule says so, adds task context, keeps the sandbox's GitHub proxy fresh, picks the route and model, and assembles the system prompt and tool list. After a turn that calls no tool, it asks again for the reply or CLI result owed. At run end it asks for the record.

**Model calls** (`rt/model_calls.py`, `rt/model_retries.py`, `rt/gateway.py`, `rt/models.py`):
- Every call has a **timeout** ("a provider stall that never raises would park the run"), and failures go to retry or fallback.
- Anthropic **prompt caching** is marked at the call, where the real model is known.
- A thread's history is replayed on every call, to whichever provider routing picks, so "a block one provider wrote can break every later call on another."
- **Gateway:** model calls go through the LLM gateway "as whoever the run acts for": a person's run uses the person's LangSmith login; other runs use the deployment's key. The backend decides which from the run token.

**Routing** (`rt/routing.py`, `openswe/model_routing.py`): a thread's route is classified once, with the run's preparation. Classification uses Jev (`runtime_api.classifier`) through the gateway. Route questions are in `runtime_api.route_questions`, worded from `mda/prompts/model-selection/`.

**Tools** (`rt/file_tools.py`, `rt/run_tools.py`, `rt/tools.py`, `rt/remote_files.py`, `rt/search_tools.py`, `rt/local_tools.py`, `rt/local_results.py`):
- The file and shell tools run in the **thread's sandbox** (MDA-owned), or against the thread's files on the backend (`rt/remote_files.py`) when the sandbox is not MDA's (a bridged thread) or for paths the backend serves.
- Around every call: in auto mode on a person's own machine, the call is first reviewed; a command that may push or touch credentials is checked.
- `rt/run_tools.py` provides `RunCodeInterpreter` (code mode), `RunModelCallLimit`, `RunSubagentMiddleware`, and `BackendTools`. Each run's operations are the tools its model call is offered.
- Code mode uses `langchain-quickjs` (`CodeInterpreterMiddleware`), vendored in `vendor/langchain-quickjs`. Tools are callable from JavaScript as `tools.<name>`.

**Auto-review** (`rt/auto_review.py`): "Auto mode for a thread run on a person's own machine: each file and shell call is let through, put to Jev, or refused before it runs." It "reads what the person asked for and the calls the run made this turn, never tool results or the model's prose, so text a tool returned cannot argue it" past the check.

**Sandbox** (`rt/managed_sandbox.py`): one sandbox per thread, declared by the graph, opened as the run starts, replaced on request. `EXECUTE_TIMEOUT_SECONDS` bounds shell calls. Details in file 06.

**Subdirectory guidance** (`rt/subdir_agents.py`): auto-loads applicable `AGENTS.md` files after file reads, from the sandbox the read ran in. This is how repository-local instructions reach the model.

**Skills** (`rt/skills.py`, `rt/skills` answered from memory): reads of a run's skills are answered from skills this runtime keeps.

**Browser** (`rt/browser.py`, `rt/session_handoff.py`): the run's LangSmith browser is named by MDA and reported to the backend so the dashboard can open it. Browser sessions returned by MCP are kept in run memory and referred to by handle.

**Reporting** (`rt/outbox.py`, `rt/git_evidence.py`, `rt/tracing.py`):
- The outbox batches reports to the backend (see file 02 §6).
- `git_evidence.py` fingerprints checkouts in the sandbox (via `sandbox_scripts/git_trace.py`) before and after file or shell tools, to tag traces with repository and branch metadata.
- `tracing.py` sets a trace policy so middleware does not trace full payloads on every wrapper span.

**Budgets** (`rt/automation_budget.py`): "best-effort automation token budgets in checkpointed thread state."

**Slack handling** (`rt/slack.py`, `rt/slack_message.py`, `rt/slack_prompt.py`, `rt/slack_clicks.py`, `rt/slack_move.py`, `rt/input_messages.py`): message envelopes, button clicks, prompts and thread moves. `rt/input_messages.py` holds a byte-identical copy of the backend's `<input-message>` envelope, enforced by a test.

**Intake and routing of channel events** (`rt/intake.py`, `rt/github_routes.py`, `rt/github_issues.py`, `rt/github_automations.py`, `rt/linear*.py`, `rt/repositories.py`, `rt/images.py`, `rt/public_http.py`): what a channel delivery becomes as a run input. Attachments and images referenced in a message are fetched here.

**Shell and output guards** (`rt/tool_errors.py`, `rt/validate_image_reads.py`, `rt/offload.py`): large results go to backend files instead of the model's context; image reads are validated.

**Tasks** (`rt/task_retry.py`): retry policy for subagent `task` calls.

## 4. Identity and memory from the MDA side

- `identity.py` routes every channel sender through the backend's `/mda/resolve-user` before a run starts. A linked account runs as its Robin user; anyone else runs as the channel's own principal.
- `memory.py` declares **user memory only**. Agent-level and assistant-level memory are not used by Robin; per-run state lives in the thread instead.

## 5. Vendored SDK

`mda/` installs the runtime from `vendor/managed-deepagents-sdk/packages/pypi` (editable). The `mda` CLI is built from the vendored Rust source (`make mda-cli`, `cargo build --locked --release`) into the runtime's `_binaries/`. `vendor/README.md` describes a `scripts/vendor.py` tool that updates the vendored tree, merges upstream pull requests before they land (`--pr <n>`), and records local changes in `vendor/managed-deepagents-sdk/mda-changes/`.

## 6. Tests on this side

`mda/tests/` holds **24** test files. `AGENTS.md`: "Never import `openswe` there; test each side of an endpoint against the models it exchanges." Run with `make mda-test` and `make mda-typecheck`.

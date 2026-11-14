# 05. deepagents on Temporal: how each feature maps

Versions: `deepagents==0.7.38`, `temporalio-deepagents==0.0.3` (pre-release), `temporalio==1.36.0`. Sources: the `temporalio-deepagents` README and source, the `deepagents` package source, and `docs/research/01-temporal-deepagents.md` and `docs/research/02-langchain-deepagents.md`. Checked against the installed packages on 2026-11-14: the plugin's activity names (`deepagents.invoke_model`, `invoke_model_streaming`, `invoke_tool`, `backend_op`), `DeepAgentsPlugin(backends=…, streaming_topic=…, data_converter=…)`, `tool_as_activity` and `activity_as_tool`, `run_deep_agent(state_snapshot=…)`, the testing helpers, and `deepagents.middleware.async_subagents`.

## The mapping

| deepagents feature | Temporal realisation | Where it runs | Status |
|---|---|---|---|
| Agent loop (`create_deep_agent`) | `create_temporal_deep_agent(model="provider:name", …)` inside the thread workflow; the loop replays deterministically | workflow | **[implemented]** `michel/agent.py` |
| Model call | `deepagents.invoke_model` activity (one per model call); the workflow ships only the model name | `llm` queue | **[implemented]** by the plugin |
| Streaming tokens | `streaming_topic` on the plugin; activity publishes chunk batches to a workflow stream; the final message still returns to the workflow | `llm` queue → clients | **[designed]**. The plugin accepts `streaming_topic`, and the SDK ships `temporalio.contrib.workflow_streams`. End-to-end behaviour **[verify]** |
| Planning (`write_todos`) | built-in state middleware | workflow | **[implemented]** (built-in) |
| Files in state (`StateBackend`, default) | in workflow state; replayed deterministically | workflow | **[implemented]** |
| Durable workspace files (`TemporalBackend("workspace")`) | `deepagents.backend_op` activities against a worker-side filesystem factory | `io` / `sandbox` queue | **[implemented]** in `michel/workflows.py`; **[verify]** end to end |
| Sandbox execution (`execute`) | a custom backend whose operations are activities against the sandbox provider | `sandbox` queue | **[designed]** (see `07`) |
| Custom tools with I/O | `tool_as_activity(fn, start_to_close_timeout=…)` | `io` queue | **[implemented]** `michel/tools.py` |
| Existing activity as a tool | `activity_as_tool(activity, start_to_close_timeout=…, retry_policy=…)` (signature checked in 1.36.0 plugin source) | any | available |
| Pure tools (no I/O) | plain LangChain tools in the workflow | workflow | the plugin warns about unwrapped I/O tools |
| Human-in-the-loop | `interrupt_on={tool: True}` with a checkpointer; resume with `Command(resume=…)` after a `decide_approval` update | workflow + Postgres audit | **[implemented]** offline; **[verify]** with the server |
| Sync subagents (`task`) | deepagents `SubAgent` specs; run inside the parent's loop | workflow | **[implemented]** (`researcher`) |
| Async subagents | `SubagentWorkflow` child workflow; the parent starts it, queries or awaits it | child workflow | **[designed]** (deepagents has its own async-subagent middleware; choose one, see below) |
| Skills | skills middleware reading skill files from the workspace backend | workflow + `io` | **[designed]** |
| Memory | memory middleware with mounts (`/memories/...`) routed to Postgres-backed activities via a composite backend | workflow + `persist` | **[designed]** |
| Summarisation | summarisation middleware (keeps context within limits) | workflow | **[designed]** |
| Prompt caching | prompt caching middleware | workflow | available in deepagents |
| Checkpointer | `InMemorySaver`, rebuilt by replay inside the workflow | workflow | **[implemented]** |

## Why the checkpointer is in memory

The plugin's README says a durable checkpointer that performs its own I/O is not replay-safe inside a workflow, and the plugin warns when one is passed. The thread's history is already durable: Temporal replays the workflow and rebuilds the in-memory checkpointer. Across continue-as-new the messages are restored with `aupdate_state` from a snapshot (implemented, tested offline in `tests/test_agent.py`).

## Async subagents: a choice to make

deepagents ships async-subagent middleware, which runs a subagent in a separate graph and lets the parent check on it. Temporal child workflows offer the same shape with durable history, cancellation and retries. Recommendation: use child workflows as the mechanism and keep deepagents' `task` tool as the interface the model sees, so model behaviour does not change. **[verify]** that the middleware's wire format can be routed to a child workflow, or write a small adapter tool that starts and queries the child. Deciding this is ADR-005.

## Budgets

The model activity checks the thread's budget counter (passed in its input) before the provider call and returns the usage after it. The workflow applies the usage to its counters. The check is in the activity so that a budget can stop a call before money is spent, and the counter update happens in the workflow so it is replayable.

## Context control

- Summarisation keeps the active window bounded; the summary is an ordinary message, stored in the transcript.
- Tool results above a size limit are written to the workspace and replaced by a reference (offload pattern), so the model context and the history stay small.

## What deepagents does not give us

- Durable execution of its own: the Temporal layer provides it.
- Permissions beyond `interrupt_on` and the backend's own checks: the security layer (see `11`) supplies approvals, egress and budgets.
- A multi-tenant store: Postgres and the gateway provide it.

## Pinning and upgrades

Pin all three packages together. The `temporalio-deepagents` package is pre-release; each upgrade is a replay test (see `13`) because the plugin changes activity and payload shapes.

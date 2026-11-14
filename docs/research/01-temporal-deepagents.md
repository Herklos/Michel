# Research 01: Temporal Deep Agents integration

Date of research: 2026-11-14. Status: research complete; no runtime test has been executed (see section 7).

## 1. Summary

Temporal ships an integration that makes a LangChain Deep Agent durable. The agent's control loop runs and replays deterministically inside a Temporal workflow. Each non-deterministic step (LLM call, I/O tool, real filesystem or shell operation) runs as a Temporal activity. Adding one `DeepAgentsPlugin` to the client or worker is the only required wiring.

The integration is pre-release. Its code has moved out of the SDK into a separate package.

## 2. Where the integration lives

| Location | What it is | Version seen |
|---|---|---|
| `temporalio.contrib.deepagents` in the Python SDK | Compatibility shim; its README says the integration moved | temporalio 1.36.0 |
| `temporalio-deepagents` on PyPI | Standalone package; canonical API is `temporalio.deepagents` | 0.0.3 (pre-release) |
| `temporalio/ai-integrations`, `python/deepagents` | Source repository and README | main branch |

Migration as stated by the shim README: remove the `deepagents` extra from `temporalio[...]` and run `uv add temporalio-deepagents`. Change imports to `from temporalio.deepagents import DeepAgentsPlugin`.

## 3. Public API (verified from the package source)

From `temporalio/deepagents/__init__.py`, `__all__`:

- `DeepAgentsPlugin`
- `TemporalModel`
- `TemporalBackend`
- `activity_as_tool`
- `tool_as_activity`
- `run_deep_agent`
- `create_temporal_deep_agent`
- `DeepAgentsWorkflowError`

`DeepAgentsPlugin.__init__` keyword arguments (from `_plugin.py`):

| Argument | Purpose |
|---|---|
| `model_provider` | Callable from model name to a LangChain chat model. Default uses `init_chat_model`. Keys live here, on the worker. |
| `model_activity_options` | One config, or a map keyed by model name |
| `tool_activity_options` | One config, or a map keyed by tool name |
| `backends` | Mapping of name to factory, used by `TemporalBackend` |
| `streaming_topic` | Enables a streaming model activity that publishes chunks to a workflow stream |
| `streaming_batch_interval` | Default 100 ms |
| `passthrough_modules` | Extra modules to pass through the workflow sandbox |
| `data_converter` | Optional custom Temporal data converter |

Registered activities: each plugin instance registers four activities: `deepagents.invoke_model`, `deepagents.invoke_model_streaming`, `deepagents.invoke_tool`, `deepagents.backend_op`.

## 4. Behavior, as documented

Source: the package README (`temporalio-deepagents`), sections "What this plugin gives you", "Configuring activity options", "Tools", "Durable file and shell backends", "Human-in-the-loop", "Streaming", "Continue-as-new", "Runtime behavior", "Composing with other plugins".

- **Drop-in durability.** `create_deep_agent(...).ainvoke(...)` runs in a workflow without changes. Sub-agents, planning, filesystem middleware and HITL keep working.
- **One LLM call per activity.** The workflow ships only the model name. The worker's `model_provider` builds the client. Temporal owns retries; the LLM SDK's own retries are disabled.
- **Sub-agents inherit durability** because they inherit the parent's model object and tools.
- **Tool choice is explicit.** A tool that only changes agent state can run in the workflow. A tool doing real I/O must be wrapped with `activity_as_tool` (existing activity) or `tool_as_activity` (LangChain tool). An unwrapped non-built-in tool runs in the workflow and triggers a warning at construction. Deep Agents' built-ins (`write_todos`, state-backed file tools) stay in the workflow.
- **`tool_as_activity` registration is process-local.** It must run at import or startup on every activity worker.
- **Durable backends.** `TemporalBackend("name", factory_argument=..., backend_type=...)`. The built-in file and shell tools run as `deepagents.backend_op` activities. The factory is registered by name on each worker. The factory argument is recorded in workflow history, so credentials stay in the worker-side factory.
- **Human-in-the-loop.** `interrupt_on={...}` plus a checkpointer. `ainvoke` returns `__interrupt__` inside the workflow. Clients read it through a query and resume with an update. Resume uses `Command(resume={"decisions": [{"type": ...}]})`.
- **Streaming.** With `streaming_topic` set, model dispatch uses a streaming activity that publishes `AIMessageChunk` batches to `temporalio.contrib.workflow_streams`. The aggregated final message still returns to the workflow.
- **Continue-as-new.** `run_deep_agent(agent, input, state_snapshot=...)` carries messages and the `files` state across runs. It does not carry todos (`TodoListMiddleware` marks them `OmitFromInput`). Repeated identical tool calls after the boundary run again; they are not deduplicated.
- **Testing helpers.** `temporalio.deepagents.testing` provides `FakeModel`, `fake_model_factory`, `mock_model_provider`, and `MockTool`.

## 5. Constraints and warnings

Source: the package README, "Runtime behavior" and "Durable file and shell backends", plus the `workflow.py` docstrings.

- One `DeepAgentsPlugin` instance per worker. Client and worker can share an instance, or use two instances with the same `model_provider` and `backends` objects. Any other second instance fails at worker start with `ValueError`.
- A local filesystem path used by `FilesystemBackend` must be reachable by every activity worker that can run the operation, or the backend activities need a task queue whose workers share that filesystem.
- Factories run once per activity attempt. They must reconnect to the same external state. Changes held only in a backend instance's memory do not survive between calls.
- A durable checkpointer that performs its own I/O is not replay-safe inside a workflow. The plugin warns when one is passed. Use the snapshot and continue-as-new path instead.
- `activity_as_tool` requires `start_to_close_timeout` or `schedule_to_close_timeout`.
- Update activity workers before or together with workflow workers, because older activity workers pass message objects as dicts.
- Experimental: the package says it "may change in future versions".

## 6. Sources

| # | Source | Access | Result |
|---|---|---|---|
| S1 | https://docs.temporal.io/develop/python/integrations/deepagents | `docs.temporal.io` DNS failure (`ENOTFOUND`) | Not read. The README links to this page as the release-stage reference. |
| S2 | `temporalio-1.36.0` wheel: `temporalio/contrib/deepagents/README.md`, `__init__.py`, `workflow.py`, `testing.py` | PyPI download (`pip download`) | Read. Shows the move to the standalone package. |
| S3 | `temporalio-deepagents==0.0.3` wheel: `temporalio/deepagents/*.py` | PyPI download | Read. Source for the API table in section 3. |
| S4 | `temporalio-deepagents` README, https://raw.githubusercontent.com/temporalio/ai-integrations/main/python/deepagents/README.md | `raw.githubusercontent.com` (200) | Read in full. Source for sections 4 and 5. |
| S5 | https://github.com/temporalio/samples-python `deepagents_plugin/*` | `gh api` returned 403 for this repo; code search found the paths | Not read. Sample paths: `hello_world`, `react_agent`, `subagents`, `streaming`, `human_in_the_loop`, `filesystem_backend`, `continue_as_new`, `external_storage`, `langsmith_tracing`. These are the most useful starting points for tests. |

## 7. What still needs to be tested

These are unverified. Each needs a Temporal server (`temporal server start-dev`) unless noted.

1. **Basic durability.** Start `hello_world`-style workflow, kill the worker mid-LLM call, restart it, and confirm the model call is retried, not the whole conversation.
2. **Determinism.** Replay recorded histories with `temporalio.worker.Replayer` after code changes, to catch non-deterministic workflow code.
3. **Sandbox import.** Confirm workflow modules that import `deepagents`, LangChain, and our `grokbot.tools` load under the sandbox without `imports_passed_through` guards. Our code uses the guard; test that the guard is still needed or harmless.
4. **Unwrapped tool warning.** Confirm an unwrapped non-built-in tool emits the construction warning.
5. **Activity registration.** Confirm `tool_as_activity` tools are found on a worker that imports the module, and fail clearly on one that does not.
6. **Plugin instance rules.** Confirm the `ValueError` when a second, different `DeepAgentsPlugin` instance is added to the worker.
7. **HITL end to end.** Approve and reject through the real update, confirm the side effect runs once on approve and never on reject, and confirm the workflow survives a worker restart while waiting for approval.
8. **Multiple decisions.** Confirm `decisions_needed` matches the number of action requests when the model emits several tool calls in one turn.
9. **Continue-as-new.** Lower the threshold, force several continue-as-new cycles, and confirm the message history restore, the transcript, and that todos are dropped as documented.
10. **Backend factory across workers.** Run two worker processes with different machines or paths, and confirm file operations land where expected. Confirm a missing path fails clearly.
11. **Streaming.** Set `streaming_topic`, subscribe with `WorkflowStreamClient`, and confirm the final message is identical to the non-streaming result.
12. **Timeouts and retries.** Force a slow model activity past `start_to_close_timeout` and confirm the retry policy and error surface.
13. **Secrets.** Confirm no API key or webhook URL appears in workflow history (inspect with `temporal workflow show`).
14. **Version pinning.** Confirm `temporalio==1.36.0` and `temporalio-deepagents==0.0.3` work together. Re-test on each upgrade, since the package is pre-release.
15. **Docs parity.** Read `docs.temporal.io/.../deepagents` once it is reachable, and diff it against the package README for differences in API or behavior.

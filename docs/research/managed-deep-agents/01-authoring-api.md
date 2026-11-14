# 01. Authoring API: `define_deep_agent` and project shape

Source: `managed-deepagents` 0.10.4 (PyPI, MIT), the README in its wheel metadata (2,051 lines) and its module list. Read 2026-11-14. Status: **public beta** per its README. The `deepagents-cli` README says it is a **private preview** with a waitlist. These conflict, so treat access as unconfirmed.

## 1. What a project is

A managed deep agent is a Python project directory. `mda` compiles it into a LangGraph Agent Server build and deploys it. The entry point is a named `agent` variable in `agent.py` at the project root.

```text
my-agent/
  agent.py              # named `agent` variable (required)
  identity.py           # managed authentication (scaffolded by `mda init`)
  memory.py             # optional durable-memory declaration
  instructions.md       # managed system prompt
  pyproject.toml        # requires-python; [tool.mda] python-version
  .env                  # local deploy secrets, never committed
  schedules/            # optional cron schedules, one per file
  tools/                # optional custom tools; tools/mcp.py declares MCP servers
  middleware/           # optional middleware
  skills/               # optional skills synced to Context Hub
  sandbox/              # optional sandbox (__init__.py, setup.sh)
```

## 2. `define_deep_agent`

- Requires `name`. Accepts the `create_deep_agent` options **except** the platform-owned `backend`, `store`, `checkpointer`, `system_prompt`, and `memory`.
- The system prompt comes from `instructions.md`. Static agents load all discovered skills.
- `agent` may be a **sync or async factory** `(runtime: ManagedServerRuntime) -> agent`. This lets one project pick model, tools, instructions, skills, MCP, sandbox, and memory per run. `None` disables a selection for that run. Empty strings and arrays are explicit selections.
- During inspection, `execution_runtime` is `None`. The factory must be repeatable and keep graph structure and schemas stable. `mda build` reads the inline literal `name` without calling the factory.
- Install all model integrations the factory can select.

Model strings use `provider:model`, e.g. `openai:gpt-5.5`. The README's examples use OpenAI; Anthropic is supported by `deepagents` and the deploy payload (`runtime.model.model_id`).

## 3. Context, tools, and middleware types

- `ManagedServerRuntime[AppContext]` for factories. Extends the native `langgraph_sdk.runtime.ServerRuntime`, adding managed fields. `access_context` identifies the Agent Server operation that called the factory.
- `ManagedToolRuntime[Context, State]` for tools and tool-call hooks. `ManagedDeepAgentRuntime` is an alias. Lifecycle and model hooks keep the native `Runtime[Context]`. `isinstance(runtime, ManagedRuntime)` gives access to MDA fields.
- Managed fields: `server_info`, `channel` (deprecated, use `thread.origin.channel`), `backend` (None without a sandbox), `schedules`, `thread`.

## 4. Memory (`memory.py`)

`define_memory(agent=..., assistant=..., user=...)` with `MemoryLayer()`. Each layer is independent. Omit a layer to disable it.

| Layer | Mount | Default policy | Backing |
|---|---|---|---|
| agent | `/memories/agent/` | available to all callers | deployment-shared Context Hub repo |
| assistant | `/memories/assistant/` | shared only by runs of the same assistant in this deployment; requires trusted assistant identity | opaque per-deployment, per-assistant repo |
| user | `/memories/user/` | trusted person only; defaults to managed Slack one-to-one DMs (`channel_type == "im"`); needs `identity.py` | opaque per-user repo keyed on trusted principal |

Details the README specifies:
- Each mount's `AGENTS.md` is injected every turn; other files are read on demand.
- Permitted **hot memory** loads once per run, on the first model call, and is not saved in thread state. A later denied run cannot load saved memory.
- Deploy never overwrites existing memories. A project without `memory.py` mounts no durable memory.
- `allow(context)` callbacks are **deprecated** for root declarations; prefer selecting memory from a dynamic agent. Policies run once per run, including interrupt resumes. A callback error fails the run. Policies cannot grant access to another person's memory.
- The legacy `scope` option still works but cannot be combined with `agent`, `assistant`, or `user`.

## 5. Custom backends

`routes={"/documents/": StoreBackend(...)}` mounts Deep Agents backends at path prefixes, like `CompositeBackend(routes=...)`. Prefixes must be absolute directories and cannot overlap `/instructions.md`, `/skills/`, or `/memories/`. Routes serve the file tools only; sandbox shell commands do not see them.

## 6. Subagents

- Every Python agent can run its `general-purpose` subagent **blocking** (`task`) or **background** (`start_async_task`). The agent chooses per task.
- Declared subagents are dict literals. `"async": True` makes a subagent its own graph in the same deployment, named `<agent>--general-purpose` for the background copy.
- An async subagent runs under the caller's identity and uses the project's sandbox, identity, and connector declarations. Unset `model`, `tools`, `permissions`, `interrupt_on` inherit from the agent. It does **not** inherit middleware or memory.
- With a sandbox, the subagent shares the starting agent's sandbox. MDA checks that the caller owns the starting agent's thread first.
- Approval for a subagent appears in the Slack thread or the subagent's own thread. A finished task's reply is posted back to the origin thread.
- Tracing: subagent runs nest under the starting call's trace. Any caller allowed to start runs can place a run inside another trace in the same workspace (the README calls this out).
- Each async subagent can also be run directly as its own assistant, with the agent's tools but **not** its instructions or middleware. Warning from the README: do not rely on the agent's middleware to guard tools shared with a subagent.

## 7. Skills

`skills/<name>/SKILL.md` with frontmatter. Synced to Context Hub on deploy. Subagents load only the skills their `skills` key names (`"skills": ["/skills/"]` gives the agent's skills).

## 8. Project sanity points (from README)

- `mda build` warns about subagent entries it cannot read statically. Subagent dicts must be literals or names bound to literals, with `name` and `"async"` after any `**spread`.
- Schedules and subagent declarations must be "statically serializable literals or top-level constants" so the build can read them without running the code.

## 9. What still needs testing

1. Build a minimal project, run `mda build`, and confirm the generated `langgraph.json` matches the README (requires running the bundled `mda` binary; not run here, see README 00).
2. Factory selection: switch model and tools per run via `execution_runtime.context`, and confirm `None` disables a selection.
3. Memory layers: confirm the default user-memory policy (Slack DMs only), and that a denied run never sees saved memory.
4. Async subagent: confirm the shared sandbox, the approval routing, and that the subagent's `interrupt_on` cannot be looser than the agent's.
5. `routes=` prefix collision errors at build time.

# 02. Runtime semantics: context, threads, origins, schedules, sandbox, MCP, connections

Source: `managed-deepagents` 0.10.4 README (wheel metadata), sections "Run context and channels", "Define a Schedule", "Runtime schedules", "Sandbox", "MCP Servers", "Connections in the sandbox proxy". Read 2026-11-14.

## 1. Run context layout

```text
runtime
  .context          // application data on direct runs; None on channel runs
  .server_info      // trusted caller and server information
  .channel          // present for a managed channel delivery (deprecated: use thread.origin.channel)
    .name .provider .event .raw_event .post(...)
  .backend          // present when a sandbox is configured; else None
  .schedules        // create/list/get/update/delete schedules for this run's caller
  .thread           // ManagedThread (see section 2)
```

- **Direct API runs** pass application data as Agent Server's `context` parameter, validated against the authored `context_schema` with native LangGraph validation.
- **Channel runs** receive `context = None` in tools, middleware, and factories. Read the message from `runtime.thread.origin.channel.event`. The schema's required fields do not apply to channel runs.
- A `channel` field in a direct API call does **not** establish a trusted channel source.
- Managed ingress resolves the verified channel before the factory runs, then strips delivery data before native execution.
- A compiled graph is scoped to one execution. Direct callers of the managed compiler must build a fresh graph per execution.

## 2. `runtime.thread` (ManagedThread)

- `id`: LangGraph thread ID. An async subagent's thread is its starting agent's thread.
- `origin`: the channel conversation the thread came from, or `None`. `origin.channel` is the delivery that started the run. On runs not started by a channel message (Studio resume, task-notification wake, scheduled run), it is the thread's last channel conversation; `event` and `raw_event` are `None`, except scheduled runs get a `schedule` event. `origin.sender` is the latest message's sender, or `None` if not a person.
- `participants`: list of `ThreadParticipant(id, role)`. First person is `owner`; later people are `member`. Recorded as IDs only, never message content, and only managed ingress writes them.

## 3. Event types delivered to a run

`message` (contains `messages`), `user_prompt_response` (`action`, optional `value`, optional `correlation_id`), and `interrupt_resume` (`resume`). For Trigger-backed Slack, `raw_event` is the inner provider event without HTTP headers or the outer Trigger envelope.

**Interrupt correlation:** put a shared ID on the prompt and on the interrupt value under `INTERRUPT_CORRELATION_KEY`. Without it, an answer resumes the only pending interrupt that isn't a tool-call review; multiple pending interrupts require a match.

## 4. Posting back to a channel

- `origin.channel.post(message, new_thread=False, run=None)` sends an **additional** message. The normal final reply is still automatic.
- `{"type": "content", "content": ...}` for portable text; `{"type": "native", "native": {...}}` for provider JSON. Supply only the matching payload.
- The helper exposes no address or destination override. The reply target is private and bound by MDA.
- When a run with a thread origin ends, MDA posts its answers to that origin. An answer of exactly `[quiet]` is not posted. A failed Slack post fails the run; a failed HTTP-channel post is logged and the run still succeeds.
- On failure, a default "Something went wrong while processing your request." message is sent.

## 5. Schedules

**Declared (in code):** one file per schedule under `schedules/`, `define_schedule(cron=..., timezone=..., prompt=...)`. `mda deploy` reconciles them as LangSmith cron jobs after the deployment is live. Stateless runs clean up their temporary thread after completion.

**Runtime (from a tool or middleware):**
- `runtime.schedules.create(owner={"type": "user"}|agent, cron=... | at=datetime, timezone=..., prompt=..., new_thread=..., run_as=...)`
- `list`, `get`, `update` (e.g. `{"paused": True}`), `delete`, all taking the same `owner`.
- `at` for one-time runs. `new_thread` chooses a new thread or the current one.
- Owner rules: a user schedule belongs to the current user; `run_as` can pick another thread participant (only the owner can manage it, but its runs act as that person with their connections).
- Limit: 20 runtime schedules per owner per agent, paused ones included. `MDA_MAX_AGENT_SCHEDULES` and `MDA_MAX_USER_SCHEDULES` change it. Expired one-time and code-defined schedules do not count.
- Runtime schedules survive redeploys.

## 6. Sandbox

- `define_sandbox(idle_ttl_seconds=600, docker_image=..., snapshot_name=..., snapshot_id=..., proxy_config=..., registry=...)` in `sandbox/__init__.py`. Delete `sandbox/` to opt out.
- The sandbox is a **LangSmith sandbox**. MDA owns naming, image or snapshot selection, reuse, and lifecycle.
- `sandbox/setup.sh`, if present, is baked **once** into a recipe snapshot at deploy or dev. Thread sandboxes clone the snapshot and do not re-run setup. A dynamic agent that selects a different base image fails, because setup was never baked on it.
- `runtime.backend` implements the Deep Agents backend interface: `ls`, `read`, `write`, `edit`, `grep`, `glob`; `delete` is optional. `upload_files` and `download_files` for binary. Async variants `aread`, `awrite`, `adelete`. All paths are sandbox paths; Context Hub routes are not included.
- The sandbox opens on first use; `await runtime.backend.aopen()` opens it now.
- Private images: `registry={"url", "username", "password_env"}`. The password is read from an env var and used only to reconcile the registry; it never enters the build.
- Naming: `{deployment}--{digest}` of the thread ID, so a restarted server re-adopts its sandbox.
- Slack attachments are saved to `/workspace/attachments/`; `upload_files(paths)` attaches completed workspace files to a reply (sandbox required).

## 7. MCP servers (`tools/mcp.py`)

- Module-level `mcp = define_mcp(servers={...})`. Each server: `transport` (e.g. `"http"`), `url`, optional `include_tools` / `exclude_tools` (raw MCP names, prefixed `{server}_` in the exposed tool name), optional `connection`, optional `jit_auth=True`.
- Connections: `connections.get(slug, {"type": "agent"})` (agent-owned, one credential for everyone) or `{"type": "user"}` (per caller, OAuth or opaque).
- Missing user grants **interrupt** the run, including from a custom tool or middleware. A pre-run gate can request all known grants before the first model call.
- `jit_auth=True`: tools for unconnected providers are offered; calling one interrupts once per model step with connect links, then runs after resume. Without a connection, those calls return a tool error.
- Scheduled agent runs have no person behind them: LangSmith MCP servers act as the agent using admin-connected credentials; servers with no agent credential are skipped with a warning.
- OAuth MCP servers report a connection URL; the user completes OAuth, then the run is retried.
- Deploy first, then `mda connections create`. Agent-owned secrets are scoped to the Agent Server. `mda deploy` fails if a declared slug is missing from the workspace.

## 8. Connections in the sandbox proxy

`define_sandbox(proxy_config={"rules": [...], "access_control": {"allow_list": [...]}})`. Each rule matches hosts and sets headers:

| Helper | Sent value |
|---|---|
| `ref` | raw token |
| `bearer(ref)` | `Bearer <token>` |
| `basic(username, ref)` | `Basic <base64(username:token)>` |

Credentials refresh before each command. A failed proxy update blocks the command. Missing user grants interrupt before the first model call; revoked grants interrupt before the next command.

Limits stated in the README:
- Long commands and background processes can fail when tokens expire.
- Runs in one thread share a proxy config. Later runs replace credentials used by background processes, so concurrent users can overwrite each other's credentials.

## 9. What still needs testing

1. Thread origin on a scheduled run versus a Studio resume (the README says these differ).
2. `correlation_id` matching with two pending interrupts.
3. Schedule limit enforcement at 20, and the behavior of `run_as` for a non-owner participant.
4. `setup.sh` baking: confirm a changed script produces a new snapshot and that live threads keep old boxes.
5. Proxy credential rotation during a background process (the README warns about overwrite).
6. `jit_auth=True` with no connected caller in a scheduled run (README: tool error, run continues).

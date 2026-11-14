# 07. Sandboxes

A sandbox is where an agent runs commands, edits files and starts services. It is untrusted code execution. Nothing in the workflow runs inside it.

## Provider interface **[designed]**

```text
SandboxProvider
  create(spec: SandboxSpec) -> sandbox_id
  attach(sandbox_id) -> SandboxHandle        # reconnect after a worker restart
  exec(handle, command, timeout, env, cwd) -> ExecResult   # streams; heartbeats
  read(handle, path) / write(handle, path, bytes) / list(handle, path)
  snapshot(handle) -> snapshot_id
  destroy(sandbox_id)
  health(sandbox_id) -> {state, last_seen}
```

`SandboxSpec` holds: base image or snapshot id, CPU, memory, disk, idle timeout, egress policy id, mounts, and credential references (never values).

Implementations:
- **Docker** (first): rootless containers on dedicated hosts, no privileged mode, read-only base layer, a per-thread writable volume.
- **LangSmith Sandboxes** (second): the SDK's `SandboxClient` covers create, exec, files, snapshots and service URLs; its auth proxy and egress rules match the design below.

## Lifecycle

```text
  (none) ─create─► PROVISIONING ─ready─► ATTACHED ─idle timeout─► IDLE ─touch─► ATTACHED
                       │                    │                         │
                  create failed        exec / files             idle timeout
                       ▼                    ▼                         ▼
                    FAILED              (in use)                 REMOVED (reaper)
```

- A thread gets its sandbox **lazily**, on the first turn that needs one.
- The sandbox id is stored in Postgres (`sandboxes` row) and in the thread's state.
- The idle timeout and the removal delay are per tenant policy (defaults in Managed Deep Agents: 600 s idle).
- The reaper runs in `MaintenanceWorkflow`: it removes idle sandboxes and reconciles rows with the provider.

## Egress and credentials

- Every sandbox has a **default-deny** egress policy: an allowlist of hosts and ports, enforced by an egress proxy outside the sandbox. Only TCP leaves; UDP and ICMP are dropped (the LangSmith proxy behaves this way, see `docs/research/langsmith/03-sandboxes.md`).
- Credentials are injected by the proxy into requests to named hosts (for example a Git host). The sandbox never holds the token; this is the pattern Open SWE uses for GitHub.
- No host mounts. Shared data enters through the object store and is copied in by an activity.
- Resource limits per sandbox: CPU, memory, disk and process count.

## Failure handling

| Situation | Response |
|---|---|
| Sandbox deleted outside the system | the handle reports gone; the thread is told the workspace is missing; a fresh sandbox is created only on the user's request (Open SWE's rule: never silently replace) |
| Sandbox unreachable | retry with backoff for a bounded time; then the turn pauses with an error and the operator is alerted |
| Command timeout | the command is killed; output so far is returned; the agent sees a timeout |
| Long command | heartbeats every 10 s keep the activity alive; a missing heartbeat cancels it |
| Worker dies during exec | the sandbox keeps running the command; the next attempt reattaches and reads the output file; commands that write to a log file survive |
| Background command left running | tracked by the sandbox layer; killed on stop, on thread close, or by the reaper |

## Files between sandbox and workspace

- Workspace files that the agent's file tools read and write are the sandbox's files.
- Files that cross the boundary (uploads to the agent, deliverables back to the person) go through the object store. Size limits per direction.

## What the current code does

Nothing sandboxed yet. The `FilesystemBackend` in `grokbot/worker.py` writes to a directory on the worker. It is a trusted-code backend and must be replaced before any untrusted code runs. **[implemented]** as a stopgap only.

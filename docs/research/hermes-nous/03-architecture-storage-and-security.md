# 03. Architecture, storage, and security (Hermes Agent)

Sources: `llms-full.txt` pages "Architecture", "Session Storage", "Profiles: Running Multiple Agents", "Security" (read in full for the approval section), "Scheduled Tasks (Cron)", "Persistent Memory", "Curator", "Skills System", and the source tree (`run_agent.py`, `tools/`, `gateway/`, `cron/`, `hermes_state*.py`, `plugins/`). Read 2026-11-14.

## 1. Entry points and the agent core

The architecture page draws five entry points into one core:

- **CLI** (`cli.py`), **Gateway** (`gateway/run.py`), **ACP** (`acp_adapter/`), **Batch runner**, **API server**, and a Python library.
- All of them drive **`AIAgent`** in `run_agent.py`, which uses three parts: a **prompt builder** (`prompt_builder.py`), **provider resolution** (`runtime_provider.py`), and **tool dispatch** (`model_tools.py`). Compression and caching sit alongside. The architecture page lists **three API modes**: chat completions, Codex responses, and Anthropic.
- The **tool registry** (`tools/registry.py`) is central. The architecture page says "70+ tools, 28 toolsets"; the source has 310 `tools/*.py` modules, and the toolset count was not reconciled (file 01 §4).
- **Tool modules** (from the page): `approval.py` (dangerous command detection), `terminal_tool.py`, `process_registry.py` (background processes), `file_tools.py`, `web_tools.py`, `browser_use_cli.py` (Python over CDP), `browser_session.py`, `browser_launcher.py`, `code_execution_tool.py`, `delegate_tool.py`, `mcp_tool.py`, `credential_files.py`, `env_passthrough.py`.
- **Terminal backends** (`tools/environments/`): local, Docker, SSH, Modal, Daytona, Vercel Sandbox. (Architecture page.)
- **Gateway** (`gateway/`): `run.py` (dispatch), `session.py` (conversation persistence), `delivery.py` (outbound), `pairing.py` (DM authorisation), `hooks.py`, `mirror.py` (cross-session message mirroring), `status.py` (token locks, profile-scoped processes).
- **Plugins** (`plugins/`): bundled platform plugins under `plugins/platforms/` (24), and others listed in file 02 §5. Home Assistant is a catalogue plugin; Yuanbao is a Hermes Labs plugin.
- **Cron** (`cron/`): `jobs.py` and `scheduler.py`, with about 60 modules for delivery, recovery, quotas, worktree maintenance and detached workers.

## 2. Where state lives

| What | Where | Notes |
|---|---|---|
| Config | `~/.hermes/config.yaml` (per profile) | the profile's `config.yaml` holds model, providers, toolsets, MCP, terminal, memory, plugins, gateway, TTS, display |
| Secrets | `~/.hermes/.env`, `auth.json` | profile-scoped |
| Identity | `SOUL.md` | first thing in the system prompt; protected by `security.protected_instruction_files` |
| Memory | `memories/MEMORY.md`, `memories/USER.md` | frozen snapshot at session start |
| Skills | `~/.hermes/skills/` (+ `.archive/` from the curator) | source of truth for skills |
| Sessions and history | `state.db` (SQLite, with `-shm` and `-wal`) | sessions, messages, FTS5 search, model config |
| Cron | `cron/jobs.json`, `cron/output/` | Bot routines use the same store with a bot namespace |
| Kanban | `~/.hermes/kanban.db` | shared across profiles |
| Logs and caches | `logs/`, `sessions/`, `cache/`, `runtime/` | operational |

**Profiles** are isolated directories: a profile named `coder` uses `<root>/profiles/coder/` with its own `state.db`, config, logs and skills. A profile can be cloned with `--clone` (config, `.env` without channel credentials, SOUL, skills, memory) or `--clone-all` (adds sessions, `state.db`, cron, backups, checkpoints).

## 3. Single writer for sessions

The session-storage page says the **profile's gateway is the only writer of canonical sessions**. The CLI, TUI, Desktop (local), API server, ACP, cron, Bot Chat and Kanban workers are clients that submit input to that session authority over `/api/ws`. Out-of-process workers write through the owner's RPC and never open `state.db` for transcript writes. Two processes pointed at one Hermes home are warned against (the memory page): they compound each other's writes.

## 4. Memory mechanics

- Two stores with fixed limits: MEMORY (2,200 chars) and USER (1,375 chars). The `memory` tool can add, patch or remove. A write over the limit returns an error; memory does not auto-compact. The agent must consolidate or remove entries in the same turn.
- The rendered block shows usage (for example "67% — 1,474/2,200 chars") so the agent knows its capacity.
- The snapshot is frozen for the session to preserve the prompt cache; changes apply next session.
- External memory providers (file 02 §1) add cross-session modelling beyond these two files.

## 5. Scheduling mechanics

- The cron page has a **Model resolution** order: per-job pin, then `cron.model` in config, then the main model at fire time.
- **Admission recovery:** an agent-backed run keeps its fire identity until output and a durable delivery handoff are recorded; the scheduler reconciles unfinished receipts on each tick, including after restart. A known terminal result goes to the delivery queue without re-running the agent. An interrupted execution stays paused for operator review; paused jobs are not auto-resumed.
- Cron sessions cannot create more cron jobs (loop guard).

## 6. Curator mechanics

The curator is a background pass over **agent-created** skills. It is triggered by inactivity (interval 7 days; idle at least 2 hours), not by cron. The first run after a fresh install is deferred by one full interval. A dry run reports what would change. Automatic transitions are deterministic (no LLM): 14 days unused to `stale`; 30 days unused moves to `.archive/`. Pinned skills and skills referenced by any cron job are skipped.

## 7. Security model (the docs' own eight layers)

From `docs/security` ("Overview"): (1) user authorisation (allowlists, DM pairing); (2) dangerous command approval; (3) file write safety (denylist and optional write sandbox); (4) container isolation (Docker, Modal, and a Singularity plugin) with hardened settings; (5) MCP credential filtering (environment isolation for MCP subprocesses); (6) context file scanning for prompt injection; (7) cross-session isolation (cron storage paths hardened against traversal); (8) input sanitisation (working directories checked against an allow-list).

### 7.1 Approval modes (`approvals` in config)

| Key | Default | What it controls |
|---|---|---|
| `approvals.mode` | `smart` | `smart`, `manual` or `off` |
| `approvals.timeout` | 300 s | how long to wait for a user response |
| `approvals.cron_mode` | `deny` | what cron jobs do at a dangerous command |
| `approvals.single_query_mode` | `deny` | what single-query (`-q`) sessions do |
| `approvals.unattended_mode` | `deny` | what webhook and API sessions do |
| `approvals.mcp_reload_confirm` | `true` | `/reload-mcp` asks before dropping the MCP tool cache |
| `approvals.destructive_slash_confirm` | `true` | `/clear`, `/new`, `/reset`, `/undo` ask first |

**YOLO mode** (`/yolo`) disables all dangerous-command checks for that session, except a **hardline blocklist**. It also skips the untrusted-MCP prompt. It is saved with the session and shows a red banner and a status-bar marker. The docs warn it is for fully trusted automation only. YOLO still asks for:
- MCP tool spend limits (a call past a declared `spend_limit`); where nobody can answer, the call is refused;
- MCP elicitation (requests for input);
- payment-card fill prompts from the credential vault;
- MCP event subscriptions, which install a standing trigger.

**Supervised-gateway guard:** the terminal tool refuses to stop or restart the gateway from inside its own supervised process, and refuses process killers aimed at the interpreter image the gateway runs as (for example `pkill python`). User approval, YOLO and `force=True` do not bypass this guard. macOS `launchctl submit` and `bootstrap` are restricted regardless of label.

## 8. Official domains and phishing

A page exists on official domains and phishing safety (Getting Started). Its content was not read.

## 9. Assessment (this review)

- The approval design is explicit and configurable, with separate defaults for unattended contexts (deny). The default `smart` mode's classifier was not read, so its precision is unknown.
- The guards that protect the gateway from itself are unusually specific. They show the product has been hardened against its own supervisor loops.
- Container isolation is optional (the default is local); the docs say so for terminal backends.

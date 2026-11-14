# 05. Control plane (`/v1/deepagents/*`), deploy payloads, and the CLIs

Sources:
- `deepagents-cli` 0.3.0 (PyPI, MIT): read the `deploy/api_client.py`, `deploy/payload.py` and README. **Deprecated; this is its final release.** Its README redirects to `managed-deepagents` and the `mda` CLI.
- `managed-deepagents` 0.10.4 README (wheel metadata). The `mda` CLI itself is a **bundled Rust binary** (`_binaries/mda`, classifier "Programming Language :: Rust"). Its subcommands below come from the README. **The binary was not executed**: a sandbox policy blocked running it, and I did not work around that.

Read 2026-11-14.

## 1. Control-plane endpoints (verified in `deepagents-cli` `api_client.py`)

Base for deploy: `/v1/deepagents`. Hub base: `/v1/platform/hub`.

| Method | Path | Purpose |
|---|---|---|
| POST | `/v1/deepagents/agents` | create a managed agent |
| GET | `/v1/deepagents/agents` | list (paged; `iter_agents`) |
| GET | `/v1/deepagents/agents/{id}` | get one |
| PATCH | `/v1/deepagents/agents/{id}` | update metadata |
| DELETE | `/v1/deepagents/agents/{id}` | delete |
| GET | `/v1/deepagents/agents/{id}/health` | health check (used by deploy) |
| GET | `/v1/deepagents/mcp-servers` | list workspace MCP servers |
| POST | `/v1/deepagents/mcp-servers` | register an MCP server |
| GET / PATCH / DELETE | `/v1/deepagents/mcp-servers/{id}` | get, update, remove |
| GET | `/v1/deepagents/mcp/tools` | list a server's tools (resolves by id, name or URL) |
| (auth) | `register_mcp_oauth_provider`, `create_auth_session`, `get_auth_session` | MCP OAuth flow |
| GET | `/v1/platform/hub/repos/-/{agent_id}/directories` | read the agent's directory tree |
| (commit) | `commit_agent_directory` | write a delta of files (`null` deletes) |

Related platform routes referenced by the managed package and README: `/v1/managed-tools/` and `/v1/managed-tools/servers/exa/mcp` (LangSmith-hosted tool servers), `/v1/agent-auth/connections`, `/v1/agent-auth/credentials`, `/v1/agent-auth/principals`, `/v1/agent-auth/oauth-providers`, `/v1/agent-auth/oauth-authorization-sessions`, `/v1/channels/`, `/v1/channels/{name}/events`, `/v1/batch`, `/v1/user`, `/v1/platform/workspaces/current/info`, `/v1/platform/mda/otel/...`.

## 2. Agent payload (verified in `deploy/payload.py`)

Create/PATCH body is built from the project:

```text
name                  required
description           optional
runtime               {"model": {"model_id": "<provider:model>"}}  (or a full runtime object)
backend               e.g. {"type": "sandbox", "sandbox_config": {"scope": "thread"|"agent", "policy_ids": [...], ttl...}}
permissions           optional
extras                optional
system_prompt         the AGENTS.md text
tools                 list (must reference registered MCP servers; empty tools.json deploys)
skills                [{"type": "inline", "name", "description", "instructions", "files"?}]
subagents             [{"name", "description"?, "model_id"?, "instructions", "tools"?}]
files                 {"subagents/<name>/<rel>": {"content": "..."}}  (raw subagent files)
```

Default backend is `state`. Sandbox is opt-in with `backend.type = "sandbox"`. The CLI does not run sandboxes locally; the platform does.

**Directory model:** the agent's file tree is managed separately from the PATCH body, through Hub directory commits:

```text
AGENTS.md
tools.json                       (optional)
skills/<name>/SKILL.md (+ extra files)
subagents/<name>/AGENTS.md       (frontmatter: description, model_id; then instructions)
subagents/<name>/tools.json      (optional)
```

`build_directory_delta` returns only changed paths; a path present remotely but absent locally and under `AGENTS.md`/`tools.json`/`skills/`/`subagents/` is deleted (`null`). This is a **declarative reconcile**: deploy makes the remote tree match the local tree.

## 3. Deploy flow (from the deprecated CLI and the `mda` README)

1. Read project (`agent.json` in the old CLI; `agent.py` and friends in the new one).
2. Create or PATCH the agent with the metadata payload.
3. Commit the directory delta to Hub.
4. Health-check `/agents/{id}/health`.
5. For the new CLI: `mda deploy` also builds the Agent Server image (`.mda/build`), reconciles schedules as LangSmith cron jobs after the deployment is live, and sets up Slack, GitHub and Linear channels. A channel already set up is set up again *before* the new revision uploads, so a failed setup stops the deploy first.

## 4. `mda` CLI (from the `managed-deepagents` README)

| Command | Purpose | Notable flags |
|---|---|---|
| `mda init [name]` | scaffold a project | `-i` interactive (can hand off to a coding agent); `--instructions "..."` or `--instructions-file`; `--model <spec>`; `--memory agent`; `--no-sandbox`; `-c slack` / `--channel` / `--channels` |
| `mda evals init -i` | scaffold Harbor eval workspace | creates `evals/harbor-job.json` once; `.mda/evals/` is generated |
| `mda build <path>` | compile to `<root>/.mda/build` | reads literal `name` without calling the factory |
| `mda dev <path>` | run on the local LangGraph dev server | requires `uv` on PATH |
| `mda deploy <path>` | deploy to LangSmith | `--name`, `--agent-server-type serverless\|dedicated` (default serverless), `--workspace-id`, `--no-wait` |
| `mda logs <path>` | read server logs | `--lines N`, `--level error`; streams in a terminal, prints last 1000 lines when piped |
| `mda delete <path>` (alias `destroy`) | remove Agent Server, tracing project, Context Hub repo, managed sandboxes | `--yes` skips confirmation; **memory and thread history are not recoverable** |
| `mda channels setup` | set up or finish channel setup without deploying | |
| `mda connections create` | provision connections after deploy | agent-owned secrets refuse before first deploy |

Other facts from the README:
- Python: `requires-python` in `pyproject.toml`; server Python selected via `[tool.mda] python-version` (quoted `major.minor`, 3.11–3.14) or `MDA_PYTHON_VERSION`. Default: newest allowed, or 3.14 if none declared.
- Secrets: model keys (for example `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`) must be in the project `.env` or workspace secrets. A value exported in the shell is **not** deployed. `LANGSMITH_API_KEY` in `.env`, or interactive browser sign-in (writes the key to `.env`).
- `LANGSMITH_WORKSPACE_ID` or `--workspace-id` when credentials require a workspace.
- PyPI install is `uv tool install managed-deepagents`; private-beta dev builds need `--prerelease allow`. The wheel bundles the `mda` binary per platform (macOS x86_64/arm64, Linux x86_64/aarch64, Windows x86_64/arm64).

## 5. The deprecated `deepagents-cli` (for migration context)

Commands (README): `deepagents init`, `deploy`, `agents list|get|delete`, `mcp-servers list|add|get|tools|update|delete|connect`. `deepagents init` scaffolds `tools.json` (empty), an example skill, and an example subagent. Its README states the new path is `uv tool install managed-deepagents` followed by `mda init my-agent`, `mda deploy`.

The interactive coding agent `dcode` moved to `deepagents-code` and is unaffected.

## 6. What still needs testing

1. Confirm the control-plane endpoints above respond as described, with a valid LangSmith key and private-preview access. Not testable here.
2. Confirm `build_directory_delta` deletes remote files outside the managed set and never touches other paths (review in code is done; run it against a test tree).
3. Run `mda build` on a minimal project and inspect `.mda/build` (blocked: binary not executed).
4. Check `mda deploy --no-wait` followed by `mda channels setup` reaches the same state as a waited deploy.
5. Confirm `mda delete` removes sandboxes created by the Agent Server (the README says it does).
6. Confirm the migration path from `deepagents-cli` `agent.json` to `agent.py` keeps `runtime.model` and `backend` semantics.

# 07. What must be tested, and what remains open

Companion to files 01–06. Lists what was not verified in this session, why, and the test that would settle it.

## 1. Environment limits in this session (2026-11-14)

| Limit | Effect |
|---|---|
| `docs.langchain.com` and `docs.temporal.io` DNS-blocked (`ENOTFOUND`) | No primary docs site read. Used packages and READMEs instead. |
| The bundled `mda` binary was **not run** (sandbox policy denied the execution; not worked around) | `mda build`, `mda init` and CLI behavior are documented from the README only. |
| Temporal dev server cannot be downloaded | No real workflow execution. |
| `api.github.com` returns 403 for unlisted repositories | Could not browse the managed-deepagents repo's source or issues. |
| Managed platform is public beta (resolved by the docs, file 08) | Control-plane endpoints still need a workspace to test. |

## 2. Test plan by area

### 2.1 Authoring (file 01)
- Build a minimal project, `mda build` it, and diff `langgraph.json`. (Blocked: binary.)
- Dynamic factory: different model and tools per `execution_runtime.context`; `None` disables a selection.
- Memory: default user-memory policy is Slack DMs only; a denied run never loads saved hot memory.
- Subagent `async: True`: shared sandbox, approval routing, and no looser `interrupt_on` than the agent.
- `routes=` prefix collisions with `/memories/` raise at build time.

### 2.2 Runtime semantics (file 02)
- Scheduled-run origin versus Studio resume: differing `origin.channel.event`.
- `correlation_id` matching with two pending interrupts.
- Runtime schedule limit at 20 per owner; `run_as` for a non-owner participant.
- `setup.sh` change produces a new snapshot; live threads keep their sandboxes.
- Proxy credential overwrite across concurrent users (documented risk).
- `jit_auth=True` in a scheduled run with no connected caller: tool error, run continues.

### 2.3 Channels and identity (file 03)
- Forged `Linear-Signature` rejected; timestamps older than 60 s rejected.
- `on_finish` lost on restart (documented). Confirm before depending on it.
- `multitask_strategy` `interrupt` vs `rollback` on a long Slack run.
- `resolve_user` `reply` for an unlinked account; reply carries no sender identity.
- Endpoint handler retries: 429 and 5xx retried with the same `webhook-id`; other errors fail the handler.
- `trigger_mode` migration: dropping `"all"` moves an existing deployment to `"mention"`.
- GitHub channel reply behavior (open question; see file 03 §1).

### 2.4 Platform (file 04)
- `langgraph dev` with a minimal graph; `curl` each route in file 04 §2.
- `on_disconnect` and `multitask_strategy` on the real server, not only the SDK literals.
- Store TTL sweep and vector index on Postgres (the in-memory store is pickle-backed and not representative).
- Webhook URL policy blocks private IPs and loopback under `disable_private_ips`.
- AES-JSON encryption round-trip and key rotation.
- Event-stream capability probe fails fast with a mismatched `langgraph` version.

### 2.5 Control plane and CLI (file 05)
- `/v1/deepagents` CRUD and health against a real workspace (blocked: access).
- `build_directory_delta` deletes only managed paths (`AGENTS.md`, `tools.json`, `skills/`, `subagents/`).
- `mda deploy --no-wait` then `mda channels setup` reaches the same state as a waited deploy.
- `mda delete` removes Agent Server sandboxes (README claim).

## 3. Open questions

1. **Managed product status. Resolved (file 08):** public beta on LangSmith Cloud and BYOC, per the official docs. The waitlist text was in the deprecated `deepagents-cli` README.
2. **GitHub channel replies.** The README is inconsistent (see file 03 §1).
3. **Which Noodle/Osaurus/Grok comparisons matter now?** Out of scope for this file; see `docs/research/`.
4. **Hosted or self-hosted target?** Changes sandbox and tenancy choices (file 06 §6).
5. **Acceptable licenses.** Assumed: no Elastic-2.0 code in our runtime.

## 4. Re-read when access works

- `docs.langchain.com/langsmith/python/managed-deep-agents-overview`, `…-quickstart`, `…-cli`, and the deepagents overview. These are referenced by the README and the deprecation notice.
- `github.com/langchain-ai/managed-deepagents-sdk` (linked as the repository in the package metadata) and `github.com/langchain-ai/managed-deepagents`.
- Once the `mda` CLI can be run in an approved way: `mda --help` and `mda build` output for a sample project.

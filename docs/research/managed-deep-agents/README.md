# Managed Deep Agents: research index

Exploration of the LangChain/LangGraph managed Deep Agent runtime, to inform building a similar runtime. Collected 2026-11-14.

Primary sources were the PyPI wheels (read directly) and their READMEs. The official docs (`docs.langchain.com`) became reachable after an allowlist change; file 08 records what was checked against them.

| File | Topic | Main source |
|---|---|---|
| [01-authoring-api.md](01-authoring-api.md) | `define_deep_agent`, project layout, memory layers, subagents, skills | `managed-deepagents` 0.10.4 README |
| [02-runtime-semantics.md](02-runtime-semantics.md) | Run context, threads and origins, posting to channels, schedules, sandbox, MCP, connections | same |
| [03-channels-and-identity.md](03-channels-and-identity.md) | Slack, GitHub, Linear and HTTP channels; signed endpoints; identity mapping | same |
| [04-platform-agent-server.md](04-platform-agent-server.md) | LangGraph Agent Server: routes, config, streaming, store, checkpointer, auth, licensing | `langgraph-api`, `langgraph-runtime-inmem`, `langgraph`, `langgraph-sdk`, `langgraph-cli` wheels |
| [05-control-plane-and-cli.md](05-control-plane-and-cli.md) | `/v1/deepagents` control plane, deploy payloads, `mda` CLI | `deepagents-cli` 0.3.0 source (deprecated) and `managed-deepagents` README |
| [06-build-gap-analysis.md](06-build-gap-analysis.md) | 33-row feature matrix against our `grokbot/`, licensing, priorities | files 01–05 and our code |
| [07-testing-and-open-questions.md](07-testing-and-open-questions.md) | Limits of this session, test plan, open questions | all |
| [08-docs-verification.md](08-docs-verification.md) | Check of files 01–07 against the official docs (`docs.langchain.com`), corrections, and new facts | official docs pages |

## Key facts

- The managed product is **Managed Deep Agents**: a code-first project (`agent.py`, `instructions.md`, `tools/`, `skills/`, `subagents/`, `schedules/`, `sandbox/`), compiled and deployed with the `mda` CLI to a LangSmith-hosted LangGraph Agent Server.
- The runtime adds, on top of LangGraph: channels (Slack, GitHub, Linear, HTTP), identity mapping, layered memory, sandboxes with setup snapshots, MCP with per-user connections, and runtime schedules.
- **Licensing:** the server (`langgraph-api`, `langgraph-runtime-inmem`) is Elastic-2.0. The SDKs and `deepagents` are MIT. Do not build on the server code for a competing hosted service.
- **Status:** public beta on LangSmith Cloud and BYOC, per the official docs (file 08).

## Not verified

- Anything requiring the hosted platform, a LangSmith workspace, or the `mda` binary (not executed; a sandbox policy blocked it, and I did not work around that).
- The docs site is now reachable through `llms.txt`. File 08 covers the pages read; the rest of the docs index is unread.

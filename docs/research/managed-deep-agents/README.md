# Managed Deep Agents: research index

Exploration of the LangChain/LangGraph managed Deep Agent runtime, to inform building a similar runtime. Collected 2026-11-14.

Primary sources were the PyPI wheels (read directly) and their READMEs. The documentation site (`docs.langchain.com`) was not reachable from this sandbox.

| File | Topic | Main source |
|---|---|---|
| [01-authoring-api.md](01-authoring-api.md) | `define_deep_agent`, project layout, memory layers, subagents, skills | `managed-deepagents` 0.10.4 README |
| [02-runtime-semantics.md](02-runtime-semantics.md) | Run context, threads and origins, posting to channels, schedules, sandbox, MCP, connections | same |
| [03-channels-and-identity.md](03-channels-and-identity.md) | Slack, GitHub, Linear and HTTP channels; signed endpoints; identity mapping | same |
| [04-platform-agent-server.md](04-platform-agent-server.md) | LangGraph Agent Server: routes, config, streaming, store, checkpointer, auth, licensing | `langgraph-api`, `langgraph-runtime-inmem`, `langgraph`, `langgraph-sdk`, `langgraph-cli` wheels |
| [05-control-plane-and-cli.md](05-control-plane-and-cli.md) | `/v1/deepagents` control plane, deploy payloads, `mda` CLI | `deepagents-cli` 0.3.0 source (deprecated) and `managed-deepagents` README |
| [06-build-gap-analysis.md](06-build-gap-analysis.md) | 33-row feature matrix against our `grokbot/`, licensing, priorities | files 01–05 and our code |
| [07-testing-and-open-questions.md](07-testing-and-open-questions.md) | Limits of this session, test plan, open questions | all |

## Key facts

- The managed product is **Managed Deep Agents**: a code-first project (`agent.py`, `instructions.md`, `tools/`, `skills/`, `subagents/`, `schedules/`, `sandbox/`), compiled and deployed with the `mda` CLI to a LangSmith-hosted LangGraph Agent Server.
- The runtime adds, on top of LangGraph: channels (Slack, GitHub, Linear, HTTP), identity mapping, layered memory, sandboxes with setup snapshots, MCP with per-user connections, and runtime schedules.
- **Licensing:** the server (`langgraph-api`, `langgraph-runtime-inmem`) is Elastic-2.0. The SDKs and `deepagents` are MIT. Do not build on the server code for a competing hosted service.
- **Status is unclear:** public beta in one README, private preview with waitlist in another.

## Not verified

- Anything requiring the hosted platform, a LangSmith workspace, or the `mda` binary (not executed; a sandbox policy blocked it, and I did not work around that).
- The primary docs site. Re-read it once reachable (file 07 §4).

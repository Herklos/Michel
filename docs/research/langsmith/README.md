# LangSmith: deep research index

Collected 2026-11-14. Sources: the LangSmith documentation (266 pages downloaded from `docs.langchain.com/langsmith/...`, found via the `llms.txt` indexes) and the open-swe repository at `42db6cc` (the "preview" in the question is open-swe's preview deployment, `scripts/deploy_preview.py`).

| File | Topic |
|---|---|
| [01-feature-catalogue.md](01-feature-catalogue.md) | Product areas, page counts, release-stage labels, cross-cutting concepts |
| [02-agent-server-and-deployments.md](02-agent-server-and-deployments.md) | Agent Server: deployment types, revisions, runs and double texting, streaming, HITL, cron, MCP and A2A, TTLs, runtime topology |
| [03-sandboxes.md](03-sandboxes.md) | Sandboxes: SDK, system and custom snapshots, auth proxy, egress rules, access delegation, mounts, service URLs, permissions |
| [04-observability-and-evaluation.md](04-observability-and-evaluation.md) | Runs, traces, threads, trajectories; integrations; the coding-agent metadata contract; privacy controls; sampling; costs; automation rules; online evaluators |
| [05-llm-gateway.md](05-llm-gateway.md) | The gateway's eight-step request pipeline, two credential layers, API formats, fallbacks, spend, rate, access and data policies, decision models, credits |
| [06-identity-auth-context-and-mcp.md](06-identity-auth-context-and-mcp.md) | Authentication and authorisation, resource and store isolation, Agent Auth (beta), Context Hub, Prompt Hub, managed MCP and tool kits |
| [07-fleet-engine-insights-export-and-deployment-control.md](07-fleet-engine-insights-export-and-deployment-control.md) | Fleet (no-code agents), Engine (issues and fixes from traces), Insights, data export, Cloud and self-hosted deployment control |
| [08-open-swe-usage-map.md](08-open-swe-usage-map.md) | Every LangSmith surface open-swe uses, with file references; the preview deployment flow |
| [09-verification-and-open-questions.md](09-verification-and-open-questions.md) | What was verified, what could not be, open questions, re-check list |

## Key findings

1. **LangSmith is a platform with six parts that share one identity and billing model:** the Agent Server (deployments), Sandboxes, the LLM Gateway, tracing and evaluation, Agent Auth and Context Hub, and the no-code and analysis products (Fleet, Engine, Insights).
2. **The model-call path is the most governed part.** Every call through the gateway authenticates a key, resolves the route, loads a provider credential that the client never sees, checks spend, rate and access policies, and writes a trace.
3. **Sandbox credentials are injected outside the sandbox.** The auth proxy adds headers to outbound requests and enforces egress rules per connection. Sandbox code never holds the key.
4. **open-swe depends on LangSmith in six ways.** Its preview is a deployment revision driven from GitHub Actions; its runtime is an Agent Server deployment with the Interrupt double-texting mode; its sandboxes, its model calls, its traces and its managed MCP consent all go through LangSmith services.
5. **Some features are beta.** The LLM Gateway and Agent Auth are beta; Cloud deployments and preview builds are public beta. Fleet, Engine and tracing core pages carry no stage label.
6. **The platform internals are not published.** The docs describe behaviour, not implementation. The one open-source server is LangGraph's Agent Server (Elastic-2.0), read in an earlier research note.

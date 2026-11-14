# 01. LangSmith feature catalogue

Source: the LangSmith documentation as published on `https://docs.langchain.com/langsmith/...`. The 266 LangSmith page URLs were taken from the `llms.txt` indexes (`/llms.txt`, `/_llms/products-and-setup.txt`, `/_llms/agent-development-lifecycle/{monitor,deploy,build}.txt`), then downloaded as Markdown. Read 2026-11-14. Page counts below come from a keyword grouping of the page file names, so they are approximate.

## 1. Product areas

| Area | Pages | Release status on the pages | What it is |
|---|---|---|---|
| Agent Server runtime | ~86 | Cloud deploy and preview builds: **public beta**; the page notes "LangSmith Deployment is now LangSmith Agent Server" | Hosts graphs as assistants, with threads, runs, cron, store, streaming, auth, MCP and A2A endpoints; deployed to Cloud, BYOC or self-hosted |
| Tracing and observability | ~57 | No stage label on the core pages (some integrations, such as Gemini Live and LiveKit, are **beta**) | Records every model call, tool call and retrieval as runs in traces, threads and trajectories; integrations for about 35 frameworks and coding agents |
| LLM Gateway | ~20 | **beta** (every gateway page carries the label) | One endpoint that routes model calls, applies spend, rate, access and data policies, falls back between models, and traces each call |
| Fleet (no-code agents) | ~24 | No stage label found; "Agent Builder is now LangSmith Fleet" | Create agents from templates or by describing them; connect Slack, Teams, Salesforce, tools and MCP servers; schedules and webhooks; approvals |
| Engine | ~14 | No stage label found | Reads production traces, groups failures into issues, proposes fixes as pull requests, creates datasets for offline tests |
| Context and Prompt Hub | ~13 | No stage label found | Versioned prompts, and "contexts" (agents and skills as commits with environments) pulled by running agents |
| Evaluation | ~8 | No stage label found | Online evaluators (LLM-as-judge, code, composite, multi-turn, decision models); tuned evaluators; classifier optimisation |
| Sandboxes | ~9 | **generally available** (the overview page says so) | Isolated Linux environments for agent code, with snapshots, mounts, egress and auth proxies, service URLs, permissions, SDK and CLI |
| Agent Auth | ~4 | **beta** ("under active development") | OAuth 2.0 credential brokering so agents can act in third-party systems on a user's behalf |
| Data export, insights, alerts, rules | ~12 | No stage label found; bulk export is Enterprise-only for accounts that signed up after 2026-08-03 | Automation rules, webhooks, annotation queues, dashboards, Insights (failure-mode analysis), Parquet export to S3-compatible buckets |
| Deployment and control | ~19 | — | Cloud (Serverless or Dedicated), BYOC data planes, self-hosted with a control plane; regions, static IPs, env vars, encryption |

## 2. Cross-cutting concepts used across areas

- **Runs** (spans), **traces** (trees of runs, up to 25,000 runs each), **threads** (sequences of traces), **trajectories** (flat, de-duplicated message lists). (observability-concepts)
- **Assistants** (a graph's blueprint) and **threads** (conversations) in the Agent Server. (agent-server, assistants, threads)
- **Metadata and tags** on runs, plus a standard metadata contract for coding agents (`coding-agent-metadata-contract`). (add-metadata-tags)
- **Workspaces, service keys and personal access tokens.** Personal access tokens are prefixed `lsv2_pt_` and carry the creator's permissions; service keys are prefixed `lsv2_sk_` (llm-gateway-authentication, administration-overview).
- **Regions and data planes**: Cloud is regional; BYOC and self-hosted use a data plane URL in `LANGSMITH_ENDPOINT`. (sandbox-sdk, cloud-platform-features)
- **Release stages** are linked from each page (beta, public beta, generally available). Labels were checked page by page and are reported as found, not inferred.

## 3. Full page list

The page list with titles and descriptions is in the working catalogue (`catalog.txt` in the research scratch area). The complete set of 266 URLs was grouped above; the individual titles are summarised area by area in files 02 to 07.

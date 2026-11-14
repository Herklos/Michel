# 04. Observability, metadata, and evaluation: features and mechanisms

Sources: docs pages `observability-concepts`, `add-metadata-tags`, `coding-agent-metadata-contract`, `mask-inputs-outputs`, `sample-traces`, `trace-replicas`, `cost-tracking`, `filter-traces`, `trace-query-syntax`, `view-traces`, `access-current-span`, `conditional-tracing`, `distributed-tracing`, `agent-server-distributed-tracing`, `rules`, `insights`, `dashboards`, `alerts`, `webhooks`, `online-evaluations-llm-as-judge`, `tuned-evaluators`, `feedback-data-format`, `run-data-format`. Read 2026-11-14; the list of integrations is taken from the page list (about 35 frameworks).

## 1. The data model

- **Run**: one unit of work (a model call, a prompt format, a retrieval, a tool call). Like an OpenTelemetry span.
- **Trace**: runs for one operation, as a tree. Each trace is capped at **25,000 runs**; further runs are rejected.
- **Thread**: traces for one multi-turn session. A turn is one user message and everything the agent does in response.
- **Trajectory**: a projection over a thread; a flat, ordered list of human, AI and tool messages, each appearing once. It is for seeing the path an agent took, not for debugging one failure.

## 2. Getting data in

- **Decorators and wrappers** (`@traceable`, `wrap_openai`) in the Python and JavaScript SDKs; LangChain and LangGraph trace automatically when `LANGSMITH_TRACING` is on.
- **OpenTelemetry**: an OTel exporter path exists (`trace-with-opentelemetry`) and an OTel gateway architecture that can redact data before it reaches LangSmith (`otel-gateway-trace-redaction`).
- **Integrations** (page per integration): OpenAI, Anthropic, Bedrock, Gemini, Mistral, DeepSeek, LiteLLM and any OpenAI-compatible provider; LangChain, LangGraph, CrewAI, AutoGen, Google ADK, OpenAI Agents SDK, Pydantic AI, Semantic Kernel, Microsoft Agent Framework, Strands, Mastra, Vercel AI SDK (JS), Temporal, Instructor, n8n, Pipecat and LiveKit (voice), Deep Agents; and coding agents: Claude Code, Claude Cowork, Claude Managed Agents, Codex, Cursor, Pi, OpenCode, VS Code Copilot Chat.
- **Trace without environment variables** (`trace-without-env-vars`) and **upload files with traces** (`upload-files-with-traces`).
- **Replicas** send every trace to several environments or workspaces at once, with per-replica metadata. A legacy destination setting is used.

## 3. Metadata, tags and the coding-agent contract

- Metadata is a key-value dict on a run; tags are labels. Both can be set statically (on a decorator) or per call.
- **Coding-agent metadata contract** (`coding-agent-metadata-contract`): every run from a coding agent must carry an identity block: `ls_agent_type` (`root`, `subagent`, `middleware`, `compaction`), `ls_agent_purpose` (for example `coding`), `ls_integration` (the emitting integration), `ls_agent_runtime` (human-readable runtime name), `thread_id` (groups runs in the Threads view), and `ls_trace_schema_version` (`coding-agent-v1`). Fields are marked **always**, or in lower tiers for when the runtime can supply them. Integrations listed as implementing it: `claude-code`, `openai-codex`, `deepagents-code`, `cursor`, `pi`, `opencode`, `copilot`.
- Metadata is searchable through filters and the query syntax, and drives dashboards and rules.

## 4. Privacy controls

- **Hide inputs and outputs** entirely (environment variable or Client setting).
- **Hide metadata**, or transform it.
- **Rule-based masking** with regex or an anonymiser library.
- **Redact secrets** with the SDK anonymiser's built-in patterns for API keys, tokens and credentials.
- **Per-function processing** of inputs and outputs.
- **Conditional tracing**: enable or disable tracing per request, for example by tenant, sensitivity or feature flag.

## 5. Volume and cost

- **Sampling** with `LANGSMITH_TRACING_SAMPLING_RATE` globally, or per Client instance.
- **Cost tracking** records token use and cost for major providers automatically, and accepts custom pricing. Costs roll up across the whole application. The LLM Gateway records costs for calls routed through it.

## 6. Querying and viewing

- Views: trace tree, thread (sequence of traces with timing), trajectory (messages), and the Trajectory view integrations.
- Filters on runs and traces, with a query syntax (`trace-query-syntax`) and ClickHouse-backed filtering for large projects (`filter-traces-in-application`).
- `export-traces` and `query-threads` SDK methods; **bulk export** of trace data in Parquet to S3-compatible buckets (file 07).

## 7. Automation: rules, alerts, webhooks, annotation queues

**Automation rules** (`rules`) run actions when traces match conditions: add to a dataset, add to an annotation queue (for example 10% of threads for spot checks, or all with negative feedback), trigger a webhook (for remote evaluation), or extend retention (for example all traces with errors). **Automation webhooks** POST a payload containing the rule ID and the matched run or thread when a rule fires. **Alerts** notify on metric thresholds. **Dashboards** chart project metrics.

## 8. Evaluation

- **Online evaluators** score production traces as they arrive. Types: **LLM-as-a-judge**, **code** (a function), **composite** (combines others), **multi-turn** (scores a whole thread), and **decision models** (TypeSafe and OpenAI classifiers, see file 05). Evaluator runs auto-upgrade the trace to extended retention.
- **Offline evaluation** on datasets with `aevaluate` (used by open-swe's reviewer eval, file 08).
- **Tuned evaluators** (LangChain Tuned Evaluators): an evaluator trained on labelled examples.
- **Optimise a classifier** from labelled feedback.
- **Feedback** is stored as typed records (`feedback-data-format`) and can drive rules.
- **CI/CD**: a pipeline example combines Agent Server deployment and evaluation (`cicd-pipeline-example`).

## 9. Analysis products

- **Insights** (Plus and Enterprise): automatic analysis of traces with hierarchical categories, to find usage patterns and failure modes without reading traces. Needs a model configuration. Run per environment.
- **Engine** (file 07): opens issues and proposes fixes from traces.

## 10. Distributed tracing

Trace context passes between services, including between the Agent Server and clients (`agent-server-distributed-tracing`, `distributed-tracing`), so one trace can span a caller, the deployment and a sub-agent. Conditional tracing and `access-current-span` let code reach the current run from inside a traced function.

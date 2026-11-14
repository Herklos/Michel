# 02. Agent Server and deployments: what it does and how

Sources: docs pages `agent-server`, `agent-server-overview`, `deploy-to-cloud-overview`, `deployment-revisions`, `cloud-platform-features`, `double-texting`, `interrupt-concurrent`, `cron-jobs`, `streaming`, `add-human-in-the-loop`, `server-mcp`, `server-a2a`, `webhooks`, `preview-builds`, `agent-server-scale`, `configure-ttl`, `store-auth`, `resource-auth`, `auth`, `caching`, `background-run`, `custom-middleware`, `custom-routes`, `configurable-headers`, `env-var-cloud`, `env-var-self-hosted`, `deploy-with-control-plane`. Read 2026-11-14.

## 1. What the Agent Server is

"A workflow orchestration runtime for agent workloads. It offers an API for creating and managing agent-based applications." A deployment contains **graphs** (each graph is a blueprint for an assistant), a **database** for persistence, and a **task queue**. Cloud manages the database. Graphs need not be LangGraph: the docs list Strands, Claude Agent SDK and Google ADK as deployable.

## 2. Deployment types and modes

| Choice | Behaviour (from the docs) |
|---|---|
| Cloud, **Serverless** | scales to zero when idle; for background agents and latency-tolerant work |
| Cloud, **Dedicated** | stays on and autoscales across replicas; for latency-sensitive production |
| BYOC | the same managed model, run in a customer data plane |
| Self-hosted | operator runs the stack; **control plane** UI (self-hosted only) builds images and deploys |
| Runtime topology (self-hosted) | **single host** (API process runs the queue), **split API and queue** (`queue.enabled: true`), or **distributed runtime** (API and queue run separately, with a separate execution process per graph) |

Cloud requires a Plus plan or above (docs). Regional data residency: a deployment's region is that of its organisation and cannot be migrated.

## 3. Revisions: how code reaches a running server

- The first deploy creates the Agent Server and its first revision. Later code changes are **revisions** on the same server: `langgraph deploy` (CLI) finds the server by name, or `--agent-server-id`. The UI has **+ New Revision**, where you set the config file path, Studio sharing and secrets.
- A revision **queues** for deployment and passes build and deploy stages. Interrupting a stuck revision is documented as "undefined behaviour".
- **Preview builds** (public beta, GitHub-integrated Cloud servers): a pull request triggers a temporary preview Agent Server built from the PR's latest commit; each new commit makes a new revision.

## 4. Runs, threads and double texting

- A **thread** holds conversation state across runs. A **run** is one execution of an assistant on a thread; **stateless runs** have no thread and are cleaned up afterwards.
- When a second input arrives while a run is active ("double texting"), the server applies one of four strategies:
  - **Enqueue** (default): wait for the current run, then run the new input.
  - **Reject**: refuse concurrent runs.
  - **Interrupt**: stop the current run, keep its progress, insert the new input and continue from that state. The graph must cope with a half-finished tool call.
  - **Rollback**: stop and discard the current run's progress, then treat the new input as a fresh run from the initial state.
- Double texting is **not** in the open-source LangGraph framework; it is an Agent Server feature.

## 5. Streaming and human-in-the-loop

- Streaming via the LangGraph SDK: `client.runs.stream(thread_id, assistant_id, input, stream_mode=...)`. Stream modes are the LangGraph ones (`values`, `updates`, `messages`, `custom`, `checkpoints`, `tasks`, `debug`), plus v2 events.
- Human-in-the-loop uses LangGraph **interrupts**. `runs.wait` returns `__interrupt__` and a later run resumes with a `Command`.
- **MCP over HTTP:** `/mcp` implements the Streamable HTTP transport and accepts protocol revisions from `2024-11-05` through `2026-07-28`. **A2A:** `/a2a/{assistant_id}` speaks A2A v1.0 JSON-RPC and accepts v0.3 method names.
- **Webhooks:** two kinds: LangGraph API callbacks (a `webhook` parameter on a run) and **automation webhooks** (POST when rules match runs or threads). Both are documented.

## 6. Cron jobs

Creates a **new thread** on each tick and sends the same input to it. Schedules are cron expressions **interpreted in UTC**. The API has endpoints under `/runs/crons` (create, search, count, get, delete). Managed Deep Agents and Fleet use the same underlying mechanism for their schedules (see file 07).

## 7. State, TTLs, caching and scale

- **Checkpointer** persists thread state; **store** holds cross-thread memory (Postgres-backed by default).
- **TTL** (`configure-ttl`): checkpoints and memories can be set to expire by a strategy (delete, or keep the latest).
- **Caching**: server-side caching of graph results (page `caching`).
- **Scale** (self-hosted): configured through Helm values for read and write load; Cloud autoscales (Serverless or Dedicated).
- **Encryption at rest**: AES (`aes-encryption`) and custom providers (`custom-encryption`) are documented.

## 8. Configuration surface

- `langgraph.json` declares graphs, dependencies, env files and HTTP options (see open-swe's file for a real example in `08`).
- **Custom middleware**, **custom routes** and **custom lifespan** events can be added to the server app.
- **Configurable headers**: request headers mapped to graph configuration at run time; included in server logs when configured.
- Environment variables are set per revision (cloud) or on the host (self-hosted) (`env-var-cloud`, `env-var-self-hosted`).

## 9. How it works internally (what the docs state)

Container architecture and the run lifecycle are documented (`agent-server` "Runtime architecture"): an API container accepts requests and a queue container (or the same process, on single host) executes runs. Persistence goes to the database; streaming goes back through the API. The internals beyond that are not published on these pages. The open-source packages that implement the server are covered in `docs/research/managed-deep-agents/04-platform-agent-server.md`.

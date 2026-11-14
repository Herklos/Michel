# 04. Platform: the LangGraph Agent Server and what the managed runtime is built on

Sources: `langgraph-api` 0.18.0 (wheel, read), `langgraph-runtime-inmem` 0.38.0 (wheel, read), `langgraph-sdk` 0.4.14 (wheel, read), `langgraph-cli` 0.4.43 (wheel, read), `langgraph` 1.2.22 (wheel, read). Read 2026-11-14. The managed runtime's hosted control plane is not in any package; the Agent Server is the open-serving layer the managed product deploys onto.

## 1. Licensing (important for the build decision)

| Package | License | Implication |
|---|---|---|
| `langgraph`, `langgraph-sdk`, `langgraph-cli` | MIT | Free to use and modify |
| `managed-deepagents`, `deepagents` | MIT | Free to use and modify |
| `langgraph-api` | **Elastic-2.0** | Free to use; **may not be offered to third parties as a managed service** without a separate license |
| `langgraph-runtime-inmem` | **Elastic-2.0** | Same restriction |

Practical consequence: we can reuse MIT parts freely. Do not copy the Agent Server into a competing hosted offering. Build our own server on MIT components, or get a license.

## 2. HTTP surface (routes from `langgraph_api/api/*.py`)

**Assistants:** `/assistants`, `/assistants/search`, `/assistants/count`, `/assistants/{assistant_id}`, `/assistants/{assistant_id}/graph`.

**Threads:** `/threads`, `/threads/search`, `/threads/count`, `/threads/prune`, `/threads/{thread_id}`, `/threads/{thread_id}/copy`, `/threads/{thread_id}/state`.

**Runs:** `/threads/{thread_id}/runs` (create), `/threads/{thread_id}/runs/stream`, `/threads/{thread_id}/runs/wait`, `/threads/{thread_id}/runs/{run_id}` (get), `/threads/{thread_id}/runs/{run_id}/cancel`, `/threads/{thread_id}/runs/{run_id}/join`, `/runs` (stateless), `/runs/stream`, `/runs/wait`, `/runs/batch`, `/runs/cancel`.

**Crons:** `/runs/crons`, `/runs/crons/search`, `/runs/crons/count`, `/runs/crons/{cron_id}`, `/threads/{thread_id}/runs/crons`.

**Store (cross-thread memory):** `/store/items`, `/store/items/search`, `/store/namespaces`, plus `/store_put`, `/store_get`, `/store_search`, `/store_delete`, `/store_batch`.

**Event streaming v2:** `POST /threads/{thread_id}/stream/events` (SSE; the request body is an `EventStreamRequest` filter, and closing the connection unsubscribes), `POST /threads/{thread_id}/commands` (JSON command request/response), `WebSocket /threads/{thread_id}/stream/events` (full-duplex commands and events), and `WebSocket /threads/{thread_id}/runs/{run_id}/protocol` (compatibility route).

**Other:** `/mcp` (MCP server endpoint), `/a2a/{assistant_id}` (Agent2Agent JSON-RPC 2.0; push notifications not implemented), with agent cards at `/a2a/{assistant_id}/.well-known/agent-card.json` and `/.well-known/agent-card.json` (and the older `agent.json` names), `/ui/{graph_id}` (Studio UI), `/info`, `/ok`, `/metrics`, `/profile`, `/docs`, `/openapi.json`, `/` (root).

The managed control-plane surface (`/v1/deepagents/*`) is covered in file 05, not here.

## 3. Run and thread semantics (from SDK literals and server code)

- **Thread status:** `idle`, `busy`, `interrupted`, `error`.
- **Run status:** `pending`, `running`, `error`, `success`, `timeout`, `interrupted`.
- **Multitask strategy** (busy thread): `reject`, `rollback`, `interrupt`, `enqueue`.
- **Stream modes** (from `langgraph` core): `values`, `updates`, `messages`, `custom`, `checkpoints`, `tasks`, `debug`. The server's v2 protocol adds `tools`, `lifecycle` and subagent transition events, plus `messages-tuple` and `events` appear in the server code.
- **Durability** (core): `sync`, `async`, `exit`. Controls when checkpoints are written.
- **Run options seen in server code:** `on_disconnect` (12 references), `if_not_exists` (for threads), `webhook` (per run), `stream_mode`.
- **Event-stream capability probe:** the server checks the installed `langgraph` and `langchain-core` symbols at run start and rejects the run early with a clear error if they are missing (for v2 streaming). This means runtime and user library versions must match.

## 4. `langgraph.json` (CLI config) keys

From `langgraph_cli/schemas.py` (`Config` TypedDict):

`python_version`, `node_version`, `api_version`, `base_image`, `image_distro`, `pip_config_file`, `pip_installer`, `source`, `dockerfile_lines`, `dependencies`, `graphs` (name → import path or definition), `env`, `store`, `checkpointer`, `auth`, `encryption`, `priority`, `http`, `webhooks`, `ui`, `keep_pkg_tools`.

Server config (`langgraph_api/config/schemas.py`):

- **`http`**: toggles `disable_assistants`, `disable_threads`, `disable_runs`, `disable_store`, `disable_meta`, `disable_webhooks`, `disable_ui`, `disable_mcp`, `disable_event_streaming`; `cors`; `mount_prefix`; `configurable_headers` and `logging_headers` allow/deny lists; `enable_custom_route_auth`; `middleware_order`.
- **`store`**: `path`, `index` (vector index: `dims`, `embed`, `fields`), `ttl` (`refresh_on_read`, `default_ttl`, `sweep_interval_minutes`).
- **`checkpointer`**: `default` (with `ttl`: `strategy` `delete` or `keep_latest`, `default_ttl`, sweep settings), `custom` (a `path`), and `mongo` (`uri`). Serialization is configurable (`serde`: allowed JSON modules, `pickle_fallback`).
- **`auth`**: `path` (custom auth), `disable_studio_auth`, `allow_langsmith_api_keys`, `openapi` security schemes, `cache` (`cache_keys`, `ttl_seconds`, `max_size`).
- **`encryption`**: `path`, with `aes_json` and `custom` modules present in the package.
- **`webhooks`**: `env_prefix`, `url` policy (`require_https`, `allowed_domains`, `allowed_ports`, `disable_loopback`, `disable_private_ips`, `max_url_length`), `headers`, `allowed_fields`. This is a built-in SSRF guard, which is relevant to our `fetch_url` gap.
- **`priority`**: `path` to a priority-settings module.
- **`ui`**: mapping for custom UI components.

## 5. Execution model (from module docstrings)

- **Python API process** (`langgraph_api/server.py`, `api/*`) handles HTTP and SSE.
- **Executor** (`langgraph_api/executor/`): "Process-isolated graph executor for the Go multi-process queue worker." It connects to an Orchestrator at `LANGGRAPH_ORCHESTRATOR_ADDRESS` over bidirectional gRPC streams, and "intentionally avoids importing the HTTP/SSE server stack."
- **gRPC** (`langgraph_api/grpc/`): servicers for checkpointer, encryption, and ops (assistants, crons, runs, threads, cache). The package has no module docstring, so its exact role is inferred from the names.
- **Cron scheduler** (`cron_scheduler.py`) and **webhook dispatcher** (`webhook.py`): no docstring; inferred from names and the route/config fields.
- **Queue** (`queue_entrypoint.py`, `runtime_inmem/queue.py`): run queue. The in-memory runtime is the local reference.
- **In-memory runtime** (`langgraph-runtime-inmem`): stores state under `.langgraph_api/` using **pickle** files (`.langgraph_ops.pckl`, `.langgraph_retry_counter.pckl`). Intended for development. **Do not reuse pickle for production state**, since loading an untrusted pickle executes code.
- **Tunneling**: `langgraph_api/tunneling/cloudflare.py` exists (local dev tunnel, inferred from name).
- **Telemetry and metrics**: `metrics_otlp.py`, `self_hosted_metrics.py`, `self_hosted_logs.py`, `go_prometheus_metrics.py`, `otel_context.py`, `tracing_session.py`.

## 6. Auth and encryption model

- Studio and API auth can use LangSmith API keys or a custom `auth.path` handler.
- Encryption is opt-in (`encryption.path`), supporting AES-JSON encryption of stored state and custom encryption modules. Middleware (`encryption/middleware.py`) applies it per request.
- Auth middleware (`auth/middleware.py`) and backends `langsmith/` and `noop/` exist (inferred from names).

## 7. SDK (`langgraph-sdk` 0.4.14)

Sync and async clients: `langgraph_sdk/client.py`, `_sync/client.py`, `_async/client.py`. The managed `managed-deepagents` runtime pins `langgraph-sdk>=0.4.13,<0.5`.

## 8. Versions

- `langgraph` 1.2.22; `managed-deepagents` requires `langgraph>=1.2.19,<2`.
- `langgraph-api` 0.18.0 and `langgraph-runtime-inmem` 0.38.0 are the server versions read.
- `deepagents` requires `>=0.7.30,<1` per managed-deepagents.

## 9. What still needs testing

1. Run `langgraph dev` (from `langgraph-cli`) locally with a minimal graph, and check each route in section 2 with `curl`. Not run in this sandbox.
2. Confirm the `on_disconnect` and `multitask_strategy` behavior on the actual server, not just the SDK literals.
3. Check the store TTL sweep and vector index config against a real Postgres or equivalent backend. The in-memory store is pickle-backed and not representative.
4. Confirm the webhook URL policy blocks private IPs and loopback under `disable_private_ips`. Our `fetch_url` lacks this.
5. Test encryption round-trip with `aes_json` and key rotation.
6. Measure executor throughput with multiple executor processes behind the orchestrator (not available in the open packages; only the client side is).
7. Confirm which event-stream protocol version a given `langgraph` version supports (the capability probe fails fast otherwise).

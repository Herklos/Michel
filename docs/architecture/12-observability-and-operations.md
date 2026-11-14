# 12. Observability and operations

## Tracing

- **OpenTelemetry**: Temporal's OpenTelemetry interceptor (`temporalio.contrib.opentelemetry`) propagates trace context through workflows, activities and child workflows **[verify]** the plugin composition with `DeepAgentsPlugin` (its README says the two compose in either order).
- **LangSmith**: the standalone `temporalio-langsmith` package (`from temporalio.langsmith import LangSmithPlugin`) links runs to workflow ids. Use it when LangSmith is the trace store. The Deep Agents plugin's README lists it as a composable plugin.
- Span names carry the thread id (not message content). Message content is recorded only at the level the tenant allows.

## Metrics

| Metric | Source | Alert when |
|---|---|---|
| active threads, running turns | workflow state via a periodic query or search attributes | sudden drops |
| turn latency p50/p95 | turn start and end events | p95 over target for 15 min |
| model call latency and errors by provider | activity metrics | error rate over 5% for 5 min |
| approval wait time | approval events | pending over 24 h |
| budget burn per tenant and bot | usage ledger | 80% of budget |
| sandbox count, create failures, reaper removals | sandbox provider | create failures spike |
| workflow task failures | Temporal metrics | any sustained |
| stuck threads | threads RUNNING with no history event for N minutes | any |

## Search attributes

Set on each workflow for visibility queries in the Temporal UI and in operations: `TenantId`, `BotId`, `ThreadStatus`, `Channel`, `OwnerId`, `ScheduleId`. **[verify]** custom search attribute registration on the target server. Keep the set small; attributes are indexed.

## Logs

Structured JSON logs with `thread_id`, `run_id`, `tenant_id`, `activity_id`, `attempt`. No message bodies or secrets at default level.

## Dashboards

1. Operations: threads, turns, approvals pending, errors, queue depth per task queue.
2. Cost: tokens and spend per tenant, bot and provider; budget burn.
3. Quality: turns per outcome (done, failed, stopped, rejected), tool error rates, approval decision rates.
4. Sandboxes: count, state, age, reaper activity.

## Deployment

| Component | Local | Production |
|---|---|---|
| Temporal | `temporal server start-dev` | self-hosted Temporal (with Postgres persistence and visibility) or Temporal Cloud |
| PostgreSQL | docker compose | managed Postgres, one database per environment |
| Object store | MinIO | S3 or compatible |
| Gateway | `uvicorn grokbot.asgi:app` | container, horizontal replicas |
| Workers | `python -m grokbot.worker` | one container per task-queue group, horizontally scaled |
| Sandbox hosts | local Docker | dedicated hosts or a sandbox provider |
| Telemetry | console | OpenTelemetry collector → metrics and traces backend |

Configuration is environment variables (`grokbot/config.py`). Secrets come from the platform's secret manager, never from the image.

## Versioning and rollout

- **Workflow code changes** use `workflow.patched("change-id")` so running workflows take the old path. Remove the old path after the last old workflow closes (check with a visibility query).
- **Worker build ids** (Temporal worker versioning) route new workflows to new builds while old ones drain. **[verify]** the 1.36.0 API.
- **Dependencies** are pinned together: `temporalio`, `temporalio-deepagents`, `deepagents`, `langchain` family. Any upgrade passes the replay suite (see `13`) before rollout.
- **Database migrations** are forward-only and run before the workers that need them start.

## Backup and recovery

- Postgres: point-in-time recovery; restore drills quarterly.
- Temporal: persistence backups per the Temporal operator guide; the namespace can be restored to a point, and workflows resume from history.
- Object store: versioning on, lifecycle rules per retention.
- Recovery order: database, then Temporal, then workers. Workflows continue from their history; activities that were running are retried.

## Runbooks (to write)

Stuck thread; approval backlog; provider outage (fallback in the gateway, pause in workflows); sandbox host down; budget breach; webhook signature failures; workflow determinism error after deploy (roll back the build).

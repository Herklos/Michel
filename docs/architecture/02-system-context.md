# 02. System context and components

## Context

```text
 people (web, CLI, mobile)     external systems       schedules / events
           │                    (Slack, GitHub,            │
           │                     Linear, webhooks)         │
           ▼                          ▼                    ▼
   ┌───────────────────────────────────────────────────────────────┐
   │  Gateway (FastAPI, stateless)                                  │
   │  auth · signature checks · identity mapping · idempotency      │
   └───────────────┬───────────────────────────────┬────────────────┘
                   │ start / signal / update / query│
                   ▼                                 ▼
   ┌───────────────────────────────┐   ┌──────────────────────────────┐
   │ Temporal service               │   │ PostgreSQL                    │
   │ workflow histories, timers,    │   │ transcript, memory, approvals,│
   │ schedules, visibility          │   │ audit, bindings, usage        │
   └───────────────┬───────────────┘   └──────────────▲───────────────┘
                   │ task queues                       │
                   ▼                                    │
   ┌───────────────────────────────────────────────────┴───────────┐
   │ Workers (Python; deepagents + temporalio-deepagents)            │
   │  thread workflows · subagent workflows · schedule workflows     │
   │  activities: model calls · tools · file ops · sandbox ops ·     │
   │              persistence · channel posts                       │
   └──────┬──────────────────────┬─────────────────────┬────────────┘
          │                      │                     │
          ▼                      ▼                     ▼
   model providers        sandboxes (containers)  object store (S3-compatible)
   (via LLM gateway)      with egress proxy        files, attachments
```

## Components

| Component | Responsibility | State | Scales by |
|---|---|---|---|
| **Gateway** | HTTP API, webhook intake, authentication, input validation, identity mapping, idempotency keys, response shaping | none | replicas behind a load balancer |
| **Temporal service** | durable event histories, timers, signals, updates, schedules, visibility | in Temporal persistence | Temporal's own topology |
| **Thread workflow** | owns one conversation: inbox, turns, approvals, budget counters, stop state | workflow history (small) | one workflow per thread |
| **Subagent workflow** | runs a delegated background task with its own history | its own history | one per task |
| **Schedule workflow** | delivers a scheduled prompt to a thread | none | Temporal Schedule |
| **Activity workers** | run model calls, tools, file and sandbox operations, persistence, posts | none (except sandbox handles) | worker replicas per task queue |
| **PostgreSQL** | system of record for everything a person or auditor reads | durable | managed Postgres |
| **Object store** | large files referenced by key | durable | object store |
| **Sandbox provider** | creates, attaches to and removes sandboxes | sandbox itself | host pool |
| **LLM gateway** (optional) | one place for provider keys, spend policy and fallbacks | per its own system | service |

## Process layout

- `michel-gateway` (1 or more replicas) — FastAPI. **[implemented]** as `michel/gateway.py` and `michel/asgi.py`.
- `michel-worker` per task queue (thread, llm, io, sandbox, maintenance). **[implemented]** as one worker on one queue (`michel/worker.py`); splitting queues is **[designed]**.
- `temporal` (dev server locally; production service separately). **[verify]** against a running server.
- `postgres`, `objectstore` (MinIO for dev), `otel-collector` (optional).

## Trust zones

1. **Public**: gateway endpoints and webhook receivers. Authenticated and signature-checked.
2. **Control**: Temporal service and Postgres. Reachable from gateway and workers only.
3. **Execution**: workers and their activities. Hold provider keys and channel tokens.
4. **Sandbox**: untrusted code. No access to control or execution zones except through the egress proxy.

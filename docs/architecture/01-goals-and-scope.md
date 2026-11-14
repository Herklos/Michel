# 01. Goals and scope

## Goal

A self-hosted, multi-channel **agent runtime**: people and external systems start conversations with named bots. Each bot is a deep agent that plans, uses tools, works in an isolated sandbox, delegates to subagents, remembers across sessions, runs on schedules, and asks before acting on the outside world. The runtime keeps working across crashes, restarts, long waits for human approval, and days-long tasks.

It is the open alternative to hosted products such as Grok Bot, and it borrows the operating model of managed Deep Agents (channels, schedules, layered memory, sandboxes, identity mapping) without depending on the managed service.

## Functional requirements

| # | Requirement | Source of the requirement |
|---|---|---|
| F1 | Conversations per bot, with messages from people and from schedules | Grok Bot, Noodle, Hermes |
| F2 | Agent loop with planning, file tools, shell in a sandbox, web fetch, subagents | Deep Agents |
| F3 | Human approval before any side effect outside the sandbox, with the exact action shown | Noodle, Open SWE, Hermes |
| F4 | Stop, suspend, budget and resume controls per bot and per thread | Noodle |
| F5 | Layered memory: per bot, per person, per thread | Managed Deep Agents, Hermes |
| F6 | Scheduled and event-triggered work, including runtime-created schedules | Managed Deep Agents, Hermes cron |
| F7 | Channels: HTTP first, then Slack, GitHub and Linear through signed webhooks | Managed Deep Agents, Open SWE |
| F8 | Identity mapping from channel senders to users | Managed Deep Agents |
| F9 | Bounded memory with explicit errors; curation of learned skills | Hermes |
| F10 | Each run ends with a visible result or an explicit failure | Open SWE |

## Non-functional requirements

| # | Requirement | Target |
|---|---|---|
| N1 | Durability: no accepted message or approval is lost on process crash | Temporal event history |
| N2 | Long waits: approvals and schedules for days or weeks cost nothing while waiting | Temporal timers and signals |
| N3 | Determinism: the agent loop replays identically | Workflow code has no I/O; model and tool calls are activities |
| N4 | Isolation: a bot cannot read another tenant's data or another bot's files | Namespaces, per-bot workspaces, sandbox per thread |
| N5 | Secrets never in workflow input or history | Worker-side secret store; payload encryption for anything sensitive |
| N6 | Bounded cost: per-bot and per-tenant token and spend limits, enforced before a model call | Budget state in the thread workflow, checked in an activity |
| N7 | Auditability: who asked for what, what was approved, what ran | Append-only audit table |
| N8 | Operability: upgrades without stopping in-flight threads | Temporal worker versioning and `workflow.patched` |

## Out of scope (for now)

- A multi-region active-active deployment.
- Running untrusted code outside a sandbox.
- A consumer chat product. The API and channels are the interfaces.
- Training or fine-tuning models.
- Replacing the Deep Agents harness with a custom loop.

## Assumptions

- A Temporal server is available (dev server locally; self-hosted or Cloud in production).
- Python 3.11 or newer for the workers (the pinned `deepagents` requires it).
- One operator per deployment; multi-tenancy is designed in (namespaces, tenant ids) but not built.

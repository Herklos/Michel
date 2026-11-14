# 01. Goals and scope

## Goal

A **structured agent platform for businesses**. A business describes its processes as **procedures**: ordered steps that agents carry out, with human approvals, conditions, loops and bounded access to the business's tools. Procedures are configured at run time through Temporal workflows, not compiled into the product. Each procedure can be started by a schedule, a webhook, another agent or a person, and runs for minutes, days or weeks.

The product has a familiar chat-first experience, in the style of Grok Bot, for people who talk to a bot. It is built for the Open SWE operating model: agents do work inside a sandbox and report results, with controls around them. Where Open SWE is a coding agent for one team, this platform targets business processes across departments, and it adds what businesses need to govern them: approval policies, enforced limits, and a full audit trail, in the way LangSmith Cloud provides tracing and governance for LangChain applications.

The product has two sides:

- **Admin side.** Defines procedures, bots (agents), tools and connections, triggers, approval policies, budgets and roles. Reviews runs, approvals and the audit log. Publishes versions.
- **User side.** A chat-style interface where people talk to bots, start procedures, see the progress of their runs, and decide approvals they are asked for. Users see only what their role allows.

The runtime is the Temporal + deepagents stack described in `02` to `15`. The admin and user sides are clients of the gateway (`02`).

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
| F11 | Procedures: versioned step graphs (agent, tool, approval, condition, loop, wait, sub-procedure, end), defined as data and validated on publish | Business requirement; Open SWE (configured runs) |
| F12 | Triggers for procedures: schedule, signed webhook, agent or procedure event, manual, channel message | Business requirement |
| F13 | Approval policy per step: when required, who may approve, timeout route, exactly what the approver sees | Noodle, Open SWE; business requirement |
| F14 | Enforcement in the workflow, not in prompts: agents cannot skip steps, widen tools, or change policies | Business requirement |
| F15 | Admin side: define procedures, bots, connections, triggers, policies, budgets and roles; publish versions; review runs | Business requirement |
| F16 | User side: chat with bots, start procedures, follow run progress, decide approvals, within role | Grok Bot (chat UX) |
| F17 | Audit: who defined, changed, started, approved, and what ran, queryable and exportable | LangSmith Cloud (tracing, governance) |
| F18 | Tenant roles: operator, admin, approver, user, auditor | Business requirement |

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
- A consumer product. The target users are employees and teams inside a business.
- Training or fine-tuning models.
- Replacing the Deep Agents harness with a custom loop.

## Assumptions

- A Temporal server is available (dev server locally; self-hosted or Cloud in production).
- Python 3.11 or newer for the workers (the pinned `deepagents` requires it).
- One operator per deployment at first; multi-tenancy is designed in (namespaces, tenant ids) but not built. Hosted or self-hosted is an open decision (`15`).
- Business processes are described by business users with help from admins; they should not need to write code to define a procedure.

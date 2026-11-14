# 14. Architecture decisions

Each record: context, decision, consequences. Status is **accepted** unless marked otherwise.

## ADR-001: Temporal is the durable execution layer

**Context.** Agents wait for hours or days (approvals, schedules, long tasks) and must survive crashes. LangGraph Agent Server packages are Elastic-2.0 (no managed-service use), and the in-memory runtime persists state to pickle files, which is for development only.
**Decision.** Use Temporal for workflows, timers, signals, updates, schedules and child workflows.
**Consequences.** One durable log for conversations; Temporal operations to run; determinism rules for workflow code; the deepagents plugin is pre-release.

## ADR-002: deepagents is the agent harness

**Context.** Planning, files, subagents, human-in-the-loop, skills, memory and summarisation are needed; building them again is a large risk. deepagents is MIT and maintained by LangChain.
**Decision.** Use `deepagents` for the loop and its middleware. Do not build a custom loop.
**Consequences.** Model behaviour follows deepagents releases; upgrades need replay tests; the framework's own assumptions (state-backed files, its checkpointer) apply.

## ADR-003: temporalio-deepagents is the integration

**Context.** Its plugin turns model calls, I/O tools and file operations into activities, and handles the sandbox boundary for the workflow.
**Decision.** Use the plugin; keep our own code to tools, backends, policies and channels.
**Consequences.** Dependence on a pre-release package; mitigated by pinning and by owning the thin layer above it.

## ADR-004: one workflow per thread, turns inside it

**Context.** Turns share context, approvals and the sandbox. A turn-per-workflow model would copy that state.
**Decision.** A thread is one long-lived workflow; each turn is a sequence of steps in it. Subagents are child workflows.
**Consequences.** Histories grow per thread, bounded by continue-as-new. Turn-level isolation comes from activities, not workflows.

## ADR-005: async subagents as child workflows

**Context.** deepagents has async-subagent middleware with its own wire format. Temporal child workflows give durable history, cancellation and retries.
**Decision.** Child workflows, reached through the `task` interface the model already uses. The adapter is ours.
**Consequences.** One more component to write; a clear recovery story. Alternative (deepagents' middleware directly) kept as a fallback. Status: **proposed** until the adapter is tested.

## ADR-006: sandboxes sit behind a provider interface, outside the workflow

**Context.** Code runs in a sandbox; the workflow must stay deterministic and must not hold sandbox state.
**Decision.** Sandbox operations are activities on the `sandbox` queue, through a provider interface; the sandbox id is the only handle in state.
**Consequences.** Provider implementations can change without touching workflows; reconnect logic lives in activities.

## ADR-007: Postgres is the system of record for transcript, memory, approvals and audit

**Context.** People and auditors need to query these; workflow history is not a query store.
**Decision.** Postgres holds them, written by persist activities keyed for idempotency.
**Consequences.** Two sources must not disagree: workflow state keeps references, Postgres holds content. Writes need retries and keys.

## ADR-008: secrets are references, never payloads

**Context.** Workflow history is durable and visible to operators.
**Decision.** Activities read secrets from the worker's secret store by name. Sensitive payloads are encrypted by a payload codec.
**Consequences.** Workers need the secret store; rotation is a worker concern.

## ADR-009: double-texting policies are explicit and per submission

**Context.** Open SWE, Managed Deep Agents and the Agent Server each offer enqueue, interrupt, reject and rollback. The right default differs by channel.
**Decision.** Four policies, enqueue by default, chosen per submission; behaviour defined in `06`.
**Consequences.** Interrupt and rollback need safe points and transcript compensation; tests per policy.

## ADR-010: approvals gate side effects, shown exactly

**Context.** Noodle auto-approves within access; Open SWE and Managed Deep Agents ask people. A silent approval is an unacceptable failure mode.
**Decision.** Side effects outside the sandbox need an explicit decision on the exact action; expiry rejects.
**Consequences.** Some friction; a clear audit trail.

## ADR-011: no Redis, no Kafka, no separate scheduler

**Context.** Temporal provides queues, events and schedules. Adding another service adds failure modes.
**Decision.** Do not add them. Re-open if a measured need appears.
**Consequences.** Fewer moving parts; Temporal capacity planning is the scaling story.

## ADR-012: LangSmith is optional

**Context.** LangSmith gives tracing, evaluation and a gateway. It is a SaaS dependency, and its gateway is beta.
**Decision.** Tracing through OpenTelemetry by default; the LangSmith plugin and gateway are switches.
**Consequences.** The system runs without a LangSmith account; some features (online evaluators) are unavailable without it.

## ADR-013: procedures are the core unit, enforced by a workflow interpreter

**Context.** The product is for businesses that describe their processes and want agents to carry them out. A prompt cannot guarantee that an approval happens, that a loop stops, or that a step uses only its granted tools. Bots alone (free-form agents with schedules) do not express a process.
**Decision.** A procedure is a versioned, validated graph of steps (agent, tool, approval, condition, loop, wait, sub-procedure, end). `ProcedureWorkflow` interprets one pinned version deterministically; agents run only inside agent steps, with a tool grant and an output schema. Approval policy, loop bounds and tool effects are part of the version, set by the operator, not by an agent. Triggers are schedules, signed webhooks, agent events, procedure events, manual calls and channel messages, correlated by a business key.
**Consequences.** The process is enforced by code and is auditable. Authoring is a data problem (schema, validator, editor). The interpreter is a new component to build and test with replay tests. Agents become replaceable inside steps. See `16-procedures.md`.

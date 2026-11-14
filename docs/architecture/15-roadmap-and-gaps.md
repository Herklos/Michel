# 15. Roadmap, gaps, risks and open questions

## Where the code stands

| Area | Designed here | In `grokbot/` today |
|---|---|---|
| Gateway (HTTP API, auth, schedules, approvals, transcript) | yes | **implemented** (offline tests, fake Temporal client) |
| Thread workflow | yes | **implemented** as `BotWorkflow`, with the inbox and approval wait; not run on a server |
| Schedule workflow | yes | **implemented** |
| Agent graph with approval gate | yes | **implemented** (offline tests) |
| Tools with I/O as activities | yes | **implemented** (`fetch_url`, `deliver_channel_message`) |
| Durable workspace backend | yes | **implemented**, but `FilesystemBackend` on the worker is not isolated |
| Transcript and memory in Postgres | yes | not implemented (in-workflow list and snapshot) |
| Double-texting policies | yes | enqueue only |
| Stop, suspend, budgets | yes | not implemented |
| Sandboxes | yes | not implemented |
| Channels other than HTTP | yes | not implemented |
| Approval timeout and expiry | yes | not implemented |
| Child workflows for subagents | yes | not implemented |
| Audit log | yes | not implemented |
| Observability | yes | not implemented |
| Replay tests and time-skipping tests | yes | not implemented (no Temporal server here) |
| Multi-tenancy | yes | single tenant |

## Phases

**Phase 1: run end to end on Temporal.** Start a Temporal dev server; run the worker and gateway; send a message; approve a delivery; check the webhook; add replay and time-skipping tests. Exit: the offline tests and the server tests pass on the same workflow code.

**Phase 2: persistence and a real sandbox.** Postgres for transcript, approvals and audit; continue-as-new with the message snapshot in Postgres; Docker sandbox provider with egress proxy and credential injection; the `sandbox` queue; double-texting `interrupt` and `rollback`; stop; approval timeout.

**Phase 3: channels and memory.** Slack and GitHub channels with signed webhooks, identity linking, bindings and channel posts; bot and user memory layers with limits; skills directory and curator.

**Phase 4: operations.** Budgets and suspend; schedules API with runtime creation and loop guards; child-workflow subagents; observability (OpenTelemetry, search attributes, dashboards); runbooks; multi-queue deployment; worker versioning.

**Phase 5: scale and product.** Tenants and namespaces; evaluations; MCP tool grants with OAuth; a web client; load tests; backup drills.

## Risks

| Risk | Likelihood | Impact | Response |
|---|---|---|---|
| `temporalio-deepagents` changes shape before 1.0 | high | medium | pin; replay tests; own a thin adapter layer |
| Workflow history grows faster than continue-as-new keeps up | medium | high | snapshot in Postgres; history-size metrics; test long threads |
| Interrupt and rollback leave the transcript inconsistent | medium | high | safe points; compensation tests per policy |
| Sandbox isolation weaker than assumed | medium | high | rootless, no privileged; security suite before any untrusted use |
| Side-effect tools repeated after a crash | medium | high | idempotency keys; approvals re-raised when unsure |
| Model provider cost overruns | medium | medium | budgets checked before each call; gateway spend policy |
| Team cannot run Temporal locally on every laptop | low | medium | dev server in compose; documented setup |

## Open questions

1. The project goal document (the Claude artifact referenced in the request) could not be opened from this session. Reconcile these pages with it, especially the scope in `01`, the phases in `15`, and any constraints it sets that are not listed here.
2. Hosted or self-hosted first? This changes the Temporal choice (Cloud or self-hosted) and the sandbox provider order.
3. Which channels come first: Slack or GitHub?
4. Is a web client in scope for phase 1, or only the API?
5. Does the deepagents async-subagent middleware route cleanly to child workflows (ADR-005)? Needs a prototype.
6. Payload codec: is encryption of history required by the data policy? (ADR-008, `11`)
7. Which Temporal version and deployment target (Cloud or self-hosted) are approved?

## What this design does not decide

- Pricing, plans and limits for end users.
- The UI.
- The choice of model providers beyond "through the gateway".

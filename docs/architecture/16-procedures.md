# 16. Procedures

A **procedure** is a business process written down as data: an ordered graph of steps, each step either an agent's work, a deterministic tool call, a human approval, a wait, a branch or a loop. A **procedure run** is one execution of it. Agents do the work inside steps, but the procedure decides what happens next. An agent cannot skip a step, call a tool the step does not grant, or move on without an output that passes the step's schema.

This is the core unit of the product. Bots (`03`) are the agents a procedure uses, and threads (`06`) are the conversations a person may have with a run. Procedures are what the business defines and what runs unattended.

## Why the process is enforced by code, not by prompt

A prompt that says "always ask finance before paying over 5 000" fails when the model forgets, is injected, or reasons around it. Here the rule is data the workflow interprets: the approval step exists in the graph, and the interpreter cannot advance past it without a decision. Model output is validated against a schema before the interpreter reads it. Prompts still describe *how* a step's agent does its work. The procedure definition says *what must happen*.

## Concepts

| Concept | What it is | Lives in | Identity |
|---|---|---|---|
| **Procedure** | a named process with an owner and a business description | Postgres | `procedure_id` |
| **Procedure version** | immutable definition: steps, triggers, policies, bindings | Postgres (JSON, validated on publish) | `procedure_id` + `version` |
| **Trigger** | what starts a run: schedule, webhook, agent or procedure event, manual, channel message | Postgres row; Temporal Schedule for time triggers | `trigger_id` |
| **Run** | one execution of one version, with the business key that correlates it | `ProcedureWorkflow` history; Postgres index | workflow id = `run:{tenant}:{procedure}:{business_key}` when the trigger is correlated, else `run:{tenant}:{procedure}:{run_id}`; reuse allowed after the run closes |
| **Step run** | one attempt of one step in a run | run history; Postgres row for audit | `(run_id, step_id, attempt)` |
| **Agent** | a bot definition with a role, model, instructions and tool grants, used by agent steps | Postgres (bot version) | `bot_id` + version |
| **Connection** | an external tool source: MCP server, HTTP API, or a native tool; holds the secret reference | Postgres (reference) + secret store | `connection_id` |
| **Approval** | a human decision on one step run | Postgres + run state | `approval_id` |

## Definition shape

The definition is data, validated when it is published. The example below is the shape, not final syntax: the step types and fields are what matters.

```yaml
procedure: vendor-invoice-intake
version: 3
business_key: invoice.number            # correlates events to a run
triggers:
  - type: webhook                       # external event, signed (see 09)
    source: email-parser
  - type: schedule
    cron: "CRON_TZ=Europe/Paris 0 9 * * 1-5"
    purpose: sweep unprocessed invoices
steps:
  - id: extract
    type: agent
    agent: invoice-reader@2             # bot version
    tools: [mcp.ocr.read_pdf]           # grant: subset of the agent's tools
    input: { document: trigger.payload.attachment }
    output_schema: schemas/invoice.json # validated before the interpreter continues
    on_error: { retry: 2, then: escalate }

  - id: over_threshold
    type: condition
    expr: steps.extract.output.total > 5000    # CEL, deterministic, no I/O
    then: approve_payment
    else: post_entry

  - id: approve_payment
    type: approval
    approvers: { role: finance-lead }
    show: [steps.extract.output, trigger.payload.attachment]
    timeout: 48h
    on_timeout: escalate                # or reject
    on_reject: end_rejected

  - id: match_lines
    type: loop
    over: steps.extract.output.lines
    max_iterations: 50                  # required; loops without a bound are refused
    body: [{ id: find_po, type: tool, tool: mcp.erp.find_purchase_order, args: { line: item } }]

  - id: post_entry
    type: tool
    tool: mcp.accounting.create_entry   # write effect: approval policy applies
    args: { invoice: steps.extract.output }
    effect: write
```

## Step types

| Type | Runs | Can call | Ends when |
|---|---|---|---|
| `agent` | a deepagents agent, as a child workflow (`AgentStepWorkflow`) | only its granted tools and subagents | output validates against `output_schema`, or retries and error route are exhausted |
| `tool` | one activity (`invoke_tool` through the plugin, or an MCP call activity) | the one tool named | the tool returns, or retries are exhausted |
| `approval` | nothing; the workflow waits on a signal or update | nothing | a decision arrives, or the timeout route runs |
| `condition` | nothing; deterministic evaluation in the workflow | nothing | branch chosen (`then` / `else`) |
| `loop` | the body steps, once per item of `over` | body steps only | items are done, or `max_iterations` is reached |
| `wait` | a timer or a correlated external event (signal) | nothing | timer fires or event arrives, with a timeout |
| `procedure` | a child `ProcedureWorkflow` of another procedure | the child's own grants | child completes |
| `end` | nothing | nothing | run completes with a status (`completed`, `rejected`, `failed`) |

Step statuses: `pending`, `running`, `waiting_approval`, `succeeded`, `failed`, `skipped`, `timed_out`.

## Triggers

| Trigger | Mechanism | Correlation |
|---|---|---|
| **Schedule** | Temporal Schedule (`10`) starts a run; overlap `SKIP` by default | none; each fire is a new run, or a run keyed by a schedule-supplied key |
| **Webhook** | gateway verifies the signature and timestamp, then signal-with-start on the business key | `business_key` from the payload; the delivery id is the idempotency key |
| **Agent** | an agent step emits an event through the `emit_event` tool, which the definition must list | the event names a key the target procedure declares |
| **Procedure** | a `procedure` step, or an end-of-run event another procedure subscribes to | parent run id |
| **Manual** | API or client call | caller-supplied key |
| **Channel** | a message in a bound conversation (`09`) | channel binding |

Signal-with-start is the rule for event triggers: if a run with the business key is open, the event is delivered to it; otherwise a new run starts. Duplicate deliveries of the same event id are dropped, so a webhook retry never starts a second run.

## Approval policy per step

Approval is declared on the step, not decided by the agent. The policy has four parts:

| Field | Meaning |
|---|---|
| `required` | `always`, `never`, or `when: <CEL expression>` (for example `steps.extract.output.total > 5000`) |
| `approvers` | a role, a named user, or a group; the decider must hold it at decision time |
| `timeout` and `on_timeout` | how long to wait; then `reject`, `escalate` (to a second role) or `approve` (only if the operator allows it, and audited) |
| `show` | exactly what the approver sees: the proposed action, bounded arguments, the step output it relies on |

Tool steps with `effect: write` or `effect: external` require an approval unless the procedure version says otherwise. The rule applies to every connection, including MCP tools, so a tool cannot skip it by being new. Read-only tools default to `effect: read` and no approval.

Approval decisions are recorded with the decider's identity and the exact text shown. The first decision wins. A decision after the timeout is refused.

## Conditions and expressions

Conditions use CEL (Common Expression Language): no loops, no I/O, no unbounded recursion, and the same result on every replay. It is evaluated in the workflow, so there is no activity call and no history entry beyond the branch taken. `[verify]` Check that the Python CEL implementation we pick is maintained and that its types match the output schemas.

## Loops and bounds

- Every loop has `max_iterations`. Publishing a procedure without it fails validation.
- A loop body may contain `agent` and `tool` steps. Approval inside a loop is allowed; it is asked per iteration unless the policy says batch.
- A `procedure` step may call another procedure. The call graph must be acyclic at publish time, and nesting depth is capped (default 5).
- Iteration state is in workflow history. Long loops use continue-as-new with the run state moved to Postgres (`08`).

## Enforcement in the workflow

`ProcedureWorkflow` is an interpreter for one pinned version. It has no model code and no I/O. It:

1. Starts with the trigger payload in `trigger.*` and an empty step output map.
2. Walks the graph. For each step it starts the matching child workflow or activity, with the step's grants and the output schema.
3. Validates each output before writing it to `steps.<id>.output`. Invalid output counts as a step failure and follows `on_error`.
4. Waits in `workflow.wait_condition` for approvals and events, with the declared timeout.
5. Records every transition in history and in the audit log (`11`).

An agent step cannot change the graph, add a step, widen its tool grant, or change an approval policy. Those are part of the version, changed only through the operator API, which creates a new version.

## Agents and tools inside a step

- An agent step runs a bot version in deepagents. Its tools are the intersection of the bot's tools and the step's `tools` list. Anything else is not registered with the model at all.
- Subagents are allowed only if the step lists them.
- Tool results are data. They are marked untrusted in the context (`11`), so a page or document cannot direct the next step. The next step is chosen only by the graph.
- MCP connections are bound per tenant. A connection's tool list is fetched when the version is published and pinned into it; a tool added to the server later is not usable until a new version lists it. This prevents silent tool expansion.

## Mapping to Temporal

| Concept | Temporal mechanism | Notes |
|---|---|---|
| Run | workflow `ProcedureWorkflow` | id from the business key for correlated triggers, so signal-with-start reaches the open run; from `run_id` otherwise; reuse policy allows a new run after the old one closes |
| Agent step | child workflow `AgentStepWorkflow` (deepagents) | parent close policy `REQUEST_CANCEL`; its history stays separate |
| Tool step | activity on the `tools` queue | retries per step; non-idempotent tools need an idempotency key |
| Approval | `wait_condition` + signal / update `decide_approval` | update validator checks the approver and the expiry |
| Timeout | `wait_condition(timeout=...)` | no external timer needed |
| Condition | interpreter code, CEL evaluation | no activity |
| Loop | interpreter loop with a counter | continue-as-new past the history threshold |
| Time trigger | Temporal Schedule | `10` |
| Event trigger | signal-with-start | `[verify]` against the Temporal server |
| Sub-procedure | child workflow `ProcedureWorkflow` | depth capped |

## Guards

- A run started by a schedule cannot create schedules or start procedures that create schedules (`10`).
- A run's total cost and duration have a budget (`11`). Exceeding it fails the run with `budget_exceeded` and notifies the owner.
- A run waiting for an approval longer than the approval timeout has a terminal route. No run waits forever.
- Publishing a version runs the validator: reachability, bounded loops, acyclic procedure calls, every write tool behind an approval, every agent tool a subset of its grant, every connection present, every approval with a timeout.

## Example runs

1. **Invoice intake.** The email parser posts a signed webhook. The run starts, the agent extracts fields, the condition routes invoices over 5 000 to finance approval with a 48-hour timeout. On approval, the accounting tool posts the entry (approval already satisfied, so the tool step does not ask again). On timeout, the run escalates to the finance director.
2. **Weekly reconciliation.** A schedule starts a run each Monday. A tool step pulls the ledger through an MCP connection (read only, no approval). A loop over unmatched items (bounded to 200) calls an agent step per item, which proposes a match. Proposals above a threshold need a human; the rest are written.
3. **Customer escalation.** A support thread (a channel binding) hits a keyword. The agent emits `escalation.requested`. The escalation procedure is started with the thread id as its business key. It waits for a manager's decision with a 4-hour timeout, then notifies the customer through the channel.

## Versioning and running runs

- A run pins the procedure version it started with. Publishing a new version affects new runs only.
- A run already waiting at an approval keeps its version. Migrating a run to a new version is an explicit operator action, and it is refused when the step ids it needs no longer exist.
- Temporal worker versioning applies to the interpreter itself (`workflow.patched`); definitions are data and do not need code deploys.

## Relation to the rest of the design

- **Bots** (`03`) become the agents that procedure steps use. A bot alone is still available as a chat assistant.
- **Threads** (`06`) can attach to a run, so a person can talk to the agent of the step that is running. Chat never changes the graph.
- **Schedules** (`10`) are one trigger type among several.
- **Approvals** (`11`) are the same mechanism, now declared per step and bound to roles.
- **Memory** (`08`) is readable by agent steps through the same scopes; a run's own state is in `steps.*`.

## Current code **[designed]**

Nothing in `michel/` implements procedures. The current `BotWorkflow` and `ScheduledTurnWorkflow` deliver messages to one free-form agent. They are the seed of the agent-step runtime and the trigger code, not of the interpreter.

## Open questions

1. Authoring format: YAML/JSON with schema validation first, and a visual editor later? Or a visual editor from the start? The business user is the author, so this matters.
2. Expression language: CEL (proposed) or a smaller custom grammar?
3. Should an agent step run as its own child workflow (proposed) or inside the thread's workflow? The child keeps the step's history separate and lets it run in parallel with other steps.
4. Batch approval for loops: needed in v1, or is per-item approval acceptable?
5. The project goal document was not accessible when this page was written. Check the procedure concept against it.

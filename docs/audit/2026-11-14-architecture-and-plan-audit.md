# Architecture, technical choices and plan: audit

Date: 2026-11-14. Scope: `docs/architecture/` (17 pages), `michel/`, and `docs/spikes.md`, judged against the goal: a structured agent platform for businesses, where **procedures** (versioned step graphs) are the core unit, agents work inside steps, the workflow enforces approvals, limits and tool access, there is an admin side and a user side with a chat-first experience, and the audit is as complete as LangSmith Cloud's.

This audit is a judgement, not a measurement. Where a finding rests on code or a doc, it names the file. Where it rests on my reasoning, it says so.

## 1. Verdict

| Area | Verdict |
|---|---|
| Direction (Temporal enforcing a procedure interpreter, agents inside steps) | Sound. It is the one design where "enforced by code, not by prompt" is true by construction. |
| Evidence | Weak. Nothing has run on a Temporal server. 14 `[verify]` labels remain. The only code is a free-form chat bot, not the product. |
| Scope of the design | Too wide for the goal. About half the pages come from Open SWE's coding-agent heritage and are not on the critical path of a business-process product. |
| Phase order in `15` | Wrong for the goal. Sandboxes, double-texting policies and memory layers come before the interpreter. |
| Enforcement story | Has two real holes (sections 3.1 and 3.2). They sit exactly where the product promises its guarantees. |
| Missing pieces | A read model for the admin and user sides, realtime updates for the chat UI, step-output size limits, CI, and tenant isolation. |

## 2. What is strong

- **The core idea is right.** An interpreter workflow with no I/O, driven by a pinned definition, makes "the agent cannot skip a step" a property of the code (`16`, "Enforcement in the workflow").
- **Labels and honesty.** Every page says what is built, designed or unverified. That made this audit possible.
- **Replay and idempotency are taken seriously** (`13`, `06`), which is where Temporal projects usually fail.
- **Version pinning of tools per procedure version** (`16`, "Agents and tools inside a step") prevents silent tool expansion. This is a better answer than most agent platforms have.
- **Separation of stores** (`08`): references in workflow state, content in Postgres, bytes in the object store.

## 3. Findings, ranked by how much they threaten the goal

### 3.1 Agent steps can bypass the approval policy (design hole)

`16` puts approval on `tool` steps with `effect: write` or `external`. An `agent` step receives a tool grant that is "the intersection of the bot's tools and the step's `tools` list", but the page never says whether that grant may contain write tools. If it can, the agent calls the write tool inside its loop, and the only gate is deepagents' `interrupt_on`. That is a second approval mechanism, with different semantics: no role, no timeout route, no `show` list, no audit shape. The validator rule "every write tool behind an approval" (`16`, "Guards") is also silent on this.

*Consequence:* the product's headline guarantee (F13, F14) holds for tool steps but not for agent steps.
*Recommendation:* decide one rule and write it into `16`. The simplest: **agent steps get read-only tools; every write goes through a `tool` step after the agent proposes it**. If agents must write, map `interrupt_on` to the step's approval policy so there is one mechanism and one audit shape.

### 3.2 Approver identity cannot be checked where `16` says it is checked (design hole)

`16` says the `decide_approval` update validator "checks the approver" and that "the decider must hold [the role] at decision time". `04` says validators "reject without side effects", and workflow code does no I/O. A validator therefore cannot look up a role in Postgres.

*Recommendation:* the gateway authenticates the person, checks the role, and passes a verified identity in the update. The workflow checks the identity against the approver list the version declares (data it already holds). Role changes between request and decision are accepted as a documented limit, or the workflow re-checks through an activity before acting on the decision. Record the rule in ADR-014. Do not rely on the validator for authorization.

### 3.3 The plan builds the wrong things first

`15` orders phases as: run on a server (1), persistence plus sandbox plus double-texting (2), procedures (2b), channels and memory (3). For a business-process product:

- **Sandboxes** matter for coding agents. Most business steps call MCP or HTTP tools. `07` is a large design for a capability the first customer procedure may never need. (My reasoning, not a measurement: the three example runs in `16` need none.)
- **Double-texting with `interrupt` and `rollback`** (`06`) is a chat-bot concern. Procedure runs do not take free-form input mid-step. `06` itself says these need safe-point logic and per-policy tests. That is weeks of work for no procedure benefit.
- **Three memory layers** (`08`) are not needed for a deterministic process. Procedure state is `steps.*`.
- The thing the goal is about, the interpreter, has no code, and it is phase 2b.

*Recommendation:* the plan in section 5.

### 3.4 Nothing has run, and there is no CI

The sandbox blocks the Temporal test server download (`docs/spikes.md`, S-02). The repository has no CI configuration, Dockerfile or compose file (checked with `git ls-files`). So every claim about replay, signal-with-start, approval timeouts and `TemporalBackend` is untested, and nothing stops a regression.

*Recommendation:* the first milestone is a CI job that runs the existing workflow tests against `WorkflowEnvironment.start_time_skipping()` on a runner that can download the server. This one change resolves most of the 14 `[verify]` labels.

### 3.5 No read model for the admin and user sides

F15 and F16 need lists: runs by status, approvals waiting for me, procedures by owner, an audit trail filtered by person. `03` says runs have a "Postgres index", but no page says how it is kept in step with workflow state, and Temporal queries and visibility are poor dashboard sources.

*Recommendation:* adopt the T3 Code shape (`docs/research/peers/01-open-swe-and-t3code-structure.md`, section 3.2): every state transition is an event, a projection writer builds the Postgres read model, and clients read a snapshot plus a cursor. In Temporal terms: the workflow starts a `record_event` activity on each transition. Add a reconciliation job that compares Postgres with workflow visibility.

### 3.6 Audit completeness is eventual, not guaranteed

`11` writes audit records from activities. A transition recorded in workflow history whose audit activity then fails permanently leaves a gap. LangSmith-level audit means auditors can trust that nothing is missing.

*Recommendation:* define the guarantee. Either audit rows are written by an activity with unlimited retries and the workflow does not advance until it succeeds (slower, simple), or a reconciliation job rebuilds missing rows from workflow history (spike).

### 3.7 Step outputs can overrun workflow history

`16` stores each step output in `steps.<id>.output`, in workflow state and history. A document extraction or a ledger pull can exceed Temporal's payload limit (the SDK warns at 512 KiB, `04`). `16` mentions moving run state to Postgres at continue-as-new but sets no per-output cap.

*Recommendation:* add to the procedure schema a maximum inline size per step output. Outputs above it are written to the object store by the step, and `steps.<id>.output` holds a reference. Validate output schemas against the size at publish time.

### 3.8 The authoring decision is the largest unpriced cost

The goal says business users describe processes. `16` defines a YAML step graph with CEL, loops, sub-procedures and approval policies, and leaves the format open (question 1). A visual editor for this is a product in itself. The docs do not weigh building against adopting a standard (BPMN, the CNCF Serverless Workflow specification) or borrowing Temporal's own DSL interpreter sample. (I believe such a sample exists in Temporal's Python samples. I have not checked it. This is spike S-39.)

*Recommendation:* ship schema-first (JSON Schema plus a form-based editor that edits the same data), keep the YAML as the interchange format, and price the visual editor as a separate phase after the first customer procedure runs.

### 3.9 Tenant isolation is weaker than the product implies

`04`: tenants share one namespace in v1 and are separated by task queue and workflow-id prefix. Business customers will ask for isolation. Namespace-per-tenant is "the upgrade path", but a workflow id scheme, client wiring and search attributes chosen now are expensive to change later. Noisy-neighbour effects (one tenant's burst) also share one namespace's limits.

*Recommendation:* put `tenant_id` in every workflow id and every Temporal client call now, behind one factory that can later return a per-tenant namespace client. Decide per-tenant encryption keys with the payload codec (N5).

### 3.10 The chat-first UX has no realtime design

`05` marks streaming as designed. There is no page on how a browser receives tokens, approval requests, or step progress. Temporal does not push. The SDK has a `workflow_streams` module, but its behaviour is untested here. Without this, the "Grok Bot style" experience is not designed.

*Recommendation:* a page for the client protocol: snapshot at a sequence, then a stream of events after it (as T3 Code does), fed by the projection writer from 3.5. Token streaming is a separate, optional channel.

### 3.11 Pre-release dependency at the centre

`temporalio-deepagents` is 0.0.3 and marked pre-release (`05`). The design uses deepagents for every agent step, including steps that are one bounded call with a schema-checked output. deepagents' planning, filesystem and subagents add surface and replay risk for that case.

*Recommendation:* define an `AgentStep` interface (input, tool grant, output schema, result) and implement it first with the simplest loop that satisfies it, behind the same interface deepagents would implement. ADR-013 already says agents are "replaceable inside steps"; the interface makes it true. Use deepagents where a step needs planning or files. Skip async subagents for v1, so ADR-005 does not block anything.

### 3.12 Smaller issues

| Issue | Where | Note |
|---|---|---|
| CEL library choice affects replay | `16` | A library upgrade can change evaluation results and break replay. Pin it and treat it as part of worker versioning. Spike S-13 covers the choice. |
| Two systems of record | `03`, ADR-007 | Postgres and Temporal both hold approvals and runs. Name the reconciliation job and its alert. |
| Self-hosted Temporal in `12` as a default | `12` | A small team should start on Temporal Cloud. Question 2 in `15` is open. State the recommendation. |
| Code and docs disagree on names | `04`, `03` | `BotWorkflow` vs `ThreadWorkflow`, `bot-...` vs `thread:...`. Noted in the pages, but the first procedure code should use the design's names. |
| `fetch_url` allowlist checks hostnames only | `README.md` | Known; DNS rebinding and private addresses are not blocked (spike S-40). |
| No Dockerfile, compose or release process | repo | Needed before any shared environment. |

## 4. Technical choices, one by one

| Choice | Assessment | Keep, change or decide |
|---|---|---|
| Temporal | Right tool: long waits, signals, timers, replay. Costs: determinism rules, operations, payload limits. | Keep. Prefer Temporal Cloud first. |
| Procedure interpreter workflow | Right. Enforcement by code. | Keep. Build it first. |
| deepagents inside steps | Powerful but heavy for bounded steps; pre-release plugin. | Keep behind an `AgentStep` interface (3.11). |
| `temporalio-deepagents` 0.0.3 | Pre-release. | Keep, pinned. Own a thin adapter. Replay test every bump. |
| CEL for conditions | Good fit if a maintained Python library passes S-13. | Decide after S-13. |
| Postgres for transcript, approvals, audit, read model | Right. | Keep. Add the projection and reconciliation design (3.5, 3.6). |
| S3-compatible object store | Right for large outputs. | Keep. Needed earlier than `15` implies (3.7). |
| FastAPI gateway, stateless | Right. | Keep. Generate the OpenAPI schema and a typed client for both UIs. |
| Docker sandboxes, LangSmith sandboxes | Right pattern, wrong priority. | Defer until a procedure needs code execution. |
| No Redis, Kafka or separate scheduler | Right. Temporal covers them. | Keep. |
| OpenTelemetry plus optional LangSmith | Right. | Keep. Declare `opentelemetry-sdk` before use. |
| OIDC for people, signatures for channels | Right. | Keep. Do role checks in the gateway (3.2). |
| Web client stack | Not chosen. | Decide. Both reference projects use TypeScript and React (`docs/research/peers`). |
| Python only | Fine for workers and gateway. | Keep. UI is a separate TypeScript project. |

## 5. Plan to achieve the goal

Principle: **prove the enforcement claim end to end on a real server before anything else, then add surfaces.** Each milestone ends with a demonstrable exit test. Sizes are relative (S under a week, M one to three weeks, L longer), for one or two engineers; they are guesses, not commitments.

| # | Milestone | Content | Exit test | Size |
|---|---|---|---|---|
| M0 | Unblock and fix | CI with the Temporal test server; run the existing workflow tests; fix S-27, S-28, S-29; obtain the goal artifact (S-30); pick one real customer procedure as the acceptance case (use the invoice example if none) | Existing `BotWorkflow` approve, reject and close tests pass on a server in CI; the 14 `[verify]` labels are re-triaged | S |
| M1 | Walking skeleton of the interpreter | Procedure schema and validator; `ProcedureWorkflow` with `tool`, `approval`, `condition`, `end`; definition pinned at run start; approval by gateway-verified identity (3.2); replay tests; no agent yet | The acceptance procedure runs with fake tools. A deliberate attempt to skip the approval step fails. Replay test passes after an interpreter edit | M |
| M2 | Agent step | `AgentStep` interface (3.11); child workflow; output-schema validation; read-only tool grants; one MCP read tool; rule for write tools written (3.1) | An agent step returns a schema-valid result. An agent with a write tool in its grant is refused by the validator | M |
| M3 | Persistence and audit | Postgres: versions, runs, step runs, approvals, insert-only audit, projections (3.5); object store for large outputs (3.7); roles (F18) | The run list and approval inbox come from Postgres. Killing a worker mid-run loses no audit row (3.6) | M to L |
| M4 | Triggers and flow control | Signed webhook intake with signal-with-start and business key; schedules; manual start; loops with bounds; timeouts and escalation routes; budgets | The acceptance procedure starts from a signed webhook; a duplicate delivery does not start a second run; a timeout routes to escalation | M |
| M5 | Admin and user sides, minimal | Client protocol (3.10); run list, run detail with steps, approval inbox, procedure publish by editing the YAML, audit viewer; chat attached to a run | A non-developer completes the acceptance procedure through the UI, including an approval | L |
| M6 | Hardening and multi-tenancy | Payload encryption; worker versioning; OpenTelemetry; tenant factory for per-tenant namespaces (3.9); runbooks; load test | Rolling deploy with a running run; a tenant cannot read another's runs | L |
| M7 | Only if needed | Sandbox provider; memory layers; double-texting `interrupt` and `rollback`; child-workflow subagents; Linear; evaluations; visual editor | Each has its own exit test written when it is pulled in | per item |

Deferred on purpose: everything in M7. The pages stay as design. `15` should be reordered to match, once you agree.

### What I would decide now (needs your answer)

1. Temporal Cloud first, or self-hosted? Recommendation: Cloud.
2. Is the first customer procedure the invoice example? If not, which?
3. Authoring: schema-first with a form editor, visual editor later? Recommendation: yes.
4. Is a free-form chat bot a product on its own (question 9 in `15`)? If not, `BotWorkflow` becomes the agent-step runtime and its double-texting work is dropped.
5. Web client stack. Recommendation: TypeScript and React, generated from the gateway's OpenAPI schema.

## 6. Risks to the plan

| Risk | Likelihood | Why | Mitigation |
|---|---|---|---|
| The server tests reveal that `temporalio-deepagents` does not behave as `05` assumes | Medium | It is 0.0.3 and untested here | M0 before anything else; the `AgentStep` interface limits the blast radius |
| CEL library is unmaintained or its types do not fit | Medium | Unchecked (S-13) | Decide in M1; fall back to a small custom grammar |
| The visual editor is far larger than estimated | High | Unpriced in the docs | Ship YAML plus a form editor first |
| Audit gaps found late | Medium | Completeness is eventual today (3.6) | Design the guarantee in M3, test by killing workers |
| Scope creep from the reference projects | High | Open SWE has 60+ tables and a review pipeline; T3 has 15 providers | The deferral list in M7; add a feature only with a procedure that needs it |
| The goal artifact says something different | Unknown | Never read | M0; reconcile before M1 |

## 7. What this audit did not do

- It did not read the goal artifact (S-30), so scope, naming and constraints in it are unchecked.
- It did not run any workflow on a server.
- It did not price the milestones with data. Sizes are judgement.
- It did not evaluate BPMN, Serverless Workflow or Temporal's DSL sample in depth (S-39).

# Spikes

A spike is a time-boxed experiment that answers one question. It produces a short result (a note, a test, or a decision) and does not ship product code. Each spike below names the question, how to run it, what counts as an answer, and what it blocks.

Status values: **open** (not started), **partial** (some of it done, noted), **done** (answered; result recorded where shown), **blocked** (needs something outside this container).

Time boxes are suggestions, not commitments. Unless noted, a spike ends when its question is answered or its box is spent.

## A. Gates for phase 1 (run end to end on Temporal)

| ID | Question | How to run | Answer looks like | Blocks | Status |
|---|---|---|---|---|---|
| S-01 | Do the primary docs (`docs.temporal.io`, `docs.langchain.com`, `cursor.com`) change any claim in `docs/research/01, 02, 03, 05`? | Re-read the pages now reachable (curl returned 200 on 2026-11-14). Update the notes. Box: 1 day | Each research note lists the re-read date and any changed claim | Confidence in `05`, `13` | open |
| S-02 | Can we run workflows on a Temporal test server here? | `WorkflowEnvironment.start_time_skipping()` downloads a test server, and `temporal server start-dev` needs the CLI. GitHub releases return 403 from this container (checked 2026-11-14). Try a machine where GitHub is reachable, or a CI runner | A passing time-skipping test for `BotWorkflow` (approve, reject, close) | Every `[verify]` label in `04`, `05`, `06`, `16` | blocked |
| S-03 | Does the approval `wait_condition(timeout=…)` return or raise on expiry in 1.36.0? | Time-skipping test: wait 24 h with no decision | The observed result is written into `04` ("Timers") and the approval timeout route is designed to match | Approval timeout (F13) | blocked on S-02 |
| S-04 | Does signal-with-start deliver to a running workflow, and does it start one when none exists? | Client test with `start_signal` on a running and a missing id | Both cases observed; the result replaces the `[verify]` in `04`, `16` | Webhook triggers (`16`), channel binding (`09`) | blocked on S-02 |
| S-05 | Does `BotWorkflow` replay identically after a code change? | Record histories from S-02 runs; replay them after an edit to `workflows.py` | Replay test in `tests/` that fails on a deliberate non-deterministic change | Release gate 2 in `13` | blocked on S-02 |
| S-06 | Does an approval survive a worker restart mid-wait? | Kill the worker while `WAITING_APPROVAL`; restart; decide | Decision accepted after restart; no duplicate tool call | N1 (durability) | blocked on S-02 |
| S-07 | Is `deliver_channel_message` sent at most once across a worker crash after the request left? | Fake HTTP endpoint with a crash injected after send | Count of deliveries is 1 or the risk is written down in `06` | Side-effect rule (`04`, retry table) | blocked on S-02 |

## B. Gates for phase 2 (persistence, sandbox)

| ID | Question | How to run | Answer looks like | Blocks | Status |
|---|---|---|---|---|---|
| S-08 | Does continue-as-new with messages in Postgres keep history within the limit for long threads? | Run 5,000 turns with a small model stub; measure history size per continue-as-new | Threshold chosen and recorded in `06` | Risk "history grows faster than continue-as-new" (`15`) | open |
| S-09 | Does `TemporalBackend("workspace")` work end to end with `FilesystemBackend`? | Run a turn that writes and reads a file, on the server | File persists across turns and across a worker restart | File tools (`05`) | blocked on S-02 |
| S-10 | Which sandbox provider works first here: Docker or LangSmith Sandboxes? | Create, exec and destroy on each. Check that UDP is dropped and an unlisted host is refused | Table of results in `07` | Sandbox phase (`15`, phase 2) | open |
| S-11 | Does the egress proxy inject a credential without the sandbox seeing it? | Sandbox calls a host; inspect the environment and the request | The token is absent from the sandbox's environment and files | Credential rule (`07`, `11`) | open |
| S-12 | Does a Postgres transaction for "events, projections, receipt and outbox" work with the approval and transcript writes? | Prototype the commit path in one transaction (ADR-014) | Atomic commit proven by a test that kills the process mid-write | ADR-014 (`14`) | open |

## C. Gates for phase 2b (procedures)

| ID | Question | How to run | Answer looks like | Blocks | Status |
|---|---|---|---|---|---|
| S-13 | Which Python CEL implementation is maintained, and do its types match JSON output schemas? | Check the package's release date, licence and maintainers. Evaluate `steps.extract.output.total > 5000` on a schema-typed value | A package chosen, or a custom grammar chosen (open question 2 in `16`) | Conditions (`16`) | open |
| S-14 | Does `AgentStepWorkflow` as a child workflow keep its history separate and cancel cleanly with `REQUEST_CANCEL`? | Parent starts a child; cancel the parent; inspect both histories | Child cancelled, history kept, no orphan | Agent step design (`16`, mapping table) | blocked on S-02 |
| S-15 | Is the deepagents async-subagent wire format routable to a child workflow (ADR-005)? | Read `deepagents/middleware/async_subagents.py` in 0.7.38; write a stub adapter that starts a child and returns a task id to the model | Adapter works with a scripted model, or ADR-005 stays proposed with the reason | ADR-005 (`14`), `05` "Async subagents" | open |
| S-16 | How many procedure runs can one worker hold open before the scheduler slows? | Start 10,000 timers and signals on the dev server | A number, recorded in `12` | Capacity plan (`12`) | blocked on S-02 |
| S-17 | Does a typed run catalog, written when a procedure run starts and read per step, keep steps replayable? | Prototype the catalog as a Pydantic model stored in the run's input; replay a run after a catalog change | Catalog stays fixed for a run; a version change does not affect a running run (`16`, "Versioning") | Versioning rule (`16`) | open |

## D. Gates for phase 3 (channels, triggers, memory)

| ID | Question | How to run | Answer looks like | Blocks | Status |
|---|---|---|---|---|---|
| S-18 | Can Slack's signed events be verified and deduplicated with the design in `09`? | Use Slack's documented signing example with a replayed event | Replay rejected; duplicate delivery id dropped | Slack channel (`09`) | open |
| S-19 | Which channel is first, Slack or GitHub (open question 3 in `15`)? | Decision with the user, not a test | Decision recorded as an ADR | Phase 3 scope | open (needs user) |
| S-20 | Do the three memory layers stay within their character limits with explicit errors? | Write past the limit in each layer; check the error the agent sees | Explicit error, no silent truncation (`08`) | Memory rules (`08`) | open |
| S-21 | Can a skill that a schedule references survive the curator? | Curator run on a fixture with an unused, scheduled skill | Skill kept. The rule is ours, not Hermes' (`08`) | Curator (`08`) | open |

## E. Gates for phase 4 and 5 (operations, product)

| ID | Question | How to run | Answer looks like | Blocks | Status |
|---|---|---|---|---|---|
| S-22 | Do OpenTelemetry spans carry the workflow id through `DeepAgentsPlugin` in either order? | Install `opentelemetry-sdk` (not declared yet); run one turn with a collector | Spans from workflow and activity share a trace id | Observability (`12`) | open |
| S-23 | Does `temporalio-langsmith` link LangSmith runs to workflow ids? | Install `temporalio-langsmith`; run one turn | Runs linked, or the plugin is dropped from the design | LangSmith tracing (`12`) | open |
| S-24 | Is the payload codec applied on both client and worker, and does a key rotation keep old history readable? | Encrypt, rotate, read old and new histories | Both readable; rotation procedure written in `11` | Payload encryption (N5, `11`) | open |
| S-25 | What does a connection retry policy with jittered backoff capped at 5 minutes do to the gateway client? | Simulate server restarts in a gateway client test | Clients do not reconnect in lockstep (adapted from T3 Code, `09`) | Gateway client (`09`, `12`) | open |
| S-26 | Can the double-texting race (enqueue, interrupt, rollback during a turn) be checked formally? | Write a small TLA+ model after `docs/tla/SteerRace.tla` in Robin's repo | Model checked; a counterexample or a clean run recorded in `06` | Double-texting policies (`06`) | open |

## F. Bugs found while reading the code (confirm and fix)

These were found by reading the code on 2026-11-14. They are not yet tested.

| ID | Problem | Evidence | Confirm by | Status |
|---|---|---|---|---|
| S-27 | A bot name with a dot or slash creates a bot id that the worker's workspace factory rejects | `gateway.py` builds `bot-{name}-{hex}` with only spaces replaced. `worker.py` `workspace_factory` raises `ValueError` unless the id is alphanumeric with dashes | A test that creates `ops.team` and runs one file operation | open |
| S-28 | Sending a message to a closed bot returns an error, not a clean response | `gateway.py` `send_message` signals the workflow. After `close` the workflow has finished, so the signal fails and FastAPI returns 500 | A test that closes a bot, then posts a message; expect a 409 or 410 | open |
| S-29 | The transcript is capped at 500 items and older items are dropped without any marker | `workflows.py` `MAX_TRANSCRIPT_ITEMS = 500`; `_record` deletes the oldest entries. This is silent truncation, which `08` forbids for memory (and the transcript should not truncate either) | A test that records 501 items and checks that the query shows a truncation marker | open |

## G. Information and decisions needed

| ID | Question | Who | Status |
|---|---|---|---|
| S-30 | Obtain the project goal artifact (`claude.ai/artifact/Hhff31XsAZSJFPar424KwJ`). `read_artifact` returned "not found" on 2026-11-14. Ask the user to share it or paste its text, then reconcile `01`, `15` and `16` | User | open |
| S-31 | Hosted or self-hosted first (open question 2 in `15`) | User | open |
| S-32 | Procedure authoring format: schema first or visual (open question 8 in `15`, question 1 in `16`) | User | open |
| S-33 | Is a free-form chat bot a product on its own (open question 9 in `15`) | User | open |
| S-34 | Set `main` as the GitHub default branch (Settings, Branches). No tool in this session can change repository settings | User | open |

## H. Research notes to write

| ID | Topic | Source | Status |
|---|---|---|---|
| S-35 | Admin side and user side design pages (referenced in `01` and `15`, no page yet) | Goal artifact (S-30) and `docs/research/peers` | open |
| S-36 | Robin's `docs/reference/review-approval-threat-model.md` read in full | `langchain-ai/open-swe` | open |
| S-37 | T3 Connect relay (`infra/relay`) and its trust boundary | `pingdotgg/t3code` | open |
| S-38 | `docs/research/managed-deep-agents/` vendored SDK licence check (`vendor/managed-deepagents-sdk`) before any reuse | `langchain-ai/open-swe` | open |

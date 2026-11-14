# 13. Testing and quality

## Levels

| Level | What it covers | Needs | Status |
|---|---|---|---|
| Unit | pure functions, policies, validators, idempotency, approval rules, budget arithmetic | nothing | **[implemented]** for agent graph, tools, gateway (22 offline tests) |
| Agent graph (offline) | approval pause and resume, rejection, history restore, subagent wiring, with a scripted model | `FakeModel` from the plugin's testing module | **[implemented]** (`tests/test_agent.py`) |
| Workflow (time-skipping) | thread lifecycle, double-texting policies, stop, approval timeout, continue-as-new, schedules | Temporal test server (`WorkflowEnvironment.start_time_skipping`) | **[designed]**; the dev server binary could not be downloaded in the research sandbox, so this runs in CI |
| Replay | the workflow code produces the same commands from recorded histories | histories from real runs, stored as fixtures | **[designed]**; required before every deploy |
| Activity | each activity against real dependencies (Postgres, object store, a Docker sandbox) | containers in CI | **[designed]** |
| Channel and gateway contract | signatures, replay windows, idempotency, payload limits | HTTP client | partly **[implemented]** (gateway) |
| Sandbox security | egress blocked hosts, credential not visible in the sandbox, no host mounts, resource limits | Docker in CI | **[designed]** |
| Prompt-injection suite | tool results with instructions cannot trigger side effects without approval | scripted model and malicious fixtures | **[designed]** |
| End to end | a message through a channel, an approval, a reply, a schedule | full stack in compose | **[designed]** |
| Evaluation of agent behaviour | task success, tool choice, approval rate on a fixed task set | LangSmith evaluators or a local harness | Phase 4 |

## Determinism checks

- Replay tests run on every change to workflow code.
- A lint check forbids `datetime.now`, `random`, `uuid.uuid4`, `os.environ` and direct I/O imports inside workflow modules (outside the deepagents passthrough list).
- Each activity has an idempotency test: calling it twice with the same key has the effect of once.

## Test data

- Scripted model responses for the agent graph, including tool calls, errors and refusals.
- Recorded provider responses (sanitised) for the activity tests.
- Malicious tool-output fixtures for injection tests.

## Coverage targets

- Workflow code: 90% line coverage, plus every branch of the double-texting and approval logic.
- Gateway and channel code: 90%.
- The remainder is measured, not targeted.

## Release gates

1. Unit and offline agent tests pass.
2. Replay suite passes against the previous release's histories.
3. Workflow time-skipping tests pass.
4. Security suite passes.
5. A staging run of one scripted conversation with an approval and a schedule.

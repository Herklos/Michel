# 06. Thread lifecycle

## States

```text
          start
            │
            ▼
   ┌────► IDLE ──submit_turn──► RUNNING ──done──► IDLE
   │        ▲                      │
   │        │                      ├──approval needed──► WAITING_APPROVAL ──decide──► RUNNING
   │        │                      │                              │
   │        │                      │                              └──timeout──► RUNNING (rejected)
   │        └────── resume ◄── SUSPENDED ◄── suspend (operator or budget)
   │                               │
   └──── stop (cancels turn) ──► IDLE (stopped notice)
                    close ──► CLOSED (terminal, workflow returns)
```

## Turn lifecycle

1. **Intake.** The gateway authenticates the caller, checks the idempotency key against Postgres, and sends `submit_turn` (an update). The validator rejects oversize input, a closed or suspended thread, or an exhausted budget. A valid update is recorded in history and returns a `run_id`.
2. **Persist.** The first activity of the turn writes the user message to the transcript (`persist`). Writes are keyed by `run_id`, so a retry does not duplicate them.
3. **Context.** The workflow builds the model input from its snapshot and the bot version (both in state).
4. **Model loop.** deepagents runs. Each model call is an activity; each tool call is an activity or an in-workflow tool.
5. **Approvals.** A tool marked `interrupt_on` pauses the loop. The workflow writes an approval row (`persist`), exposes it through `pending_approval`, and waits. `decide_approval` resolves it and the loop resumes with `Command(resume=…)`.
6. **Reply.** The final message is written to the transcript and posted to the channel (an activity). The run is marked done.
7. **Completion notice.** Whatever happened, the workflow's end-of-turn step posts a result or a failure reply. Open SWE's rule: a run that died never leaves the user silent. **[designed]**.

## Double texting: what happens when input arrives during a turn

Policies are chosen per submission (default per thread). They map Agent Server semantics onto the workflow:

| Policy | Behaviour | Implementation |
|---|---|---|
| `enqueue` (default) | queued; starts after the current turn | inbox queue in state; loop drains it |
| `reject` | refused with a busy status | validator returns busy when `RUNNING` |
| `interrupt` | the current turn stops at its next safe point; progress up to the last completed step is kept; the new input starts | `stop` on the current run, then `enqueue` with the new input |
| `rollback` | the current turn's messages after its start are dropped from the transcript and state, then the new input starts | transcript compensation in `persist` plus a state reset to the turn-start snapshot |

**[designed]** for all four. The current code has only the inbox behaviour (enqueue). Interrupt and rollback need the safe-point logic in `07` and `08`, and a test per policy (see `13`).

## Stop

`stop` cancels the in-flight activity (cancellation type `WAIT_CANCELLATION_COMPLETED` for model calls, so partial output is not written half-way), writes a "stopped by user" entry, and returns the thread to `IDLE`. Sub-agents of the turn receive cancellation. Background sandbox commands started by the turn are killed by the sandbox layer (`07`). **[designed]**

## Suspend and budgets

- **Suspend** (operator or budget): the thread finishes its current turn, then waits in `SUSPENDED`. Queued input is kept. Resume clears the state. **[designed]**
- **Budget exhausted:** the validator rejects new turns. A turn that exhausts the budget mid-way finishes with a notice. The model activity refuses to call the provider once the budget is spent.

## Crash and retry behaviour

| Failure | What happens |
|---|---|
| Worker crashes during a model call | the activity is retried (model call retry policy); the model call is repeated; cost may be counted twice, which the usage ledger records as attempts |
| Worker crashes during a side-effect tool | the activity is retried only if the target honours the idempotency key (`run_id` + tool call id); otherwise the approval is re-raised for a human |
| Gateway crashes during submission | the client retries with the same idempotency key; the update is recognised |
| Temporal service restarts | workflows resume from history; in-flight activities are retried by their workers |
| Thread workflow stuck (no progress) | an alert after a configurable time with no history event while `RUNNING` (see `12`) |

## Continue-as-new

Triggered when `workflow.info().is_continue_as_new_suggested()` is true and the thread is idle.

Carried over (the snapshot, which must stay small):
- thread id, bot version id, tenant id, owner id;
- the sandbox reference (provider id);
- the budget counters;
- the summary pointer and the transcript cursor;
- the status (`IDLE` or `SUSPENDED`).

Not carried: messages. deepagents' message list is written to Postgres by a `persist` activity before the continue-as-new, and restored by the next run with `aupdate_state` (implemented). The current code puts messages in the snapshot as serialised dicts; for long threads that exceeds the payload budget, so the design moves them to Postgres.

## Close and archive

`close` rejects pending approvals, lets the current turn end, unbinds the channel, and ends the workflow. The transcript and audit records stay. The sandbox is released by the reaper (`07`). Archived threads can be read but not resumed. **[designed]**

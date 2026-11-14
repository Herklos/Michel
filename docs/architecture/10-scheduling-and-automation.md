# 10. Scheduling and automation

## Kinds of automation

| Kind | Created by | Mechanism | Example |
|---|---|---|---|
| Declared schedule | operator, in the bot's definition | Temporal Schedule created at deploy | "every weekday at 9" digest |
| API schedule | a user or client through the gateway | Temporal Schedule | "remind me Friday" (one-shot) |
| Runtime schedule | the agent, through a tool | Temporal Schedule created by an activity, under limits | "check the deploy again in 2 hours" |
| Event trigger | a channel or webhook | signal-with-start | "a PR gets a review comment" |
| Self wake-up | the agent, for work it is waiting on | timer in the thread workflow, with a note | "come back to this at 16:00" |
| Procedure trigger | a procedure version's trigger list | Temporal Schedule starts `ProcedureWorkflow` | "sweep unprocessed invoices every weekday at 9" (see `16`) |

Scheduled procedures are the main form of unattended work. Their steps, approval policies and loop bounds come from the procedure version, not from the schedule, so a schedule cannot widen what a procedure may do.

## Temporal Schedules

- Spec: cron (UTC, or a time zone), intervals, or one-shot times. Pause and resume are supported.
- Overlap policy **SKIP** by default: a firing that finds the previous run still going is dropped and recorded.
- Catch-up (misfire) policy: skip missed fires by default; a bot may opt into "run once for the missed window".
- Each firing starts `ScheduleTurnWorkflow`, which delivers the prompt to the thread as a `schedule` sender. The thread is created if it does not exist. A schedule that targets a thread uses the thread's bot version at the time of the firing.
- Schedule metadata in Postgres: owner, bot, thread policy (new thread or the same thread), channel target for results, budget class.

## Limits

| Limit | Default | Why |
|---|---|---|
| runtime schedules per owner per bot | 20, paused included | prevents runaway creation (Managed Deep Agents' number) |
| minimum interval | 5 minutes | protects budgets and providers |
| total schedules per tenant | set by operator | capacity |
| schedule-created schedules | not allowed | loop guard (below) |

## Loop guards

- **A run started by a schedule cannot create schedules** (Hermes' rule: cron sessions cannot create more cron jobs). It can read and pause its own schedule.
- **A run cannot create a schedule that fires more often than its own parent** (not needed while the first rule holds; kept as a check if the rule is relaxed).
- Budget checks apply to scheduled runs exactly as to people's turns.
- Schedules that fail three times in a row pause and notify the owner.

## Schedule results

A schedule's result goes to its target channel conversation when one is set. Otherwise it stays in the thread's transcript. The result is a normal reply, or a notice if the run produced nothing to report (`[quiet]`).

## Background work

Work that needs no model (cleanup, sweeps, polling a status) runs as a scheduled activity or in `MaintenanceWorkflow`, never as an agent turn. This follows Open SWE's rule that timers and periodic work go through one job mechanism, not ad hoc tables.

## Current code **[implemented]**

`POST /v1/bots/{id}/schedules` creates a Temporal Schedule that starts `ScheduledTurnWorkflow`. Overlap policy, misfire policy, runtime-created schedules, limits and loop guards are **[designed]**.

# 08. Memory and state

Three stores, each with one job. The rule: **a fact has one home**. Workflow state holds references and counters; Postgres holds what people and auditors read; the object store holds bytes.

| Store | Holds | Durability | Size per item | Read by |
|---|---|---|---|---|
| Workflow state (Temporal history) | thread status, bot version id, inbox of references, budget counters, pending approval summary, sandbox id, transcript cursor, summary pointer | Temporal persistence | small (tens of KB at most per run) | the workflow only |
| PostgreSQL | transcript, runs, approvals, memory items, audit, usage, bindings, sandboxes, bot versions | database | rows | API, workflows through activities, audit |
| Object store | attachments, tool results over the inline limit, exported transcripts, skill bundles | object store | up to the store's limit | activities by key |

## Workflow state: what is allowed

- Identifiers, enums, counters, timestamps, and references (keys into the other stores).
- The **pending** approval summary: the action name, a hash of its arguments, and a preview of at most a few hundred characters. The full arguments are in Postgres.
- The deepagents checkpoint, rebuilt by replay. Within one run, messages live in the checkpointer; across continue-as-new they are restored from Postgres (see `06`).

Not allowed: message bodies longer than the inline limit, secrets, file contents, provider responses in bulk.

## Transcript

- Append-only table `messages(thread_id, seq, run_id, role, sender, content_ref, created_at)`.
- Writes come from the `persist` queue, keyed by `(run_id, step)`, so retries are idempotent.
- Content up to a limit is inline; larger content goes to the object store and the row keeps the key.
- The API pages through the transcript from Postgres. The workflow never returns the whole transcript.
- Redaction (for example of secrets detected in tool results) happens before the write, in the persist activity.

## Memory layers

Three scopes, each stored in Postgres with versions, and mounted into the agent's filesystem as deepagents routes:

| Layer | Mount | Who reads | Who writes | Default policy |
|---|---|---|---|---|
| Bot (tenant-shared) | `/memories/bot/` | every thread of the bot | the agent, the operator | readable by all callers of the bot; the agent is told not to store per-person detail here |
| User | `/memories/user/` | threads of that user, for that bot | the agent | only for an authenticated person; never for a channel conversation with several people |
| Thread | `/memories/thread/` | the thread only | the agent | deleted with the thread, unless promoted |

Managed Deep Agents, Hermes and Open SWE all converge on this shape. Rules:

- A memory **file** is read once per run and kept as a frozen snapshot for that run (Hermes' pattern: the prompt cache stays stable).
- Each memory store has a **character limit**. A write over the limit returns an explicit error the agent must handle by consolidating (Hermes' pattern). No silent truncation.
- Writes to bot-scope memory can require approval (configurable per bot).
- Memory writes are versioned; `supersede` keeps history and `delete` writes a tombstone.

## Skills

Skills are files in `/skills/` with a `SKILL.md`. Agent-created skills are stored with a usage counter. A curator (`MaintenanceWorkflow`) marks unused skills stale and archives them after a period; skills referenced by any schedule are never archived (Hermes' rule). **[designed]**

## Retention

| Data | Default retention | Notes |
|---|---|---|
| Transcript | 365 days, then export and delete | per tenant |
| Audit | 7 years | append-only, separate schema |
| Memory | until deleted or superseded | tombstones kept 30 days |
| Workflow history | until the thread closes; continue-as-new bounds it | Temporal retention setting |
| Object store | with its referencing row | orphans reaped weekly |

## Migration from the current code

The current `BotWorkflow` keeps a transcript list in state (bounded to 500 items) and messages in the continue-as-new snapshot. Both move to Postgres in the first implementation phase (`15`).

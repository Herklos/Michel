# grokbot

A structured agent platform for businesses. A business defines its processes as
**procedures** (ordered steps that agents carry out, with approvals, conditions, loops
and bounded tool access). Procedures run as Temporal workflows, enforced by code, with
an admin side to configure and audit them and a chat-style user side. Each bot is one
long-lived Temporal workflow that runs a LangChain Deep Agent. The agent plans, delegates to sub-agents, reads
and writes a per-bot workspace, pauses for human approval before side effects, and
survives crashes, restarts and long histories.

Research behind the design, with sources and the gaps: [docs/RESEARCH.md](docs/RESEARCH.md).

## Architecture

```
 channels / clients / cron
          │  HTTP (X-API-Key)
          ▼
 ┌────────────────────┐   start / signal / query / update / create_schedule
 │ gateway (FastAPI)  │ ───────────────────────────────────────────────┐
 └────────────────────┘                                                 ▼
                                                        ┌─────────────────────────────┐
                                                        │ Temporal                     │
                                                        │  BotWorkflow (one per bot)   │
                                                        │   └ Deep Agent (in-workflow) │
                                                        │  ScheduledTurnWorkflow       │
                                                        └──────────────┬──────────────┘
                                                                       │ activities
                                                                       ▼
                                                        ┌─────────────────────────────┐
                                                        │ worker (DeepAgentsPlugin)    │
                                                        │  • LLM calls (model names)   │
                                                        │  • fetch_url (allowlist)     │
                                                        │  • deliver_channel_message   │
                                                        │  • per-bot FilesystemBackend │
                                                        └─────────────────────────────┘
```

Key decisions:

- **Durable loop, side effects in activities.** The agent loop replays inside the workflow. The LLM call, every I/O tool, and every file operation are activities, so a crash retries the step, not the conversation.
- **Human approval.** `deliver_channel_message` is registered with `interrupt_on`. The workflow pauses and exposes the pending action through the `pending_approval` query. A client resolves it through the `decide_approval` update (`approve` or `reject`).
- **Secrets stay on the worker.** Model keys, webhook URLs and fetch allowlists are read from worker environment variables. Workflow input carries only config and messages.
- **Secure defaults.** `FETCH_ALLOWED_HOSTS` is empty, so nothing can be fetched until you allow it. Only `https` URLs are fetched, redirects are not followed, and responses are capped. Outbound channels are named in `CHANNEL_WEBHOOKS`; an unknown name is rejected.
- **Long conversations.** The workflow continues-as-new when Temporal suggests it. The transcript and the agent's message history carry over, restored with `aupdate_state`.
- **Schedules.** `POST /v1/bots/{id}/schedules` creates a Temporal Schedule. Each run sends a prompt to the bot as a normal `schedule` message.

## Layout

| Path | Purpose |
|---|---|
| `grokbot/workflows.py` | `BotWorkflow` (conversation, approvals, continue-as-new) and `ScheduledTurnWorkflow` |
| `grokbot/agent.py` | Builds the Deep Agent: tools, sub-agent, approval policy |
| `grokbot/tools.py` | `fetch_url` and `deliver_channel_message` as activity-backed tools, plus policy checks |
| `grokbot/worker.py` | Worker process and `DeepAgentsPlugin` wiring, including the per-bot workspace factory |
| `grokbot/gateway.py` | HTTP API that maps requests to Temporal operations |
| `grokbot/config.py` | Environment settings |
| `tests/` | Offline tests (no Temporal server or LLM needed) |

## Run it

Requires Python 3.11+ and a Temporal server.

```bash
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"

# 1. Temporal (dev server, local)
temporal server start-dev

# 2. Worker (needs your model provider key, e.g. ANTHROPIC_API_KEY)
export FETCH_ALLOWED_HOSTS=docs.python.org
export CHANNEL_WEBHOOKS='{"ops": "https://hooks.example.com/ops"}'
export WORKSPACE_ROOT=./data/workspaces
python -m grokbot.worker

# 3. Gateway
export GATEWAY_API_KEY=change-me
uvicorn grokbot.asgi:app --port 8000
```

### Example session

```bash
B=http://localhost:8000; H='X-API-Key: change-me'
BOT=$(curl -s -H "$H" -H 'content-type: application/json' -d '{"name":"ops"}' $B/v1/bots | jq -r .bot_id)
curl -s -H "$H" -H 'content-type: application/json' -d '{"sender":"alice","text":"Post a status update to ops."}' $B/v1/bots/$BOT/messages
curl -s -H "$H" $B/v1/bots/$BOT/approval                      # pending approval, if any
curl -s -H "$H" -H 'content-type: application/json' -d '{"decision":"approve"}' $B/v1/bots/$BOT/approval
curl -s -H "$H" $B/v1/bots/$BOT/transcript
curl -s -H "$H" -H 'content-type: application/json' -d '{"name":"morning","cron":"0 9 * * 1-5","prompt":"Brief me on open issues."}' $B/v1/bots/$BOT/schedules
```

## API

| Method | Path | Temporal operation |
|---|---|---|
| POST | `/v1/bots` | start `BotWorkflow` |
| POST | `/v1/bots/{id}/messages` | signal `enqueue_message` (sender allowlist applies) |
| GET | `/v1/bots/{id}/transcript` | query `transcript` |
| GET | `/v1/bots/{id}/approval` | query `pending_approval` |
| POST | `/v1/bots/{id}/approval` | update `decide_approval` |
| POST | `/v1/bots/{id}/schedules` | create Schedule → `ScheduledTurnWorkflow` |
| DELETE | `/v1/bots/{id}` | signal `close` (rejects any pending approval) |

## Configuration

| Variable | Where | Default | Meaning |
|---|---|---|---|
| `TEMPORAL_ADDRESS`, `TEMPORAL_NAMESPACE`, `TASK_QUEUE` | both | `localhost:7233`, `default`, `grokbot` | Temporal connection |
| `BOT_MODEL` | gateway | `anthropic:claude-sonnet-5-5` | Model name stamped into new bots |
| `ANTHROPIC_API_KEY` | worker | — | Model provider key (read by LangChain on the worker) |
| `WORKSPACE_ROOT` | worker | `./data/workspaces` | Per-bot filesystem root |
| `FETCH_ALLOWED_HOSTS` | worker | empty (deny all) | Comma-separated hosts for `fetch_url` |
| `CHANNEL_WEBHOOKS` | worker | `{}` | JSON map of channel name → webhook URL |
| `GATEWAY_API_KEY` | gateway | unset (auth off, dev only) | Required `X-API-Key` header |
| `ALLOWED_SENDERS` | gateway | empty (any) | Comma-separated sender allowlist |

## Tests

```bash
pytest
```

22 tests cover the approval gate (approve, reject, no pre-approval side effects),
history restore after continue-as-new, fetch and delivery policy, and the gateway's
HTTP-to-Temporal mapping (auth, allowlists, update validation, schedules). They run
offline, using a scripted model and a fake Temporal client.

**Not covered here:** actual workflow execution and activity dispatch. The sandbox
had no Temporal dev server. Run an end-to-end check against `temporal server start-dev`
before deploying. The first thing to check: send a message, approve, and confirm the
webhook is hit exactly once.

## Limitations and next steps

- **Pre-release dependency.** `temporalio-deepagents` is 0.0.3 and marked pre-release. Pin it and read its changelog before upgrading.
- **Not yet done:** the streaming topic (`streaming_topic=`) for live token output.
- **SSRF.** `fetch_url` checks the hostname against an allowlist. It does not re-check the resolved IP. Keep the allowlist to public hosts you trust, or add an IP check in `fetch_page_text`.
- **Memory.** The agent's built-in file tools write to the per-bot workspace. There is no long-term memory store across bots yet.
- **Channels.** Only outbound webhook delivery exists. Inbound channel adapters (Slack, Telegram) would call `POST /v1/bots/{id}/messages`.
- **Todos.** Deep Agents' todo list is not carried across continue-as-new. The earlier `write_todos` calls remain in the message history.

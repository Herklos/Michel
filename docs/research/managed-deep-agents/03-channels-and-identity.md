# 03. Channels, identity, and delivery lifecycle

Source: `managed-deepagents` 0.10.4 README sections "Slack channels", "GitHub channels", "Linear channels", "Mapping channel senders to your users", "HTTP channels", "Asking your service what to start", and the signing rules under "HTTP channels". Read 2026-11-14. Channel backends (Trigger Server, GitHub App, Linear app) are hosted by LangSmith; only the client-side declarations are in the package.

## 1. Channel types

| Channel | How messages arrive | Built-in? | Posts replies? |
|---|---|---|---|
| Slack | Trigger Server (LangSmith) | yes, `channels.slack(...)` | text and native (Block Kit) via Trigger |
| GitHub | GitHub App webhook at `<deployment-url>/channels/github/events` | yes, `channels.github(...)` | **Unclear from the README.** The agent acts on GitHub through tools (comments, labels, pull requests, per the README's GitHub section). The `resolve_user` section says "A GitHub channel can't post". Verify before relying on channel replies. |
| Linear | Linear app webhook | yes, `channels.linear(...)` | comments and agent-session replies |
| HTTP | Your own adapter at `/channels/<name>/events` | yes, `channels.http(provider=..., verify=..., parse=..., post=...)` | your `post` callback |

MDA has **no built-in Slack HTTP adapter**. A custom provider (for example Photon) is written as an HTTP channel.

## 2. Slack

- `trigger_mode`: `"mention"` (only @-mentions; new apps default here), `"thread"` (one mention, then all replies in that thread), `"all"` (every message in joined channels). Direct messages always reach the agent. If unset, a deployed agent keeps its mode, except that dropping `"all"` moves to `"mention"`.
- `on_event` maps kinds to handlers: `"mention"`, `"directMessage"`, `"message"`, plus `"interaction"` for clicks on agent-posted buttons. A handler returns the run input, optionally `(input, {"context", "metadata", "webhook"})`. Returning `None` starts nothing. A handler that raises starts nothing and logs without the message text.
- Handlers can be dict literals or endpoint URLs or `httpx.Request` objects (see section 6).
- `multitask_strategy` for a message arriving while the thread is busy: `enqueue` (default), `interrupt` (cancel and keep progress, start now), `rollback` (cancel and discard progress), `reject`.
- `event.actor`: the Slack user, with `team_id`. MDA checks it against the principal Agent Auth signed for the delivery. A Slack Connect guest's own team is not checked.
- `post(message, new_thread=True, run=...)` starts a new top-level Slack thread, optionally starting a run there as the current person. Returns `thread_id` and the message `url`.
- Files: saved to `/workspace/attachments/` (sandbox required). Thread history is scanned up to 5 pages × 100 messages, needing the bot's history scope.
- `on_finish(event, thread, finished)` runs once per message with `finished["type"]` in `run` (status `success`, `error`, `timeout`, `interrupted`), `skipped` (`ignored`, `rejected`), or `failed`.
- Approvals: a run that pauses for approval shows it in a Slack thread; the answer there resumes the run.

## 3. GitHub

- `on_event={"issues.labeled": handler, ...}`. Handler gets `GitHubEvent[payload]` and `GitHubChannelThread`.
- `mda deploy` creates a GitHub App subscribed to the handled events. Agent Auth holds the App key, webhook secret, and bot ID.
- Acting on GitHub uses an App installation token: `connections.get("mda/github-token", {"type": "agent"})`, auto-renewed.
- Acting *as the person* who triggered the event is **not supported yet**; `{"type": "user"}` throws and deploy refuses it.
- A run acts for the GitHub sender's principal `(github, github.com, <numeric id>)`. Bots and orgs run as the channel. Without `resolve_user`, a GitHub sender is not a user of the agent's identity, so user-connected MCP tools are dropped with a warning.
- Issues and pull requests are shared conversations, so the sender gets user memory only where the user memory layer's `allow` opts in.
- `app` argument narrows what the agent can reach; applied on each run.

## 4. Linear

- `channels.linear(app={"teams": ["ENG"]}, on_event={"Issue.update": handler})`.
- Handled event keys: `Issue.create`, `Issue.update`, `Comment.create`, `AgentSessionEvent.created`, `AgentSessionEvent.prompted`. Unknown keys raise.
- Each issue is a conversation; each agent session is another. The reply posts as a comment in the thread of the comment that started the run.
- Signature: `Linear-Signature` verified; deliveries older than one minute rejected.

## 5. HTTP channels (custom adapters)

- `verify(request)` runs first, with the original bytes and headers, and checks the provider signature.
- `parse(request)` returns `{"type": "message", "message": {user_id, thread_id, content, target}, "raw_event"?}`, or `ignore`, or `cancel` (cancels the thread's queued and running runs, keeping progress, and drops messages waiting for it).
- `thread_id` is the stable LangGraph thread UUID. `target` is opaque reply-routing data (for example a Slack channel and thread timestamp), kept private and bound to `runtime.thread.origin.channel.post`.
- `post(message)` receives `HttpChannelPostInput` with `{"type": "content"|"native", "content"|"native", "target"}`, returns `{"id", "url"?}`. A callback error is a delivery failure.
- `reply="none"` disables automatic replies; the agent replies itself.
- Lifecycle hooks: `on_received(target, delivery)` (before anything starts), `on_error(error, target)` (replaces the default failure notice), `on_finish(target, delivery)` with `type` in `run`, `skipped` (`cancel`, `waiting`, `ignored`, `duplicate`, `rejected`, `dropped`), or `failed` (`start`, `retry`, `observe`). `interrupts` lists pending decisions.
- Hooks run in the server process. **A restart loses an in-flight `on_finish`.** The README recommends reconciliation or the run's `webhook` for delivery guarantees.

## 6. Service endpoints (`on_event` as a URL)

A handler can be an HTTP endpoint instead of a function. The channel POSTs `{"event": {"key", "deliveryId", "payload"}, "thread": {"id", "channel", "interrupted"?}}` and starts the run the service returns: `{"input", "context"?, "metadata"?, "webhook"?}`. `null` or HTTP 204 starts nothing.

- Retry: network error, HTTP 429, or 5xx retried up to three attempts with the same `webhook-id`. Other errors fail the handler.
- Timeout: 60 seconds. Response size limit 10 MB. URL must be https, or plain http to loopback only, with no credentials.
- Signing (`MDA_SERVICE_SECRET` in `.env`): Standard Webhooks, HMAC-SHA256 over `id.timestamp.body`, with headers `webhook-id`, `webhook-timestamp`, `webhook-signature`. IDs: `msg_<deliveryId>` for the run call, `msg_<deliveryId>_interrupted` (GitHub), `msg_<deliveryId>_resolve_user`. Secrets are `whsec_` + base64 of 24–64 random bytes; comma-separated lists support rotation. Verifiers reject timestamps older than five minutes.
- Typed request models: `LinearEndpointRequest`, `GitHubEndpointRequest`, `SlackEndpointRequest`, `EndpointAnswer`.
- The README requires answering every `resolve_user` request, even a repeat, because a receiver that dedupes and answers 204 makes the delivery run as the channel's own principal.

## 7. Identity mapping (`identity.py`)

`define_identity(auth=..., resolve_user=...)`. Auth options named in the README: `auth.langsmith_api_key()` (explicit; `mda init` scaffolds it), `auth="backend"`, and the trusted LangSmith/Supabase identity providers under `identity/` (`supabase.py`, `claims.py`, `options.py` exist in the package).

`resolve_user(request)` runs before every channel run or resume with the verified `actor` (or `None`) and the channel name. It returns:
- `{"type": "user", "id": ...}`: run as your user; channels and your backend then share connections and memory.
- `{"type": "identity", "provider", "issuer", "subject"}`: an exact Agent Auth identity.
- `{"type": "reply", "message": ...}`: start nothing and post the message (only when the event would have started a run). Used to ask a stranger to link an account.
- `{"type": "ignore"}`: start nothing; also stops a stranger answering an interrupt.
- `None`: channel default. Each sender runs as their own provider principal.

A channel's own `resolve_user` overrides the identity's. If `resolve_user` raises, nothing starts. Key on `provider` and `id`, never `name` or `email`.

## 8. Security notes stated in the README

- Slack `actor` is Trigger-signed and checked; GitHub `sender` is signed by GitHub.
- `actor` is personal data: MDA does not log it or add it to run metadata unless you do.
- Endpoints receive `event["actor"]` with camelCase keys.
- Tools and MCP servers acting for a user are left out of runs whose sender has no user mapping.

## 9. What still needs testing

1. Build a minimal HTTP channel with signature verification and confirm that a forged `Linear-Signature` or a timestamp older than 60 seconds is rejected.
2. Confirm `on_finish` is lost on server restart, as documented, before relying on it.
3. Test `multitask_strategy` `interrupt` versus `rollback` on a Slack thread with a long run.
4. Verify `resolve_user` returns `reply` for an unlinked account and that the reply does not carry sender identity in the link.
5. Confirm the retry behavior for a 429 and a 5xx from an endpoint handler, including the same `webhook-id`.
6. Confirm `trigger_mode` migration: dropping `"all"` moves an existing deployment to `"mention"`.

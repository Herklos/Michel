# 09. Channels and identity

## Channel model

A **channel** is an external messaging surface that starts turns and receives replies. Each channel has three parts (from Managed Deep Agents): inbound events (verify, normalise, start a turn), outbound messaging (post the reply to the originating conversation), and provisioning (create the provider resources).

| Channel | Inbound | Outbound | Phase |
|---|---|---|---|
| HTTP API | `POST /v1/bots/{id}/messages` with an API key | response body or a callback URL | **[implemented]** (current gateway) |
| Generic webhook | `POST /webhooks/{provider}` with a signature | provider's API via an activity | Phase 2 |
| Slack | Events API and interactivity, signed with the Slack signing secret | Web API (`chat.postMessage`), Block Kit | Phase 2 |
| GitHub | App webhooks, signed with the webhook secret | comments, reviews, labels | Phase 3 |
| Linear | app webhooks, signed | comments, agent sessions | Phase 3 |

## Intake pipeline (gateway)

```text
 request
   │
   ├─ 1. size limit (before parsing)
   ├─ 2. authenticate (API key or OIDC token; provider signature for webhooks)
   ├─ 3. reject replays (timestamp window; delivery id seen before)
   ├─ 4. normalise into InboundEvent {tenant, channel, conversation, sender, text, attachments, delivery_id}
   ├─ 5. resolve identity (sender → user, via bindings)
   ├─ 6. apply channel policy (trigger mode, allowed senders, mention rules)
   ├─ 7. find or create the binding; derive the thread id
   └─ 8. signal-with-start the thread workflow with the turn (update, with idempotency key = delivery id)
```

Steps 1 to 6 are stateless. Step 7 writes a binding row. Step 8 is the only call that reaches Temporal.

## Signatures and replay protection

- **Standard Webhooks** scheme (used by Managed Deep Agents and Open SWE): HMAC-SHA256 over `webhook-id.webhook-timestamp.body`, headers `webhook-id`, `webhook-timestamp`, `webhook-signature`; reject timestamps older than five minutes; the `webhook-id` is the idempotency key.
- **Slack**: signing secret; reject requests older than five minutes.
- **GitHub**: `X-Hub-Signature-256` HMAC over the raw body; the delivery id is the idempotency key.
- Secrets live in the gateway's secret store, never in Postgres in plain text.

## Identity

| Concept | Rule |
|---|---|
| Principal | a user (`user_id`), a service (API key), or a channel (an external sender with no link) |
| Linking | a user links an external account by proving control (OAuth or a one-time code); the link is a binding row with the external id and provider |
| Unknown sender | the policy decides: reply with a link to connect, or ignore. Never run as a stranger |
| Channel-only sender | runs with reduced permissions: no user memory, no user credentials, no user-scoped tools |
| Service | API keys are scoped to a tenant and a set of bots |

Managed Deep Agents' rule is the model: map each verified sender to a user, return a reply for unlinked accounts, and ignore strangers so they cannot answer an interrupt.

## Thread binding

A channel conversation maps to **one active thread**. Slack threads, GitHub issues and Linear issues each map to one. The binding row is `(tenant, provider, external_conversation_id) → thread_id`. Messages from a binding's conversation go to its thread; the thread's workflow id is derived from the binding, so a new binding for the same conversation resumes the same thread after a restart.

Multi-person conversations: the thread records the participants and the owner (the first person). Memory scoped to a user is not used when the sender is not that user.

## Outbound

- Replies are activities on the `io` queue with an idempotency key (`run_id` + step). A retry does not post twice where the provider honours keys; where it does not, the activity records the post id before returning.
- A reply can be suppressed by the agent's `[quiet]` answer (Managed Deep Agents' convention).
- A failure to post is retried; after the limit, the failure is written to the transcript and the operator is alerted. The run is not failed for a missing reply.

## Notices

Events from elsewhere that the thread should know (a schedule fired, another thread changed a shared setting) are written as **notices** in the transcript, not as user messages. The agent's view of a channel conversation must match the channel (Open SWE's rule for thread coherence).

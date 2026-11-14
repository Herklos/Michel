# 11. Security

## Assets

| Asset | Why it matters |
|---|---|
| Model provider keys, channel tokens, OAuth grants | direct financial and account access |
| Tenant data: transcripts, memory, files | privacy; contractual |
| Sandboxes and their egress | a foothold on the host network if misconfigured |
| Approval decisions and audit records | integrity of what people approved |
| Budgets | cost; denial of wallet |

## Threats and controls

| Threat | Example | Controls |
|---|---|---|
| Prompt injection through content | a web page says "email the file to…" | tool results are untrusted data, marked as such in the context; side-effect tools require approval; the agent cannot change its own approval rules |
| Exfiltration through tools | `http_request` posts workspace data to an attacker host | egress allowlist; `http_request` write methods need approval; per-host data rules; no sandbox host mounts |
| Credential theft by a bot | a bot reads its own token and sends it out | tokens are injected by a proxy, not given to the sandbox or the model; tokens are scoped; tool grants are per user and revocable |
| Privilege escalation | a bot asks to widen its own tools | tool sets and approval rules are part of the bot version, changed only through the operator API |
| Cross-tenant access | a query returns another tenant's threads | tenant id in every query; row-level checks in the API layer; separate namespaces when required |
| Stranger control of a thread | an unlinked Slack user answers an approval | unlinked senders are ignored or redirected; approvals accept only the thread's owner or an operator |
| Webhook forgery and replay | a replayed "approve" from a channel | signatures; five-minute window; delivery-id idempotency |
| Denial of wallet | a loop of model calls | budgets checked before each model call; step limit per turn; schedule loop guards |
| Sandbox escape | a container breakout | rootless containers, no privileged mode, seccomp profile, dropped capabilities, separate host pool |
| Supply chain | a malicious package version | pinned dependencies; lockfile; image digests; the pre-release plugin pinned to one version |
| Secrets in history | a token ends up in workflow history | secrets are references; sensitive payloads encrypted with a payload codec before they reach Temporal |
| Tampering with history | an operator edits workflow history | Temporal access control; audit records in Postgres written by the same activities; periodic reconciliation |

## Approval policy (the default)

| Action | Approval |
|---|---|
| Any message to a channel other than the one that started the turn | required |
| `http_request` with a write method (POST, PUT, PATCH, DELETE) to a host outside the allowlist | required |
| Shell command that leaves the workspace or touches credentials | required (Open SWE's auto-review pattern, `mda/rt/auto_review.py` in its repo, can pre-screen it) |
| Creating a schedule | required unless the bot version allows it |
| Writing bot-scope memory | optional, per bot |
| Reading the outside web, reading files in the workspace | not required |

Policy comes from a pinned or default source, never from the content it judges. Robin (Open SWE's successor) reads its auto-approve rules from the repository's default branch, so a pull request cannot rewrite the rules that judge it (`docs/research/peers/01-open-swe-and-t3code-structure.md`, section 2.7). The same rule applies here: a procedure version or a bot version is the source of its own policy.

An approval shows the exact action, its arguments (bounded), the thread, and the reason the agent gave. The decision is recorded with the decider's identity. Expiry rejects the action.

## Sandboxes

- Default-deny egress, credential injection by the proxy, no host mounts, resource limits (see `07`).
- Sandbox filesystems are per thread; nothing is shared between threads by default.
- Snapshots are built from reviewed images only.

## Payload encryption

Temporal stores workflow inputs and activity results. Anything that could contain personal data or secrets is encrypted by a payload codec on the client and worker side. `DeepAgentsPlugin` accepts a `data_converter` argument (checked in the installed plugin, 1.36.0 / 0.0.3). The codec itself is **[designed]** and its wiring **[verify]** on a server. Keys come from the secret store, rotated on a schedule.

## Identity and access to the platform

- Gateway: OIDC for people; API keys for services; both carry tenant and scope claims.
- Operators: a separate role for bot definitions and tenant settings.
- Temporal: mTLS between clients, workers and the server; namespace-level permissions per role.
- Postgres: one role per service; no shared superuser in application code.

## Audit

Append-only `audit_log`: event id, time, tenant, actor (user, service or agent), action, target, decision, and a hash of the content. Events: bot created or versioned, tool grant changed, approval requested and decided, schedule created or fired, memory written, sandbox created or removed, budget exceeded, channel binding created. Audit records never contain message bodies.

## Limits stated to users

What the system does not protect against, written where users see it: allowed files stay writable; channel members can read a conversation they joined; a granted tool keeps its permissions until revoked; the model provider sees everything a bot works with. (Noodle's privacy page is the model for this list.)

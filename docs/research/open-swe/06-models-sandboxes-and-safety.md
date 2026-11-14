# 06. Models, sandboxes, safety, and data governance

Sources: `docs/CUSTOMIZATION.md` (§1 sandbox, §2 model, §3 tools, §6 middleware), `docs/reference/review-approval-threat-model.md`, `docs/reference/auto-approve-rules.md`, `docs/reference/audit-logs.md`, `docs/TRACE_ACCESS.md`, `openswe/sandboxes/*.py`, `openswe/database/migrations`, `langgraph.json`, `mda/rt/*.py` docstrings, `README.md` "Control and safety". Read 2026-11-14.

## 1. Models

**Defaults** (`docs/CUSTOMIZATION.md` §2):
- `LLM_MODEL_ID` and `LLM_REASONING_EFFORT` set deployment defaults. If `LLM_MODEL_ID` is unset, an Anthropic-only deployment (`ANTHROPIC_API_KEY` set, `OPENAI_API_KEY` unset) defaults to `anthropic:claude-opus-5-5`. Everything else defaults to `openai:gpt-6.1-sol`, including deployments with both keys. Default reasoning effort is `medium`.
- Allowed defaults are listed in `openswe/dashboard/options.py`. Unsupported models or efforts raise at startup.

**Model choice** is a `ModelChoice(model_id, kwargs)`. Examples from the guide: `anthropic:claude-opus-5-5` with `max_tokens` 16,000; `openai:gpt-6.1-sol` with `max_tokens` 128,000 and a reasoning effort; `google_genai:gemini-2.5-pro`. OpenAI models use the Responses API on MDA. `make_model` in `packages/runtime-api/src/runtime_api/models.py` is the single place where provider chat models are built, for both the backend and MDA.

**Routing: "Auto"**
- Eligible turns use **Jev** through `langchain-typesafe`'s `TypeSafeClassifier`, model `typesafe/jev-1.13.0`, called through the LangSmith Gateway System One API.
- Jev sees the latest human task text, up to 8,000 characters. Deadline 3 seconds. Confidence below **0.6** falls back to the resolved default. The guide calls the threshold "an initial heuristic, not a calibrated correctness probability."
- Classifier runs are tagged `nostream` so they stay out of the transcript.
- **Model in the opening request:** new Slack threads and routed dashboard threads recognize phrases like "use Opus" or `/model Oppus` with the same classifier. A recognized model is checked for availability and image support, persisted before work starts, and kept for follow-ups. A clearly unavailable model stops the run.
- Model experiments: `openswe/model_routing.py` defines "the model experiment's arms" that set which tier an Auto thread runs on.

**Gateway:** model calls go through the LangSmith LLM gateway. A person's run uses the person's LangSmith login; other runs use the deployment's gateway key (`mda/rt/gateway.py`). `LANGSMITH_GATEWAY_API_KEY` falls back to `LANGSMITH_API_KEY`.

**Reviewer evaluation model:** `claude-opus-4-5` judges reviewer output (`evals/reviewer/judge.py`).

## 2. Sandboxes

**Who creates them.** MDA creates each thread's sandbox when the run starts and replaces it when the agent asks. The backend "never creates a thread's sandbox: it connects to the one MDA opened" (`docs/CUSTOMIZATION.md` §1; `openswe/sandboxes/AGENTS.md`).

**Providers.** The code has **one** provider: LangSmith (`openswe/sandboxes/providers/langsmith.py`, registry in `providers/registry.py`). Searching the repo for Modal, Daytona or Runloop finds only UI "modal" dialogs. Other providers and local execution are described as configurable in the README, but no alternative provider implementation was found.

**Defaults** (from `docs/CUSTOMIZATION.md`):

| Setting | Default |
|---|---|
| vCPUs | 4 (`DEFAULT_SANDBOX_VCPUS`) |
| Memory | 16 GiB |
| Filesystem | 128 GiB (snapshot capacity) |
| Idle TTL | 7,200 s (2 h); 0 disables |
| Delete after stop | 604,800 s (7 days); 0 disables |

**Snapshots.** New sandboxes boot from LangSmith's root snapshot unless the workspace has its own base snapshot. Workspace setup and update scripts receive the selected repositories in `OPENSWE_WORKSPACE_REPOS`. The default snapshot includes the GitHub CLI; agents run `gh`, which uses the LangSmith proxy for credentials. Snapshot building: `scripts/create_sandbox_snapshot.py`, `scripts/list_snapshots.py`.

**Credentials in sandboxes.** GitHub proxy rules are set on each sandbox at creation or reattachment (`docs/CUSTOMIZATION.md`). The proxy token is minted at runtime from the GitHub App installation. "Do not store GitHub access tokens as deployment environment variables."

**Reconnect and loss.** `openswe/sandboxes/connect.py` reconnects by sandbox id. `SandboxGoneError` distinguishes a deleted sandbox (no working tree, so the thread is handed back to MDA) from an unreachable one (not silently replaced). `read_only_backend.py` covers threads that cannot run.

**Bridged sandboxes.** A thread bridged to a person's machine runs commands on that machine (file 05 §7). It is not isolated.

## 3. Shell and file guards

- Shell commands pass **guards** (`openswe/agent_api/shell_guards.py`, endpoint `check_shell`) before running.
- File and shell tools in `mda/rt/file_tools.py` run checks around each call. Commands that may push are checked by approval.
- Large tool results are offloaded to backend files (`mda/rt/offload.py`) rather than the model's context.
- Image reads are validated (`mda/rt/validate_image_reads.py`).
- `expedite_pr_approval` and merges have their own checks (file 04 §5).
- Reviewers "are instructed not to commit or push" (README).

## 4. Auto-review (person's machine)

`mda/rt/auto_review.py` reviews calls on a bridged machine. It uses the same classifier family (Jev). Decisions: allow, refuse, or ask. Prompt families (`mda/prompts/auto-review/`): authorization (`explicit`, `none`), hard-denied, refused, refused-repeatedly, reason, and risk (see file 03 §2). The classifier reads the person's request and the calls made this turn, never tool results or the model's prose, so a tool result cannot argue its way past the check.

## 5. Approval and rule model

- **Human approvals** for risky actions are interrupts in the MDA run; the thread waits on a decision.
- **Workflow approval prompts** "guard detected Git pushes, not every possible shell or API write" (README). This is a stated limit.
- **Auto-approve rules** and **approval modes** (file 04 §3).
- **Stale approvals** and their withdrawal (threat model; file 04 §3).
- **Expedited approvals** and their fingerprint (file 04 §5).

## 6. Audit logs

`docs/reference/audit-logs.md`: `open_swe.audit_logs` (per the doc: `id`, `request_time`, `operation_name`, `operation_succeeded`, `user_id`, `api_key_id`, `workspace_id`, JSONB `enrichments`), insert-only, with no cascading foreign keys so deleting an account does not erase history.

- **Covered:** authenticated dashboard `POST`, `PUT`, `PATCH`, `DELETE`; settings tools (`save_user_settings`, `save_user_instructions`, `manage_feature_flags`, `manage_review_approval_mode`); workspace lifecycle.
- **Not covered:** unauthenticated failures, GET, login/logout, webhook-driven actions, arbitrary shell commands, and tools not in the list.
- **Never stored:** request or response bodies, tool arguments or results, query strings, headers, credentials, exception text. IP addresses are not inferred from forwarded headers.
- **Setting changes:** `settings_scope` and `before`/`after` values for changed fields, with secret-like text values replaced by `[REDACTED]`.
- The doc itself says a "POST" is "API activity, not proof of a committed business mutation."

## 7. Trace access

`docs/TRACE_ACCESS.md`: each run's trace is tagged with `owner_ls_user_id` (the owner's stable LangSmith user id, stored when the thread is created). A LangSmith ABAC condition on `root_run_metadata.owner_ls_user_id` restricts non-admin users to their own traces. Shared threads keep the original owner. Service keys remain privileged, and "service credentials must never be exposed to personal clients." The doc lists a rollout procedure with checks for two non-admin users.

## 8. Encryption and secrets

- Agent Server encryption: `encryption` config (`aes_json` and `custom` modules in `langgraph-api`; file 04 of the managed research).
- Backend encryption helpers: `openswe/encryption.py`.
- Secrets for runs come from Agent Auth or the backend; deployment `.env` holds model keys and the service secret. Do not store GitHub tokens as environment variables.
- `mda/rt/*` never logs personal data: `actor` is "personal data: MDA doesn't log it" (managed docs).

## 9. Threat model in short

From the documents:
- **Stale GitHub approvals** can satisfy required reviews after new code is pushed (threat model). Mitigated by withdrawal, not eliminated; repository rules still matter.
- **Sandboxes have powerful tools and network access.** README: "Use least-privilege credentials, restrict repositories and integrations, and tailor approval policies to your deployment." Local execution "does not provide cloud sandbox isolation."
- **Prompt injection from tool results** is handled in auto-review by excluding tool results from the classifier's input. Not a general defense.
- **Shell and push** approvals are a detection heuristic, not a complete control (README).

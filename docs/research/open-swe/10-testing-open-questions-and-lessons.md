# 10. Testing, open questions, and lessons for our build

## 1. What was and was not verified

| Area | Status |
|---|---|
| Repository structure, file counts, config files | **Verified** from the shallow clone at `42db6cc` |
| Architecture, endpoint contract, run kinds | **Verified** from code and docstrings (Python 3.14 modules that the 3.13 sandbox parser could not read were read as text) |
| Product features and their rules | **Verified** from `docs/` and the code's docstrings |
| API surface | **Verified** names, tags and counts from `swagger.json`; behavior of each route **not** verified |
| Blog posts | **Not verified** against primary text (access declined for `www.langchain.com`). Search summaries only |
| Running the backend, the UI, the CLI, the desktop app or the mobile app | **Not run.** Needs Python 3.14, Node 26, Postgres 16, LangSmith credentials and a GitHub App |
| Test suite | **Not run.** `AGENTS.md` says "Never run the full test suite locally"; this sandbox also lacks Python 3.14 |
| Managed Deep Agents runtime behavior | **Not run.** Documented in files 01–05 of `managed-deep-agents/` |

## 2. What the LangChain docs index shows (`https://docs.langchain.com/llms.txt`)

Read after `docs.langchain.com` was allowlisted. The index is a tree of `_llms/*.txt` files:
- **Agent development lifecycle** (about 1,507 pages): Build (470 pages), Deploy (254), Monitor (705).
- **Build / Python** (238 pages): Overview, **Managed Deep Agents**, **Deep Agents**, LangChain, LangGraph, **OpenWiki**, Integrations, Learn, Reference, Contribute.
- **Products and setup** (227 pages): LangSmith setup, LLM Gateway, No-code agents, Engine, Deep Agents Code.
- OpenAPI specs: the Agent Server spec (`/langsmith/agent-server-openapi.json`), the LangSmith platform spec, and the API host spec (`https://api.host.langchain.com/openapi.json`).

Pages fetched from that index for this research (Markdown):
- `managed-deep-agents-overview.md` and `managed-deep-agents-runtime.md` (see `managed-deep-agents/08-docs-verification.md`).
- `deepagents/overview.md`, `subagents.md`, `backends.md`, `human-in-the-loop.md`, `memory.md`, `skills.md`, `going-to-production.md`, `permissions.md` (downloaded to scratch; used for cross-checks only, not summarized here).

OpenWiki appears as a LangChain product in the docs index. The repo's `openwiki/` directory (53 files: `INSTRUCTIONS.md`, `architecture`, `concepts`, `index.md`, `integrations`, `operations`, `quickstart.md`, `testing`, `workflows`) is probably generated from it by `.github/workflows/openwiki-update.yml`. Not read in this pass.

## 3. Open questions

1. **Is "Robin" the same product as the blog's "Open SWE"?** The repo says so (README links the blog as background). Confirm with the maintainers before citing the blog as Robin's design.
2. **Which sandbox providers exist in practice?** The code has only LangSmith. The blog summary says more. Check whether other providers live in another branch.
3. **Is Redis used?** `docs/INSTALLATION.md` shows `REDIS_URI`; the code has no Redis references. Likely stale docs.
4. **Which of the 309 operations are stable?** Only `swagger.json` names were read.
5. **What does `review-scout` produce end to end?** It plans a PR walkthrough, but the output path was not traced.
6. **How are approvals enforced in practice?** README says push-detection is a heuristic.
7. **What is the managed-runtime dependency for a self-hosted team?** The README says deploying requires Managed Deep Agents, and forking is the alternative. A fork would replace `mda/` with our own runtime (our `michel/`).
8. **Vendored code licensing:** `vendor/` is explicitly unlicensed. Any reuse must go through the MDA SDK's own MIT license (for the Python package) or a new implementation.
9. **`openwiki/` and `trace_flight_*` tables:** not read.

## 4. Lessons for our own build (`michel/`)

These are concrete patterns from this repo that our design does not yet have.

1. **Split the stateful loop from the stateless backend.** Robin's backend answers typed, token-authenticated calls and holds no run state; the runtime owns the loop. Our `BotWorkflow` owns the loop inside Temporal, and gateway calls are already stateless. Making the gateway's contract a typed package shared by workflow and gateway (as `packages/runtime-api` does) would prevent drift.
2. **Build the run context once, at start.** Robin computes a `Catalog` from the backend when a run starts and sends it in context; later calls derive facts from the token. We could compute per-bot policy (allowed hosts, channels, approval rules) at workflow start and pass it as input, rather than reading configuration in activities.
3. **Explicit approval rules read from the default branch.** Robin reads `.open-swe/auto-approve-rules/` from the default branch so a PR cannot change its own judge. The same idea applies to our bot policies: load them from a trusted source, not from the request.
4. **Stale-approval withdrawal.** When a bot's approval no longer matches the state being approved, withdraw it. We have approvals but no invalidation when the proposed action changes. Add a fingerprint of the approved action.
5. **Expedited, bounded approvals.** Robin caps what can be approved in one click (1–20 lines, 25 enforced) and refuses binaries. Our `deliver_channel_message` approval should show the exact message and be bounded in size.
6. **Audit records that say what they do not record.** Robin's audit doc lists coverage and non-coverage explicitly. We should do the same for our approvals and tool calls.
7. **Notices, not silent edits.** Robin posts changes made by other threads as notices so no agent's view diverges from the channel. Our transcript could record the same kind of notice when a schedule or another bot changes shared state.
8. **Run-completion webhook as a guarantee.** Every dispatched run carries a completion webhook that posts a failure reply, so "the run died" is never silent. Our workflow should always end with a reply or an explicit failure status for the sender.
9. **Background work through one job queue.** Robin forbids hand-rolled due-time columns and polling. Our Temporal Schedules and timers play the same role; keep all deferred work in Temporal rather than in ad-hoc tables.
10. **Engineering rules as code.** `AGENTS.md` and CI checks (`check_httpx.py`, `check_langgraph_client.py`, swagger regeneration) enforce conventions. We should add equivalent checks (for example, no secrets in workflow input, no non-deterministic calls in workflow code).
11. **Dashboards that edit settings should also expose agent tools.** Robin requires every setting to have a matching agent tool with the same validation. Our gateway endpoints could have a matching tool for the bot itself.
12. **Plugins with no network.** A sandboxed frame that can reach the backend only through a permissioned API is a strong pattern for user-built UI. Not a near-term need for us.

## 5. Suggested next steps

1. Run the repo's `make dev` locally with Python 3.14 and Postgres to confirm the startup path (needs LangSmith credentials).
2. Read `docs/INSTALLATION.md` in full to list every external credential and GitHub App permission.
3. Read the managed docs for the agent definition and channels (`managed-deep-agents-agent-definition.md`, `managed-deep-agents-channels.md`) and map them to this repo's `mda/`.
4. Trace one `agent` run from `openswe/dispatch.py` through `mda/agent.py` to a tool call, to confirm the endpoint sequence in file 02 §2.
5. Decide which of the lessons in §4 to adopt in `michel/`, starting with items 2, 4 and 8.

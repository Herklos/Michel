# Open SWE (now Robin): research index

Exploration of `langchain-ai/open-swe` (the product is now named **Robin**) and the LangChain blog post about it. Collected 2026-11-14.

Repository read at commit `42db6cc` (2026-11-13), shallow clone at `/home/user/langchain-ai/open-swe`. Blog text was not read: the `www.langchain.com` allowlist request was denied by the user, so blog claims are search summaries checked against the code.

| File | Topic |
|---|---|
| [01-identity-and-history.md](01-identity-and-history.md) | Rename to Robin, status, licensing (including unlicensed `vendor/`), names |
| [02-architecture.md](02-architecture.md) | Two processes (backend and MDA runtime), endpoint contract, run kinds, dispatch, outbox, storage, engineering rules |
| [03-agent-runtime-mda-side.md](03-agent-runtime-mda-side.md) | The `mda/` project: graph, 54 runtime modules, loop, model calls, tools, auto-review, sandbox |
| [04-product-features.md](04-product-features.md) | Features: build, review, approvals, human review, expedited review, merge queue, operate, plugins, governance |
| [05-integrations-and-channels.md](05-integrations-and-channels.md) | GitHub, Slack, Linear, MCP, web tools, the bridge to a person's machine, Claude Code |
| [06-models-sandboxes-and-safety.md](06-models-sandboxes-and-safety.md) | Model defaults and routing (Jev), sandbox facts, guards, audit logs, trace access, threat model |
| [07-data-operations-and-api.md](07-data-operations-and-api.md) | 161 migrations, 80 tables, Makefile, containers, CI, scripts, API surface (253 paths, 309 operations) |
| [08-clients-and-surfaces.md](08-clients-and-surfaces.md) | Dashboard, CLI, shared bridge, desktop, iOS, plugins, Claude Code plugin, evals |
| [09-blog-claims-vs-code.md](09-blog-claims-vs-code.md) | Blog claims checked against the code, with verdicts |
| [10-testing-open-questions-and-lessons.md](10-testing-open-questions-and-lessons.md) | What was verified, the LangChain docs index, open questions, 12 lessons for our build |

## Key findings

1. **The blog post is out of date for the code.** Its multi-agent roles (Manager, Planner, Programmer, Reviewer) are not in the current repo. The current design is three run kinds (`agent`, `reviewer`, `review-scout`) that run on Managed Deep Agents. The blog's supported-sandbox claim (Modal, Daytona, Runloop) is not in this snapshot: only LangSmith is implemented (file 09).
2. **Robin is a product, not a framework.** It has a dashboard, reviews and approvals in Slack, a merge queue, plugins, a desktop app, a CLI, an iOS app, and 309 API operations.
3. **The backend holds all credentials and plans each run; MDA runs the loop.** The contract between them is typed endpoints in `packages/runtime-api` (file 02).
4. **Governance is a first-class design goal.** Auto-approve rules are read from the default branch, approvals are withdrawn when stale, expedited approvals are size-bounded, and audit logs say what they do not record (files 04, 06).
5. **Reuse is restricted.** Robin's code is MIT, but `vendor/` is explicitly unlicensed, and Robin requires Managed Deep Agents to run as shipped.
6. **Some docs are stale.** `docs/INSTALLATION.md` mentions Redis; no code uses it (file 07).

## Access notes

- `docs.langchain.com/llms.txt` was blocked until `docs.langchain.com` was allowed, then read. The allowlist also got `blog.langchain.com` (read via redirect check only).
- `www.langchain.com` was requested for the blog and **denied by the user**. Not retried.
- The GitHub repository needed read access; it was served by the anonymous git proxy after `add_repo` (public repo). The GitHub API stayed blocked for it.
- The docs pages used for verification are in `docs/research/managed-deep-agents/08-docs-verification.md`.

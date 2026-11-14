# 09. Verification, limits, and open questions

## 1. What was verified

| Area | Method | Result |
|---|---|---|
| Product list and page inventory | `llms.txt` indexes read; 266 LangSmith page URLs downloaded as Markdown; titles catalogued | verified (the group counts in file 01 are approximate) |
| Mechanisms described in files 02 to 07 | full reads of the pages listed in each file's Sources line; the rest read by headings only | verified as the docs describe them |
| Release-stage labels | grep across the 266 pages | verified for LLM Gateway (beta), Agent Auth (beta), Sandboxes (GA), Cloud deploy and preview builds (public beta); no label found for Fleet, Engine, tracing core and Prompt Hub |
| API key prefixes | grep in pages | `lsv2_pt_` (personal token) and `lsv2_sk_` (service key) verified; `lsv2_tr_` seen, purpose unread |
| open-swe usage | targeted searches and reads in the clone at `42db6cc` | verified for the file references in file 08 |
| Preview deploy flow | `scripts/deploy_preview.py` and `build_preview_branch.py` read | verified |

## 2. What could not be verified

- **How LangSmith is implemented.** The LangSmith platform (control plane, data plane, sandbox VM technology, gateway and tracing storage, ClickHouse behind filters) is closed. Files 02 to 07 describe behaviour from the docs; the internals are not published. The one open implementation to read is LangGraph's Agent Server (`langgraph-api`, Elastic-2.0), covered in `docs/research/managed-deep-agents/04-platform-agent-server.md`.
- **Live behaviour.** No LangSmith workspace was available, so no sandbox was created, no run traced, and no gateway call made.
- **The full text of 150+ pages.** Most integration pages (about 35 framework trace guides), most Fleet pages and most Engine pages were catalogued by title and description only.
- **Pricing and plan limits.** The pages mention plans but the pricing page was not read.
- **open-swe's preview environment.** The script names a deployment and reads its revisions. Which deployment ID and branch are used is set through environment variables and GitHub secrets not in the repository.

## 3. Open questions

1. What exactly does the Engine's fix-validation step run, and how is "validated" defined?
2. How do the `lsv2_tr_` tokens differ from the others, and where are they used?
3. Does the Sandbox auth proxy's `access_delegation` appear in open-swe? The repository does not show it (checked by search only).
4. The gateway's data protection (redaction) and open-swe's own redaction (`runtime_api` guards) overlap. Which runs first for a model call?
5. open-swe avoids Agent Server crons in favour of its own job queue. Is that a cost, latency or control decision? The repository does not say.
6. Which Agent Server version does open-swe pin? `langgraph.json` has `api_version ">~=0.15.0rc1"`, while `pyproject.toml` pins a dev build of `langgraph-api` (`0.19.0.dev3`) through a constraint.

## 4. Re-check when access allows

- A LangSmith workspace: create a sandbox from a snapshot, add an auth-proxy rule, and check egress on a blocked host.
- A gateway key: send one request through each API format and check the trace fields.
- The full text of the Engine, Fleet and integration pages (their titles are listed in file 01).

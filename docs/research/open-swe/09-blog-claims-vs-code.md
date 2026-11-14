# 09. The blog posts, checked against the code

Two LangChain blog posts are relevant. Only search summaries of them were available, because `www.langchain.com` access was declined (see §1).

## 1. Access status

| Source | Result |
|---|---|
| `https://www.langchain.com/blog/open-swe-an-open-source-framework-for-internal-coding-agents` (the link you gave) | Not read. The host `www.langchain.com` was requested for the allowlist and **denied by the user**. I did not retry or use another route to get it. |
| `https://blog.langchain.com/open-swe-an-open-source-framework-for-internal-coding-agents` | Redirects (301) to the `www.langchain.com` URL above. Not read. |
| `https://blog.langchain.com/introducing-open-swe-an-open-source-asynchronous-coding-agent` | Found by search. Not fetched. |
| `https://docs.langchain.com/llms.txt` | **Read** after allowlisting `docs.langchain.com`. Index only; see file 10 §2. |
| Search snippets (WebSearch, extended mode) | Used for claims in §2. Those claims are secondary summaries, not the posts. |
| Secondary coverage (devops.com, mager.co, tuncer-byte.com, byteiota, getcoai, CO/AI) | Search results only; not read |

Because the primary text was not read, every blog claim below is a summary claim, and the verdict column checks it against the code and docs that **were** read.

## 2. Post A: "Open SWE: An Open-Source Framework for Internal Coding Agents" (the one you linked)

Search summary of this post, with the verdict from code:

| # | Claim (as summarized) | Verdict | Evidence in the repo |
|---|---|---|---|
| A1 | Open SWE is composed on Deep Agents rather than forked from an existing agent | **Consistent** | `pyproject.toml` depends on `deepagents==0.7.35`; `mda/agent.py` builds on `deepagents` middleware; README: "Deep Agents supplies planning, filesystem, shell, skills, and subagent primitives." Note: today the loop runs on Managed Deep Agents, which wraps Deep Agents. |
| A2 | Toolset includes `read_file`, `write_file`, `edit_file`, `ls`, `glob`, `grep`, `write_todos`, `task` | **Partly consistent** | Deep Agents provides these built-in names. `mda/rt/remote_files.py` defines a `FILE_TOOLS` list, and `rt/file_tools.py` wraps the file and shell tools with checks. Exact names in `FILE_TOOLS` were not listed. |
| A3 | A root `AGENTS.md` is read from the sandbox and injected into the system prompt | **Consistent** | `mda/rt/subdir_agents.py` auto-loads applicable `AGENTS.md` files after file reads, from the sandbox. `docs/CUSTOMIZATION.md` has "Using AGENTS.md". The behavior is "after reads," not only at startup. |
| A4 | Sandboxes: Modal, Daytona, Runloop, and LangSmith supported out of the box; custom sandbox backend possible | **Contradicted for this snapshot** | Only `openswe/sandboxes/providers/langsmith.py` exists. The registry lists LangSmith only. No Modal, Daytona or Runloop code. A custom provider is described as configurable in the README, but no second provider implementation exists here. |
| A5 | Code is on GitHub at `langchain-ai/open-swe`; hosted version at swe.langchain.com | **Consistent (repo); not verifiable (hosted)** | Repo confirmed. The hosted URL is not in the repo; the README points to the managed runtime instead. |
| A6 | Hosted version requires an Anthropic API key | **Unverified** | No hosted-service code in this repo. Defaults in `docs/CUSTOMIZATION.md` are Anthropic for Anthropic-only deployments and OpenAI otherwise. |
| A7 | MIT-licensed | **Consistent for Robin's code; qualified** | `LICENSE` is MIT. `vendor/README.md` says vendored code is not licensed by the repo. |
| A8 | Motivation: Stripe (Minions), Ramp (Inspect), Coinbase (Cloudbot) built similar internal agents | **Not checked** | Claim about other companies, not in the code. |

## 3. Post B: "Introducing Open SWE: An Open-Source Asynchronous Coding Agent" (August 2025, per secondary coverage)

Search summary of this earlier post, with verdict:

| # | Claim (as summarized) | Verdict | Evidence |
|---|---|---|---|
| B1 | Multi-agent architecture with **Manager, Planner, Programmer and Reviewer** roles | **Not present in current code** | Searching the repo for `Programmer` finds 0 matches; `Manager` finds 0 matches in `openswe/` and `mda/rt/`. "Planner" appears in five files, but only as the PR-walkthrough planner (`openswe/walkthrough/planner.py`), not as an agent role. The current design has three run kinds (`agent`, `reviewer`, `review-scout`) and subagents (`general-purpose`, `reviewer`). |
| B2 | The Reviewer checks outputs before any pull request is created | **Not supported as stated** | The reviewer is a run kind that acts on pull requests (`reviewer` graph; `review_scout` runs on PRs; events include `pull_request.opened`). The repo has no reviewer step described as gating PR creation. The agent opens PRs itself (`open_pull_request` tool). |
| B3 | Accepts new requests or changes mid-execution (async) | **Consistent** | `openswe/dispatch.py` defaults to `multitask_strategy="interrupt"`: a follow-up halts the active run and resumes with full history. The MDA run takes follow-ups from the inbox before each model call (`docs/CUSTOMIZATION.md` §6). |
| B4 | Built on LangGraph and LangGraph Platform; LangSmith for debugging and evaluation | **Consistent** | `langgraph.json`, Agent Server, LangSmith tracing, reviewer eval with LangSmith datasets (`evals/reviewer/`). |
| B5 | Hosted version at swe.langchain.com; an Anthropic key is enough to start | **Unverified** | Not in this repo. |
| B6 | Fully open source and extensible | **Consistent, with limits** | MIT for Robin's code. Contribution policy: "not accepting issues or external contributions at this time" (README). Vendored code is not licensed. |

## 4. What changed between the two posts (from the repo)

- Multi-agent roles (Manager, Planner, Programmer, Reviewer) were replaced by **run kinds plus subagents** on a managed runtime.
- The product grew from "a coding agent that opens PRs" to a **factory** with reviews, human approvals in Slack, merge queues, plugins, and a dashboard (`README.md`: "Robin turns engineering work into a repeatable system").
- The name changed from Open SWE to **Robin**. Identifiers keep `open-swe`.
- The runtime changed from the LangGraph Agent Server running the code itself to **Managed Deep Agents** running the loop, with the backend answering calls (file 02).

The repo's own README links to the original announcement as "background on the internal coding-agent framework" at `blog.langchain.com`, so the two posts are the same project at different stages. Secondary sources (search summaries) date the first post to August 2025 and the second to March 2026; those dates are not verified.

## 5. What to take from this

- Claims about **architecture** in the blog summaries are out of date. Use the repo.
- Claims about **supported sandboxes** and **hosted access** need the primary post or the hosted service to confirm.
- The most useful reference is the repo's `AGENTS.md`, which documents the design rules.

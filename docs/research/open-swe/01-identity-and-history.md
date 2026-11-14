# 01. Identity, naming, license, and status

Sources: repository `langchain-ai/open-swe` at commit `42db6cc` (committed 2026-11-13), cloned shallow to `/home/user/langchain-ai/open-swe` (read-only). Read 2026-11-14.

## 1. The repository is now "Robin"

- The README title is **Robin**: "An open-source software factory built on Deep Agents by LangChain."
- `pyproject.toml` names the package `open-swe-agent` with description "Robin Agent - Python agent for automating software engineering tasks".
- `AGENTS.md` says: "The product is Robin: name it that in new prose, comments, prompts... 'Open SWE' survives only in existing identifiers (`open-swe`, `openswe`, `open_swe_notice.`); don't rename those in passing."
- The repository name, the Python package (`openswe/`), the graph names and the Docker image are still `open-swe`. Expect both names.

**Implication for research:** the blog post you linked describes "Open SWE". The code you can read today is the larger Robin product built on the same idea.

## 2. Status and contribution policy

From the README (verbatim fragments):
- "**Under active development.** Expect breaking changes and rough edges. We're not accepting issues or external contributions at this time. You're welcome to explore and fork the code, but correctness, stability, and compatibility are not guaranteed."
- "Deploying it as is requires [Managed Deep Agents]..., which runs its agent; without it, we recommend forking and adapting the code to your own runtime."

So the runtime is not self-contained: the agent loop is run by the managed product. Running it yourself means replacing that part.

## 3. License

- Robin's own code: **MIT** (`LICENSE`; `pyproject.toml` `license = { text = "MIT" }`).
- `vendor/` is **not** covered. `vendor/README.md` says: "Vendoring grants no license. The code in this directory is copied here only so this repository can build and run it. Neither Open SWE's MIT License nor the code's presence in this repository licenses it to anyone."
- The vendored code is the Managed Deep Agents SDK (Rust `mda` CLI source plus the `managed-deepagents` Python runtime) and `langchain-quickjs`. Treat both as "all rights reserved by their owners" unless their upstream licenses say otherwise. The MIT `managed-deepagents` package on PyPI (file 01 in the managed research) is a separate, licensed copy.

## 4. Who builds it

- Maintained by LangChain (`LICENSE`, `claude-code-plugin` author "LangChain").
- The repo ships `CLAUDE.md`-style agent guidance (`AGENTS.md`) and `.agents/`, `.claude/` skill directories, meaning it is developed with coding agents.
- Commit history in the shallow clone is one commit; full history was not fetched.

## 5. Names and surfaces seen in the repo

| Name | Where | Meaning |
|---|---|---|
| Robin | README, UI, CLI (`robin`), desktop app, iOS app, Claude Code plugin | The product |
| `oswe` | CLI README | Legacy CLI name, still installed by the cask |
| `open-swe` | `langgraph.json` graph prefix, Docker image, `open-swe-runtime-api`, `open-swe-dashboard` | Identifier kept for compatibility |
| `openswe/` | Python backend package (about 850 `.py` files, 51 subpackages) | The backend |
| `mda/` | Python project deployed to Managed Deep Agents | The agent runtime |
| `Robin Agent` | `pyproject.toml` description | Display name |

## 6. Sources and access for this file

| Source | Access | Used for |
|---|---|---|
| `README.md`, `AGENTS.md`, `LICENSE`, `pyproject.toml`, `vendor/README.md` | local clone | all sections |
| `https://raw.githubusercontent.com/langchain-ai/open-swe/main/README.md` | direct (200) | cross-check |
| `https://github.com/langchain-ai/open-swe` and `api.github.com` | 403 until the repo was attached for read; then clone via git proxy | clone |
| Blog post: `https://www.langchain.com/blog/open-swe-an-open-source-framework-for-internal-coding-agents` | blocked: `www.langchain.com` denied by user (see 09) | search snippets only |

# 01. Hermes Agent (Nous Research): overview, releases, and versions

Sources: `https://hermes-agent.nousresearch.com/` (site, HTTP 200), `/llms.txt` and `/docs/llms.txt` (index), `/llms-full.txt` (full docs, 6.3 MB), `/compare.md` and `/compare/*.md`, `https://nousresearch.com/releases` (HTML, 1.1 MB, parsed), and the source repository `https://github.com/NousResearch/hermes-agent` (shallow clone, HEAD `2026-11-13`, commit subject "fix(install-e2e): ..."). Read 2026-11-14.

## 1. What it is (the project's words)

"Hermes Agent is the open-source, self-hosted AI agent built by Nous Research. It runs on your own machine or server, keeps persistent memory across sessions, writes its own reusable skills, and can be reached from Telegram, Discord, Slack, WhatsApp, Signal, email, and the CLI. It is free under the MIT license." (`llms.txt`)

Interfaces (site and docs): command-line app (`hermes`), TUI (`hermes --tui`), native desktop app (macOS Apple silicon, Windows, Linux), web dashboard (`hermes dashboard`), a browser workspace (`hermes webapp`), and a messaging gateway.

Hosting options: self-hosted (Linux, macOS, WSL2, native Windows, Android via Termux, Nix), or **Hermes Cloud** (paid; "every paid Nous Portal plan includes one Hermes Cloud agent"). Models: any OpenAI-compatible API, local models, or a **Nous Portal** login for hundreds of models and hosted tools.

## 2. Versions and releases (verified)

- **Source versioning:** git tags use a calendar pattern, for example `v2026.8.19`, `v2026.9.7`, `v2026.9.24`. The repository has **250** release tags. The latest in sorted order is **`v2026.9.24`**. `pyproject.toml` declares `version = "0.0.0"` as a placeholder, so the tag is the real version.
- **Nous releases page** (`nousresearch.com/releases`): shows 9 of 43 items and says "Last release · February 25, 2026", which lists **Hermes Agent** as an AGENT release on 02/25/26. That page catalogues models, papers and datasets too (Hermes 4, NousCoder-14B, Nomos 1, Psyche, Atropos). It is **not** the agent's changelog and is stale for the agent (tags run to September 2026).
- **Skill-pack version in your skills repo:** the `hermes-profiles` skill is version 1.46.0 and mentions "v0.23 hearth gateway". That is a skill version and a product milestone name, not a tag in this repository. Do not confuse the two.

## 3. Positioning and comparisons (vendor claims)

Nous's comparison pages make claims about 9 products: OpenClaw, ChatGPT dots, Muse, Grok Bot, Claude Cowork, Manus, Claude Code, Codex, OpenCode. Their own summary table lists "Open source", "Runs on", "Models", "Chat apps", "Learns from use", "To start". Each comparison says "Sources checked 2026-11-09". These are vendor-authored claims and were not verified (see file 05).

## 4. Source-code footprint (verified in the clone)

| Measure | Count | Note |
|---|---|---|
| Files (excluding `.git`) | 25,745 | whole repo |
| `tools/*.py` | 310 | tool modules |
| `gateway/platforms/` (non-`__` files) | 50 | core ingress adapters and shared helpers; most chat platforms are plugins instead (24 under `plugins/platforms/`) |
| Bundled skills (`SKILL.md` under `skills/`) | 44 | the default catalogue |
| Optional skills (`optional-skills/`) | 141 | installable |
| `plugins/` directories | 24 | general, memory, context engine, platforms, dashboard, cron providers, and others |
| `cron/` modules | about 60 | scheduler, delivery, recovery, jobs |
| `hermes_state*.py` modules | about 60 | session storage, FTS, migrations, locking |
| `hermes_cli/` files | 698 | CLI subcommands and runtime |
| Test files (`test_*.py`) | 8,057 | includes many small suites |
| Apps | `apps/` (`bootstrap-installer`, `desktop`, `shared`) and `web/` (dashboard), `ui-tui/`, `tui_gateway/` | |

The docs' "70+ tools, 28 toolsets" claim (architecture page) was not reconciled: `toolsets.py` gives about 61 named entries by a rough pattern count. Treat the exact toolset number as unverified.

## 5. Where it runs (site and install docs)

Linux, macOS, Windows (native and WSL2), Android (Termux), Nix/NixOS, Docker and a Docker Compose stack (`docker/`, `docker-compose.yml`, `docker-compose.windows.yml`). Install scripts: `setup-hermes.sh`, `setup-hermes.ps1`.

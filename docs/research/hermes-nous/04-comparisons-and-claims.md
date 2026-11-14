# 04. Hermes's comparison pages, checked

Sources: `https://hermes-agent.nousresearch.com/compare.md` (8,277 bytes) and the Markdown copies `compare/grok-bot.md` (14,725 bytes), `compare/claude-code.md` (13,691 bytes), `compare/openclaw.md` (15,065 bytes). Read 2026-11-14. The pages say their sources were "checked 2026-11-09". The cited sources themselves were not fetched. Everything below is a vendor claim unless marked verified.

## 1. The field table on `compare.md`

Ten products compared by the vendor: Hermes Agent, OpenClaw, ChatGPT dots, Muse, Grok Bot, Claude Cowork, Manus, Claude Code, Codex, OpenCode. The table is by the vendor; competitor cells are not sourced in the file.

## 2. The Grok Bot comparison (`compare/grok-bot.md`)

Its key claims and how they hold up:

| Claim | Status |
|---|---|
| Grok Bot "picks a model for each request, and its docs say you cannot choose, request or block one" | **Not verified** here. The page attributes it to Cursor's help centre. |
| Grok Bot usage is a "weekly pool, then top-ups" on The X Subscription (Premium, Super, Ultra) | **Not verified** here. The page cites a usage-reset history on X posts (Aug 26, Sep 5, Oct 2, Nov 9, 2026). |
| Grok Bot runs only on "Cursor-hosted cloud computers in the United States", and xAI's docs say on-premises is not supported | **Not verified**. |
| Grok Bot is closed source and its consumer terms "forbid trying to derive its source code" | **Not verified**. |
| Elon Musk posted (October 7, 2026) that Grok Bot will route each task to the "best back end model" | Attributed to a social post; not verified. |
| Elon Musk posted on November 1 that serving cost was "unsustainably high", and on November 8 that efficiency fixes were coming | Attributed to social posts; not verified. |
| `hermes migrate grok-bot` imports Grok Bot routines, skills and memory | **Verified in source**: `hermes_cli/subcommands/migrate.py` and `hermes_cli/setup_agent_import.py` reference `grok-bot`. The import behaviour was not tested. |
| Hermes can talk to you in X's encrypted DMs through an "official X Chat plugin" | **Not verified in the repository**: `plugins/` has no X Chat plugin (only `context_engine` matched "x"). It may be a separate package. |

Two further observations: the page's Grok facts are dated and tied to X posts, which can change; and the "migrate" claim is the most concrete, because it can be checked in code.

## 3. The Claude Code comparison (`compare/claude-code.md`)

The summary says Hermes "answers on more than 20 messaging platforms, runs scheduled jobs and works with hundreds of models, and it hands coding to Claude Code." The page makes the same kind of claim about Claude Code's own features; those were not checked. The Hermes-side claims are consistent with the source (messaging plugins, cron, providers) and the docs read in file 02.

## 4. The OpenClaw comparison (`compare/openclaw.md`)

Claims: Hermes is "a free, MIT-licensed OpenClaw alternative that Nous Research can also host on Hermes Cloud". `hermes migrate openclaw` is referenced in the source (`cli_tui_runtime_mixin.py`, `left_core_migration.py`, `cli_render.py`), so a migration path exists. The migration behaviour was not tested.

## 5. The top-level claims ("Why Hermes Agent")

1. "Free and open source under the MIT license." **Verified**: `LICENSE` and `pyproject.toml`.
2. "Runs on your hardware or Hermes Cloud." **Verified in part**: the self-hosted path is in the source and docs; Hermes Cloud is not in this repository and was not tested.
3. "Works with the model you pick." **Verified in part**: model and provider configuration pages exist; the Nous Portal catalogue was not checked.
4. "Lives in your chat apps and learns." **Verified in part**: 24 platform plugins exist; skill creation is in the docs and source (`skill_manage`).

## 6. Assessment

The comparisons are marketing: well-sourced in form, but the competitor cells are the vendor's view. Two checkable points are real: the migration commands, and the platform count. Prefer the competitors' own documentation for their claims.

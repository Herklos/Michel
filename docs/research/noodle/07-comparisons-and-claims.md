# 07. Noodle's own comparisons, and how they hold up

Sources: the comparison table in `README.md` ("How Noodle compares"), `docs/privacy.md`, `docs/security.md`, `Enterprise/`. Read 2026-11-14. Each claim is the project's own. "Check" marks what can be verified from this repository and what cannot.

## 1. The README comparison (Grok Bot, Muse, Noodle)

| Claim (Noodle's wording, condensed) | Check |
|---|---|
| Grok Bot and Muse run only their own models; Noodle lets you bring your harness and runs local models for free | Partly checkable: Noodle's harness list and local-model changelog entries exist. Grok Bot and Muse model limits were not checked (no source for them here). |
| Grok Bot and Muse are closed source; Noodle is Apache 2.0 | Noodle: **partly correct**. The app is Apache 2.0 except `Enterprise/` (PolyForm Small Business) and `Incubator/` (PolyForm Noncommercial). The competitors' licences were not checked. |
| Grok Bot and Muse are HTML-based, not native | Not checked. |
| Grok Bot and Muse use a remote VM run by xAI or Meta for computers; Noodle uses local computers | Noodle: checkable (Computer runs Linux images on the Mac). Competitors: not checked. |
| Grok Bot and Muse send voice to their servers; Noodle transcribes on device | Noodle: checkable in `docs/privacy.md` ("Voice messages are transcribed on your Mac or iPhone"). Competitors: not checked. |
| Grok Bot and Muse have cloud connectors only; Noodle has OS integration and MCP | Noodle: checkable (Tools, MCP, Calendars, Reminders). Competitors: not checked. |
| Grok Bot trains nothing and has no privacy mode; Muse trains on chats; Noodle keeps data local | Noodle: "your data stays local" is **qualified** by `docs/privacy.md`: provider sees everything a bot works with. Competitors: not checked. |

## 2. Noodle's own claim about itself, checked

- "Your data stays local": partly true. Chats and workspaces are on the Mac; the provider receives the model input. The docs say this directly.
- "Restricted by default": true, and documented (`docs/security.md`).
- "No analytics or crash reports": the Noodle app code makes no such calls in the sources checked (`Shared/`, `Sources/`), but this was a text search, not an audit.
- "Free and open source": the Apache-2.0 claim holds for most of the code, with the two exceptions in file 01 §4.

## 3. Noodle compared with Hermes Agent (from both projects' materials)

These two products are close in purpose: each runs persistent, multi-channel agents on the user's own machine.

| Dimension | Noodle | Hermes Agent (Nous) |
|---|---|---|
| Where the agent runs | the user's Mac; harnesses run as processes under the user's account; Hub and Server for others | the user's machine or server; Hermes Cloud (paid) |
| Model source | the harness's account (Codex, Claude Code, FX, Grok Build, Muse Code, OpenCode, Antigravity, Apple Intelligence, custom OpenAI-compatible servers, local models) | any provider or local model; Nous Portal login for hundreds of models |
| Agent runtime | external harness programs (Noodle supervises them) | Hermes' own agent loop (`run_agent.py`) |
| Interfaces | native Mac, iPhone and iPad apps; terminal; Linux server | CLI, TUI, desktop app (macOS, Windows, Linux), web dashboard, 20+ messaging platforms |
| Chat apps | none outside Noodle's own clients | Telegram, Discord, Slack, WhatsApp, Signal, Teams, iMessage (via BlueBubbles) and many more |
| Memory | per-bot workspace, backstory, memory files and shared notes; memory summary injected into instructions | bounded MEMORY.md and USER.md, plus external memory providers |
| Scheduling | bot wake-ups and cron-style repeating wake-ups (per bot) | cron jobs with scripts, skills, delivery to any platform |
| Multi-agent | groups (a shared goal in one conversation) and per-bot task lists | sub-agent delegation, Kanban board of workers, goal loops |
| Security stance | restricted bots, folder allow-lists, private sign-in copies | command approval modes, container isolation options, context-file scanning |
| Licence | Apache 2.0 with Enterprise and Incubator exceptions | MIT |

Neither product's claims about the other were checked here. See `docs/research/hermes-nous/05-comparisons-and-claims.md` for the Nous side.

## 4. What Noodle's comparison omits

- It does not compare with Hermes, OpenClaw, Claude Code or Codex directly.
- It does not state usage limits, pricing, or the cost of the Hub's plans.
- Its privacy claim omits the messaging-group effect: every bot in a group sends the whole conversation to its own provider.

# 01. Michel (`Herklos/Michel`): what it is and what it stores

Source: `https://github.com/Herklos/Michel`, shallow clone at `/home/user/herklos/michel`, commit `17a6d1c` (2026-11-13). Read: `README.md`, `docs/architecture.md`, `docs/anytype-backend.md`, `docs/PLAN.md` (headings and storage parts), file list. The Rust gateway and Exact client were not built or run.

## 1. What it is

A self-hosted personal AI "Bots" app. Each Bot has a name, instructions, a workspace folder and a conversation. The `hbots` gateway (Rust) runs on your machine or a VPS and serves a web app (Exact client, same source for web, desktop and mobile). The gateway talks to the agent runtime through a `Harness` trait; **T3 Code** is the only production runtime wired in.

## 2. Features, grouped

| Group | Features (from README) |
|---|---|
| **Bots** | Guided setup (name, look, instructions, first message); per-Bot instructions and workspace; model choice; autonomy level with per-Bot caps enforced by Michel |
| **Conversation** | One-to-one and group chats; attachments and voice clips; reply, react, pin; `@mention`, `@all`, or naming a Bot in groups; stop a running answer; approve requests in chat |
| **Background work** | **Watches**: scheduled checks of a web page or workspace file, with rules, then a webhook or routine on change. **Routines**: recurring or one-off work |
| **Collaboration** | **Helpers**: other Bots step in on request, with limits set in Bot details |
| **Bot details** | Routines, memory, usage, code files, library; watch or take over the Bot's browser through T3 |
| **Memory** | Memory summary injected into the Bot's `AGENTS.md`; shared notes kept in sync |
| **Secrets** | **Vault**: encrypted logins, CSV import/export; Bots can use saved credentials without seeing passwords |
| **Access** | Password, then choice of device, local network, or Tailscale access |
| **Storage** | Local folder today; optional Anytype pairing (tier A file sync implemented per `docs/anytype-backend.md`) |
| **Operations** | Checksummed releases, background service, update and restart from Settings, CLI rollback |

## 3. Where Michel stores things (`docs/anytype-backend.md`, "What exists today")

Everything is files under `~/.hbots` (`HBOTS_HOME`). Bots live in `HBOTS_ROOT` (default `~/.hbots/bots`), with app state in `bots/.botapp`.

| Data | Location | Shared to Anytype? |
|---|---|---|
| Bot state and config | `<bot>/.bot/bot.json` | shared fields |
| T3 binding, per-machine overrides | `.bot/local.json` | no |
| Instructions | `AGENTS.md` (`CLAUDE.md` symlink) | prompt only |
| Tool wiring (holds Bot bearer token) | `.mcp.json`, `.codex/config.toml`, `.claude/settings.json` | no |
| Memory | `memory/MEMORY.md`, `memory/log.md`, notes, `.botapp/shared-memory.md` | yes |
| Skills, library files | `skills/`, `library/` | yes |
| Library records | `.bot/library.json` | one object per record |
| Groups and group messages | `.botapp/groups.json` | messages yes; runtime state no |
| Settings | `.botapp/settings.json`, `main-bot.json`, `apps.json` | some prefs yes |
| Reactions, pins, usage, routine history | `.botapp/thread-meta.json`, `usage.json`, `routine-history.json` | no |
| Routines (executor) | T3 `scheduledTasks` | definitions only |
| Secrets | `vault.enc`, `.vault-key`, `access.json`, `session-secret`, `.bot-mcp-token`, `t3-token`, `.env` | **never** |
| Conversation transcripts | owned by T3 Code (the harness) | not in Michel's folder |

The `Workspace` trait has a `LocalDisk` adapter and a test `MemoryWorkspace`. Most data still reads the disk directly. Anytype pairing and space checks exist in Settings, but Bot storage still uses the file system.

## 4. Design choices worth noting

- **Two programs, no shared process.** The gateway is the server; the client never reads disk.
- **Harness boundary enforced by a script.** `scripts/check-t3-boundary.sh` fails if T3 RPC names appear outside the adapter.
- **Capability traits with explicit "unsupported".** A runtime lacking a capability returns 501, not a silent no-op.
- **Secrets never sync** to Anytype.

## 5. Relation to our build

Michel (Herklos) and our `michel/` package in this repo solve the same product shape (persistent Bots, channels, approvals, schedules) with different substrates: Michel uses a local folder plus T3 Code; we use Temporal workflows. Michel's storage table is a useful checklist for what a Bot needs to persist, and its secret-never-syncs rule matches our worker-only secrets.

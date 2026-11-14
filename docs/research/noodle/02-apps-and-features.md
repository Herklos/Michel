# 02. Noodle features, grouped

Sources: `README.md`, `docs/usage.md`, `docs/harness-setup.md`, `docs/security.md`, `docs/privacy.md`, `docs/mcp-connections.md`, `docs/voice-messages.md`, `docs/gaming.md`, `docs/attachment-annotations.md`, `docs/keyboard-shortcuts.md`, `CHANGELOG.md` (0.80.x to 0.85.0), each component README, `Scenarios/*/scenario.json`. Read 2026-11-14. Features are grouped by what a user does, not by changelog order.

## 1. Bots (the core unit)

- **Each bot** has a name, avatar, a **public description** (what others see) and a private **backstory** (instructions), its own workspace, history, and a harness (see file 03).
- **Creation:** a first-run welcome creates a team (a personal assistant, a full-stack developer, a researcher) once an account is signed in. Faces are drawn for new bots and can be chosen.
- **Access:** every bot starts **restricted** (see file 04). **Unrestricted** access is a per-bot setting and needs confirmation.
- **Work tracking:** bots keep a short **task list** linked to the conversation each task came from (0.83.0). They keep their own **assignments file**; each heartbeat advances each item. A bot can schedule its own wake-ups (at most three waiting at once) and repeating cron wake-ups.
- **Controls:** **Stop** ends a turn with its sub-agents and background commands, keeping the session (0.85.0). **Suspend** for 1 hour, 4 hours, until tomorrow, a week, or until resumed (0.82.0). **Kick** restarts a stuck bot. Spending **budgets** per hour, day, week or month (0.81.1).
- **Organise:** asks an idle bot to tidy its own files, move recurring work into assignments, and update memory.
- **Self-maintenance:** a built-in skill keeps preference and memory files current, replacing superseded instructions.
- **Visibility:** a per-bot **activity log** window (tool activity and output), usage charts by bot, harness or model, and a sidebar status line (what the bot says it is doing).

## 2. Conversations

- **Direct chats and groups.** In a group, `@` mentions a bot; `@all` addresses everyone; with no mention the last speaker usually answers. Members can be changed, and removing a member keeps history.
- **Windows:** open a conversation in its own window, float it over other apps (on every Space, above full-screen apps), or show several side by side as columns (0.80.0). **Choose Conversation** from anywhere with ⌃⌥Space.
- **Messages:** Markdown; reactions; pins; attachments by picker, drag or Finder; Quick Look previews; drafts kept per chat; **Forward** a file to another bot or group; drag a file from a chat onto a sidebar bot to send it.
- **Annotations** on a conversation or an attachment before sending (`docs/attachment-annotations.md`).
- **Chat effects:** a bot can trigger on-screen effects in a chat (`messenger --effect pasta` is the documented example).
- **Long replies:** can be split into a bubble per paragraph or into short chunks.
- **Notifications** per group: Default, All Messages, Mentions Only, or Muted.
- **Shortcuts:** the app has a keybinding editor and a Shortcuts-app integration (Open Chat, Call Agent).
- **Widgets:** Bot, Bots, and Bot Status widgets on the desktop, iPhone and Lock Screen (mobile).

## 3. Voice

- **Voice messages** on supported macOS 26 Macs. Transcription happens on the Mac or iPhone; the bot receives both the audio and the transcript (`docs/privacy.md`).
- **Voice calls:** bots on a harness that supports calls (Codex) can call you. Calls from Hub bots ring on your Mac; calls ring your iPhone even when Noodle is closed (0.80.0, via Push).
- **Dictation** is on-device, per the README comparison.

## 4. Tools

- **Catalogue:** "dozens of MCP services" (README). Services named in the changelog include Basecamp, Coinbase, Inkbox, Kling and Krea. Google Workspace (Gmail, Docs, Drive, Calendar) is marked **experimental** and limited to accounts added as testers.
- **Sign-in:** connections use browser sign-in only. Services that want an API key, token or client secret, or that run as a program on the Mac, are **not supported** (`docs/mcp-connections.md`).
- **Custom connections:** any MCP service by URL. Separate connections per account; editing a connection's instructions affects every bot assigned to it.
- **Built-in tools** (folders in `Tools/`): Calendar and Reminders (bots read and change only the lists you assign), Maps, Vision (on-device OCR and analysis), **Image Generation** (on-device Stable Diffusion XL models, nothing sent elsewhere), Applet, Browser, Computer.
- **Remote models:** TensorFold (0.80.0) and Custom accounts for any OpenAI-compatible server (see file 03).
- **Assignment:** a tool is added in Settings and then assigned in the bot's Tools tab. The tool's permissions are granted once at sign-in.

## 5. Computers (Noodle Computer)

- Linux computers, Shell (terminal only) or Desktop (browser, terminal, file manager), created from downloadable images. Advanced options set CPU, memory, disk and network. Files and installed software persist across restarts. No Docker Desktop needed.
- Several bots can share one computer. Each bot gets its own terminal sessions.
- Files: copy between a bot's work area and the computer (up to 8 GB per file); a file manager at `/workspace` with import and export by drag, progress, cancel, and previews (up to 20 MiB).
- **External agents** (Claude Code, Codex and others) can use Noodle Computer through the `noodle-computer` command or an MCP server, after **Allow agents** is turned on in Settings. Each app must be allowed, can only see computers it created or was lent, and cannot be used by Noodle's own bots.
- Upgrades to newer images keep files; stopping a bot's computer after work is a bot behaviour (0.80.0).
- On macOS 27 or later, Desktop computers draw with the Mac's GPU.

## 6. Browsers (Noodle Browser)

- A built-in browser, not Safari. Each browser has its own sign-ins, history, bookmarks, downloads and files. Deleting a browser deletes them.
- **Pause Agents** stops bots acting in that browser while you use it; it cannot undo actions already taken.
- Bots can open, read, fill forms, click, upload and download, take screenshots and use history and bookmarks. A cyan target shows where the bot points. Bots cannot drag or right-click.
- Some websites offer tools for AI agents; bots can use them in a signed-in tab. Experimental.
- Pages can be sent to a conversation as cards with screenshots. The card does not carry sign-ins.
- External agents can use browsers through `noodle-browser` or MCP, with the same allow-list model as Computer.
- Browsers start muted; the app has search-engine and launch settings.

## 7. Noodlets and Applet

- A **noodlet** is software a bot writes and you open like an app. In Finder it looks like one document.
- Applet has a library (All, Recent, Pinned, Hidden, and categories). Noodlets can be removed from the library without deleting files, or moved to the Trash.
- A bot can share a noodlet as a link; the link opens the live noodlet in Applet. Links point to this Mac and are not copies.
- **Play on a TV** over AirPlay: fixed-size games are scaled and centred; resizable ones fill the screen.
- Bots can build games from standard web exports (Godot, Unity, Emscripten), including multi-threaded builds (0.80.0).
- Permissions per noodlet (microphone, camera, speech, screen, local network) with one-time consent; a **Secrets** panel shows key names, never values.
- Noodlets have a sandbox: they read only their own files and saved data (see file 04).

## 8. Groups, Hubs, and multi-device

- **Hubs** (Noodle Hub, Noodle Server) run bots for other people on the Hub's harnesses. Covered in file 03.
- **Let My Devices Reach This Mac** (Settings → Hub) lets your iPhone and other Macs reach your bots, and ring you.
- **Spaces:** switch between All, This Mac and joined Hubs; order them with drag and drop.
- **Shared bots:** a bot on this Mac can be shared with people on any joined Hub. Reactions travel both ways; typing @ offers the people a bot is shared with.

## 9. Games and the TV

Game noodlets (`docs/gaming.md`): a bot makes a game on the Mac or on a Hub; play on the Mac, on iPhone (Screen Mirroring to a TV), with a PlayStation, Xbox or Switch controller, two-player on the couch, or shared through a Hub.

## 10. Native integration (what the README compares against cloud-only rivals)

Calendars, Reminders, Shortcuts, accessibility, Spotlight, notifications, Quick Look, screen capture with annotations, the system log (every command a bot runs is written to the Mac's system log, 0.80.0), and background heartbeats.

## 11. Scenario demos (`Scenarios/`)

Twenty-two scenario files are reproducible demo setups (a `scenario.json` per scenario, with agents, settings and seeded conversations). Titles include "Building AgentFleet: what did the coding agent actually do?" (development team), "Bots waiting on each other in a group" (group tasks), "7 a.m. Everything's already done." (morning shift), "Alfred runs the family Christmas" (family butler), breach response, change review, code review, finances, freelance pipeline, launch week and renewal season. They show the intended use: bots that work while you are away, shared groups, and personal-assistant roles.

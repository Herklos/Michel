# 06. Release timeline: what changed, by release

Source: `CHANGELOG.md` in the root of the Noodle repository (about 200 KB), read at its Unreleased section and at each dated release from 0.80.x to 0.85.0. Dates are the changelog's own. Read 2026-11-14.

## 1. Timeline (dated headings in the changelog)

| Version | Date | Theme (from its entries) |
|---|---|---|
| Unreleased | — | Push (calls to a closed app on iPhone) |
| 0.85.0 | 2026-11-13 | Stop a working bot; Suite installer with companion choice; Hub installer |
| 0.84.0 | 2026-11-11 | Enterprise MDM profiles; larger local models |
| 0.83.0 | 2026-11-10 | Task lists per bot; Space Picker in the sidebar |
| 0.82.1 | 2026-11-08 | not read in detail (patch release) |
| 0.82.0 | 2026-11-06 | Harness installation ownership; Suspend Bot for a period |
| 0.81.1 | 2026-11-05 | FX team choice; per-bot spending budgets |
| 0.81.0 | 2026-11-03 | not read in detail |
| 0.80.x | 2026-11-01 to 2026-11-02 | the large batch: ~80 entries across bots, Hubs, calls, computers, browsers, widgets, models, games |

The changelog does not show 0.80.0's own date in the portion read; the 0.80.x patch entries are dated 2026-11-01 and 2026-11-02.

## 2. Feature groups added across 0.80.x to 0.85.0

**Bots and autonomy**
- Assignments file and heartbeats; bots move recurring work into it.
- Bots schedule their own wake-ups (at most three waiting) and repeating cron wake-ups.
- Organize: asks an idle bot to tidy files and memory.
- Built-in skill to keep preference and memory files current.
- Spending budgets per bot; suspend for a period; stop a working bot (0.85.0); kick with recovery.
- Harness fallback across logins, including specific profiles; usage retries.
- A bot warned to stop a computer it started and left unused for 30 minutes.

**Hub and multi-device**
- Calls from bots ring the phone (even when the app is closed, via Push) and other Macs.
- Shared bots across joined Hubs; reactions and effects travel both ways.
- Hub: Computers & Browsers lists per joined Hub; Hub bots' status says why they are paused ("plan limit, resumes …").
- Spaces menu: order joined Hubs.

**Conversation**
- Column view and floating windows; Choose Conversation hotkey.
- Notifications per group; sort conversations (newest first, unread first, or grouped).
- Sidebar line can show Latest Message or Description; status under names.
- Drag a file to another bot or group; Forward to another bot.
- Paste as Attachment (⌥⌘V); long replies split into bubbles.
- Drop a picture onto the icon editor.

**Tools, computers, browsers**
- Image Generation (on-device Stable Diffusion XL models).
- Remote models: TensorFold.
- Tools added: Basecamp, Coinbase, Inkbox, Kling, Krea.
- Computer `terminals` tool lists a bot's open terminals.
- Browser tabs left unused for six hours can be closed by the bot.
- `.patch` and `.diff` files open in a review with a walkthrough.
- The system log records every command a bot runs (who, program, start and end, peak memory).

**Noodlets and games**
- Godot, Unity and Emscripten web exports, including multi-threaded ones.
- Play on TV and phone; Show on iPhone.

**Harnesses and settings**
- Choose Harnesses (turn on and off); harness status for Codex and Claude Code plan limits.
- Sign Out and Sign In Again per harness.
- Manage installation (Your Own or Managed by Noodle).

**Enterprise**
- MDM configuration profiles (0.84.0) with restrictions by key (see file 03 §10).

**Installers and companions**
- Suite Installer (signed, notarised) with a companion chooser; Hub Installer for always-on Macs.

**Demos**
- Scenario demos (morning demo, breach response, others).

## 3. Patterns across the releases

- **Hub and Mobile are the fastest-growing surface** (most entries from 0.80.0).
- **Trust-related changes are explicit**: sign-in copies, suspend, budgets, system-log records of commands, folder permissions.
- **The release cadence is high**: about eleven dated versions (0.80.1 to 0.85.0) between 2026-11-01 and 2026-11-13.
- **Companions are shipped separately** with their own changelogs and tags.

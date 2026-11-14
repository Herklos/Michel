# 02. `Herklos/skills`: where your agents, groups, rules, memory, tasks and history live

Source: `https://github.com/Herklos/skills`, shallow clone at `/home/user/herklos/skills`, commit `05de789` (2026-11-08). README and the storage-related references of each skill were read. Paths below are the ones the skills document; nothing on your machine was inspected.

## 1. The short answer

The skills describe **two layers**:

1. **Anytype is the source of truth** for the organization: the agent roster, groups, shared rules, memories, projects and tasks, suggestions, and the Anytype space itself is synced by Anytype's peer-to-peer network.
2. **Each runtime keeps its own copy of what it runs on**, in its own home directory. The runtime pulls only what it needs; Anytype is not pushed into live bots (`README.md`: "Editing Anytype does not push configs; apply with `hermes-profiles` after an accepted suggestion").

So "where is it stored" has two answers: the **definition** lives in Anytype; the **running state** lives under each runtime's home.

## 2. The five skill packs

| Skill | Version | Role |
|---|---|---|
| `anytype-agents` | 1.59.0 | Org roster, typed objects, groups, shared rules, memories, suggestions, projects, via Anytype MCP |
| `hermes-profiles` | 1.46.0 | Lifecycle and config for Hermes Agent profiles (one home per agent) |
| `osaurus-agents` | 1.5.2 | Define Osaurus agents via `osaurus config`, bundles and tools |
| `monocode-agents` | 1.0.0 | Create and manage MonoCode "Monos": soul, memory, projects, habits |
| `any-agents` | 1.3.1 | Install and operate agents and teams on the open-source `any` / `anyrt` runtime; sync; backup |

## 3. Storage map by kind of data

### 3.1 Agent roster and architecture (who each agent is, how they are organized)

| Item | Where it lives | Source |
|---|---|---|
| Agents hub, HQ pages, Primary, Drafts | **Anytype**, space found by searching for "Agents" and "Projects" | `anytype-agents/SKILL.md` "Resolve space and roots" |
| Agent object (role, memory links, skills, harness profile, subagents, system prompt link, runtime links) | **Anytype** typed `agent` | `anytype-agents/references/object-types.md` |
| Team / Subteam / Subagent / Harness / Harness profile / Browser / Computer / Tool profile / Runtime / Vault grant | **Anytype** typed objects | `object-types.md` |
| Per-HQ computer and browser pair | **Anytype** Computer object with `cua_space`; Cua Spaces (live) | `hq-runtime-pair.md`, `cua-hq-spaces.md` |
| Hermes profile (one agent's home) | `~/.hermes/profiles/<slug>/` (or `$HERMES_HOME`) | `hermes-profiles/SKILL.md` |
| Osaurus agent | `~/.osaurus/agents/{UUID}.json`, avatar at `~/.osaurus/agents/avatars/{UUID}.png` | `osaurus-agents/references/cli-map.md`, `anytype-apply.md` |
| MonoCode Mono | in the MonoCode app (soul, memory, habits, projects); location not documented in the skill | `monocode-agents/SKILL.md` |

### 3.2 Group and harness configs (groups, delegation, routing, models)

| Item | Where | Source |
|---|---|---|
| Org group (typed Group: purpose, notes, routing, platform ids) | **Anytype** `group` object | `anytype-agents`, `messaging-groups.md` |
| Hosted group rooms (2–6 bots) | Hermes Bot Mode "Group Chats", stored as `hosted_rooms`; UI sections in browser Local Storage `group-chats` | `messaging-groups.md`, `bot-mode-sections.md` |
| Delegation (`model_map`, `profile_routes`, `default`) | Hermes `config.yaml` in the profile | `hermes-profiles/references/delegation.md` |
| Model settings | Hermes `config.yaml` (`model`, providers, fallbacks) | `profile-map.md` |
| Osaurus declarative config | `osaurus config export` → YAML (you choose the path); live config under `~/.osaurus/config/*.json` | `osaurus-agents/references/config-document.md`, `cli-map.md` |
| Any-agents overlays, tiers, triggers, connectors | Any's data dir, `$ANY_DATA_DIR` (default `~/.any`) | `any-agents/reference/multi-device-and-sync.md` |

### 3.3 Rules and instructions

| Item | Where | Source |
|---|---|---|
| Shared Rules (versioned core + topic prompts) | **Anytype** `prompt` objects; `shared_rules` kind; versions logged | `anytype-agents/references/shared-rules-starter.md`, `prompts.md` |
| Operating Guide (where each kind of item goes; conflict order) | **Anytype** `prompt` with `prompt_kind=operating_guide` | `shared-memory.md` |
| Per-agent system prompt | **Anytype** `prompt` linked from the agent; written to the runtime's instructions | `prompts.md` |
| Hermes always-on identity | `SOUL.md` in the profile | `profile-map.md` |
| Hermes protected files | `SOUL.md`, `AGENTS.md`, `CLAUDE.md` (protected by `security.protected_instruction_files`) | `security.md` |
| Osaurus / Michel instructions | the agent's JSON; Michel's `AGENTS.md` per Bot | `osaurus-agents`, Michel `docs/architecture.md` |

### 3.4 Memory

| Item | Where | Source |
|---|---|---|
| Human profile (About) | **Anytype** `memory`, `memory_scope=human` | `shared-memory.md` |
| Atomic facts and preferences | **Anytype** one `memory` object per fact (`topic`, `observed_at`, `source_agent`) | `shared-memory.md` |
| Never-save list and forget protocol | **Anytype** `memory_kind=exclusion`, org scope | `shared-memory.md` |
| Hermes agent notes / user profile | `memories/MEMORY.md` and `memories/USER.md` in the profile (char-limited; agent writes via tool) | `hermes-profiles/references/memory.md` |
| Hermes session search | FTS5 over `state.db` | `memory.md` |
| Osaurus memory | `~/.osaurus/memory/memory.sqlite` and `vectura/{agent}/`; config `~/.osaurus/config/memory.json` | `cli-map.md`, `config-document.md` |
| MonoCode memory | in the Mono's memory page (facts, topic notes, archive) | `monocode-agents/references/behavior.md` |
| Michel memory | `memory/MEMORY.md`, `memory/log.md`, `.botapp/shared-memory.md` | Michel `docs/anytype-backend.md` |

### 3.5 Tasks, projects and schedules

| Item | Where | Source |
|---|---|---|
| Projects, epics, user stories, tasks | **Anytype** `project`, `epic`, `user_story`, `task` (with kinds such as spike) and filtered Roadmap / Backlog / TODO queries | `project-pm.md` |
| Agenda and schedules | **Anytype** `schedule` objects and an Agenda query; bound to Hermes cron | `agenda-and-schedules.md` |
| Hermes scheduled jobs | `cron/jobs.json` and `cron/output/` in the profile; Bot routines use the same store | `profile-map.md`, `cron.md` |
| Osaurus schedules and watchers | `~/.osaurus/schedules/{uuid}.json`, `~/.osaurus/watchers/{uuid}.json` | `cli-map.md` |
| MonoCode habits | Mono's habits page; run while MonoCode is open | `behavior.md` |
| Any-agents triggers | configured in the any runtime; not located in this pass | `reference/triggers.md` (not read) |

### 3.6 History and transcripts

| Item | Where | Source |
|---|---|---|
| Hermes sessions | `state.db` (+ `-shm`, `-wal`) and `sessions/` in the profile | `profile-map.md`, `security.md` |
| Osaurus chat history | `~/.osaurus/chat-history/…` | `cli-map.md` |
| Osaurus harness scratch | `~/.osaurus/harness/<chat id>/` | `cli-map.md` |
| Anytype logs | **Anytype** `log` objects per rules change, plus Query on summary | `shared-memory.md` |
| Michel transcripts | owned by T3 Code | Michel `docs/anytype-backend.md` |
| Any-agents chat history | under the data dir; export with `export-ndjson.sh` | `any-agents/scripts/export-ndjson.sh` |

### 3.7 Secrets and credentials

| Item | Where | Source |
|---|---|---|
| Osaurus per-agent sandbox secrets | macOS Keychain, service `ai.osaurus.agent-secrets`, account `{agentUUID}.{KEY}` | `osaurus-agents/references/anytype-apply.md` |
| Hermes auth and vault | `auth.json` and `.env` in the profile; Hermes vault grants (Anytype `vault_grant` respected) | `profile-map.md`, `browser-and-computer.md` |
| Michel secrets | `vault.enc`, `.vault-key`, `t3-token`, `.env` (never synced) | Michel docs |

## 4. Backup and sync

- **Anytype** syncs over its peer-to-peer network; `any-agents` documents LAN sync, internet sync via relays, and self-hosting sync nodes (`multi-device-and-sync.md`).
- **Hermes:** `--clone` copies config, `.env` (non-channel), SOUL, skills, and memory; `--clone-all` also copies sessions, `state.db`, cron and checkpoints (`profile-map.md`).
- **Any:** the data directory (`~/.any` or `/var/lib/any`) should be snapshotted with the server stopped (`upgrades-and-backup.md`).
- **Osaurus:** `osaurus config export` for declarative config; bundles for agents (`bundles.md`).

## 5. Runtimes named in the skills

The shared-memory doc says: "each runtime (Hermes, Osaurus, Grok Bot, Noodle) keeps pointers or a short digest only." So **Grok Bot** and **Noodle** are treated as runtimes in your setup, though the skill packs contain no install or storage steps for them. See `03-grok-bot-features.md` and `docs/research/open-swe`'s sibling research in `docs/research/` for the other two.

## 6. Recent changes

Latest commit `05de789` (2026-11-08): "Remove MonoCode operator skill". The `monocode-agents` pack still describes `/operator`, which the commit title suggests was removed elsewhere; check before relying on it.

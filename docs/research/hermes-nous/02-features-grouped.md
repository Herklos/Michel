# 02. Hermes Agent features, grouped

Sources: the full documentation dump `llms-full.txt` (read by section), the docs index `docs/llms.txt` (289 entries), and the source tree. Read 2026-11-14. Features are grouped by function. Each line says where it was read.

## 1. Memory and learning

- **Persistent memory:** `MEMORY.md` (agent notes, 2,200 chars) and `USER.md` (user profile, 1,375 chars), in `~/.hermes/memories/`. Injected into the system prompt as a **frozen snapshot** at session start, to keep the prefix cache. The agent edits them through a `memory` tool (add, patch, remove). A write over the limit returns an error; the agent must consolidate first. Entries are separated by `§`. (Persistent Memory page.)
- **Memory providers (plugins):** external memory backends for cross-session user modelling: RetainDB, ByteRover, Honcho, Hindsight, Supermemory, Mem0, OpenViking, Holographic. Honcho has its own page. (Features Overview; Memory Providers.)
- **Session search:** FTS5 over past chats in `state.db`, separate from curated memory. (Memory section.)
- **Skills:** on-demand knowledge documents in `~/.hermes/skills/`, progressive disclosure, compatible with the agentskills.io standard. The agent can create, patch and delete its own skills (`skill_manage`). Skills can be installed from a Skills Hub, with a security scan and an action log. Skills can be preloaded with `-s`. (Skills System.)
- **Curator:** a background pass over agent-created skills. Runs on inactivity (7 days between runs and 2 hours idle by default). Automatic transitions: unused for 14 days marks a skill **stale**; 30 days moves it to `~/.hermes/skills/.archive/`. Pinned skills and skills used by any cron job are skipped. Dry-run available. Built-in skills can be archived only if `curator.prune_builtins` is on. (Curator.)
- **Context files:** discovers `.hermes.md`, `AGENTS.md`, `CLAUDE.md`, `SOUL.md`, `.cursorrules` in a project. (Features Overview.)
- **Context references:** `@` injects files, folders, git diffs and URLs into a message. (Features Overview.)
- **Personality:** `SOUL.md` is the first thing in the system prompt; `/personality` presets per session. (Features Overview.)

## 2. Work and automation

- **Tools:** 310 tool modules in the source. Tools are grouped into toolsets that can be enabled per platform (web search, terminal, file editing, memory, delegation, and more). (Tools & Toolsets; source.)
- **Tool search:** a search over the tool catalogue so the model need not see every tool. (Features Overview list.)
- **Code execution:** `execute_code` lets the agent write Python that calls Hermes tools in a sandboxed RPC, collapsing multi-step work into one turn. (Code Execution; Features Overview.)
- **Scheduled tasks (cron):** one `cronjob_manage` tool with actions (create, pause, resume, edit, trigger, remove, stop an in-flight run). Natural language or cron expressions. Attach zero, one or several skills; deliver to the origin chat, a local file, or a platform target. **No-agent mode:** a script runs on schedule, stdout delivered verbatim, with no model call. **Event-triggered:** a webhook route with `cron_job` set fires a job when something happens. Model resolution: per-job pin, then `cron.model`, then the main model at fire time. Per-job reasoning effort. Cron runs cannot create cron jobs (loop guard). Admission recovery after restart, with an operator-review pause for interrupted executions. (Scheduled Tasks.)
- **Subagent delegation:** `delegate_task` spawns child agents with their own conversation, terminal and toolset; only the final summary returns. Three concurrent by default. Children cannot use `clarify`. (Delegation & Parallel Work; Subagent Delegation.)
- **Kanban (multi-agent board):** a durable board in `~/.hermes/kanban.db`. Agents use a `kanban_*` toolset (`kanban_show`, `kanban_list`, `kanban_complete`, `kanban_request_review`, `kanban_request_changes`, `kanban_block`, `kanban_heartbeat`, `kanban_comment`, `kanban_attach…`). Humans use `hermes kanban` or the dashboard. Named profiles act as workers; patterns include research triage, scheduled ops, digital twins, engineering pipelines (decompose, implement in worktrees, review), and fleet work. Completion checkpoints near 90% of a worker's iteration budget; a consecutive-failure circuit breaker; PR completion contracts. (Kanban; Kanban tutorial.)
- **Persistent goals (`/goal`):** a standing objective that survives turns. After each turn a judge model checks whether the goal is met; if not, a continuation prompt is fed back. Single-session; kanban cards can run the same engine per card. Described as the "Ralph loop". (Persistent Goals.)
- **Recurring loops, hooks, batch processing:** recurring loops (a page exists); event hooks for logging, alerts, webhooks, and plugin interception; batch runs over thousands of prompts with ShareGPT trajectories for training or eval. (Features Overview.)
- **Mixture of Agents** and **Code Execution**: listed on the features page.
- **Git worktrees:** `hermes -w` starts an isolated worktree per run; `.worktreeinclude` controls what is copied. (CLI and configuration.)
- **Checkpoints and rollback:** snapshots of the working directory before file changes; `/rollback` restores. (Features Overview.)

## 3. Interfaces and reach

- **CLI and TUI:** interactive sessions; single-query mode; `--resume` and session naming; `-w` worktrees; verbose mode. (CLI Interface; TUI.)
- **Desktop app:** native app on macOS (Apple silicon), Windows and Linux, sharing config, keys, sessions, skills and memory with the CLI. `hermes desktop` uses existing config. Includes a browser workspace via `hermes webapp` (sessions, profiles, capabilities, messaging, artifacts, scheduled jobs, file tree, git review, previews and a terminal). (Hermes Desktop.)
- **Web dashboard:** `hermes dashboard`, a browser admin panel with a Chat tab that embeds the TUI through a pseudo-terminal. (Features Overview; Desktop page.)
- **Messaging gateway:** the source bundles 24 platform plugins under `plugins/platforms/` (Telegram, Discord, Slack, WhatsApp, Matrix, Mattermost, email, SMS, DingTalk, Feishu, WeCom, IRC, LINE, Teams, Google Chat, Buzz, ntfy, Photon, Raft, SimpleX, WhatsApp Cloud, Signal, Weixin, BlueBubbles, QQ Bot); core ingress adapters (API server, webhook, Microsoft Graph webhook) live in `gateway/platforms/`. The docs list about 35 platforms: Telegram, Discord, Slack, WhatsApp (and WhatsApp Business Cloud API), Signal, SMS, Email, Matrix, Mattermost, Home Assistant, Webhooks, A2A, BlueBubbles (iMessage), Photon iMessage, Buzz, DingTalk, Feishu/Lark, Google Chat, IRC, LINE, Microsoft Graph webhook, ntfy, Open WebUI, QQ Bot, Raft, Hermes Relay, SimpleX Chat, Microsoft Teams (and Teams Meetings), WeCom (and callback), Weixin, Yuanbao. (Messaging overview.)
- **Teams and meetings:** Teams Meetings is its own page. (Messaging list.)
- **API server:** an OpenAI-compatible HTTP endpoint for frontends such as Open WebUI, LobeChat and LibreChat. (Features Overview.)
- **ACP (IDE integration):** runs inside VS Code, Zed and JetBrains; chat, tool activity, diffs and terminal output render in the editor. (Features Overview; `acp_adapter/` in source.)
- **Voice:** CLI microphone mode; spoken replies in messaging; Discord voice channels; wake word ("Hey Hermes") on CLI, TUI and desktop with an on-device hotword listener; speech-to-text for voice messages. (Voice Mode; Wake Word.)
- **Text-to-speech:** ten native providers (Edge TTS free; ElevenLabs; OpenAI; MiniMax; Mistral Voxtral; Google Gemini; xAI; NeuTTS; KittenTTS; Piper), plus custom command providers. (Features Overview.)
- **Vision and images:** paste images into the CLI; image generation through FAL.ai (eleven models, including FLUX, GPT-Image, Nano Banana Pro, Ideogram, Recraft, Qwen, Z-Image, Krea). (Vision; Image Generation.)

## 4. Tools and integrations

- **MCP:** connects to MCP servers over stdio or HTTP; per-server tool filtering; sampling support; utility wrappers for resources and prompts. Claude Code's `mcpServers` block migrates with `hermes import-agent claude-code` (the `agent-importers` plugin). (MCP.)
- **Browser automation:** backends include Browserbase (cloud), Browser Use (cloud), local Chrome, Brave, Chromium or Edge over CDP, and local Chromium. (Features Overview; Browser.)
- **Computer use:** a page exists (Computer Use). Details not read.
- **Web search and extract:** page exists (Web Search & Extract). **X (Twitter) search:** page exists.
- **Spotify:** page exists.
- **Passwords and logins:** a credential vault page exists ("Passwords & Logins"). Details not read.
- **Nous Tool Gateway:** web search, image generation, text-to-speech and browser in one Nous Portal login (`hermes setup --portal`). (Features Overview.)
- **Provider routing:** sort by cost, speed or quality; whitelists, blacklists and priority order. (Provider Routing.)
- **Fallback providers:** automatic failover to backup providers, including separate fallbacks for vision and compression. (Fallback Providers.)
- **Credential pools:** several keys for one provider with rotation on rate limits or failures. (Credential Pools.)
- **Prompt caching:** a built-in one-hour prefix cache for Claude on native Anthropic, OpenRouter and Nous Portal. (Features Overview.)
- **Subscription proxy:** a page exists. Details not read.
- **Language packs, skins and themes, pets (Petdex mascots):** cosmetic features, pages exist.

## 5. Plugins

Three plugin types: **general plugins** (tools and hooks), **memory providers**, and **context engines** (alternative context management). Managed through `hermes plugins`. A plugin catalogue exists. The source has 24 plugin directories, including `browser`, `computer_use`, `config_backends`, `context_engine`, `cron_providers`, `dashboard_auth`, `delegation`, `google_meet`, `image_gen`, `kanban`, `memory`, `model-providers`, `platforms`, `security-guidance`, `teams_pipeline`, `video_gen`, and `web`. (Plugins; source.)

## 6. Models and providers

- Hundreds of models through one Nous Portal login; OpenRouter; local servers (Ollama, vLLM); any OpenAI-compatible API; ChatGPT sign-in for Codex models; SuperGrok or X Premium+ sign-in for Grok models; Anthropic API key for Claude. (Compare page, Questions; Configuring Models.)
- Auxiliary tasks (summarisation, vision, compression) can use different models. (Configuring Models.)
- Architecture page: three API modes (chat completions, Codex responses, Anthropic).

## 7. Operations

- Installation in about 60 seconds; updating and uninstalling; Nix flakes; Docker. (Installation; Updating; Nix Setup.)
- Sessions: `state.db` (SQLite); export to JSONL, HTML, Markdown; pin, rename, prune ended sessions older than 90 days by default. (Sessions; Session Storage.)
- Profiles: named isolated homes under `profiles/<name>/`, each with its own config, logs and state. (Session Storage; Profiles.)
- Session heartbeats and a Desktop-attached gateway.

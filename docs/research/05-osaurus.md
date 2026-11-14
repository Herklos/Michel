# Research 05: Osaurus

Date of research: 2026-11-14. Status: research complete from the GitHub README. The documentation site and its architecture page were unreachable, so architecture details are thin. The product is macOS-only and was not run.

## 1. Summary

Osaurus is an MIT-licensed, open-source agent harness for macOS, written in Swift for Apple Silicon. It runs agents with persistent memory, skills, tools and autonomous execution, using either local models (MLX) or cloud models. It exposes a local API that speaks several provider-compatible wire formats, so existing clients can use it. Its main design goal is that data stays on the Mac unless the user opts in to a cloud model or a connected feature.

## 2. Sources and access

| # | Source | Access | Result |
|---|---|---|---|
| S1 | https://github.com/osaurus-ai/osaurus (README) | Read via the web-fetch agent (HTTP 200, full README) | Primary source for this file |
| S2 | https://docs.osaurus.ai/ | DNS failure (`getaddrinfo ENOTFOUND docs.osaurus.ai`) | Not read |
| S3 | https://docs.osaurus.ai/architecture | Same DNS failure | Not read |
| S4 | https://docs.osaurus.ai/chat-interface, `/app-intents` | Search result URLs only | Not read |
| S5 | https://github.com/osaurus-ai/osaurus-tools (plugin registry) | Named in the README | Not read |
| S6 | Search: "Osaurus AI agent app features" (standard mode) | Search tool | Snippets. Secondary sites (blog.brightcoding.dev, chatgate.ai, scriptbyai.com) describe the app; not read in full. Claims are consistent with the README. |

Note on S1: the content was retrieved through a fetching sub-agent, so the quotes below come from its report. They should be re-checked against the file on GitHub before any external use.

## 3. Facts from the README

**Identity.** Repo "About": "Own your AI. The open-source agent harness for macOS. Run local or cloud models with persistent memory, skills, tools, and autonomous execution. Built in Swift." Intro: "Agents, memory, tools, and identity that live on your Mac. Built purely in Swift. Fully offline. Open source." Also: "Nothing leaves your Mac unless you choose a cloud model or turn on a feature that connects out."

**License and platform.**
- MIT.
- Native Swift on Apple Silicon. No Electron.
- macOS 15.5 or later. The sandbox VM and Apple Foundation Models need macOS 26 or later.
- Install: `brew install --cask osaurus`, or a DMG from GitHub Releases (about 70 MB standard; about 4 GB "full" build with Raptor 0.7 bundled, per the README).
- Source build: Xcode 26 or later and Git LFS.

**Front end.** One "Orchestrator" assistant routes each request. It can answer directly, change settings (after an approval card), hand work to a built-in agent, use a helper, or run a workflow. Default team on a fresh install: Planner (Calendar and Reminders), Courier (Mail), Keeper (Downloads and Notes), Scout (web). Builder (a project folder) appears on developer-configured Macs. Helpers: Research, Files, Browser, Code (isolated sandbox).

**Features.**
- **Agents.** Each has its own prompt, model, tools, memory, working folder and avatar. They run on Osaurus's own agent loop (`docs/AGENT_LOOP.md`) or an external harness such as Claude Code (`docs/HARNESS_RUNTIMES.md`).
- **Workflows and the Architect.** Typed, repeatable multi-step workflows. A built-in Architect agent designs, tests and fixes them.
- **Automations.** "Run a workflow, an agent, or a model on a schedule, a folder change, a webhook, or a feed." (`docs/AUTOMATIONS.md`)
- **Memory and knowledge.** Layered memory and document libraries that agents can search (`docs/MEMORY.md`, `docs/KNOWLEDGE.md`).
- **Sandbox.** Code runs in an isolated Linux VM with a per-agent user and home folder, on macOS 26 or later (`docs/SANDBOX.md`).
- **Browser and computer use.** Per-agent browser session and macOS control, with per-app autonomy rules. Both off by default.
- **Apple apps.** Calendar, Reminders, Contacts, Notes, Mail, Messages, Maps, Music, Shortcuts as native tools, enabled per agent.
- **Channels.** Discord, Slack, Telegram, iMessage, WhatsApp, Email, n8n, with strict allowlists.
- **Privacy filter.** An on-device classifier replaces names, emails, keys and other secrets with placeholders before a cloud send. "It fails closed if anything leaks."
- **Identity and secure channels.** Each agent has a cryptographic address, can be reached through a relay, and talks to other Osaurus agents end to end encrypted (`docs/IDENTITY.md`, `docs/SECURE_CHANNEL.md`). Relay wording is the only tunnel-like feature stated.
- **Devices and workspaces.** End-to-end encrypted chat sync between Macs and iPhone. Agents and workflows can be shared with teammates (`docs/SYNC.md`, `docs/OSAURUS_WORKSPACES.md`).
- **Voice.** On-device transcription, wake word, and a system-wide dictation hotkey (`docs/VOICE_INPUT.md`).
- **Images.** On-device image generation and editing with local image models.
- **Skills and plugins.** Imports Agent Skills and Claude plugins, or installs native plugins from a registry (`docs/SKILLS.md`, `docs/CLAUDE_PLUGINS.md`).
- **MCP both ways.** Osaurus is an MCP server for other clients, and an MCP client for remote MCP services with one-tap OAuth (`docs/REMOTE_MCP_PROVIDERS.md`).
- **System integration.** "Ask Osaurus" and "Run Osaurus Agent" through Spotlight, Siri, and Shortcuts (`docs/APP_INTENTS.md`).

**Models.**
- Local: Gemma, Qwen, GPT-OSS, Llama, LFM and others, run with MLX on Apple Silicon. Stored in `~/MLXModels` (override with `OSU_MODELS_DIR`). Existing Hugging Face cache or LM Studio models can be used.
- Apple Foundation Models on macOS 26 or later, as `foundation`.
- Cloud: OpenAI, Anthropic, Gemini, xAI, Venice AI, OpenRouter, Ollama, LM Studio, or any OpenAI-, Anthropic- or Open-Responses-compatible endpoint.
- Osaurus Cloud through "Osaurus Router" (pay as you go).

**Local API.** Base `http://127.0.0.1:1337`:

| Path | Format |
|---|---|
| `/v1/chat/completions` | OpenAI. Strict semantics: returns `tool_calls` for the client to run. |
| `/v1/responses` | Open Responses |
| `/v1/messages` | Anthropic |
| `/api/chat` | Ollama |
| `POST /agents/{id}/run` | Server-side autonomous agent run |

CLI: `osaurus ui`, `osaurus serve` (`--expose` for LAN access), `osaurus status`, `osaurus stop`, `osaurus mcp` (stdio MCP entry point). Network-exposed MCP uses `OSAURUS_MCP_ACCESS_KEY` (format `osk-v1...`).

**Storage and privacy.**
- Chats, memory, agents and configuration live in `~/.osaurus/`. Plaintext by default, protected by FileVault. Opt-in SQLCipher encryption (`docs/STORAGE.md`).
- Anonymous aggregated analytics through Aptabase, on by default, can be turned off under Settings → Privacy & Security.
- Crash and hang reports to Sentry, on by default, with a separate toggle. Source builds have both off unless keys are configured.

**Repository layout.** `App`, `Packages/OsaurusCore`, `sandbox`, `scripts`, `docs`, `helpers/osaurus-wa`, plus an Xcode workspace `osaurus.xcworkspace`.

## 4. Relevance to this project

Patterns worth comparing with the grokbot backend:

1. **Automations** triggered by schedule, folder change, webhook or feed. Our backend has schedules only, through Temporal Schedules. Webhook and folder triggers are missing.
2. **Approval card before settings changes.** Similar to our `interrupt_on` gate, applied to configuration.
3. **Privacy filter before cloud send.** We have no equivalent. This would be a worker-side activity that redacts model input before the model activity runs.
4. **Per-agent sandbox.** Our `FilesystemBackend` workspace is weaker than a VM-level sandbox.
5. **Local OpenAI-compatible API.** Our gateway is FastAPI and is not OpenAI-compatible. Adding a `/v1/chat/completions` shim would let existing clients use our bots.
6. **Allowlisted channels.** Matches our `ALLOWED_SENDERS` and `CHANNEL_WEBHOOKS`.

Osaurus is a single-user, local-first desktop product. It does not use Temporal. Its durability model (how a scheduled run survives a restart) is not described in the README.

## 5. What still needs to be tested

1. **Read the docs site** once `docs.osaurus.ai` is reachable. Priority pages: `AGENT_LOOP`, `AUTOMATIONS`, `INFERENCE_RUNTIME`, `SANDBOX`, `PLUGIN` authoring.
2. **Confirm the durability model.** Does a scheduled automation resume after a crash or reboot, or is it dropped?
3. **Run the local API** and confirm each wire format with a real client: the OpenAI SDK, the Anthropic SDK, and an Ollama client. Check how `tool_calls` are returned.
4. **Confirm the privacy filter** on a set of test secrets, and check it fails closed when a cloud model is selected.
5. **Test the approval card** for settings changes, and check whether it can be bypassed by an agent.
6. **Test the relay and E2E channel**: that messages are encrypted and that relay operators cannot read them. The README does not say how keys are exchanged.
7. **Verify the license file** (`LICENSE`) directly. The README says MIT.
8. **Run the app on a Mac** (macOS 26 for sandbox and Foundation Models) to see the bot lifecycle. This cannot be done from this Linux sandbox.

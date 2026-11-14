# 08. Clients and surfaces: dashboard, CLI, desktop, mobile, plugins, Claude Code

Sources: `ui/package.json`, `ui/AGENTS.md` (not read in full), `desktop/README.md`, `cli/README.md`, `mobile/README.md`, `bridge-client/package.json`, `claude-code-plugin/.claude-plugin/plugin.json`, `plugins/`, `docs/PLUGINS.md`, `packages/`, `Makefile`. Read 2026-11-14.

## 1. Web dashboard (`ui/`)

- **Stack** (from `ui/package.json`): React with `react-dom`; TanStack Start, Router, Query and Virtual; `@langchain/react`, `@langchain/langgraph-sdk` and `@langchain/macaw-components` (LangChain's UI kit); Tailwind CSS; Vite; Nitro server; Zustand; Lexical (rich text); Monaco (editor); `@pierre/diffs` and `@pierre/trees` (diff and file tree); Mermaid; Shiki (highlighting); Sonner (toasts); `capnweb` (plugins). Telemetry: Datadog RUM, PostHog, Segment.
- **Scripts:** `dev`, `lab`, `build`, `preview`, `test` (Vitest), `typecheck`.
- **Conventions** (`AGENTS.md`): read `ui/AGENTS.md` and `ui/DESIGN.md` before changing it. The dashboard uses the React Compiler, so memoization is written as plain expressions. User-initiated mutations are **optimistic**: update immediately, roll back on failure, show an error toast.
- **Serving:** the built UI is served by the backend at `/` (`DASHBOARD_STATIC_DIR`), with a mount prefix from `langgraph.json`.

## 2. Command line (`cli/`)

- `robin` (and the legacy `oswe`) "starts a normal cloud Robin agent on a remote deployment and makes the current directory on the machine running it that agent's sandbox."
- The agent's shell, uploads and downloads run **locally, unsandboxed, as the user**. The CLI long-polls the backend, runs requests, and posts results back. Because the deployment cannot dial the machine, the CLI makes an outbound connection.
- Install: Homebrew cask `langchain-ai/tap/open-swe-desktop` (Apple Silicon, macOS Ventura or later) or standalone downloads (`darwin-arm64`, `darwin-x64`, `linux-arm64`, `linux-x64`) with `robin-SHA256SUMS`. macOS binaries are signed and notarized (per the README).
- Source: `cli/src/` (`main.ts`, `api.ts`, `stream.ts`, `login.ts`, `credentials.ts`, `git.ts`, `config.ts`, `input.ts`), tests in `cli/test/`.

## 3. Shared bridge (`bridge-client/`)

- Package `open-swe-bridge-client` 0.1.0, private, "the machine side of a Robin sandbox bridge, shared by the robin CLI and the desktop app."
- TypeScript built with `tsc`; tests run with `bun test`. Exports `dist/index.js` and a Bun source entry.
- Code: `bridge.ts` (session), `executor.ts` (runs commands), `github-remote.ts` (git remote handling), `api.ts` (backend calls), `json.ts`.

## 4. Desktop app (`desktop/`)

- **Electron** app, labeled experimental. The web UI is recommended.
- The app **downloads a standalone UI release** selected by the connected backend and keeps the last complete UI on disk for offline use. No dashboard is embedded in the installer. First launch needs connectivity.
- **"This Mac"** in the new-task composer runs a thread over a selected local project. The thread is an ordinary cloud thread (same transcript, models, settings, MCPs, skills), with the sandbox being the Mac's project.
- Commands run with the login shell's environment, minus secret-shaped variables (except `GITHUB_TOKEN` and `GH_TOKEN`).
- A thread runs only while the app that started it is open. Quitting closes the bridge; the thread is visible elsewhere but only this Mac can continue it.
- Modules: `main.cts`, `local-bridges.cts`, `local-thread-store.cts`, `terminal-manager.cts`, `project-store.cts`, `git-diff.cts`, `preview-files.cts`, `login-server.cts`, `diagnostics.cts`, `desktop-environments.cts`. Tests in `desktop/test/`.
- Release-gating rule (`AGENTS.md`): native shell, preload, bundled bridge, packaging and incompatible IPC changes need a desktop release; UI-only and backend-only changes do not.

## 5. iOS app (`mobile/`)

- **Expo (React Native)** client for iOS only, requiring Xcode 26+ and CocoaPods. Needs a development build (not Expo Go) because it includes a native auth module (`modules/open-swe-auth`) and `@expo/ui` SwiftUI controls.
- **Screens** (`src/app/`): inbox (categories: All Agents, Needs Attention, Working, In Review; workspaces as repositories), agent list, thread transcript (`thread/[id]`), changes and diffs (`changes/[id]`), details, customize, new agent (repository picker), sign-in.
- **Core** (`src/core/`): `apiClient.ts`, `agentService.ts`, `serverSentEvents.ts` (streaming), `transcript.ts`, `diffLines.ts`, `signIn.ts`, `accountStore.ts`; `demoAgentService.ts` provides in-memory sample agents without a backend.
- **Sign-in:** either a Robin backend URL through the browser, or the local dev login through the `gh` CLI user when the backend runs under `langgraph dev`.

## 6. Plugins (sandboxed web apps)

- SDK: `plugins/sdk` (`@openswe/plugin-sdk`, imported by the dashboard's plugin host).
- Examples: `plugins/starter` (small app), `plugins/docs` (Markdown pages in a repository, edited live and published as pull requests), `plugins/design-qa`.
- Runtime limits (`docs/PLUGINS.md`): opaque origin (no cookies or storage APIs); CSP `default-src 'none'` (no network); no navigation; forms never submit; clipboard write allowed. Data flows through the host API over Cap'n Web, checked by both the web UI and the backend against installer approvals and the person's GitHub access.
- Storage APIs are the only persistence (`docs/PLUGINS.md` "Storage").
- Docs state the WebRTC constraint: the host removes `RTC…` interfaces from the plugin window, which "isn't a wall against code written to get around it".

## 7. Claude Code plugin

- `claude-code-plugin/`: plugin `robin` (version 0.1.0), described as "Mirror Claude Code sessions into Robin threads, use Robin's MCP tools, and find a session's thread." Author LangChain, MIT.
- User configuration: `server_url` (Robin URL; default is the hosted deployment).
- Skills: `connect` (`skills/connect/SKILL.md`, `connect.py`) and `thread` (`skills/thread/SKILL.md`). `.mcp.json` connects Claude Code to Robin's MCP server.
- Backend side: `openswe/claude_code/` with `hooks.py`, `transcript.py`, `sync_tokens.py`, `routes.py`; `/dashboard/api/claude-code/*` endpoints.

## 8. Evaluation harnesses (`evals/`)

- `evals/reviewer/`: offline reviewer eval over 50 PRs and 173 golden comments from `withmartian/code-review-benchmark`, with LangSmith dataset building, a judge, cost accounting, and live status reporting to the dashboard (`status_reporter.py`).
- `evals/ask_messages/`: evaluation of message handling (`run_eval.py`).
- `evals/model_request.py`: shared helper for requests.
- Golden comments for five open-source repositories: `cal_dot_com`, `discourse`, `grafana`, `keycloak`, `sentry`.

## 9. Plugins vs. Managed Deep Agents' channels

Both let outside surfaces start runs, but they differ: plugins are **front-end apps inside Robin's dashboard**, with no network and no backend code. Channels are **inbound event sources** that start runs in the MDA runtime. A new integration usually means a channel, not a plugin.

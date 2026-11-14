# 06. Identity, authorisation, Agent Auth, Context Hub, Prompt Hub, and managed MCP

Sources: docs pages `auth`, `custom-auth`, `set-up-custom-auth`, `add-auth-server`, `resource-auth`, `store-auth`, `openapi-security`, `agent-auth` (read in full); `use-the-context-hub`, `context-hub-webhooks`, `prompt-context-hub`, `prompt-commit`, `create-a-prompt`, `manage-prompts`, `use-tools`, `langsmith-remote-mcp`, `langsmith-mcp-server`, `server-mcp-elicitation` (read in part). Read 2026-11-14.

## 1. Two kinds of "auth" in the docs

- **Authentication** ("who is calling") and **authorisation** ("what may they do on this resource"). The docs keep them apart. Authentication runs as middleware on every request through an `@auth.authenticate` handler. Authorisation runs per resource through `@auth.on` handlers.

## 2. Default security models

- **LangSmith (default):** LangSmith API keys in the `x-api-key` header. A custom auth handler can replace or extend this; `auth.allow_langsmith_api_keys` lets both work side by side (Agent Server 0.14.0rc2+). Custom auth is supported on all plans.
- **Self-hosted:** no default authentication; the operator supplies it.

Reference architecture from the docs: an identity provider (Auth0, Supabase Auth, Okta or a custom server) issues tokens; the Agent Server is the resource server that validates tokens and enforces access; client applications hold the tokens.

## 3. Resource-level isolation

- Authorisation handlers receive a resource (thread, assistant, run) and return **metadata** (for example the owner's ID) plus **filters**. Searches and reads are then limited to resources the caller owns.
- Worked example (`resource-auth`): every user gets private conversations, implemented by one handler that stamps each thread with its owner and filters lists to that owner.

## 4. Store isolation

- The Agent Server includes a **Postgres-backed store** for long-term cross-thread memory. Namespaces are tuples defined by the application (for example `("memories", "preferences")`), so authorisation is per namespace and per key, not by a built-in owner field.
- The auth handler validates the caller and returns a unique identity; the store handler scopes namespaces to it.

## 5. Agent Auth (beta)

"Enable secure access from agents to any system using OAuth 2.0 credentials."
- **Client libraries:** `langchain-auth` (Python) and `@langchain/auth` (JavaScript). The client takes a LangSmith API key and, when self-hosted, the `/api-host` URL (`LANGSMITH_API_URL`).
- **Set-up:** choose a provider identifier (for example `github-local-dev`), create an OAuth application at the provider, and register the LangSmith callback URL `https://smith.langchain.com/host-oauth-callback/{provider_id}` (Cloud; self-hosted uses the instance's own callback).
- **Flow:** an agent asks for a connection for a provider and user; if no grant exists, LangSmith starts an OAuth authorisation session (`/v1/agent-auth/oauth-authorization-sessions`), the user consents in the browser, and the grant is stored. Agents then get tokens for their calls. Other endpoints in the platform API: `/v1/agent-auth/connections`, `/credentials`, `/principals`, `/oauth-providers`.
- The docs mark the feature beta and under active development.

## 6. Context Hub (versioned agent and skill bundles)

- A **context** is a versioned bundle: an **agent** (an `AGENTS.md` file and tools) or a **skill** (a `SKILL.md` file, with a required description).
- Each save creates a **commit** in the history panel; any commit can be browsed. Markdown is read in Preview; the Edit tab shows raw text.
- **Environments** let a context be promoted to an environment (for example staging, then production), so running agents pull the version for their environment. Promotion is the step that makes a commit live.
- **Commit webhooks** (`context-hub-webhooks`) notify external systems when a context commit lands.
- Context Hub mounts can be attached to sandboxes (`sandbox-mounts`), so an agent reads its memory as files.
- Requires the Context Hub feature to be enabled for the workspace and the right permissions.

## 7. Prompt Hub

Prompts are versioned objects, created in the UI or from the SDK. Prompts can be committed to GitHub (`prompt-commit`), synced programmatically (`manage-prompts-programmatically`), use template formats (`prompt-template-format`), include multimodal content, and reference tools (`use-tools`). The Playground runs them against model providers (`playground-model-providers`).

## 8. Managed MCP and tool kits

- The Agent Server exposes its own **MCP endpoint** at `/mcp` (Streamable HTTP), so a deployed agent can be called as a tool from Claude Code or another MCP client. Protocol revisions `2024-11-05` through `2026-07-28` are supported.
- **LangSmith Remote MCP** and the **LangSmith MCP Server** let clients query LangSmith itself (traces, prompts, datasets) through MCP.
- **Managed tool kits** (LangSmith Tools): hosted MCP servers and kits (`/v1/managed-tools/servers`, `/kits`), with OAuth consent through Agent Auth. Fleet's tool pages name Arcade and Salesforce integrations (file 07). Harbor is an evaluation harness, not a tool kit (see file 04).
- **MCP elicitation** lets an MCP server ask the user for input mid-run; the human answer goes back through the run (`server-mcp-elicitation`).

## 9. Tokens and key types (verified in the docs)

- `lsv2_pt_` personal access tokens carry the creator's permissions.
- `lsv2_sk_` service keys are workspace-level and tied to no user.
- `lsv2_tr_` appears in the docs as a third prefix; its purpose was not read.

# Research: Temporal Deep Agents, LangChain Deep Agents, and Grok-Bot-style products

> **Status note (2026-11-14).** This is the first combined summary, written during the first research session. It is superseded by the per-topic notes in `docs/research/README.md`. Some sections below say sites were unreachable; a later check showed `docs.temporal.io`, `docs.langchain.com` and `cursor.com` reachable. Section 5 is out of date for those hosts.

Sources were read on 2026-11-14. Each claim names where it came from. Pages that
could not be reached are listed at the end. Nothing in this file is taken from
memory without a source.

## 1. Temporal Deep Agents integration

**Where it lives now.** The integration moved out of the SDK. The SDK still ships
`temporalio.contrib.deepagents` (temporalio 1.36.0, wheel inspected), but its
`README.md` says the integration "has moved to the independently versioned
`temporalio-deepagents` package. Its canonical Python API is `temporalio.deepagents`."
Source: `temporalio/contrib/deepagents/README.md` in the 1.36.0 wheel, and
https://github.com/temporalio/ai-integrations/tree/main/python/deepagents#readme.

The version used here is `temporalio-deepagents==0.0.3`, which the README calls
"Pre-release". Source: the package README at
https://raw.githubusercontent.com/temporalio/ai-integrations/main/python/deepagents/README.md.

**Install and wiring.**
- `uv add "temporalio-deepagents"`; Python ≥ 3.11.
- Import `from temporalio.deepagents import DeepAgentsPlugin, create_temporal_deep_agent`.
- Add `plugins=[DeepAgentsPlugin(...)]` to the Client. The plugin propagates to any Worker built from that client.

**Core model.** The agent's control loop runs and replays deterministically inside
the workflow. Each LLM call becomes an activity (`deepagents.invoke_model`, plus
`invoke_model_streaming` when streaming is on). I/O tools become activities via
`activity_as_tool` / `tool_as_activity`. Real file and shell operations become
`deepagents.backend_op` activities through `TemporalBackend`. The plugin registers
four built-in activities per instance. Source: the package README, "What this plugin gives you" and "Runtime behavior".

**Tools.** A tool that only changes agent state can stay in the workflow. A tool
that does I/O must be wrapped. An unwrapped non-builtin tool runs in the workflow,
and the plugin warns at construction. `tool_as_activity` must run at import or
startup on every activity worker, because registration is process-local. Source:
the package README, "Tools: the Workflow-vs-Activity choice".

**Human-in-the-loop.** `interrupt_on={...}` plus a durable-looking checkpointer
(in practice `InMemorySaver`, rehydrated by replay). `ainvoke` returns
`__interrupt__` in the workflow. The workflow waits on a Query and an Update.
Source: the package README, "Human-in-the-loop".

**Continue-as-new.** `run_deep_agent(..., state_snapshot=...)` carries messages
and file state, but not todos (`TodoListMiddleware` marks them `OmitFromInput`).
A durable checkpointer that does its own I/O is not replay-safe in a workflow, and
the plugin warns about it. Source: the package README, "Continue-as-new".

**Testing.** `FakeModel`, `fake_model_factory`, `mock_model_provider` and `MockTool`
in `temporalio.deepagents.testing`. Source: `testing.py` in the package.

**Constraints I found in the source and docs.**
- One `DeepAgentsPlugin` instance per Worker, and the same configuration on Client and Worker. A second instance fails with `ValueError` at Worker start.
- A filesystem backend's root must be reachable from every activity worker that can run that operation, or those activities need their own task queue.
- Factory arguments are recorded in workflow history. Credentials stay in the worker-side factory.
- The Temporal dev server could not be started in this sandbox (see section 5), so this project's workflows have not been executed against a Temporal server.

## 2. LangChain Deep Agents (deepagents 0.7.38)

Verified from the PyPI wheel, `deepagents-0.7.38-py3-none-any.whl`, and its
`METADATA` (https://pypi.org/project/deepagents/). The docs site
(docs.langchain.com) was unreachable from this session.

Modules that show the feature set:
- **Planning:** `TodoListMiddleware` (`write_todos`).
- **Filesystem:** `middleware/filesystem.py`, with `backends/` for `state`, `filesystem`, `local_shell`, `store`, `composite`, `sandbox`, `langsmith`, `context_hub`.
- **Subagents:** `middleware/subagents.py`. A `SubAgent` spec takes `name`, `description` and optional `tools`, `system_prompt`, and so on. A `CompiledSubAgent` takes a pre-built runnable. `mode="fork"` is experimental.
- **Memory and skills:** `middleware/memory.py`, `middleware/skills.py`.
- **Human-in-the-loop:** `interrupt_on`, plus `middleware/permissions.py` and `_fs_interrupt.py`.
- **Context management:** `middleware/summarization.py`, `_message_eviction.py`, `_blob_offload.py`, `_overflow_clip.py`, `_prompt_caching.py`.
- **Model profiles:** `profiles/`, with harness profiles for Anthropic Haiku 4.5, Sonnet 4.6, and Opus 4.7.
- **Entry point:** `create_deep_agent(model=..., tools=..., subagents=..., backend=..., interrupt_on=..., checkpointer=..., system_prompt=...)` in `graph.py`.

## 3. Grok Bot (SpaceXAI / Cursor)

Only search snippets were available. The product pages (`cursor.com/docs/grok-bot.md`)
and the news and blog pages failed with DNS errors, so details below are
provisional.

- A search summary says Grok Bot launched in beta, with access limited to some Cursor and SuperGrok subscribers. Sources: https://thenextweb.com/news/spacexai-grok-bot-ai-agents-cursor and https://cursor.com/docs/grok-bot.md (not loaded).
- A blog review said Grok Bot is closed source, runs only xAI models, and cannot be self-hosted. Source: https://openalternative.co/alternatives/grok-bot (search snippet only).
- A ZenML write-up about "persistent, multi-agent workflows for Grok Bot" argues always-on agents need a durable workflow engine such as Temporal or Restate, since runs can last a day or more. Source: https://www.zenml.io/llmops-database/designing-persistent-multi-agent-workflows-for-grok-bot (not loaded; snippet only).

The shape of the product, as far as these sources go: long-running, persistent
agents; multi-agent work; durable execution; and a chat-style front end. This is
what the backend mirrors.

## 4. Noodle and Osaurus (open-source alternatives)

**"Noodle" is ambiguous.** Several products share the name. The one matching a
Grok Bot alternative is `pdparchitect/noodle`, a personal-agent app.
- Source: https://raw.githubusercontent.com/pdparchitect/noodle/main/README.md, read directly.
- License: Apache-2.0 (per the README).
- Platform: Mac, iPhone and iPad apps, with a "Noodle Server" for Linux.
- Features, as stated in the README:
  - **Harnesses:** runs agents on the user's own harness and account: Codex, Claude Code, FX, Grok Build, Muse Code, OpenCode v2, Antigravity, Apple Intelligence.
  - **Groups:** several agents in one conversation working toward a shared goal.
  - **Computers:** a sandboxed Linux, macOS or Windows machine per agent.
  - **Browser:** signed-in browsers assigned to agents, with persistent profiles.
  - **Applet:** tools, websites and games that agents build and run.
  - **Hub / Server:** share harnesses with family and friends from an always-on machine. The Server is for Linux, with each bot in its own sandbox.
  - **Security:** access restricted by default, with per-bot folder sharing.

Other "Noodle" projects (a Seed no-code assistant, a Noodl AI feature, an education
TA) are unrelated. The poteto/noodle project is a Go coding framework. Source: search
results; the poteto project is at https://poteto.github.io/noodle.

**Osaurus.** Read from the GitHub README, https://github.com/osaurus-ai/osaurus
(loaded). The docs site (docs.osaurus.ai) was unreachable.
- License: MIT. Native Swift for macOS on Apple Silicon. macOS 15.5+; the sandbox and Apple Foundation Models need macOS 26+.
- Agents: each agent has its own prompt, model, tools, memory, working folder and avatar. Runs on Osaurus's own agent loop, or on an external harness such as Claude Code.
- Workflows: typed, repeatable multi-step workflows, plus an "Architect" agent that designs and tests them.
- Automations: run a workflow, agent or model on a schedule, a folder change, a webhook, or a feed.
- Memory and knowledge: layered memory and searchable document libraries.
- Sandbox: agents run code in an isolated Linux VM, with a per-agent user and home folder.
- Channels: Discord, Slack, Telegram, iMessage, WhatsApp, Email, n8n, with strict allowlists.
- Privacy filter: an on-device classifier redacts names, emails, keys and other secrets before any cloud call, and fails closed.
- Identity and relay: each agent has a cryptographic address, is reachable through a relay, and talks to other Osaurus agents end-to-end encrypted.
- Models: local MLX models, plus OpenAI, Anthropic, Gemini, xAI, OpenRouter, Ollama and any OpenAI-, Anthropic- or Open-Responses-compatible endpoint.
- Local API: `http://127.0.0.1:1337` with `/v1/chat/completions`, `/v1/responses`, `/v1/messages`, `/api/chat`, and `POST /agents/{id}/run` for server-side autonomous runs.
- Skills and MCP: imports Agent Skills and Claude plugins, and is both an MCP server and an MCP client.

## 5. What could not be verified

| Source | Result |
|---|---|
| docs.temporal.io/develop/python/integrations/deepagents | DNS failure. The same content was read from the installed package README and source. |
| docs.langchain.com/oss/python/deepagents/overview | DNS failure. Replaced by package metadata and source. |
| cursor.com/docs/grok-bot.md | DNS failure. Grok Bot details are from search snippets only. |
| thenextweb.com, zenml.io articles | DNS failure. Snippets only. |
| docs.osaurus.ai | DNS failure. README used. |
| Temporal dev server binary (temporal.download, GitHub releases) | Blocked. `WorkflowEnvironment.start_local()` cannot start, so no workflow was run end to end. |

Consequence: the offline tests verify the agent graph, approval gating, history
restore, tool policy and the HTTP-to-Temporal mapping. They do not verify
workflow execution, the Worker's sandbox validation, or activity dispatch. Run
`tests/` against `temporal server start-dev` before relying on it.

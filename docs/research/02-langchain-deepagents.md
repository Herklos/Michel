# Research 02: LangChain Deep Agents (`deepagents`)

Date of research: 2026-11-14. Status: research complete from the package, not from the docs site; no runtime test executed (see section 7).

## 1. Summary

Deep Agents is a LangChain agent harness. It wraps a tool-calling model with planning (todos), a filesystem abstraction, sub-agent delegation, memory and skills, human-in-the-loop approval, and context management. The entry point is `create_deep_agent(...)`, which returns a LangGraph graph.

Version researched: `deepagents==0.7.38` (PyPI wheel `deepagents-0.7.38-py3-none-any.whl`, MIT license, requires Python ≥ 3.11).

## 2. Install

From the package metadata:

```bash
uv add deepagents
```

Direct dependencies at this version: `langchain>=1.5.0,<2`, `langchain-core>=1.8.0,<2`, `langchain-anthropic>=1.7.10,<2`, `langchain-google-genai>=4.4.3,<5`, `langsmith>=0.14.17`, `packaging>=23.2`, `wcmatch>=11.0`. Optional extras: `aws` (langchain-aws), `quickjs` (langchain-quickjs), `video` (av, pillow).

## 3. Features and where they live (package source)

The feature list below comes from the module layout of the installed wheel. Each row names the file, so claims can be checked by reading the code. The docs site could not be read.

| Feature | Module(s) | Notes from the source |
|---|---|---|
| Planning / todos | `middleware/` `TodoListMiddleware` (`write_todos`) | Todos are marked `OmitFromInput` in state |
| Filesystem tools | `middleware/filesystem.py` | Read, write, edit, list, and similar tools over a backend |
| Backends | `backends/`: `state`, `filesystem`, `local_shell`, `store`, `composite`, `sandbox`, `langsmith`, `context_hub`, `protocol`, `utils` | `StateBackend` is the default; it keeps files in graph state |
| Sub-agents | `middleware/subagents.py`, `middleware/async_subagents.py` | `SubAgent` spec: `name`, `description`, optional `tools`, `system_prompt`, `middleware`, `mode`. `CompiledSubAgent` takes a pre-built runnable. `mode="fork"` is experimental. |
| Memory | `middleware/memory.py` | Long-term memory middleware |
| Skills | `middleware/skills.py`, `middleware/_skill_tools.py` | Agent Skills support |
| Human-in-the-loop | `interrupt_on` argument; `middleware/_fs_interrupt.py`, `middleware/permissions.py` | Interrupts before named tools; filesystem permissions |
| Context management | `middleware/summarization.py`, `_message_eviction.py`, `_blob_offload.py`, `_overflow_clip.py`, `_prompt_caching.py` | Summarizes history, evicts and offloads large messages, clips overflow, enables prompt caching |
| Rubric / quality | `middleware/rubric.py` | Present in the package; not studied |
| Video | `middleware/_video.py` | Optional `video` extra |
| Model profiles | `profiles/`: `provider/` (OpenAI, OpenRouter, NVIDIA), `harness/` (Anthropic Haiku 4.5, Sonnet 4.6, Opus 4.7, OpenAI Codex, NVIDIA Nemotron) | Per-model tuning of the harness |
| Tool exclusion | `middleware/_tool_exclusion.py`, `_excluded_middleware.py` | Remove tools or middleware per model |
| Graph factory | `graph.py` | `create_deep_agent` |

## 4. Main API

`create_deep_agent` is in `graph.py`. The parameters used in this project:

- `model`: model name string or a LangChain chat model instance
- `system_prompt`
- `tools`: LangChain tools or plain callables
- `subagents`: list of `SubAgent` dicts
- `backend`: backend instance (default is `StateBackend`)
- `interrupt_on`: map of tool name to approval config. Requires a checkpointer.
- `checkpointer`: LangGraph checkpointer

Invocation uses LangGraph semantics: `agent.ainvoke({"messages": [...]}, config={"configurable": {"thread_id": ...}})`. Resume after an interrupt uses `Command(resume=...)`. State can be read and written with `aget_state` and `aupdate_state`.

## 5. What this project verified offline

These run in `tests/test_agent.py` with a scripted `FakeModel` and plain tools, without Temporal:

- A side-effect tool with `interrupt_on` pauses the graph and returns `__interrupt__`.
- The tool does not run before approval.
- `approve` runs the tool once; `reject` skips it, and the agent continues.
- Messages restored with `aupdate_state` on a fresh `InMemorySaver` are visible to the next turn.

Result: 5 agent tests passed on the pinned versions.

## 6. Sources

| # | Source | Access | Result |
|---|---|---|---|
| S1 | https://docs.langchain.com/oss/python/deepagents/overview | `docs.langchain.com` DNS failure (`ENOTFOUND`) | Not read |
| S2 | `deepagents-0.7.38` wheel, `METADATA` and module tree | PyPI download via `pip download` | Read. Source of sections 2 and 3. |
| S3 | https://pypi.org/project/deepagents/ | PyPI (reachable) | Metadata read through the wheel. Project URLs point to the docs and reference site. |
| S4 | https://github.com/langchain-ai/deepagents | `api.github.com` returned 403 for this session | Not read |
| S5 | `deepagents/graph.py`, `middleware/subagents.py` in the wheel | Local file read after unzip | Read for `SubAgent` fields and `create_deep_agent` signature |

## 7. What still needs to be tested

1. **Docs parity.** Read the docs overview and sub-pages (subagents, backends, HITL, memory, streaming, going to production) once `docs.langchain.com` is reachable, and compare to the package behavior above.
2. **Backend semantics.** `StateBackend` versus `FilesystemBackend` with `virtual_mode=True`: confirm path escapes are blocked and that files persist across turns.
3. **Sub-agent tools.** Confirm the `researcher` sub-agent in `michel/agent.py` only receives `fetch_url`, and that it cannot call `deliver_channel_message`.
4. **Approval for sub-agent tools.** Confirm whether `interrupt_on` on the parent also gates a tool called from inside a sub-agent. Our code assumes it does not; verify.
5. **Context management.** Drive a long conversation and confirm summarization and eviction trigger, and that approval state survives them.
6. **Model profiles.** Confirm which harness profile applies to `anthropic:claude-sonnet-5-5`. The package lists Sonnet 4.6 and Opus 4.7 profiles, not 5.5. Check the fallback behavior.
7. **Skills and memory.** Load a skill and a memory file, and confirm they reach the system prompt without leaking across bots.
8. **Prompt caching.** Confirm cache hits on repeated turns with the Anthropic model.
9. **Dependency pins.** Confirm `deepagents==0.7.38` with `temporalio-deepagents==0.0.3` resolves cleanly, including `langchain-google-genai` (a transitive dependency that the Anthropic-only path does not need).
10. **Sandbox backend.** If sandboxed execution is needed, test `backends/sandbox.py` against a real sandbox provider. Not tested.

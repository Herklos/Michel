# 08. Verification against the official docs (added 2026-11-14)

Files 01–07 were written without the docs site. `https://docs.langchain.com/llms.txt` became reachable after `docs.langchain.com` was added to the session's allowlist. The pages below were downloaded as Markdown from `https://docs.langchain.com/langsmith/python/` and `https://docs.langchain.com/oss/python/deepagents/`. They are the primary source for this file; the package README remains the source for the rest of 01–07.

## 1. Pages read

| Page | Used for |
|---|---|
| `langsmith/python/managed-deep-agents-overview.md` | product scope, layout, the Deep Agents relationship |
| `langsmith/python/managed-deep-agents-runtime.md` | runtime types, context, caller, channel, thread |
| `langsmith/python/managed-deep-agents-channels.md` | channel model and steering |
| `langsmith/python/managed-deep-agents-memory.md` | memory layers, access control, warnings |
| `langsmith/python/managed-deep-agents-sandboxes.md` | sandbox config, snapshots, file operations |
| `langsmith/python/managed-deep-agents-deploy.md` | deploy prerequisites, SaaS region, BYOC |
| `langsmith/python/managed-deep-agents-cli.md`, `-schedules.md`, `-subagents.md` | headings only |
| `oss/python/deepagents/overview.md`, `subagents.md`, `backends.md`, `human-in-the-loop.md`, `memory.md`, `skills.md`, `going-to-production.md`, `permissions.md` | downloaded (sizes 13–107 KB); headings and cross-checks only |

## 2. Corrections to files 01–07

| Earlier statement | Official docs say | Action |
|---|---|---|
| Status is **public beta** in one README and **private preview with waitlist** in another (file 07 §3, README) | "Managed Deep Agents is in **public beta** on LangSmith Cloud and Bring Your Own Cloud (BYOC). Use Managed Deep Agents CLI and SDK v0.10 or later for BYOC." The waitlist text belonged to the deprecated `deepagents-cli` README. | **Resolved**: public beta. |
| Memory has three layers: agent, assistant, user (file 01 §4, from the 0.10.4 README) | The memory page describes **two** layers: **Agent** (`/memories/agent/`, deployment-shared) and **User** (`/memories/user/`, the authenticated person). It says "Declare both" for a team assistant with shared and personal knowledge. It does not mention an assistant layer. | **Open discrepancy.** The package README may describe a newer or differently named layer. Verify on the installed version before designing around it. |
| User memory mounts by default for managed Slack one-to-one DMs (file 01 §4) | The memory page says user memory requires a caller the deployment authenticates **as a person**. A LangSmith API key authenticates a service, so the default identity provider never mounts user memory. Supabase is the documented option for end users. | Refined. The Slack-DM default in the README is a separate, channel-level rule. |
| Memory `allow` callbacks are deprecated (file 01 §4) | Memory page: "Select layers for each run" and "Migrate from an allow policy". Consistent with the README's deprecation. | Consistent. |
| `runtime.channel` is deprecated and removed in 0.11 (file 02) | Runtime page: "`runtime.channel` is deprecated and will be removed in `managed-deepagents` 0.11." | Consistent. |
| The runtime adds `server_info`, `thread`, `backend` (file 02) | Runtime page: "Managed Deep Agents adds three fields: `server_info`, `thread`, and `backend`." | Consistent. |
| Sandbox idle TTL default is 600 s (file 02 §6) | Sandboxes page: `idle_ttl_seconds` default `600`. "Seconds of inactivity before the sandbox and its contents are deleted. Deletion is not recoverable." | Consistent; add the unrecoverable-deletion warning. |
| Snapshot setup runs once; thread sandboxes clone it (file 02 §6) | Sandboxes page: `sandbox/setup.sh` runs with `bash -e` at deploy or dev and is saved as a snapshot. A failed script fails the deploy and LangSmith keeps the previous snapshot. Project `.env` values are available **while** the script runs; thread sandboxes do not inherit them. | Consistent; add the `.env` and failure rules. |
| `mda init` scaffolds `sandbox/__init__.py` (file 01) | Sandboxes page: "`mda init` does not create `setup.sh`. Add that file yourself." | Refined: `setup.sh` is manual. |
| Schedules: runtime schedules survive redeploy (file 02 §5) | Not checked in the schedules page (headings only). | Unverified in this pass. |

## 3. New facts from the official pages

- **Steering.** A user's message sent while the agent is running on the same thread joins the active run "at its next model call"; it does not start a new run (channels page). The package has `_steering.py`. This matches the open-swe repo's "follow-ups are taken from the inbox before each model call" (see `open-swe/02-architecture.md`).
- **Channel model.** The docs describe three parts of a channel: inbound events (verify, normalize, start a run), outbound messaging (post the reply to the originating conversation), and provisioning (create the provider resources). "Provider adapters determine which events are accepted, how provider conversations map to... threads, and how responses are delivered."
- **Memory warning.** "Agent memory is readable by every caller." On a multi-person deployment, a caller-specific detail saved to `/memories/agent/` is visible to everyone. The runtime's instruction not to do this is not enforced. The docs recommend declaring user memory alongside, or requiring approval before an agent-memory write.
- **Memory turn-off is non-destructive.** Turning memory off deletes nothing; re-declaring the layer mounts the same repositories. "The runtime never copies content between layers."
- **Deploy regions and BYOC.** SaaS region selection and a BYOC data plane are both deploy options. For BYOC, `LANGSMITH_ENDPOINT` must be the data plane's API URL, not a SaaS regional endpoint.
- **Sandbox files.** Standard Deep Agents file operations plus `upload_files` and `download_files` for binary data; limits are on the page (not summarized).

## 4. Deep Agents docs (for comparison with files 01–02 of `docs/research/`)

Headings confirm the Deep Agents feature set used in `01-temporal-deepagents.md` and `02-langchain-deepagents.md`: overview, subagents (`subagents.md`, about 107 KB), backends, human-in-the-loop, memory, skills, permissions, going to production, streaming, profiles, sandboxes, interpreters, rubric, and async subagents. `async-subagents.md` and `dynamic-subagents.md` exist, which the package-based research did not list.

## 5. Still unverified

- The assistant memory layer (see §2).
- Schedule behavior and limits (file 02 §5), which are on a page not read in full.
- Anything on the CLI reference page beyond its headings, including command flags.

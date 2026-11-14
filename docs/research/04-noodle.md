# Research 04: Noodle (pdparchitect/noodle)

Date of research: 2026-11-14. Status: research complete for the repository README; the product is not run. The name "Noodle" is shared by several unrelated products (section 2), so the choice of this one should be confirmed with the user.

## 1. Summary

Noodle, by `pdparchitect`, is an Apache-2.0 open-source suite of personal AI agent apps for Mac, iPhone and iPad, with a Linux server variant ("Noodle Server"). Its distinctive design is that agents run on the user's own existing AI harness and account (Codex, Claude Code, and others) rather than on a model bundled with the app. It adds group conversations between agents, a sandboxed computer per agent, signed-in browsers per agent, and a Hub that shares harnesses with family or friends from an always-on machine.

## 2. Which "Noodle"?

Search results showed several products with the name. Only one matches a personal-agent alternative to Grok Bot.

| Product | Repository or site | Fit to this project |
|---|---|---|
| **Noodle (pdparchitect)** | https://github.com/pdparchitect/noodle | Personal AI agents, open source, Apache-2.0. Studied here. |
| Noodle (poteto) | https://poteto.github.io/noodle | Go coding framework that orchestrates agents with skills; MIT. Not a personal assistant. |
| Noodle Seed | https://www.stork.ai/en/noodle-seed (search result) | No-code assistant that builds a ChatGPT app. Commercial. |
| Noodl AI | https://noodlapp.github.io/noodl-docs/docs/getting-started/noodl-ai (search result) | Feature inside the Noodl dev tool; uses OpenAI API keys. |
| Noodle Factory | https://www.noodlefactory.ai (search result) | Education teaching assistant (Blackboard, Teams). |
| Noodle (character) | https://shapes.inc/noodle-wfnq (search result) | Fictional chat character. |

**Action needed:** confirm with the user that "noodle" means pdparchitect/noodle.

## 3. What the README says

Source: `https://raw.githubusercontent.com/pdparchitect/noodle/main/README.md`, fetched directly. Length about 13.5 KB. Quotes are from that file.

**Positioning.** "Personal AI agents for your Mac, iPhone and iPad. Free and open source. Runs on the AI inference/subscriptions you already have."

**Harnesses.** Agents run on the user's chosen harness, "using your own account": Codex, Claude Code, FX, Grok Build, Muse Code, OpenCode v2, Antigravity, and Apple Intelligence on device. A harness is documented in `docs/harness-setup.md` (linked; not read).

**Features listed in the README:**

- **Agents.** Each agent keeps its own workspace, backstory and history.
- **Groups.** Several agents in one conversation working toward a shared goal. The README shows a "Morning crew" group of research, writing and drawing agents.
- **Noodle Mobile.** Chat with agents from iPhone and iPad.
- **Noodle Computer.** Linux, macOS and Windows computers "for you and your agents", each with its own desktop and terminal.
- **Noodle Applet.** Tools, websites, experiments and games that agents build and run.
- **Noodle Browser.** Dedicated, persistent browser profiles that you sign in to and assign to agents. Tabs, history, bookmarks and file transfer are mentioned.
- **Noodle Hub.** Shares harnesses with family and friends from an always-on Mac. Their bots run on the Hub, and sign-ins stay on the Hub.
- **Noodle Server.** "A Noodle Hub for Linux": runs bots for listed people on installed Claude Code and Codex, each in its own sandbox. Linux arm64 and x86_64 tarballs are published.
- **Security.** Access is restricted by default, with per-bot folder sharing. Unrestricted access is optional. Documented in `docs/security.md` (linked; not read).
- **Privacy.** `docs/privacy.md` (linked; not read).

**Setup.** Settings → Harness, then install and sign in. Platform: macOS 26 for most apps; Linux arm64 and x86_64 for the server.

**Releases.** Installers and DMGs are published as GitHub release assets. Components update independently.

## 4. Relevance to this project

Useful patterns, each to be verified before adoption:

1. **Harness abstraction.** Agents delegate to an external harness instead of owning the model. Our equivalent is the worker's `model_provider`. Noodle shows a user-facing version of this, with per-user sign-in.
2. **Per-agent sandboxed computer.** Matches our per-bot `FilesystemBackend` workspace. Noodle's version is a full VM-like computer, which is much stronger isolation than ours.
3. **Group conversations.** Multiple agents in one thread. Our design has one workflow per bot. Group chat would need a coordinator workflow, or a sub-agent model.
4. **Hub or Server.** Multi-user hosting on one machine. Our backend is already multi-bot, but has no per-user identity yet.
5. **Default-deny sharing.** Matches our `FETCH_ALLOWED_HOSTS` and `ALLOWED_SENDERS` defaults.

Noodle is a client-side product. It does not use Temporal, as far as the README shows. Its architecture (how it persists groups, schedules, and approvals) is not described in the README and must be read from the source.

## 5. Sources

| # | Source | Access | Result |
|---|---|---|---|
| S1 | https://github.com/pdparchitect/noodle | Not fetched directly | The README was read from the raw URL below |
| S2 | https://raw.githubusercontent.com/pdparchitect/noodle/main/README.md | Direct `curl`, HTTP 200 | Read in full |
| S3 | https://poteto.github.io/noodle | Search result | Not read |
| S4 | https://github.com/HKUDS/nanobot | Search result | Not read (another self-hosted agent, Python, chat channels) |
| S5 | Search: "Noodle AI agent bot open source self-hosted assistant 2026" (extended mode) | Search tool | Snippets only; source of section 2 |

## 6. What still needs to be tested

1. **Read the linked docs** (`docs/harness-setup.md`, `docs/security.md`, `docs/privacy.md`, `Server/README.md`, `Hub/README.md`) from the repository.
2. **Read the architecture.** Find how groups, schedules and approvals are stored and run. Check for any queue, scheduler or durable-execution component.
3. **Read the license file** directly to confirm Apache-2.0.
4. **Run Noodle Server on Linux** (arm64 or x86_64) in a sandbox to see the actual bot lifecycle, then compare it with our worker.
5. **Confirm the harness list** works with the subscriptions a user would have, and that the sign-in stays on the user's side.
6. **Test the security defaults**: that a new bot cannot read folders outside its share, and that unrestricted access is off by default.
7. **Ask the user** whether "Noodle" means this product (section 2).

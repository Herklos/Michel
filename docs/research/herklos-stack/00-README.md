# Herklos stack and Grok Bot: research index

Collected 2026-11-14. Repositories read: `Herklos/Michel` (commit `17a6d1c`), `Herklos/skills` (commit `05de789`), `Herklos/DeepMichel` (remote has one branch, `claude/serene-pasteur-gu7bbs`, which holds this project's work; no `main`). Network policy for this environment is now unrestricted.

| File | Topic |
|---|---|
| [01-michel.md](01-michel.md) | Michel: features grouped; storage map under `~/.hbots`; design choices |
| [02-skills-storage-map.md](02-skills-storage-map.md) | Where agents, groups, rules, memory, tasks and history live, across Anytype and each runtime |
| [03-grok-bot-features.md](03-grok-bot-features.md) | Grok Bot features grouped, from search summaries (changelog blocked) |

## Short answers

- **Agents, groups, rules, memory, tasks:** the definitions are typed objects in **Anytype** (the org source of truth). Each runtime keeps its running copy in its own home: Hermes under `~/.hermes/profiles/<slug>/`, Osaurus under `~/.osaurus/`, Michel under `~/.hbots/`.
- **History:** Hermes `state.db`; Osaurus `chat-history/`; Michel transcripts live in T3 Code.
- **Secrets** never sync: Keychain (Osaurus), `vault.enc` (Michel), `auth.json` and `.env` (Hermes).
- **Grok Bot:** the changelog could not be read (Cloudflare). Coverage says 1.0 left beta on 2026-11-11, adding Teams, meetings and shared connectors.

## Access

- `x.ai` returned a Cloudflare block (HTTP 403). Not retried or routed around.
- The three GitHub repos were read via anonymous clone after `add_repo`.

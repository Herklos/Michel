# Research index

Research notes for the michel backend. Each file lists findings, sources (with how each was accessed), and the tests still needed. The original combined summary is in `../RESEARCH.md`.

| File | Topic | Confidence | Main source |
|---|---|---|---|
| [01-temporal-deepagents.md](01-temporal-deepagents.md) | Temporal Deep Agents integration (`temporalio-deepagents`) | High for API and behavior (package source and README); the docs page was unreachable | Package README and source |
| [02-langchain-deepagents.md](02-langchain-deepagents.md) | LangChain Deep Agents (`deepagents`) | Medium: from package source, not the docs site | PyPI wheel 0.7.38 |
| [03-grok-bot.md](03-grok-bot.md) | Grok Bot (SpaceXAI / Cursor) | Low: search snippets only | Search summaries |
| [04-noodle.md](04-noodle.md) | Noodle (pdparchitect) | High for the README; the name is ambiguous | Repository README |
| [05-osaurus.md](05-osaurus.md) | Osaurus (macOS agent harness) | Medium-high: GitHub README; docs site unreachable | Repository README |

## Sub-folders with their own index

| Folder | Topic |
|---|---|
| [herklos-stack/](herklos-stack/00-README.md) | The user's own Michel, skills and Grok Bot notes |
| [hermes-nous/](hermes-nous/README.md) | Hermes Agent (Nous Research) |
| [langsmith/](langsmith/README.md) | LangSmith product features, sandboxes, gateway, open-swe usage |
| [managed-deep-agents/](managed-deep-agents/README.md) | Managed Deep Agents runtime and its authoring API |
| [noodle/](noodle/README.md) | Noodle (pdparchitect) |
| [open-swe/](open-swe/README.md) | Open SWE (now named Robin) |
| [peers/](peers/01-open-swe-and-t3code-structure.md) | Code structure of Open SWE / Robin and T3 Code, compared with michel (storage, config, harness, memory) |

## Access status (updated 2026-11-14)

Some notes above say a site was unreachable. That was true when the note was written, in the first session. A later check on the same day showed these hosts reachable (HTTP 200 from `curl`): `docs.temporal.io`, `docs.langchain.com`, `cursor.com`. The notes have **not** been re-read yet. Re-reading them is spike S-01 in `docs/spikes.md`.

Still blocked as of this check: GitHub release downloads (`github.com/temporalio/temporal/releases` returned 403). This blocks the Temporal test server binary used by time-skipping tests (spike S-02).

## Open items

1. Confirm with the user that "Noodle" means `pdparchitect/noodle` (see file 04).
2. Re-read the primary docs now reachable (`docs.temporal.io`, `docs.langchain.com`, `cursor.com`) and update files 01, 02, 03 and 05 (spike S-01).
3. Run the end-to-end tests in files 01 and 02 against a Temporal dev server (spike S-02).

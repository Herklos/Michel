# Research index

Research notes for the michel backend. Each file lists findings, sources (with how each was accessed), and the tests still needed. The original combined summary is in `../RESEARCH.md`.

| File | Topic | Confidence | Main source |
|---|---|---|---|
| [01-temporal-deepagents.md](01-temporal-deepagents.md) | Temporal Deep Agents integration (`temporalio-deepagents`) | High for API and behavior (package source and README); the docs page was unreachable | Package README and source |
| [02-langchain-deepagents.md](02-langchain-deepagents.md) | LangChain Deep Agents (`deepagents`) | Medium: from package source, not the docs site | PyPI wheel 0.7.38 |
| [03-grok-bot.md](03-grok-bot.md) | Grok Bot (SpaceXAI / Cursor) | Low: search snippets only | Search summaries |
| [04-noodle.md](04-noodle.md) | Noodle (pdparchitect) | High for the README; the name is ambiguous | Repository README |
| [05-osaurus.md](05-osaurus.md) | Osaurus (macOS agent harness) | Medium-high: GitHub README; docs site unreachable | Repository README |

## Access limits seen in this session

These hosts failed DNS resolution, so their pages are unread:
`docs.temporal.io`, `docs.langchain.com`, `cursor.com`, `thenextweb.com`, `www.zenml.io`, `docs.osaurus.ai`.

GitHub API calls for several repositories returned 403 without repository access. Raw file URLs on `raw.githubusercontent.com` and PyPI downloads worked.

The Temporal dev server could not be started here, because its binary host is blocked. No workflow has been executed end to end. The michel tests run offline.

## Open items

1. Confirm with the user that "Noodle" means `pdparchitect/noodle` (see file 04).
2. Allow the blocked docs hosts, then re-read the primary sources and update files 01, 02, 03 and 05.
3. Run the end-to-end tests in files 01 and 02 against a Temporal dev server.

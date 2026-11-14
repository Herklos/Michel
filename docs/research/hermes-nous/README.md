# Hermes Agent (Nous Research): research index

Collected 2026-11-14. Sources: `hermes-agent.nousresearch.com` (site, docs index, full docs, comparison pages), `nousresearch.com/releases`, and a shallow clone of `github.com/NousResearch/hermes-agent` (HEAD 2026-11-13, 250 release tags, latest `v2026.9.24`).

| File | Topic |
|---|---|
| [01-overview-releases-and-versions.md](01-overview-releases-and-versions.md) | What Hermes is; interfaces; versions and tags; source counts; the releases page |
| [02-features-grouped.md](02-features-grouped.md) | Features grouped: memory and learning, automation, interfaces and reach, tools, plugins, models, operations |
| [03-architecture-storage-and-security.md](03-architecture-storage-and-security.md) | Entry points and core; where state lives; single-writer sessions; memory, cron and curator mechanics; the eight security layers; approval modes and YOLO |
| [04-comparisons-and-claims.md](04-comparisons-and-claims.md) | Nous's comparison pages, claim by claim, with the verified ones marked |
| [05-verification-open-questions-and-lessons.md](05-verification-open-questions-and-lessons.md) | What was verified; access limits; open questions; ten lessons for our build |

## Key findings

1. **Hermes is a self-hosted agent with its own loop**, unlike Noodle, which hosts external harnesses. It has a persistent memory of two bounded files, self-written skills, cron, subagents, a kanban board, and 24 platform plugins.
2. **Versioning is by tag**, not by `pyproject.toml` (which says `0.0.0`). The releases page is a stale model catalogue for this product.
3. **Security is layered and explicit**: approval modes with separate unattended defaults, a YOLO mode that names its surviving checks, and a supervised-gateway guard against self-restart loops.
4. **The comparison pages are vendor claims.** Only the migration commands and the platform count were checked in code.
5. **Our build can borrow concrete mechanics**: a single session writer, frozen memory snapshots, bounded memory with explicit errors, cron admission recovery, loop guards, and per-context approval defaults.

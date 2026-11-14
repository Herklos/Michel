# Noodle (pdparchitect): deep research index

Full clone of `https://github.com/pdparchitect/noodle` at `1408d25b` (2026-11-13), read 2026-11-14. Current version 0.85.0. 2,130 commits, 2,349 files, about 1,400 Swift files.

| File | Topic |
|---|---|
| [01-overview-and-positioning.md](01-overview-and-positioning.md) | What Noodle is; components; shared code; three licences; release model |
| [02-apps-and-features.md](02-apps-and-features.md) | Features grouped: bots, conversations, voice, tools, computers, browsers, noodlets, groups, Hubs, games |
| [03-harnesses-hubs-and-servers.md](03-harnesses-hubs-and-servers.md) | The harness catalogue; installing and updating harnesses; profiles and fallbacks; Hub; Server; Terminal; Mobile; enterprise keys |
| [04-security-privacy-and-trust.md](04-security-privacy-and-trust.md) | Access model, approvals, sign-in copies, noodlets, Hub risks, stated limits, privacy, assessment |
| [05-architecture-engineering-and-release.md](05-architecture-engineering-and-release.md) | Build system, module map, process model, CI, engineering rules, release model |
| [06-release-timeline-and-features.md](06-release-timeline-and-features.md) | Dated release timeline and feature groups, 0.80.x to 0.85.0 |
| [07-comparisons-and-claims.md](07-comparisons-and-claims.md) | Noodle's own comparison table, checked; Noodle against Hermes |
| [08-verification-open-questions-and-lessons.md](08-verification-open-questions-and-lessons.md) | What was verified and how; open questions; lessons for our build |

## Key findings

1. **Noodle is a host for external agent programs** (harnesses), not a model runtime. Each bot runs one harness under the user's own account.
2. **The licence is three licences.** Apache-2.0 for most code; PolyForm Small Business 1.0.0 for `Enterprise/`; PolyForm Noncommercial for `Incubator/`. An earlier note that it was Apache-2.0 throughout was wrong.
3. **The security model is restricted by default** with stated limits: writable allowed files, open internet access, no resource limits, and shared accounts in Hubs. The project documents these itself.
4. **The fastest-growing surface is Hubs and mobile.** Hubs run bots for other people with lent sign-ins; that is the largest trust surface.
5. **The release cadence is high** (about eleven dated versions in 13 days) with separate products, versions and changelogs.

## Access

- Cloned anonymously (public repository). No GitHub API use.
- Not built or run: macOS 26 and Xcode 27 are required.

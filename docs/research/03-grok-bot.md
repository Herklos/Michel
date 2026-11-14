# Research 03: Grok Bot (SpaceXAI / Cursor)

Date of research: 2026-11-14. Status: **low confidence**. Only search snippets were read. The product's own documentation and all news articles were unreachable (see section 6). Treat every claim here as unverified until the primary sources are read.

## 1. Summary

Grok Bot is a hosted agent product, announced as a move into office work, with a product docs page at `cursor.com/docs/grok-bot`. Search snippets describe it as a persistent, long-running, multi-agent system with a chat-style front end. It appears to be closed source and to run only xAI models. It was described as launching in beta with restricted access. These are claims from secondary sources, not from the product.

## 2. What the sources say

Each claim is tagged with its source and how it was obtained.

| Claim | Source | Obtained by | Confidence |
|---|---|---|---|
| Launched as an agent product "as the agent race moves to office work" | https://thenextweb.com/news/spacexai-grok-bot-ai-agents-cursor | Search snippet title only | Low (article not read) |
| Beta launch on 2026-08-11; access limited to some Cursor and SuperGrok subscribers. The two sources disagree on details. | Search summary citing the TNW article and a second listing | Search summary | Low |
| Closed source; runs only xAI models; cannot be self-hosted | https://openalternative.co/alternatives/grok-bot ("review" page) | Search snippet | Low to medium (secondary review) |
| Official docs page exists at `cursor.com/docs/grok-bot.md` | Search result title | Search result only | Medium (page not read) |
| Persistent, multi-agent workflows; durable execution needed for runs of a day or more | https://www.zenml.io/llmops-database/designing-persistent-multi-agent-workflows-for-grok-bot | Search snippet | Low (article not read) |
| Other listings: aibuilderclub guide, mindstudio "agent fleet" post, dsebastien.net note | Search results | Titles only | Not read |

Caveat on the search tool: the snippets were produced by a summarizer. Quoted phrases in this file come from that summary, not from the pages.

## 3. Feature picture (provisional)

Based only on the claims above:

- Persistent agents that outlive a single chat session
- Multi-agent work
- Integration with a coding product (Cursor), so it is probably tied to developer workflows
- Hosted only; no self-host option
- Access gated by subscription

These are the features the backend in this repo is meant to mirror: durable per-bot workflows, multi-agent delegation (a `researcher` sub-agent), and approval gates before side effects. The mapping is in section 5 of `docs/RESEARCH.md`.

## 4. Why it matters for this project

Grok Bot is the reference product in the user's request. Its closed-source status means we cannot read its architecture directly. Our design goal is therefore a self-hosted equivalent, not a clone of the hosted service. We should not claim parity with Grok Bot features we have not confirmed.

## 5. Sources

| # | Source | Access | Result |
|---|---|---|---|
| S1 | https://cursor.com/docs/grok-bot.md | `cursor.com` DNS failure (`ENOTFOUND`) | Not read |
| S2 | https://thenextweb.com/news/spacexai-grok-bot-ai-agents-cursor | DNS failure | Not read |
| S3 | https://www.zenml.io/llmops-database/designing-persistent-multi-agent-workflows-for-grok-bot | DNS failure | Not read |
| S4 | https://openalternative.co/alternatives/grok-bot | Search snippet | Read as summary |
| S5 | https://pub.towardsai.net/build-your-own-grok-bot-the-model-is-the-easy-part-e201b3d5fadf | Search result title | Not read |
| S6 | https://www.aibuilderclub.com/blog/how-to-build-your-own-grok-bot | Search result title | Not read |
| S7 | https://www.mindstudio.ai/blog/grok-bot-ai-agent-fleet/ | Search result title | Not read |
| S8 | https://www.bitdoze.com/md/best-open-source-grok-bot-alternatives.md | Search result title | Not read. Lists open-source alternatives (Rakazo, OpenBot, Hermes Agent, AutoGPT, NanoClaw, OpenWork, OpenClaw). Not evaluated. |

## 6. What still needs to be tested or read

1. **Read the primary docs** at `cursor.com/docs/grok-bot.md` once the host is reachable. Record features, limits, pricing, and the security model.
2. **Read the launch article** (TNW) and confirm the launch date and access rules. The two sources conflict.
3. **Confirm the "closed source, xAI only, no self-host" claim** from the product docs, not from a review.
4. **Check the open-source alternatives** named in S8 (Rakazo, OpenBot). Evaluate whether either uses Temporal or any durable engine. Unknown.
5. **Compare features** against our backend once the docs are read: persistence, scheduling, channels, approvals, sub-agents, file workspace.
6. **Do not** publish any feature-parity claim until items 1 and 3 are done.

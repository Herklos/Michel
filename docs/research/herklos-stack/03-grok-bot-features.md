# 03. Grok Bot: features grouped and summarized

Status: **the official changelog could not be read.** `https://x.ai/changelog/bot` returns a Cloudflare "Attention Required" block (HTTP 403) from this session. The request was not repeated or routed around. Everything below comes from search summaries of x.ai and secondary coverage, and is marked by confidence.

## 1. Timeline (as reported; dates disagree)

- **Beta** (earlier in 2026): Grok Bot launched in beta with access limited to some Cursor and SuperGrok subscribers (search summary, `03-grok-bot.md` of `docs/research/`).
- **Grok Bot 1.0** left beta on **2026-11-11** according to several secondary write-ups. One source gives 2026-11-02 for the announcement and lists **1.0.1** on 11-11. Confidence: medium on the date, low on version numbers.
- **Version 0.72.0** was announced on X by a third party (`x.com/blankspeaker`): agent status shown as an elevated card, sharing an agent with a team, live status on a linked pull request. Confidence: low (a repost).

## 2. Features, grouped

### A. Bots and teammates
- **Shared Bots / Team Bots:** publish a Bot and share it; copy an agent into a team workspace. Team Bots need Team or Enterprise plans (sources agree on the plan requirement). Confidence: medium.
- **Proactive work:** Bots monitor projects, spot upcoming deadlines, follow unfinished tasks, and offer to take work on. Confidence: medium.
- **Agent status card:** status shown as a card rather than a chat bubble. Confidence: low.

### B. Where Bots appear
- **Slack:** Team Bots in Slack; people without a linked account are told which features are limited and how to link. Slack support predates 1.0 (one source says September). Confidence: medium.
- **Microsoft Teams:** new in 1.0. A Teams admin turns it on; the Bot's owner or a Manager connects it; a Teams admin approves. Confidence: medium.
- **Meetings:** a Bot joins a Google Meet, Zoom or Microsoft Teams call from a link, answers in the meeting chat, and sends a summary afterward. One source limits this to Team, Enterprise and Ultra plans. Confidence: medium.
- **Shared pages:** shared pages get a title bar with PDF download and a "Try Grok Bot" button for visitors. Confidence: medium.

### C. Connectors and access
- **Shared connectors:** an owner or manager sets them per app; "Allow Shared Logins" is the switch. If a routine needs a connected app, the team Bot asks in its Slack thread and tags the owner. Confidence: medium.
- **Named connectors:** Gmail, Google Calendar, GitHub (updated). Confidence: medium.
- **Prompt-injection guard:** when a web page hides instructions for AI agents, the Bot reports them and does not follow them. Confidence: medium.

### D. Output
- **Documents and slides:** generation reported in the 1.0 coverage. Confidence: low–medium.

### E. Reliability
- Faster reconnects after sleep or network changes; the app opens while the Bot's computer is still starting. Confidence: medium.
- **Bot computer:** one source says Bots share a cloud computer, sign in to your apps, and keep working with the laptop closed. No changelog entry found. Confidence: low (treat as unverified).

### F. Plans and model
- Seat pricing is reported as $30 against Claude's $25 (one source). Confidence: low.
- One source says the underlying model cannot be chosen in beta. Confidence: low.

## 3. What to verify when the changelog is readable

1. Exact version numbers and dates for 1.0, 1.0.1 and 0.72.0.
2. Whether "computer" means a hosted machine, and what it can reach.
3. The meeting and Teams plan requirements.
4. Connector list and the shared-login rules.

## 4. Relevance to us

Grok Bot's shape (shared team Bots, proactive work, connector permissions asked in-thread, status cards) lines up with features we planned: approvals in the originating thread, shared-connector grants, and proactive schedules. Its connector-grant model is worth copying.

## 5. Sources

- x.ai changelog: `https://x.ai/changelog/bot` (blocked, 403, Cloudflare)
- x.ai news: `https://x.ai/news/grok-bot-1-0` (not fetched; listed in search)
- Coverage (search summaries): flaviocopes.com/grok-bot-1-0, pasqualepillitteri.it, fourweekmba.com, inoryva.blogspot.com, webpronews.com, cellcog.ai/blog/grok-bot-1-0, windowsreport.com, sumus.im/blog/grok-bot-1-0, help.apiyi.com, mynextdeveloper.com, alphasignal.ai, getgrokbot.com/en/changelog (third-party), x.com/blankspeaker/status/2112337801899565120

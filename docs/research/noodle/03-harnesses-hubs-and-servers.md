# 03. Harnesses, accounts, Hubs, and Server: where a bot's intelligence comes from

Sources: `docs/harness-setup.md`, `Hub/README.md`, `Server/README.md`, `Terminal/README.md`, `Mobile/README.md`, `Enterprise/Profiles/*` (keys), `CHANGELOG.md` (0.80.x to 0.85.0), `docs/usage.md`. Read 2026-11-14.

## 1. Noodle does not run models itself

Noodle is a host for **harnesses**. A harness is "the agent program behind each bot". Noodle installs, signs in to, and supervises the harness. The model work runs in the harness, under the user's own account.

## 2. The harness catalogue (as in the code and docs)

| Harness (id) | Provider | Sign-in | Notes from the docs |
|---|---|---|---|
| Codex (`codex`) | OpenAI | Noodle sign-in | The changelog names Codex as the harness whose bots take voice calls; apps (ChatGPT connectors) can be enabled per bot |
| Claude Code (`claude-code`) | Anthropic | Noodle sign-in | Apps (Claude.ai connectors) per bot; Noodle renews its sign-in itself |
| FX (`fx`) | Vercel | Noodle sign-in | Vercel team selection in the harness menu |
| Grok Build (`grok-build`) | xAI | Noodle sign-in | Grok Build sign-ins expire after seven days |
| Muse Code (`muse`) | Meta | Noodle sign-in | Usage not counted in charts yet |
| OpenCode v2 (`opencode`) | open source | works on OpenCode's free models; own providers via `opencode.json` | Version 1 and package-manager copies not supported |
| Google Antigravity (`antigravity`) | Google | sign-in command in Terminal | Runs without tool approvals; cannot be interrupted mid-turn |
| Apple Intelligence (`apple`) | Apple (on device) | System Settings | Experimental; macOS 26; no sign-in, no network for the bot |
| Custom (OpenAI-compatible) | any | API key | vLLM, LM Studio, LiteLLM, llama.cpp, Ollama, OpenRouter, TensorFold |

The Enterprise schema lists the same eight managed harness ids (`codex`, `claude-code`, `muse`, `grok-build`, `fx`, `opencode`, `antigravity`, `apple`). Custom accounts are not in that list.

**Local models** (0.80 to 0.84): Qwen3, Llama, Gemma 4, gpt-oss (120B on 96 GB Macs), Qwen3 235B Instruct (192 GB), Qwen3.5 397B and Qwen3 Coder 480B (512 GB). They run through the harnesses that accept local models, and on Apple Intelligence.

## 3. Installing and updating harnesses

- **Install by Noodle:** downloads the provider's current release from the provider's servers. Checked before running; a failed check is discarded.
- **Install by you:** Noodle shows a command; "Check Installation" re-checks it.
- **Your own copy always wins.** If you install a harness yourself, Noodle uses yours and removes its copy at next start. Sign-ins are kept.
- **Updates:** Noodle checks every six hours and updates its own copies. A release that does not work with Noodle is rolled back, and that release is skipped. A setting turns automatic updates off. Running bots keep their version until restarted.
- **Choose who manages:** each harness's menu has *Installation › Your Own* or *Managed by Noodle* (0.82.0).
- **Turn harnesses on and off:** Settings → Harness → Choose Harnesses (0.80.0). A harness that is off is hidden everywhere, and its bots do not start.

## 4. Accounts, profiles, and fallbacks

- **Profiles:** several accounts per harness (Claude Code, Codex, FX, Grok Build, Muse Code, OpenCode, Antigravity). Each bot picks a profile in *Edit Bot → Harness → Profile*. Restricted bots cannot read other profiles.
- **Private copies:** each restricted bot gets a private copy of Noodle's sign-in for its harness. The copies share the account's identity, quotas and billing (`docs/security.md`).
- **Usage retries:** a profile can be opted in to usage retries; these are tried before the ordered fallback list and work even when that list is off (0.80.0).
- **Fallback list:** bots continue on the next available login when theirs runs out of usage. The list can name specific profiles, including several of the same harness (0.80.0).
- **Limits shown:** Settings shows how much of each Codex and Claude Code plan's limits (for example the 5-hour and weekly windows) is used.
- **Reconnect and kick:** Codex reconnects are shown as "Reconnecting…"; after ten minutes without progress, Noodle restarts the bot and continues its unfinished work, up to twice, then waits for **Kick**.
- **Model choice:** each bot picks a model and a reasoning effort, where the harness offers one. The Codex model list comes from the default sign-in.
- **Spending budgets:** per bot, per hour, day, week or month (0.81.1).

## 5. Bots and groups in practice

- **Team bots** in a group share one conversation; each bot sends the conversation to its own provider (`docs/privacy.md`).
- **Group folders:** folders shared with a group are available to all its bots in every conversation (`docs/security.md`).
- **Shared goals:** a group's description is its shared goal; the public description helps others understand a role; the backstory stays private (`docs/usage.md`).
- **Suspend, stop, kick:** three ways to pause or restart a bot (see file 02 §1).

## 6. Noodle Hub

Hub is a menu-bar Mac that runs bots for other people. Details from `Hub/README.md`.

- **Pairing:** an invitation works once and expires after 15 minutes. Devices are paired by link, QR code or code. Devices that leave the Hub in Noodle are removed.
- **Plans** decide which harnesses each user's bots may use. Every user is on one plan. New users start on *Default*, which lends nothing until harnesses are added. A bot on a model its owner's plan no longer lends cannot answer until moved.
- **Users:** Suspended (stops bots and blocks devices without deleting data), *Can Pair Devices*, *Admin* (admins can manage users but not each other or the Hub's own settings).
- **Logs:** for 90 days, who added, changed or removed users, created invitations, paired devices, and every refused attempt.
- **Network:** Open Port on Router uses UPnP or NAT-PMP to forward UDP port 38415; manual forwarding or a domain can be used instead. Shows how many people are connected.
- **Limits:** Largest File (100 MB default). Settings lists bots with heartbeat, access and archive; **New Session** restarts a bot with fresh context; Settings → Groups archives groups; Settings → Tools keeps the Hub's image models.
- **Lending:** a Hub's bots run on the Hub with its own copies of the sign-ins it lends (`docs/security.md`).

## 7. Noodle Server (Linux)

- A Hub for Linux: runs bots for people listed in one file, on the Claude Code and Codex you install, "with your sign-ins kept on the server".
- Each bot runs in a sandbox (bubblewrap); the server cannot run its bots inside an ordinary container.
- Setup: `sudo noodled/noodled setup` checks the machine, installs bubblewrap, msquic, Claude Code or Codex (asks first), writes configuration, installs the service, signs in each harness, and prints a pairing link and QR code.
- Configuration: `/etc/noodled/noodled.yaml` with harnesses (with profiles), **plans** (harnesses, profiles, models and token limits per plan), and **people** (each with a plan). `noodled check` validates it. `noodled login <harness> [--profile]` signs in.
- Runs as a dedicated system account under systemd. Updates: replace the binary and restart.
- Noodle Server never installs or updates the harnesses; the operator does.
- Limits: devices away from home are "not told about new replies yet" (README).

## 8. Noodle Terminal

- The `noodle` command in a terminal (macOS 26 Apple silicon, or Linux arm64 and x86_64 over any terminal or SSH).
- Lists bots and groups by recency, with pinned first and unread dots; images render in terminals that support them (Ghostty, kitty, WezTerm, iTerm2).
- Joins Hubs by invitation; the bots of every joined Hub share one list, All. Control-N joins another Hub.
- Clipboard copy goes to the local terminal where allowed.

## 9. Noodle Mobile (iPhone and iPad)

- An iOS 26 client for a Hub; TestFlight beta. Joining by QR code, link or photo of a code.
- First Hub welcomes with three bots in a Team group, if the plan lends harnesses.
- Admin tools on the phone: users, plans, suspension, pairing.
- Share sheet: send screenshots, photos or pages to a bot or group from any app.
- Home Screen and Lock Screen widgets (one bot, many bots, or bot status).
- **Game noodlets** can run on the phone, or live on the Hub ("Run on Hub"); a TV mirrors the game while Screen Mirroring is on, and the phone becomes the controller.
- Archive a bot or group from the list; it stays on the Hub and can be restored.

## 10. Enterprise profile keys (`Enterprise/Profiles/`)

From the JSON schema `com.pdparchitect.noodle.json` (the registry generates it; "Every key is optional and a missing key allows"). Each key says "Since Noodle 0.84.0".

- `AllowedHarnesses`: the only harnesses people may use (default: all eight).
- `AllowBrowser`, `AllowComputers`: whether Noodle Browser and Noodle Computer can be used.
- `AllowCustomMCP`: whether people can add MCP servers by URL (schema only; not in `published-keys.txt`).
- `AllowHubConnections`, `AllowHubHosting`: whether people may join Hubs and host one.
- `AllowUpdates`, `AutomaticUpdateChecks`, `AutomaticUpdateInstalls`: update control.
- Plus the Jamf schema and a sample profile. Whether bots may run outside their sandbox is also described in `ENTERPRISE.md` (the key list there is shorter than the schema).

Deployment packages and bundle IDs are in `Enterprise/Deployment.md` (for example `com.pdparchitect.noodle`, `.computer`, `.browser`, `.applet`, `.hub`).

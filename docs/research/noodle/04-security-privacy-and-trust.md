# 04. Security, privacy, and trust: what the project itself says

Sources: `docs/security.md` (full text read), `docs/privacy.md`, `docs/harness-setup.md` (profiles and private copies), `Hub/README.md`, `Applet/README.md`, `Browser/README.md`, `Computer/README.md`, `ENTERPRISE.md`. Read 2026-11-14. These are the project's own statements. None were tested.

## 1. Access model

- **Every bot starts restricted.** Unrestricted is per bot; turning it on asks for confirmation. Changing access restarts the bot and keeps its conversation.
- **Restricted bots can:** read and write files in their workspace; use folders shared with them; read and send in their conversations; use assigned tools, computers and browsers; use the internet (except Apple Intelligence, which runs on the Mac).
- **Restricted bots cannot:** read personal files, other bots' files, or Noodle's settings and saved conversations; change their own name, backstory, access or shared folders; use the Keychain; accept incoming connections.
- **Restricted bots cannot talk to other programs' local sockets** (ssh-agent, Docker). A tool that needs one fails; make the bot unrestricted instead.
- **Enforcement:** "If Noodle cannot apply the limit, the bot does not start." A restricted bot cannot ask for wider access; approving a tool cannot widen it.

## 2. Folders

- **Edit Bot → Folders:** share outside folders with one bot as Read & Write or Read Only. You cannot share the whole disk or Noodle's own storage.
- **Group Info → Folders:** share with every bot in a group, usable in all their conversations. A folder shared as Read & Write anywhere is Read & Write for the bot.
- Sharing exposes a folder's contents to the bot's provider and tools. Some harnesses (FX, OpenCode) can also see item names in parent folders.

## 3. Approvals

Noodle does not show approval forms in chat. It approves a harness's tool requests automatically, within the bot's access. Questions that need a typed answer are declined; Noodle "never makes up an answer or consent". Turning a bot's access off does not undo completed actions.

## 4. Sign-ins and credentials

- Each restricted bot gets a **private copy** of Noodle's sign-in for its harness, kept apart from the harness's own sign-in in Terminal. Copies are the same account: quotas, billing and revocation are shared.
- A bot can read its copy. A bot that follows misleading instructions "can hand your sign-in to someone else". A backup of a bot's folder includes its sign-in: treat it like a password.
- Claude Code sign-ins are renewed by Noodle, written into Noodle's own Keychain item (never the user's). Only the claude.ai sign-in in that item is replaced, and only while the item still holds the sign-in the bot started from.
- Tool sign-ins stay in the Keychain and are never written to the bot's files.
- Connected services receive only workspace files the bot chooses to send; they cannot open workspace files or post on their own.

## 5. Apps (account connectors)

Apps connected to ChatGPT or Claude.ai are **off by default**, set per bot and per harness. Turning Apps off does not disconnect the account or undo completed actions.

## 6. Noodlets (Applet)

- A noodlet does not widen the bot's access.
- It reads only its own files and saved data. It cannot read your files, another noodlet, or the Keychain; a file reaches it only when you pick it in a dialog.
- It reads the clipboard only once opened.
- It can reach the internet, but your Mac and local-network devices (TV, router) only when it asks and you agree.
- Permissions (microphone, camera, speech, screen, local network) are asked once before the noodlet starts; one macOS grant covers Applet as a whole. Settings → Permissions lists and withdraws them.
- Secrets: the names are listed, never the values.
- A noodlet from a Hub can run on your device; one that uses the camera, microphone, screen or local network always runs on your device.

## 7. Browsers and Computers

- Browsers: sign-ins and history are per browser; deleting a browser deletes them. Pause Agents stops new actions only.
- Computers: described as Linux computers (the README does not say whether they are VMs; the Mac-side "not a virtual machine" sentence in `security.md` is about restricted bot access, not about Computer).
- External agents (Claude Code, Codex and others) can use browsers and computers only after **Allow agents** is on, and each app sees only what it created or was lent.

## 8. Hub risks (`docs/security.md`, "Noodle Hub")

- **Lending a sign-in shares the account.** A borrower's bot can send the lender's sign-in to the borrower.
- **A Hub keeps its own sign-ins** and never writes a renewed sign-in back to its Mac's Keychain.
- **A shared bot works for whoever talks with it.** Anyone you share a bot with gets the same memory, files, tools, sign-ins and plan, and can ask for any of them. They cannot see its settings.
- **A bot shared from your Mac works on your Mac** with everything it can reach there, unrestricted if so set.
- **Files sent to a shared bot land on your Mac** and stay until you stop sharing.
- **Everyone on a Hub sees everyone's names**, so bots can be shared.

## 9. Stated limits

- **Allowed files remain writable.** No review and no undo.
- **Shared data stays shared.** Members can retrieve a conversation's messages; copies already delivered are not erased when a member leaves.
- **Internet access is open.** Anything a bot can read can go to a remote service, including on the local network.
- **File names are less private than contents.**
- **Some tools fail when restricted.**
- **No resource limits** (CPU, memory, disk, spending) for restricted bots; budgets are a separate per-bot setting.
- **Command arguments are not private.**

## 10. Privacy

- Noodle keeps chats and bot workspaces on the Mac. What leaves depends on the model each bot uses; everything a bot works with goes to that provider.
- Noodle has no accounts and no ads, and its own code sends no analytics or crash reports. It checks GitHub for Noodle updates and provider sites for harness updates.
- In a group, every bot sends the whole conversation to its own provider.
- **Private options the project names:** Apple Intelligence and local models (no Private Cloud Compute); an Ollama account (local); a Custom OpenAI-compatible server on your own machine or a provider whose terms exclude training. The project says a private model keeps the conversation private, not what tools do with what the bot sends them.
- **Consumer subscriptions** (ChatGPT, Claude, Grok, Google) put work under consumer terms, which may allow training unless turned off in the account. Business or API accounts usually exclude training.
- **iPhone TestFlight beta:** Apple collects crash logs and usage and shares them with Noodle's developers.

## 11. Enterprise controls

MDM profiles (Jamf Pro, Kandji, Intune, Mosyle) restrict harnesses, browsers, computers, custom MCP, Hub joins and hosting, and updates. Noodle "never blocks or limits the managed settings" for lack of a licence.

## 12. Assessment (this review, not the project's claims)

- The restricted model is layered (folder allow-list, no Keychain, no incoming connections, sign-in copies), but the project itself says restricted bots can still write their allowed files and reach the internet. The effective boundary against exfiltration is the internet rule, not the file rule.
- "Approvals" are automatic within access, so a human checkpoint exists only when a bot is restricted and a tool needs wider access (which then fails).
- The Hub design (lending sign-ins, shared bots with full capability) is the largest trust surface in the product. The project documents this openly.
- No independent security audit was found in the repository.

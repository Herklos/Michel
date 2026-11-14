# 01. Noodle: what it is, how it is built, and how it is licensed

Source: `https://github.com/pdparchitect/noodle`, full clone at `/home/user/pdparchitect/noodle`, HEAD `1408d25b` (merge of PR #320, 2026-11-13). Repository history: 2,130 commits. Files: 2,349. Swift files: 1,411, about 262,000 lines. Read 2026-11-14.

## 1. Positioning (the project's own words)

- README: "Personal AI agents for your Mac, iPhone and iPad. Free and open source. Runs on the AI inference/subscriptions you already have."
- Current version: **0.85.0**, dated 2026-11-13 (`VERSION`, `CHANGELOG.md`). Version history in the changelog reaches back at least to 0.80.1 (2026-11-01).
- Its comparison table in the README puts Noodle against Grok Bot and Muse. Those comparisons are the project's own claims and were not verified (see file 08).

## 2. Components (one repository, many products)

Each product has its own version file, changelog, and release channel (`docs/releases.md`).

| Product | Folder | Role | Platform | Status in repo |
|---|---|---|---|---|
| **Noodle** | `Sources/`, `Support/`, root `Package.swift` | the main app: bots, groups, chat, tools | macOS 26, Apple silicon | 0.85.0 |
| **Noodle Hub** | `Hub/`, `HubCore`, `HubMac` | menu-bar Mac that runs bots for other people | macOS 26 | shipped |
| **Noodle Computer** | `Computer/` (350 files) | Linux VMs for bots (Shell and Desktop images) | macOS 26, Apple silicon | shipped |
| **Noodle Applet** | `Applet/` | "noodlets": tools, websites, games bots build | macOS 15+ | shipped |
| **Noodle Browser** | `Browser/` | signed-in browsers for bots | macOS 26 | "still in development" (its README) |
| **Noodle Server** | `Server/` | Hub for Linux, `noodled` systemd service | Linux arm64 / x86_64 | shipped |
| **Noodle Terminal** | `Terminal/` | `noodle` command: chat with Hub bots in a terminal | macOS 26, Linux | shipped |
| **Noodle Mobile** | `Mobile/` | iPhone and iPad client for a Hub | iOS 26 | TestFlight beta |
| **Noodle Push** | `Push/` (Swift sources, a Dockerfile and a `worker/` folder) | rings the iPhone for bot calls when the app is closed | service | deployed from `main` |
| **Noodle Embed** | `Embed/` (Cloudflare worker) | hosts YouTube's player so noodlets can show videos | web | deployed by `embed.yml` |
| **Noodle Suite / Installers** | `Scenarios/`, `Shared/Product` | one installer that chooses companions | macOS | shipped |
| **Incubator: Pion** | `Incubator/Pion` | cyber-defence investigations with agent teams | macOS | "no release yet" |
| **Incubator: Rook** | `Incubator/Rook` | red-team tool for authorised engagements | macOS | incubating |
| **Tools** | `Tools/` (Calendar, Images, Maps, Reminders, Vision, Applet, Browser, Computer) | built-in tool packages bots can use | macOS | in the app |
| **Enterprise** | `Enterprise/`, `ENTERPRISE.md` | MDM configuration profiles | macOS | separate licence (below) |
| **Website** | `website/` (86 files) | usenoodle.app | web | deployed by `website.yml` |

## 3. Shared code

`Sources/` contains 22 folders (for example `NoodleCore`, `NoodleRuntime`, `NoodleAgentHost`, `NoodleAgentBridge`, `NoodleAppleRuntime`, `NoodleMCP`, `NoodleSharing`, `NoodleVoicePeer`, `NoodleToolScripting`, `NoodleWidgets`, `NoodleShareExtension`, `NoodleHubClient`, `HubMac`, `HubCore`, `CSQLite`). `Shared/` holds reusable packages: `Brand`, `ExternalTools`, `HubLink`, `LaunchChecks`, `Patch`, `Product`, `SettingsUI`, `Surface`, `Wallpaper`. Incubator tools are built from the same shared core (Rook's design says so explicitly: "built from Noodle's shared core ... not a fork").

## 4. Licensing: three licences, not one

| Part | Licence | Source |
|---|---|---|
| Everything outside `Enterprise/` and `Incubator/` | **Apache-2.0** | `LICENSE`, `README.md` |
| `Enterprise/` (MDM profile code, schema, guide) | **PolyForm Small Business License 1.0.0** with added permissions | `ENTERPRISE.md`, `Enterprise/LICENSE` |
| `Incubator/` tools (Pion, Rook) | **PolyForm Noncommercial License 1.0.0** | `Incubator/AGENTS.md`, each tool's `LICENSE.md` |

The Enterprise rules, as written:
- Personal use and businesses with fewer than 100 people (employees and contractors) and under US$1,000,000 revenue (inflation-adjusted, 2019 base) are free.
- Running Noodle without a configuration profile never needs a licence.
- Larger organisations need a commercial licence to manage Noodle with profiles. The project says it grants these "free of charge or on favourable terms" for now. There are no licence keys and Noodle does not check.

This correction matters: an earlier note in this research said Noodle was Apache-2.0 throughout. That was true only outside `Enterprise/` and `Incubator/`.

## 5. Platform and release model

- Apple silicon only for the Mac apps; iOS 26 for Mobile; Linux arm64 and x86_64 for Server and Terminal.
- Releases are per product with separate version files. "Pushing a new version requests publication" (`docs/releases.md`). Release workflows: `applet-release`, `browser-release`, `computer-release`, `computer-images`, `hub-release`, `mobile-release`, `prepare-noodle-release`, `publish-prepared-release`, `release`, `server-release`, `suite-release`, `terminal-release`, `testflight`, `push`, `website`, `embed`. Sixteen workflows in total.
- Noodle's own installer packages and Suite installer are signed with a Developer ID and notarised.
- The Noodle app itself sends no analytics or crash reports (`docs/privacy.md`). It checks GitHub for updates.

## 6. Engineering rules (from `AGENTS.md`, a file meant for coding agents)

- "Assume that multiple ai agents are editing this project."
- **Committing is prohibited** unless the user explicitly asks in that message.
- Keep `CHANGELOG.md` current in every user-visible change, under Unreleased, in the same change.
- No changelog entries for `website/` changes (they trigger rebuilds).
- READMEs and `docs/` are for people using the apps; code is documented only in comments.
- Run local Swift builds and tests at low priority through `scripts/build-priority.sh`.

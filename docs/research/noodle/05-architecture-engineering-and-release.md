# 05. Architecture, engineering practice, CI and release

Sources: `Sources/` (22 modules), `Shared/` (9 packages), `Tests/` (16 test targets), `.github/workflows/` (16 workflows), `AGENTS.md`, `CONTRIBUTING.md`, `docs/releases.md`, the per-product `RELEASING.md` files, `Package.swift`, `Project.swift`, `Tuist.swift`. Read 2026-11-14. The Swift code was not built here (macOS only).

## 1. Build system

- **Swift Package Manager** (`Package.swift`) and **Tuist** (`Project.swift`, `Tuist.swift`) generate Xcode projects per app. Each app folder (`Computer`, `Browser`, `Applet`, `Hub`, `Mobile`, `Terminal`, `Server`, `Push`) has its own `Package.swift`, `Project.swift`, `VERSION` and `CHANGELOG.md`.
- Dependency pins are in `Package.resolved` files.
- Local builds run at low priority through `scripts/build-priority.sh`; CI runs at full speed.
- Xcode 27 image in CI (`xcode-27`) for Mobile, which uses iOS 27 features.

## 2. Module map (from `Sources/`, `Shared/`, `Tests/`)

| Area | Modules (examples) | What they do (from names and docs) |
|---|---|---|
| Core | `NoodleCore`, `NoodleRuntime`, `NoodleRuntimeSettings` | the bot model, conversations, runtime loop, settings |
| Agents | `NoodleAgentHost`, `NoodleAgentBridge`, `NoodleAppleAgent`, `NoodleAppleRuntime` | run harness processes (host), bridge their protocol to the app, run Apple Intelligence on device |
| Tools | `NoodleMCP`, `NoodleToolScripting` | MCP client; scripted tools (noodlets' tool calls) |
| Sharing and Hubs | `NoodleSharing`, `NoodleHubClient`, `HubCore`, `HubMac`, `HubLink` (Shared) | sharing bots, the Hub client, the Hub server |
| Voice and calls | `NoodleAudioCapture`, `NoodleVoicePeer` | microphone capture and voice peers |
| Messaging | `NoodleMessenger` | the messenger command (chat effects) |
| System | `NoodleWidgets`, `NoodleShareExtension`, `CSQLite` | widgets, Share extension, SQLite access |
| UI | `Shared/SettingsUI`, `Shared/Surface`, `Shared/Brand`, `Shared/Wallpaper` | settings screens, surfaces, branding, wallpapers |
| Testing support | `Shared/LaunchChecks`, `Shared/ExternalTools`, `Shared/Patch`, `Shared/Product` | launch checks, external tool wrappers, patch and product metadata |

Test targets (16 in `Tests/`): `CoverageReporting`, `HubCoreTests`, `NoodleAgentBridgeTests`, `NoodleAppTests`, `NoodleAppleRuntimeTests`, `NoodleComputerIntegrationTests`, `NoodleCorePortableTests`, `NoodleCoreTests`, `NoodleMCPPortableTests`, `NoodleMCPTests`, `NoodleSharingTests`, `NoodleToolScriptingTests`, `NoodleWidgetsTests`, `ReleaseAutomation`, plus scripts `agent-host-startup.swift`, `build-sandbox-cli-fixture.sh`, `claude-sandbox-probe.py`. About 341 files under `Tests/`.

## 3. Harness process model

From the file and test names and `docs/security.md`: each harness runs as a separate process (`agent-host-startup.swift`, `claude-sandbox-probe.py` suggest a probe that checks the sandbox before a Claude Code bot starts). The bridge (`NoodleAgentBridge`) connects the app to that process. A restricted bot's process is launched inside a sandbox (`build-sandbox-cli-fixture.sh` builds a CLI fixture for those tests). This is inferred from names and docs; the sandbox implementation was not read.

## 4. CI workflows (`.github/workflows/`)

| Workflow | Purpose (from name and docs) |
|---|---|
| `prepare-noodle-release.yml`, `publish-prepared-release.yml`, `release.yml` | prepare and publish the main app |
| `suite-release.yml` | the Suite installer |
| `applet-release.yml`, `browser-release.yml`, `computer-release.yml`, `hub-release.yml`, `server-release.yml`, `terminal-release.yml` | per-product releases |
| `computer-images.yml` | Noodle Computer base images and registry checks |
| `mobile-release.yml`, `testflight.yml` | TestFlight builds |
| `push.yml` | Noodle Push deploys from `main` when `Push/` changes |
| `embed.yml` | Noodle Embed worker |
| `website.yml` | the website; waits until both downloads exist |

Release tags are generated, not manual: "Do not create tags manually or reuse published versions. Unchanged versions skip publication." Pull requests validate and test without publishing.

## 5. Engineering rules (`AGENTS.md`, `CONTRIBUTING.md`)

- **Concurrent agents:** the repository assumes several AI agents edit it at once.
- **No commits, pushes, tags or history rewrites** unless the user asks in that message. "A documented process, a finished task or an earlier approval is not permission."
- **Changelog discipline:** user-visible changes add an Unreleased entry in the same change.
- **Docs audience:** READMEs and `docs/` are for app users. Code is documented in comments only (a `no-code-docs` skill is referenced).
- **Low-priority local builds.**
- **Incubator tools** keep their own licence (PolyForm Noncommercial) and do not release with Noodle or appear in its changelog.

## 6. Release model

Each product has `VERSION` and `CHANGELOG.md`. Steps (`docs/releases.md`): set an unused higher version; move Unreleased notes under a dated heading; run tests; commit and push to `main` (which requests publication); watch "Validate and release versions"; verify the public download and update channel; the website deploys after both downloads exist.

Download names are stable (`Noodle-arm64.dmg` under `releases/latest/download/`); each release also has ZIPs with `.sha256` for packaging.

## 7. Signing and distribution

- Mac apps: Developer ID signed and notarised (`docs/...` and `Enterprise/Deployment.md`).
- Packages for MDM: installer packages with bundle IDs (see file 03 §10).
- Mobile: TestFlight (public link), with What to Test notes from the changelog.
- Computer images: pulled from a registry with checks (`computer-images.yml`).

## 8. Services outside the Mac

- **Push:** a service that rings iPhones for bot calls; keeps no database (its changelog says so). Phones register a VoIP token and receive it sealed.
- **Embed:** a Cloudflare Worker, `embed.usenoodle.app`, serving one static page that hosts YouTube's player with a proper referrer. It keeps no cookies, storage or request logs (its README).
- **Website:** usenoodle.app (`website/`, 86 files).

## 9. Codebase health signals

- 2,130 commits in the clone; the history is long, and the Enterprise and Incubator licence split was added recently (the changelog mentions the Enterprise profile at 0.84.0).
- The changelog is about 200 KB and dated per release: about eleven dated versions between 2026-11-01 and 2026-11-13.

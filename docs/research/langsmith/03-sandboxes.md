# 03. LangSmith Sandboxes: features and mechanisms

Sources: docs pages `sandboxes`, `sandbox-sdk`, `sandbox-snapshots`, `sandbox-auth-proxy`, `sandbox-mounts`, `sandbox-service-urls`, `sandbox-permissions` (read in full for the mechanisms listed here); `sandbox-cli`, `sandbox-download-links` (headings only). Read 2026-11-14. Status: **generally available** (the overview page).

## 1. What a sandbox is

"Isolated environments that allow agents to safely execute potentially risky operations, like running arbitrary code or interacting with the filesystem, without affecting your main infrastructure." Created and used through `SandboxClient` (Python and TypeScript), a CLI, or the REST API (`POST /v2/sandboxes/boxes` for creation).

Basic use from the docs:

```python
from langsmith.sandbox import SandboxClient
client = SandboxClient()            # reads LANGSMITH_API_KEY and LANGSMITH_ENDPOINT
with client.sandbox() as sb:
    result = sb.run("python3 -c 'print(2 + 2)'")
    print(result.stdout, result.success, result.exit_code)
```

`run()` returns `stdout`, `stderr`, `exit_code` and `success`. Long-running commands can run with `timeout=0`, `wait=False`, and return a handle with `kill()`. Python SDK streaming uses WebSockets (`websockets`); TypeScript needs `ws`.

## 2. Filesystem: system snapshots, custom snapshots, capture

- **System snapshots** are LangSmith-maintained, read-only starting filesystems shared across workspaces. The default, `system/default:latest`, starts from `ubuntu:26.04` and includes Python 3 with uv, Node.js 24 with npm, pnpm, Yarn, Go and Ruby; Git and `gh`; build tools, Docker and Buildx; shell and search tools (tmux, ripgrep, jq); network tools; SQLite and the PostgreSQL client; Chrome for Testing and `agent-browser`; and document libraries (python-docx, python-pptx, openpyxl). The `system/` namespace cannot be written to.
- **Custom snapshots** are built from a container image, or **captured** from a running sandbox (install packages, write files, then snapshot and reuse).
- Sandboxes boot from a snapshot by ID or name.

## 3. Egress and credentials: the auth proxy

The proxy runs **outside** the sandbox and enforces three things through one `proxy_config`:

1. **Credential injection.** Outbound requests to configured hosts get authentication headers added. Secrets such as `OPENAI_API_KEY` must already exist as workspace secrets. The sandbox code never holds them.
2. **Access delegation to LangSmith.** When creating a sandbox, `access_delegation` is `INHERIT` (the caller's delegatable permissions) or `EXPLICIT` (a non-empty list such as `sandboxes:read`). A delegated sandbox cannot grant access to another sandbox. Administration permissions cannot be delegated.
3. **Egress control per connection.** Access control applies to every outbound TCP connection. HTTPS to a matched host is decrypted by the proxy so it can inject headers; the sandbox trusts the proxy's CA. HTTPS to unmatched hosts and non-HTTP connections (PostgreSQL, SSH, Redis) pass through the access rules without inspection. Raw TCP to literal IPs needs an explicit entry. Only TCP leaves the sandbox; UDP and ICMP are dropped. Changes to `access_control` apply immediately.

Default posture (sandbox-auth-proxy, "Default egress posture"): with no `access_control`, every hostname is reachable on every TCP port, unless the organisation is on restricted egress. The only exception is hosts that resolve to private, loopback or cloud-metadata addresses, which the proxy refuses to dial. Restricted egress applies by default to non-Enterprise organisations, with a managed allowlist for common package registries and sources; unrestricted egress needs an approved exemption.

## 4. Mounts

Attach data to the filesystem at creation time, through `mount_config` (Python) or `mountConfig` (TypeScript):
- **S3 buckets** (access keys or an IAM role, the latter needs no stored keys), **GCS buckets** (service account), **public Git repositories**, and **Context Hub repos** (any absolute path outside system directories).
- Bucket and Git mounts go under `/mnt/mounts`. Mount IDs are unique per sandbox.
- SDK versions are pinned by feature (`langsmith>=0.8.16` for mounts, `>=0.11.0` for Context Hub mounts in Python).

## 5. Service URLs

`sb.service(port=8000)` returns a handle with `browser_url` and authenticated `get`/`post` helpers. The UI has an **Open service** widget and a **Share Link** button. This avoids tunnels for previews of web apps, notebooks or APIs. The CLI can also tunnel a TCP port.

## 6. Permissions after creation

- Each sandbox has a recorded **creator** (the workspace member whose key or session created it). Only the creator can run commands, read or write files, open tunnels or use service URLs by default.
- A workspace member with **`sandboxes:exec`** gets the same runtime actions.
- Other workspaces get **404**, not 403, so the response does not reveal the sandbox exists.
- Lifecycle actions (create, list, update, delete) keep their own `sandboxes:*` permissions.
- Denials return 403 with the rule that fired, for example "not the creator and missing sandboxes:exec".

## 7. Availability and limits

- Generally available on Cloud regions, BYOC and self-hosted (self-hosted architecture has its own page, not read here).
- Sandboxes are deleted after an idle period (`idle_ttl_seconds`, default **600 s** in the Managed Deep Agents config); deletion is unrecoverable.
- Snapshots are a Cloud and self-hosted concept; system snapshots are read-only.
- Integrations with third-party providers (AgentCore, Daytona, E2B, Modal, Runloop, Vercel) are documented in the open-source integrations section, not on the LangSmith sandbox page.

## 8. How the pieces fit (from the docs' descriptions)

Create: the API receives a snapshot reference, `proxy_config`, mounts, permissions and TTLs; boots a VM-backed filesystem from the snapshot; attaches mounts; starts the auth proxy with the rules. Run: a command goes to the sandbox host and returns streams plus an exit code. Egress: outbound connections are checked by the proxy on the host, which decrypts only the hosts it has rules for. The docs do not describe the VM technology.

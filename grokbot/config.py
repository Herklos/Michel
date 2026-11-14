"""Configuration, read from environment variables.

Secrets (provider API keys, channel webhook URLs) are read only on the worker
and never placed in workflow input or history.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field


def _csv(value: str | None) -> frozenset[str]:
    return frozenset(p.strip() for p in (value or "").split(",") if p.strip())


@dataclass(frozen=True)
class Settings:
    temporal_address: str = "localhost:7233"
    temporal_namespace: str = "default"
    task_queue: str = "grokbot"
    default_model: str = "anthropic:claude-sonnet-5-5"
    workspace_root: str = "./data/workspaces"
    # Worker-side allowlists: an empty set means "deny everything" (secure default).
    fetch_allowed_hosts: frozenset[str] = field(default_factory=frozenset)
    channel_webhooks: dict[str, str] = field(default_factory=dict)
    # Gateway-side controls.
    gateway_api_key: str | None = None
    allowed_senders: frozenset[str] = field(default_factory=frozenset)

    @classmethod
    def from_env(cls, env: dict[str, str] | None = None) -> "Settings":
        e = os.environ if env is None else env
        webhooks = json.loads(e.get("CHANNEL_WEBHOOKS", "{}") or "{}")
        return cls(
            temporal_address=e.get("TEMPORAL_ADDRESS", "localhost:7233"),
            temporal_namespace=e.get("TEMPORAL_NAMESPACE", "default"),
            task_queue=e.get("TASK_QUEUE", "grokbot"),
            default_model=e.get("BOT_MODEL", "anthropic:claude-sonnet-5-5"),
            workspace_root=e.get("WORKSPACE_ROOT", "./data/workspaces"),
            fetch_allowed_hosts=_csv(e.get("FETCH_ALLOWED_HOSTS")),
            channel_webhooks={str(k): str(v) for k, v in webhooks.items()},
            gateway_api_key=e.get("GATEWAY_API_KEY") or None,
            allowed_senders=_csv(e.get("ALLOWED_SENDERS")),
        )


# Imported by activities and tools running on the worker.
_settings_cache: Settings | None = None


def worker_settings() -> Settings:
    global _settings_cache
    if _settings_cache is None:
        _settings_cache = Settings.from_env()
    return _settings_cache

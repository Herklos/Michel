"""Tools with real I/O. Each runs as a Temporal activity, never in the workflow.

``tool_as_activity`` must run at import time on every activity worker, because
the worker looks the tool up by name when the workflow dispatches it. The
workflow imports this module too, so the same tool objects are available there.
"""

from __future__ import annotations

from datetime import timedelta
from urllib.parse import urlparse

import httpx
from langchain_core.tools import tool
from temporalio.deepagents import tool_as_activity

from michel.config import Settings, worker_settings

MAX_FETCH_BYTES = 200_000
MAX_RETURN_CHARS = 20_000


class ToolPolicyError(Exception):
    """Raised when a tool call violates the worker's policy (not retried)."""


async def fetch_page_text(
    url: str,
    settings: Settings,
    transport: httpx.AsyncBaseTransport | None = None,
) -> str:
    parsed = urlparse(url)
    if parsed.scheme != "https":
        raise ToolPolicyError("Only https URLs can be fetched.")
    host = (parsed.hostname or "").lower()
    if host not in settings.fetch_allowed_hosts:
        raise ToolPolicyError(f"Host {host!r} is not on the fetch allowlist.")
    async with httpx.AsyncClient(
        transport=transport, timeout=20.0, follow_redirects=False
    ) as client:
        async with client.stream("GET", url) as resp:
            if resp.status_code >= 300:
                return f"HTTP {resp.status_code}; redirects are not followed."
            body = b""
            async for chunk in resp.aiter_bytes():
                body += chunk
                if len(body) > MAX_FETCH_BYTES:
                    break
    text = body[:MAX_FETCH_BYTES].decode("utf-8", errors="replace")
    return text[:MAX_RETURN_CHARS]


async def post_to_channel(
    channel: str,
    text: str,
    settings: Settings,
    transport: httpx.AsyncBaseTransport | None = None,
) -> str:
    url = settings.channel_webhooks.get(channel)
    if url is None:
        raise ToolPolicyError(f"Unknown channel {channel!r}.")
    async with httpx.AsyncClient(transport=transport, timeout=20.0) as client:
        resp = await client.post(url, json={"text": text})
    resp.raise_for_status()
    return f"Delivered to {channel} (HTTP {resp.status_code})."


@tool
async def fetch_url(url: str) -> str:
    """Fetch an https web page from the worker's allowlist and return its text."""
    return await fetch_page_text(url, worker_settings())


@tool
async def deliver_channel_message(channel: str, text: str) -> str:
    """Post a message to a configured outbound channel. This has external side effects."""
    return await post_to_channel(channel, text, worker_settings())


fetch_url_tool = tool_as_activity(
    fetch_url, start_to_close_timeout=timedelta(seconds=30)
)
deliver_channel_message_tool = tool_as_activity(
    deliver_channel_message, start_to_close_timeout=timedelta(seconds=30)
)

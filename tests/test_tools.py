import asyncio

import httpx
import pytest

from michel.config import Settings
from michel.tools import ToolPolicyError, fetch_page_text, post_to_channel

SETTINGS = Settings(
    fetch_allowed_hosts=frozenset({"docs.example.com"}),
    channel_webhooks={"ops": "https://hooks.example.com/ops"},
)


def _transport(handler):
    return httpx.MockTransport(handler)


def test_fetch_requires_https():
    with pytest.raises(ToolPolicyError, match="https"):
        asyncio.run(fetch_page_text("http://docs.example.com/x", SETTINGS))


def test_fetch_denies_host_not_on_allowlist():
    with pytest.raises(ToolPolicyError, match="allowlist"):
        asyncio.run(fetch_page_text("https://evil.example.net/x", SETTINGS))


def test_fetch_empty_allowlist_denies_everything():
    with pytest.raises(ToolPolicyError):
        asyncio.run(fetch_page_text("https://docs.example.com/", Settings()))


def test_fetch_returns_text_and_does_not_follow_redirects():
    seen = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(str(request.url))
        if request.url.path == "/moved":
            return httpx.Response(302, headers={"location": "https://evil.example.net/"})
        return httpx.Response(200, text="hello docs")

    ok = asyncio.run(
        fetch_page_text("https://docs.example.com/a", SETTINGS, transport=_transport(handler))
    )
    assert ok == "hello docs"
    redirected = asyncio.run(
        fetch_page_text("https://docs.example.com/moved", SETTINGS, transport=_transport(handler))
    )
    assert "redirects are not followed" in redirected
    assert all("evil" not in u for u in seen)


def test_fetch_truncates_large_bodies():
    big = "x" * 300_000
    out = asyncio.run(
        fetch_page_text(
            "https://docs.example.com/big",
            SETTINGS,
            transport=_transport(lambda r: httpx.Response(200, text=big)),
        )
    )
    assert len(out) <= 20_000


def test_post_to_channel_posts_json_to_configured_webhook():
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append((str(request.url), request.read()))
        return httpx.Response(200)

    result = asyncio.run(post_to_channel("ops", "deploy done", SETTINGS, transport=_transport(handler)))
    assert "Delivered to ops" in result
    assert calls == [("https://hooks.example.com/ops", b'{"text":"deploy done"}')]


def test_post_to_unknown_channel_is_rejected():
    with pytest.raises(ToolPolicyError, match="Unknown channel"):
        asyncio.run(post_to_channel("random", "x", SETTINGS))


def test_settings_from_env_parses_allowlists_and_webhooks():
    s = Settings.from_env(
        {
            "FETCH_ALLOWED_HOSTS": "a.example.com, b.example.com ,",
            "CHANNEL_WEBHOOKS": '{"ops": "https://hooks.example.com/ops"}',
            "ALLOWED_SENDERS": "alice",
        }
    )
    assert s.fetch_allowed_hosts == {"a.example.com", "b.example.com"}
    assert s.channel_webhooks == {"ops": "https://hooks.example.com/ops"}
    assert s.allowed_senders == {"alice"}

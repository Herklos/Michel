"""ASGI entry point: ``uvicorn grokbot.asgi:app``.

Connects to Temporal at startup, using the same plugin configuration as the worker.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from grokbot.config import Settings
from grokbot.gateway import create_app
from grokbot.worker import connect


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings: Settings = app.state.settings
    app.state.client = await connect(settings)
    yield


def build_app() -> FastAPI:
    return create_app(None, Settings.from_env(), lifespan=lifespan)


app = build_app()

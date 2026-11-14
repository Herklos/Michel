"""Worker process: connects to Temporal with the Deep Agents plugin and runs workflows.

Run one or more of these processes. Model API keys and channel webhook URLs
live only in this process's environment.
"""

from __future__ import annotations

import asyncio
import os
from pathlib import Path

from deepagents.backends import FilesystemBackend
from temporalio.client import Client
from temporalio.deepagents import DeepAgentsPlugin
from temporalio.worker import Worker

from grokbot.config import Settings
from grokbot.tools import deliver_channel_message_tool, fetch_url_tool  # noqa: F401  (registers activities)
from grokbot.workflows import BotWorkflow, ScheduledTurnWorkflow


def workspace_factory(root: str):
    """Build the per-bot filesystem backend on the worker that runs the file operation."""

    def make(bot_id: str) -> FilesystemBackend:
        if not bot_id.replace("-", "").isalnum():
            raise ValueError("bot_id must be alphanumeric with dashes")
        path = Path(root) / bot_id
        path.mkdir(parents=True, exist_ok=True)
        return FilesystemBackend(root_dir=str(path), virtual_mode=True)

    return make


def make_plugin(settings: Settings) -> DeepAgentsPlugin:
    return DeepAgentsPlugin(
        backends={"workspace": workspace_factory(settings.workspace_root)},
    )


async def connect(settings: Settings) -> Client:
    return await Client.connect(
        settings.temporal_address,
        namespace=settings.temporal_namespace,
        plugins=[make_plugin(settings)],
    )


async def main() -> None:
    settings = Settings.from_env()
    client = await connect(settings)
    worker = Worker(
        client,
        task_queue=settings.task_queue,
        workflows=[BotWorkflow, ScheduledTurnWorkflow],
    )
    print(f"grokbot worker polling {settings.task_queue!r} at {settings.temporal_address}")
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())

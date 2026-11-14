"""Builds the Deep Agent for one bot.

This module is imported inside the workflow sandbox, so keep it free of I/O.
"""

from __future__ import annotations

from typing import Any

from temporalio.deepagents import create_temporal_deep_agent

from michel.models import BotConfig
from michel.tools import deliver_channel_message_tool, fetch_url_tool

# Tools whose calls must be approved by a human before they run.
APPROVAL_REQUIRED = {"deliver_channel_message": True}

RESEARCHER_PROMPT = (
    "You research questions using fetch_url only. Return a short, sourced "
    "summary with the URLs you used."
)


def build_bot_agent(
    cfg: BotConfig,
    *,
    checkpointer: Any = None,
    backend: Any = None,
    model: Any = None,
    tools: list[Any] | None = None,
) -> Any:
    """Create the Deep Agent.

    ``model`` and ``tools`` override the production values. Tests use them to run
    the same graph offline. Production never passes them.
    """
    fetch = tools[0] if tools else fetch_url_tool
    all_tools = tools or [fetch_url_tool, deliver_channel_message_tool]
    return create_temporal_deep_agent(
        model=model if model is not None else cfg.model,
        system_prompt=cfg.system_prompt,
        tools=all_tools,
        subagents=[
            {
                "name": "researcher",
                "description": "Gathers and summarizes information from allowed web pages.",
                "system_prompt": RESEARCHER_PROMPT,
                "tools": [fetch],
            }
        ],
        backend=backend,
        interrupt_on=APPROVAL_REQUIRED,
        checkpointer=checkpointer,
    )


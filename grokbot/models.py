"""Serializable data passed between gateway, workflows and activities."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


DEFAULT_SYSTEM_PROMPT = (
    "You are a helpful, careful assistant. Ask before taking actions with side effects."
)


@dataclass
class BotConfig:
    name: str
    system_prompt: str = DEFAULT_SYSTEM_PROMPT
    model: str | None = None  # None -> worker default model


@dataclass
class InboundMessage:
    sender: str
    text: str


@dataclass
class BotState:
    """Workflow input. Also the continue-as-new payload, so keep it small."""

    config: BotConfig
    transcript: list[dict[str, Any]] = field(default_factory=list)
    # LangChain messages serialized with messages_to_dict, restored on the next run.
    messages: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class ScheduledPrompt:
    bot_id: str
    prompt: str

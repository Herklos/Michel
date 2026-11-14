"""HTTP gateway: the entry point for chat channels, clients and schedules.

It holds no conversation state. Every request maps onto a Temporal operation:
start (create bot), signal (message, close), query (transcript, approval),
update (approve or reject), and create_schedule (recurring prompts).
"""

from __future__ import annotations

import hmac
import secrets
from typing import Any, Literal

from fastapi import Depends, FastAPI, Header, HTTPException, status
from pydantic import BaseModel, Field
from temporalio.client import (
    Client,
    Schedule,
    ScheduleActionStartWorkflow,
    ScheduleSpec,
)
from temporalio.exceptions import WorkflowAlreadyStartedError

from grokbot.config import Settings
from grokbot.models import (
    DEFAULT_SYSTEM_PROMPT,
    BotConfig,
    BotState,
    InboundMessage,
    ScheduledPrompt,
)
from grokbot.workflows import BotWorkflow, ScheduledTurnWorkflow


class CreateBot(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    system_prompt: str | None = Field(default=None, max_length=8000)
    model: str | None = None


class SendMessage(BaseModel):
    sender: str = Field(min_length=1, max_length=120)
    text: str = Field(min_length=1, max_length=20_000)


class Decision(BaseModel):
    decision: Literal["approve", "reject"]


class CreateSchedule(BaseModel):
    name: str = Field(min_length=1, max_length=60, pattern=r"^[a-zA-Z0-9_-]+$")
    cron: str = Field(description="5-field cron, e.g. '0 9 * * 1-5'")
    prompt: str = Field(min_length=1, max_length=20_000)


def create_app(
    client: Client | None,
    settings: Settings,
    lifespan: Any = None,
) -> FastAPI:
    """Build the gateway. Pass ``client=None`` and a ``lifespan`` that sets ``app.state.client``."""
    app = FastAPI(title="grokbot gateway", version="0.1.0", lifespan=lifespan)
    app.state.client = client
    app.state.settings = settings

    def tc() -> Client:
        return app.state.client

    def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
        expected = settings.gateway_api_key
        if expected is None:
            return  # auth disabled: local development only
        if not x_api_key or not hmac.compare_digest(x_api_key, expected):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid API key")

    auth = [Depends(require_api_key)]

    def handle(bot_id: str) -> Any:
        return tc().get_workflow_handle(bot_id)

    @app.post("/v1/bots", status_code=201, dependencies=auth)
    async def create_bot(body: CreateBot) -> dict[str, str]:
        bot_id = f"bot-{body.name.lower().replace(' ', '-')}-{secrets.token_hex(4)}"
        state = BotState(
            config=BotConfig(
                name=body.name,
                system_prompt=body.system_prompt or DEFAULT_SYSTEM_PROMPT,
                model=body.model or settings.default_model,
            )
        )
        await tc().start_workflow(
            BotWorkflow.run,
            state,
            id=bot_id,
            task_queue=settings.task_queue,
        )
        return {"bot_id": bot_id}

    @app.post("/v1/bots/{bot_id}/messages", status_code=202, dependencies=auth)
    async def send_message(bot_id: str, body: SendMessage) -> dict[str, str]:
        if settings.allowed_senders and body.sender not in settings.allowed_senders:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "sender is not allowed")
        await handle(bot_id).signal(
            BotWorkflow.enqueue_message, InboundMessage(sender=body.sender, text=body.text)
        )
        return {"status": "queued"}

    @app.get("/v1/bots/{bot_id}/transcript", dependencies=auth)
    async def transcript(bot_id: str) -> list[dict[str, Any]]:
        return await handle(bot_id).query(BotWorkflow.transcript)

    @app.get("/v1/bots/{bot_id}/approval", dependencies=auth)
    async def pending_approval(bot_id: str) -> dict[str, Any] | None:
        return await handle(bot_id).query(BotWorkflow.pending_approval)

    @app.post("/v1/bots/{bot_id}/approval", dependencies=auth)
    async def resolve_approval(bot_id: str, body: Decision) -> dict[str, str]:
        try:
            result = await handle(bot_id).execute_update(
                BotWorkflow.decide_approval, body.decision
            )
        except Exception as exc:  # validator rejections surface as update failures
            raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
        return {"decision": result}

    @app.delete("/v1/bots/{bot_id}", status_code=202, dependencies=auth)
    async def close_bot(bot_id: str) -> dict[str, str]:
        await handle(bot_id).signal(BotWorkflow.close)
        return {"status": "closing"}

    @app.post("/v1/bots/{bot_id}/schedules", status_code=201, dependencies=auth)
    async def create_schedule(bot_id: str, body: CreateSchedule) -> dict[str, str]:
        schedule_id = f"{bot_id}-{body.name}"
        schedule = Schedule(
            action=ScheduleActionStartWorkflow(
                ScheduledTurnWorkflow.run,
                ScheduledPrompt(bot_id=bot_id, prompt=body.prompt),
                id=f"{schedule_id}-run",
                task_queue=settings.task_queue,
            ),
            spec=ScheduleSpec(cron_expressions=[body.cron]),
        )
        try:
            await tc().create_schedule(schedule_id, schedule)
        except WorkflowAlreadyStartedError as exc:
            raise HTTPException(status.HTTP_409_CONFLICT, "schedule exists") from exc
        return {"schedule_id": schedule_id}

    return app

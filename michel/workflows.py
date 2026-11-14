"""Temporal workflows.

``BotWorkflow`` is one long-lived workflow per bot. It owns the conversation,
runs the Deep Agent for each inbound message, pauses on approval-gated tools,
and continues-as-new before history grows too large.

The agent loop itself runs inside the workflow and replays deterministically.
Each model call and each I/O tool call is an activity (see the plugin wiring
in ``michel.worker``).
"""

from __future__ import annotations

from collections import deque
from datetime import timedelta
from typing import Any

from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from langchain_core.messages import (
        AIMessage,
        HumanMessage,
        messages_from_dict,
        messages_to_dict,
    )
    from deepagents.backends import FilesystemBackend
    from langgraph.checkpoint.memory import InMemorySaver
    from langgraph.types import Command
    from temporalio.deepagents import TemporalBackend
    from temporalio.workflow import ActivityConfig

    from michel.agent import build_bot_agent
    from michel.models import BotState, InboundMessage, ScheduledPrompt

MAX_TRANSCRIPT_ITEMS = 500


def _last_ai_text(messages: list[Any]) -> str:
    for msg in reversed(messages):
        if isinstance(msg, AIMessage) and msg.content:
            content = msg.content
            if isinstance(content, list):
                return "".join(
                    part.get("text", "") if isinstance(part, dict) else str(part)
                    for part in content
                )
            return str(content)
    return ""


def _approval_summary(interrupt_value: Any) -> dict[str, Any]:
    """Shape the HITL request for clients: which tool, with which arguments."""
    actions = []
    if isinstance(interrupt_value, dict):
        for action in interrupt_value.get("action_requests", []):
            actions.append(
                {"tool": action.get("name"), "args": action.get("args", {})}
            )
    return {"actions": actions, "decisions_needed": max(len(actions), 1)}


@workflow.defn
class BotWorkflow:
    def __init__(self) -> None:
        self._inbox: deque[InboundMessage] = deque()
        self._transcript: list[dict[str, Any]] = []
        self._pending: dict[str, Any] | None = None
        self._decision: str | None = None
        self._closed = False

    # ---- main loop -------------------------------------------------------

    @workflow.run
    async def run(self, state: BotState) -> None:
        bot_id = workflow.info().workflow_id
        self._transcript = list(state.transcript)

        # File and shell tools run as durable activities against the worker's
        # per-bot workspace (see worker.workspace_factory).
        backend = TemporalBackend(
            "workspace",
            factory_argument=bot_id,
            backend_type=FilesystemBackend,
            activity_options=ActivityConfig(start_to_close_timeout=timedelta(seconds=30)),
        )
        checkpointer = InMemorySaver()
        agent = build_bot_agent(
            state.config, checkpointer=checkpointer, backend=backend
        )
        config = {"configurable": {"thread_id": bot_id}}
        if state.messages:
            # Restore the agent's message history after continue-as-new.
            await agent.aupdate_state(
                config, {"messages": messages_from_dict(state.messages)}
            )

        while True:
            await workflow.wait_condition(lambda: bool(self._inbox) or self._closed)
            if not self._inbox:
                break  # closed with nothing queued

            msg = self._inbox.popleft()
            self._record("user", msg.text, sender=msg.sender)
            result = await agent.ainvoke(
                {"messages": [HumanMessage(content=msg.text)]}, config=config
            )

            # Human-in-the-loop: pause until a client resolves the approval.
            while result.get("__interrupt__"):
                interrupt_value = result["__interrupt__"][0].value
                summary = _approval_summary(interrupt_value)
                self._pending = summary
                await workflow.wait_condition(
                    lambda: self._decision is not None or self._closed
                )
                decision = self._decision or "reject"  # closing rejects pending work
                self._pending = None
                self._decision = None
                resume = Command(
                    resume={
                        "decisions": [
                            {"type": decision}
                            for _ in range(summary["decisions_needed"])
                        ]
                    }
                )
                result = await agent.ainvoke(resume, config=config)

            self._record("assistant", _last_ai_text(result.get("messages", [])))

            if (
                workflow.info().is_continue_as_new_suggested()
                and not self._inbox
                and not self._closed
            ):
                snapshot = await agent.aget_state(config)
                workflow.continue_as_new(
                    BotState(
                        config=state.config,
                        transcript=self._transcript[-MAX_TRANSCRIPT_ITEMS:],
                        messages=messages_to_dict(snapshot.values["messages"]),
                    )
                )

    def _record(self, role: str, text: str, sender: str | None = None) -> None:
        item: dict[str, Any] = {"role": role, "text": text}
        if sender:
            item["sender"] = sender
        self._transcript.append(item)
        if len(self._transcript) > MAX_TRANSCRIPT_ITEMS:
            del self._transcript[: len(self._transcript) - MAX_TRANSCRIPT_ITEMS]

    # ---- client interface ------------------------------------------------

    @workflow.signal
    def enqueue_message(self, msg: InboundMessage) -> None:
        self._inbox.append(msg)

    @workflow.signal
    def close(self) -> None:
        self._closed = True

    @workflow.query
    def transcript(self) -> list[dict[str, Any]]:
        return self._transcript

    @workflow.query
    def pending_approval(self) -> dict[str, Any] | None:
        return self._pending

    @workflow.update
    async def decide_approval(self, decision: str) -> str:
        if self._pending is None:
            raise ValueError("No approval is pending.")
        self._decision = decision
        return decision

    @decide_approval.validator
    def _validate_decision(self, decision: str) -> None:
        if decision not in ("approve", "reject"):
            raise ValueError("decision must be 'approve' or 'reject'.")
        if self._pending is None:
            raise ValueError("No approval is pending.")


@workflow.defn
class ScheduledTurnWorkflow:
    """Started by a Temporal Schedule. Delivers a prompt to a bot as a normal message."""

    @workflow.run
    async def run(self, job: ScheduledPrompt) -> None:
        handle = workflow.get_external_workflow_handle(job.bot_id)
        await handle.signal(
            BotWorkflow.enqueue_message,
            InboundMessage(sender="schedule", text=job.prompt),
        )


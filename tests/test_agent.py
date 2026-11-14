"""Offline tests for the agent graph: approval gating, resume, and history restore.

They use a scripted FakeModel and plain LangChain tools, so no Temporal server or
LLM is required. They verify the same graph shape the workflow runs.
"""

import asyncio

from deepagents.backends import StateBackend  # noqa: F401  (documents default backend)
from langchain_core.messages import AIMessage, HumanMessage, messages_from_dict, messages_to_dict
from langchain_core.tools import tool
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command
from temporalio.deepagents.testing import FakeModel

from michel.agent import APPROVAL_REQUIRED, build_bot_agent
from michel.models import BotConfig
from michel.workflows import _approval_summary, _last_ai_text

CALLS: list[tuple[str, str]] = []


@tool
def fetch_url(url: str) -> str:
    """Fetch a page."""
    CALLS.append(("fetch_url", url))
    return f"page for {url}"


@tool
def deliver_channel_message(channel: str, text: str) -> str:
    """Post a message to a channel."""
    CALLS.append(("deliver", f"{channel}:{text}"))
    return "delivered"


def _deliver_call(text: str) -> AIMessage:
    return AIMessage(
        content="",
        tool_calls=[
            {
                "name": "deliver_channel_message",
                "args": {"channel": "ops", "text": text},
                "id": "call-1",
                "type": "tool_call",
            }
        ],
    )


def _agent(responses):
    CALLS.clear()
    return build_bot_agent(
        BotConfig(name="t"),
        checkpointer=InMemorySaver(),
        model=FakeModel(responses),
        tools=[fetch_url, deliver_channel_message],
    )


def test_approval_is_required_for_side_effect_tool():
    assert APPROVAL_REQUIRED == {"deliver_channel_message": True}


def test_side_effect_pauses_then_runs_on_approve():
    agent = _agent([_deliver_call("hello"), "Posted it."])
    config = {"configurable": {"thread_id": "t1"}}

    result = asyncio.run(
        agent.ainvoke({"messages": [HumanMessage(content="post hello")]}, config=config)
    )
    assert CALLS == [], "tool must not run before approval"
    interrupts = result.get("__interrupt__")
    assert interrupts, "agent should pause for approval"
    summary = _approval_summary(interrupts[0].value)
    assert summary["actions"][0]["tool"] == "deliver_channel_message"
    assert summary["actions"][0]["args"] == {"channel": "ops", "text": "hello"}

    done = asyncio.run(
        agent.ainvoke(
            Command(resume={"decisions": [{"type": "approve"}]}), config=config
        )
    )
    assert CALLS == [("deliver", "ops:hello")]
    assert _last_ai_text(done["messages"]) == "Posted it."


def test_reject_skips_tool_and_agent_continues():
    agent = _agent([_deliver_call("secret"), "Understood, not posting."])
    config = {"configurable": {"thread_id": "t2"}}
    asyncio.run(agent.ainvoke({"messages": [HumanMessage(content="post")]}, config=config))

    done = asyncio.run(
        agent.ainvoke(
            Command(resume={"decisions": [{"type": "reject"}]}), config=config
        )
    )
    assert CALLS == [], "rejected tool must not execute"
    assert _last_ai_text(done["messages"]) == "Understood, not posting."


def test_history_survives_continue_as_new_snapshot():
    """Continue-as-new restores messages with aupdate_state on a fresh checkpointer."""
    first = _agent(["First reply."])
    config = {"configurable": {"thread_id": "t3"}}
    asyncio.run(first.ainvoke({"messages": [HumanMessage(content="hi")]}, config=config))
    snapshot = asyncio.run(first.aget_state(config))
    payload = messages_to_dict(snapshot.values["messages"])

    CALLS.clear()
    second = build_bot_agent(
        BotConfig(name="t"),
        checkpointer=InMemorySaver(),
        model=FakeModel(["Second reply."]),
        tools=[fetch_url, deliver_channel_message],
    )
    asyncio.run(second.aupdate_state(config, {"messages": messages_from_dict(payload)}))
    restored = asyncio.run(second.aget_state(config)).values["messages"]
    texts = [m.content for m in restored]
    assert "hi" in texts and "First reply." in texts

    done = asyncio.run(second.ainvoke({"messages": [HumanMessage(content="again")]}, config=config))
    assert _last_ai_text(done["messages"]) == "Second reply."


def test_last_ai_text_handles_content_blocks():
    msgs = [AIMessage(content=[{"type": "text", "text": "a"}, {"type": "text", "text": "b"}])]
    assert _last_ai_text(msgs) == "ab"

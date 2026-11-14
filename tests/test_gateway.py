"""Gateway tests against a fake Temporal client. They check the mapping from HTTP to Temporal operations."""

import pytest
from fastapi.testclient import TestClient

from michel.config import Settings
from michel.gateway import create_app
from michel.models import BotState, InboundMessage, ScheduledPrompt
from michel.workflows import BotWorkflow


class FakeHandle:
    def __init__(self, log, bot_id):
        self.log, self.bot_id = log, bot_id

    async def signal(self, sig, arg=None):
        self.log.append(("signal", self.bot_id, sig.__name__, arg))

    async def query(self, q):
        self.log.append(("query", self.bot_id, q.__name__))
        if q.__name__ == "pending_approval":
            return {"actions": [{"tool": "deliver_channel_message", "args": {}}], "decisions_needed": 1}
        return [{"role": "user", "text": "hi", "sender": "alice"}]

    async def execute_update(self, upd, arg):
        self.log.append(("update", self.bot_id, upd.__name__, arg))
        if arg == "bad":
            raise RuntimeError("No approval is pending.")
        return arg


class FakeClient:
    def __init__(self):
        self.log = []
        self.started = []
        self.schedules = []

    def get_workflow_handle(self, bot_id):
        return FakeHandle(self.log, bot_id)

    async def start_workflow(self, run, arg, id, task_queue):
        self.started.append((run.__name__, arg, id, task_queue))

    async def create_schedule(self, sid, schedule):
        self.schedules.append((sid, schedule))


def _client(settings: Settings | None = None):
    fake = FakeClient()
    app = create_app(fake, settings or Settings(task_queue="q"))
    return fake, TestClient(app)


def test_create_bot_starts_workflow_with_default_model():
    fake, http = _client(Settings(task_queue="q", default_model="anthropic:m"))
    r = http.post("/v1/bots", json={"name": "Ops Helper"})
    assert r.status_code == 201
    bot_id = r.json()["bot_id"]
    name, state, id_, queue = fake.started[0]
    assert name == "run" and id_ == bot_id and queue == "q"
    assert isinstance(state, BotState) and state.config.model == "anthropic:m"


def test_message_is_signalled_as_inbound():
    fake, http = _client()
    r = http.post("/v1/bots/bot-x/messages", json={"sender": "alice", "text": "hello"})
    assert r.status_code == 202
    assert fake.log == [("signal", "bot-x", "enqueue_message", InboundMessage(sender="alice", text="hello"))]


def test_sender_allowlist_blocks_unknown_sender():
    _, http = _client(Settings(allowed_senders=frozenset({"alice"})))
    r = http.post("/v1/bots/bot-x/messages", json={"sender": "mallory", "text": "hi"})
    assert r.status_code == 403


def test_api_key_required_when_configured():
    _, http = _client(Settings(gateway_api_key="s3cret"))
    assert http.get("/v1/bots/b/transcript").status_code == 401
    assert http.get("/v1/bots/b/transcript", headers={"X-API-Key": "wrong"}).status_code == 401
    ok = http.get("/v1/bots/b/transcript", headers={"X-API-Key": "s3cret"})
    assert ok.status_code == 200 and ok.json()[0]["text"] == "hi"


def test_transcript_and_pending_approval_are_queries():
    fake, http = _client()
    http.get("/v1/bots/b1/transcript")
    r = http.get("/v1/bots/b1/approval")
    assert r.json()["decisions_needed"] == 1
    assert ("query", "b1", "transcript") in fake.log
    assert ("query", "b1", "pending_approval") in fake.log


def test_approval_decision_is_an_update_and_bad_values_are_rejected():
    fake, http = _client()
    assert http.post("/v1/bots/b1/approval", json={"decision": "approve"}).json() == {"decision": "approve"}
    assert ("update", "b1", "decide_approval", "approve") in fake.log
    assert http.post("/v1/bots/b1/approval", json={"decision": "maybe"}).status_code == 422


def test_close_signals_bot():
    fake, http = _client()
    assert http.delete("/v1/bots/b1").status_code == 202
    assert fake.log[-1] == ("signal", "b1", "close", None)


def test_schedule_targets_scheduled_turn_workflow():
    fake, http = _client()
    r = http.post("/v1/bots/bot-z/schedules", json={"name": "morning", "cron": "0 9 * * 1-5", "prompt": "Brief me"})
    assert r.status_code == 201
    sid, schedule = fake.schedules[0]
    assert sid == "bot-z-morning"
    action = schedule.action
    assert action.args[0] == ScheduledPrompt(bot_id="bot-z", prompt="Brief me")
    assert schedule.spec.cron_expressions == ["0 9 * * 1-5"]


def test_schedule_name_is_validated():
    _, http = _client()
    r = http.post("/v1/bots/b/schedules", json={"name": "bad name!", "cron": "* * * * *", "prompt": "x"})
    assert r.status_code == 422

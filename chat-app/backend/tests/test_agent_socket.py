import pytest
import asyncio
import types
from datetime import datetime

import socket_handlers as socket_handlers


class FakeAgent:
    def __init__(self):
        pass
    def get_display_name(self):
        return 'Fake Agent'
    async def ask(self, message, user_id, user_name):
        return 'Fake answer'
    async def ask_with_context(self, message, user_id, user_name, contact_id=None, conversation_context=None):
        return 'Fake answer with context'


@pytest.mark.asyncio
async def test_process_agent_message_emits_agent_message(monkeypatch):
    calls = []

    async def fake_emit(event, payload, to=None, room=None, skip_sid=None, **kwargs):
        calls.append({'event': event, 'payload': payload, 'to': to, 'room': room, 'skip_sid': skip_sid})

    # Monkeypatch emit
    monkeypatch.setattr(socket_handlers, 'sio', socket_handlers.sio)
    monkeypatch.setattr(socket_handlers.sio, 'emit', fake_emit)

    # Monkeypatch get_agent to return a fake agent
    import bots.agents as agents_module
    monkeypatch.setattr(agents_module, 'get_agent', lambda name, uid=None: FakeAgent())
    monkeypatch.setattr(agents_module, 'generate_agent_suggestions', lambda agent, ctx, uid, uname, n_suggestions=3: [])

    # Monkeypatch DB insert collections
    from database import agent_messages_collection
    async def fake_insert(doc):
        class Result:
            inserted_id = 'fakeid'
        return Result()
    monkeypatch.setattr(agent_messages_collection, 'insert_one', fake_insert)

    # Monkeypatch get_conversation_context to return empty
    import bots.context_loader as ctxloader
    monkeypatch.setattr(ctxloader, 'get_conversation_context', lambda *args, **kwargs: [])

    # Monkeypatch sio.get_environ to return user info
    monkeypatch.setattr(socket_handlers.sio, 'get_environ', lambda sid: {'user_id': 'user123', 'user_name': 'User'})

    sid = 'TEST_SID'
    data = {
        'agentKey': 'sdr',
        'message': 'hello',
        'userId': 'user123',
        'userName': 'User',
        'contactId': 'contact123'
    }

    await socket_handlers.process_agent_message(sid, data)

    # Should have emitted at least one agent:message call to sid
    # debug for collectors
    emitted = [c for c in calls if c['event'] == 'agent:message']
    assert len(emitted) >= 1
    payload = emitted[0]['payload']
    assert payload['agentKey'] == 'sdr'
    assert 'text' in payload

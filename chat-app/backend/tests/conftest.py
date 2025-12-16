import asyncio
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

pytest_plugins = ("pytest_asyncio",)

# Ajusta sys.path para resolver imports do backend
ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = ROOT / "backend"
sys.path.append(str(ROOT))
sys.path.append(str(BACKEND_DIR))

import main
import routers.messages as messages_router
import routers.uploads as uploads_router
from socket_manager import sio


class FakeInsertResult:
    def __init__(self, inserted_id):
        self.inserted_id = inserted_id


class FakeCursor:
    def __init__(self, data):
        self.data = list(data)
        self._limit = None

    def sort(self, *_args):
        return self

    def limit(self, limit):
        self._limit = limit
        return self

    async def to_list(self, length=None):
        data = self.data
        if self._limit:
            data = data[-self._limit:]
        return data[-(length or len(data)):]


class FakeCollection:
    def __init__(self, data=None):
        self.data = data or []

    def find(self, query=None):
        query = query or {}

        def match(doc):
            # Suporte básico para $or/$and e filtros por userId/contactId
            if "$or" in query:
                return any(all(doc.get(k) == v for k, v in cond.items()) for cond in query["$or"])
            if "$and" in query:
                return all(all(doc.get(k) == v for k, v in cond.items()) for cond in query["$and"])
            return all(doc.get(k) == v for k, v in query.items())

        filtered = [d for d in self.data if match(d)]
        return FakeCursor(filtered)

    async def insert_one(self, doc):
        if "_id" not in doc:
            doc["_id"] = f"id_{len(self.data)+1}"
        self.data.append(doc)
        return FakeInsertResult(doc["_id"])

    async def update_many(self, query, update):
        ids = query.get("_id", {}).get("$in", [])
        modified = 0
        for doc in self.data:
            if doc.get("_id") in ids:
                doc.update(update.get("$set", {}))
                modified += 1
        class Result:
            modified_count = modified
        return Result()


@pytest.fixture(autouse=True)
def patch_startup(monkeypatch):
    """Evita side effects de scheduler/automações durante testes."""
    async def _noop(*_args, **_kwargs):
        return None
    monkeypatch.setattr(main, "start_scheduler", lambda: None)
    monkeypatch.setattr(main, "load_and_schedule_all", _noop)
    # Evita criar índices e carregar bots customizados no Mongo real
    import database
    monkeypatch.setattr(database, "create_indexes", _noop)
    # Usa coleções fake para evitar dependência de Mongo
    monkeypatch.setattr(database, "agent_messages_collection", FakeCollection(), raising=False)
    monkeypatch.setattr(database, "messages_collection", FakeCollection(), raising=False)
    import bots.agents as agents_module
    monkeypatch.setattr(agents_module, "load_custom_agents_from_db", _noop)
    yield


@pytest.fixture
def fake_messages_collection():
    now = datetime.now(timezone.utc)
    return FakeCollection([
        {
          "_id": "m1",
          "author": "Alice",
          "text": "hello",
          "status": "sent",
          "type": "text",
          "userId": "u1",
          "contactId": "c2",
          "createdAt": now - timedelta(minutes=5)
        },
        {
          "_id": "m2",
          "author": "Bob",
          "text": "other",
          "status": "sent",
          "type": "text",
          "userId": "u3",
          "contactId": "u4",
          "createdAt": now - timedelta(minutes=10)
        }
    ])


@pytest.fixture
def client(monkeypatch, fake_messages_collection):
    # Override auth dependency
    main.app.dependency_overrides = {}
    def fake_user():
        return "u1"
    from deps import get_current_user_id
    main.app.dependency_overrides[get_current_user_id] = fake_user

    # Patch collections usados nas rotas
    monkeypatch.setattr(messages_router, "messages_collection", fake_messages_collection, raising=False)
    monkeypatch.setattr(uploads_router, "messages_collection", fake_messages_collection, raising=False)

    # Patch presign urls
    monkeypatch.setattr(uploads_router, "presign_put", lambda *args, **kwargs: "http://fake-put-url")
    monkeypatch.setattr(uploads_router, "presign_get", lambda *args, **kwargs: "http://fake-get-url")

    # Patch sio.emit para não usar rede
    async def fake_emit(*_args, **_kwargs):
        return None
    monkeypatch.setattr(sio, "emit", fake_emit)

    with TestClient(main.app) as c:
        yield c

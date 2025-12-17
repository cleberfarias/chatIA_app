"""
Testes para módulo de contatos (contacts.py)
Cobertura: list_contacts, get_conversation, mark_conversation_read
"""
import pytest
from datetime import datetime
from bson import ObjectId


def test_list_contacts_requires_authentication(client):
    """Testa que listar contatos requer autenticação"""
    response = client.get("/contacts/")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_contacts_returns_users_except_self(monkeypatch):
    """Testa que lista retorna todos usuários exceto o próprio"""
    # Mock do database
    fake_users = [
        {
            "_id": ObjectId("507f1f77bcf86cd799439011"),  # user1 (próprio)
            "email": "user1@test.com",
            "name": "User One",
        },
        {
            "_id": ObjectId("507f1f77bcf86cd799439012"),  # user2
            "email": "user2@test.com",
            "name": "User Two",
        },
        {
            "_id": ObjectId("507f1f77bcf86cd799439013"),  # user3
            "email": "user3@test.com",
            "name": "User Three",
        }
    ]
    
    class FakeCursor:
        def __init__(self, data):
            self.data = data
        
        async def to_list(self, length):
            # Filtra user1 (próprio usuário)
            return [u for u in self.data if str(u["_id"]) != "507f1f77bcf86cd799439011"]
    
    class FakeUsersCollection:
        def find(self, query, projection):
            # Simula filtragem do próprio usuário
            return FakeCursor(fake_users)
    
    class FakeMessagesCollection:
        async def find_one(self, query, **kwargs):
            return None  # Sem mensagens por enquanto
    
    class FakeDb:
        def __init__(self):
            self.users = FakeUsersCollection()
            self.messages = FakeMessagesCollection()
    
    import contacts
    monkeypatch.setattr("contacts.db", FakeDb())
    
    from contacts import list_contacts
    
    # Testa endpoint
    result = await list_contacts("507f1f77bcf86cd799439011")
    
    assert len(result) == 2
    assert all(c.id != "507f1f77bcf86cd799439011" for c in result)


@pytest.mark.asyncio
async def test_list_contacts_includes_last_message(monkeypatch):
    """Testa que contatos incluem última mensagem"""
    fake_users = [
        {
            "_id": ObjectId("507f1f77bcf86cd799439012"),
            "email": "user2@test.com",
            "name": "User Two",
        }
    ]
    
    last_msg_time = datetime(2024, 1, 15, 10, 30, 0)
    fake_message = {
        "_id": ObjectId(),
        "text": "Última mensagem",
        "createdAt": last_msg_time,
        "userId": "507f1f77bcf86cd799439012"
    }
    
    class FakeCursor:
        async def to_list(self, length):
            return fake_users
    
    class FakeUsersCollection:
        def find(self, query, projection):
            return FakeCursor()
    
    class FakeMessagesCollection:
        async def find_one(self, query, **kwargs):
            return fake_message
    
    class FakeDb:
        def __init__(self):
            self.users = FakeUsersCollection()
            self.messages = FakeMessagesCollection()
    
    import contacts
    monkeypatch.setattr("contacts.db", FakeDb())
    
    from contacts import list_contacts
    result = await list_contacts("user1_id")
    
    assert len(result) == 1
    assert result[0].lastMessage == "Última mensagem"
    assert result[0].lastMessageTime == int(last_msg_time.timestamp() * 1000)


@pytest.mark.asyncio
async def test_list_contacts_sorts_by_last_message_time(monkeypatch):
    """Testa que contatos são ordenados por última mensagem"""
    from datetime import datetime, timedelta
    
    now = datetime.utcnow()
    old_time = now - timedelta(days=2)
    recent_time = now - timedelta(hours=1)
    
    fake_users = [
        {
            "_id": ObjectId("507f1f77bcf86cd799439012"),
            "email": "old@test.com",
            "name": "Old Contact",
        },
        {
            "_id": ObjectId("507f1f77bcf86cd799439013"),
            "email": "recent@test.com",
            "name": "Recent Contact",
        }
    ]
    
    messages_map = {
        "507f1f77bcf86cd799439012": {
            "text": "Mensagem antiga",
            "createdAt": old_time,
        },
        "507f1f77bcf86cd799439013": {
            "text": "Mensagem recente",
            "createdAt": recent_time,
        }
    }
    
    class FakeCursor:
        async def to_list(self, length):
            return fake_users
    
    class FakeUsersCollection:
        def find(self, query, projection):
            return FakeCursor()
    
    class FakeMessagesCollection:
        async def find_one(self, query, **kwargs):
            # Identifica qual usuário pela query
            if "contactId" in query.get("$or", [{}])[0]:
                user_id = query["$or"][0]["contactId"]
            elif "userId" in query.get("$or", [{}])[1]:
                user_id = query["$or"][1]["userId"]
            else:
                return None
            
            return messages_map.get(user_id)
    
    class FakeDb:
        def __init__(self):
            self.users = FakeUsersCollection()
            self.messages = FakeMessagesCollection()
    
    import contacts
    monkeypatch.setattr("contacts.db", FakeDb())
    
    from contacts import list_contacts
    result = await list_contacts("user1_id")
    
    # Primeiro contato deve ser o mais recente
    assert result[0].name == "Recent Contact"
    assert result[1].name == "Old Contact"


def test_get_conversation_requires_authentication(client):
    """Testa que buscar conversa requer autenticação"""
    response = client.get("/contacts/contact123/messages")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_conversation_validates_contact_exists(monkeypatch):
    """Testa validação se contato existe"""
    # Mock para retornar que contato não existe
    class FakeUsersCollection:
        async def find_one(self, query):
            return None  # Contato não encontrado
    
    class FakeDb:
        def __init__(self):
            self.users = FakeUsersCollection()
    
    import contacts
    monkeypatch.setattr("contacts.db", FakeDb())
    monkeypatch.setattr("contacts.get_current_user_id", lambda: "user1")
    
    from contacts import get_conversation
    
    with pytest.raises(Exception):  # HTTPException 404
        await get_conversation("nonexistent_contact", 50, None, "user1")


@pytest.mark.asyncio
async def test_get_conversation_returns_messages(monkeypatch):
    """Testa retorno de mensagens da conversa"""
    fake_contact = {
        "_id": ObjectId("507f1f77bcf86cd799439012"),
        "email": "contact@test.com",
        "name": "Contact"
    }
    
    fake_messages = [
        {
            "_id": ObjectId("607f1f77bcf86cd799439001"),
            "author": "User1",
            "text": "Mensagem 1",
            "timestamp": 1640000000000,
            "type": "text",
            "userId": "user1",
            "contactId": "507f1f77bcf86cd799439012"
        },
        {
            "_id": ObjectId("607f1f77bcf86cd799439002"),
            "author": "Contact",
            "text": "Mensagem 2",
            "timestamp": 1640001000000,
            "type": "text",
            "userId": "507f1f77bcf86cd799439012",
            "contactId": "user1"
        }
    ]
    
    class FakeCursor:
        def __init__(self, data):
            self.data = data
            self.limited = False
        
        def sort(self, *args):
            return self
        
        def limit(self, n):
            self.limited = True
            self.limit_n = n
            return self
        
        async def to_list(self, length):
            if self.limited:
                return self.data[:self.limit_n]
            return self.data
    
    class FakeUsersCollection:
        async def find_one(self, query):
            return fake_contact
    
    class FakeMessagesCollection:
        def find(self, query, projection=None):
            return FakeCursor(fake_messages)
        
        async def count_documents(self, query):
            return len(fake_messages)
    
    class FakeDb:
        def __init__(self):
            self.users = FakeUsersCollection()
            self.messages = FakeMessagesCollection()
    
    import contacts
    monkeypatch.setattr("contacts.db", FakeDb())
    
    from contacts import get_conversation
    result = await get_conversation("507f1f77bcf86cd799439012", 50, None, "user1")
    
    assert len(result.messages) <= 50
    assert result.hasMore is not None


@pytest.mark.asyncio
async def test_get_conversation_with_pagination(monkeypatch):
    """Testa paginação com parâmetro 'before'"""
    # Cria 60 mensagens para testar paginação
    fake_messages = [
        {
            "_id": ObjectId(),
            "author": "User",
            "text": f"Mensagem {i}",
            "timestamp": 1640000000000 + i * 1000,
            "type": "text"
        }
        for i in range(60)
    ]
    
    class FakeCursor:
        def __init__(self, data):
            self.data = data
        
        def sort(self, *args):
            return self
        
        def limit(self, n):
            self.data = self.data[:n]
            return self
        
        async def to_list(self, length):
            return self.data
    
    class FakeUsersCollection:
        async def find_one(self, query):
            return {"_id": ObjectId(), "email": "test@test.com"}
    
    class FakeMessagesCollection:
        def find(self, query, projection=None):
            # Filtra mensagens antes do timestamp 'before'
            if "$lt" in query.get("timestamp", {}):
                before = query["timestamp"]["$lt"]
                filtered = [m for m in fake_messages if m["timestamp"] < before]
                return FakeCursor(filtered)
            return FakeCursor(fake_messages)
        
        async def count_documents(self, query):
            return 60
    
    class FakeDb:
        def __init__(self):
            self.users = FakeUsersCollection()
            self.messages = FakeMessagesCollection()
    
    import contacts
    monkeypatch.setattr("contacts.db", FakeDb())
    
    from contacts import get_conversation
    
    # Primeira página (sem before)
    result1 = await get_conversation("contact_id", 50, None, "user1")
    assert len(result1.messages) <= 50
    assert result1.hasMore is True  # Tem mais 10 mensagens
    
    # Segunda página (com before)
    oldest_timestamp = result1.messages[-1].timestamp if result1.messages else None
    if oldest_timestamp:
        result2 = await get_conversation("contact_id", 50, oldest_timestamp, "user1")
        assert len(result2.messages) <= 10


def test_mark_conversation_read_requires_authentication(client):
    """Testa que marcar como lido requer autenticação"""
    response = client.put("/contacts/contact123/read")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_mark_conversation_read_updates_messages(monkeypatch):
    """Testa que marca mensagens como lidas"""
    updated_count = {"value": 0}
    
    class FakeMessagesCollection:
        async def update_many(self, query, update):
            # Verifica query correta
            assert "$or" in query
            assert {"$set": {"status": "read"}} == update
            
            updated_count["value"] = 5  # Simula 5 mensagens atualizadas
            return type('obj', (object,), {'modified_count': 5})()
    
    class FakeDb:
        def __init__(self):
            self.messages = FakeMessagesCollection()
    
    import contacts
    monkeypatch.setattr("contacts.db", FakeDb())
    
    from contacts import mark_conversation_read
    result = await mark_conversation_read("contact123", "user1")
    
    assert updated_count["value"] == 5


@pytest.mark.asyncio
async def test_list_contacts_handles_no_messages(monkeypatch):
    """Testa contatos sem mensagens"""
    fake_users = [
        {
            "_id": ObjectId("507f1f77bcf86cd799439012"),
            "email": "nomsg@test.com",
            "name": "No Messages",
        }
    ]
    
    class FakeCursor:
        async def to_list(self, length):
            return fake_users
    
    class FakeUsersCollection:
        def find(self, query, projection):
            return FakeCursor()
    
    class FakeMessagesCollection:
        async def find_one(self, query, **kwargs):
            return None  # Sem mensagens
    
    class FakeDb:
        def __init__(self):
            self.users = FakeUsersCollection()
            self.messages = FakeMessagesCollection()
    
    import contacts
    monkeypatch.setattr("contacts.db", FakeDb())
    
    from contacts import list_contacts
    result = await list_contacts("user1")
    
    assert len(result) == 1
    assert result[0].lastMessage == ""
    assert result[0].lastMessageTime == 0


@pytest.mark.asyncio
async def test_get_conversation_with_attachments(monkeypatch):
    """Testa mensagens com anexos"""
    fake_messages = [
        {
            "_id": ObjectId(),
            "author": "User",
            "text": "Foto anexada",
            "timestamp": 1640000000000,
            "type": "image",
            "attachment": {
                "url": "https://example.com/image.png",
                "mimetype": "image/png"
            }
        }
    ]
    
    class FakeCursor:
        def sort(self, *args):
            return self
        def limit(self, n):
            return self
        async def to_list(self, length):
            return fake_messages
    
    class FakeUsersCollection:
        async def find_one(self, query):
            return {"_id": ObjectId(), "email": "test@test.com"}
    
    class FakeMessagesCollection:
        def find(self, query, projection=None):
            return FakeCursor()
        async def count_documents(self, query):
            return 1
    
    class FakeDb:
        def __init__(self):
            self.users = FakeUsersCollection()
            self.messages = FakeMessagesCollection()
    
    import contacts
    monkeypatch.setattr("contacts.db", FakeDb())
    
    from contacts import get_conversation
    result = await get_conversation("contact_id", 50, None, "user1")
    
    assert len(result.messages) == 1
    assert result.messages[0].type == "image"
    assert result.messages[0].attachment is not None

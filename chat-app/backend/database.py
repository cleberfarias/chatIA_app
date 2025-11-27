from motor.motor_asyncio import AsyncIOMotorClient
from os import getenv

DATABASE_URL = getenv("DATABASE_URL", "mongodb://mongo:27017/chatdb?replicaSet=rs0")

# Cliente MongoDB assíncrono
client = AsyncIOMotorClient(DATABASE_URL)
db = client.chatdb
messages_collection = db.messages

# 🤖 Collection separada para mensagens dos agentes
agent_messages_collection = db.agent_messages

# 🧠 Collection para logs de interações com NLU
interactions_collection = db.interactions

# 🤝 Collection para requisições de handover (bot→humano)
handovers_collection = db.handovers

# 📅 Collection para eventos do calendário
calendar_events_collection = db.calendar_events


# Criar índices para otimizar consultas
async def create_indexes():
    """Cria índices nas collections para melhor performance"""
    # Índice para buscar interações por usuário e timestamp
    await interactions_collection.create_index([("user_id", 1), ("timestamp", -1)])
    await interactions_collection.create_index([("agent", 1)])
    await interactions_collection.create_index([("intent", 1)])
    
    # Índice para buscar handovers por status e prioridade
    await handovers_collection.create_index([("status", 1), ("priority", -1)])
    await handovers_collection.create_index([("customer_id", 1)])
    await handovers_collection.create_index([("assigned_agent", 1)])
    await handovers_collection.create_index([("created_at", -1)])
    
    # Índice para buscar eventos por data e status
    await calendar_events_collection.create_index([("start_time", 1)])
    await calendar_events_collection.create_index([("customer_id", 1)])
    await calendar_events_collection.create_index([("agent_id", 1)])
    await calendar_events_collection.create_index([("status", 1)])
    await calendar_events_collection.create_index([("google_event_id", 1)], unique=True)

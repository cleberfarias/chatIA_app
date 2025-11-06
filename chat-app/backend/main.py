import socketio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from database import messages_collection
from models import MessageCreate, MessageResponse
from bson import ObjectId

# FastAPI app
app = FastAPI(title="Chat API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Socket.IO server
sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins="*",
    logger=True,
    engineio_logger=True
)

# Wrap com Socket.IO
socket_app = socketio.ASGIApp(sio, app)


@app.get("/")
async def health_check():
    return {"status": "ok", "message": "Chat API running with Python"}


@app.get("/messages")
async def get_messages(limit: int = 50):
    """Retorna histórico de mensagens"""
    cursor = messages_collection.find().sort("createdAt", -1).limit(limit)
    docs = await cursor.to_list(length=limit)
    
    # Transforma documentos para o formato esperado pelo frontend
    messages = []
    for doc in reversed(docs):  # Inverte para ordem crescente
        messages.append(MessageResponse(
            id=str(doc["_id"]),
            author=doc["author"],
            text=doc["text"],
            timestamp=int(doc["createdAt"].timestamp() * 1000),
            status=doc.get("status", "sent"),
            type=doc.get("type", "text")
        ).model_dump())
    
    return messages


@sio.event
async def connect(sid, environ):
    print(f"🔌 Cliente conectado: {sid}")


@sio.event
async def disconnect(sid):
    print(f"🔌 Cliente desconectado: {sid}")


@sio.on("chat:send")
async def handle_chat_send(sid, data):
    """Recebe mensagem do cliente, salva no MongoDB e broadcast para todos"""
    try:
        print(f"📨 Mensagem recebida de {sid}: {data}")
        
        # Validação com Pydantic
        message_create = MessageCreate(**data)
        
        # Cria documento para MongoDB
        doc = {
            "author": message_create.author,
            "text": message_create.text,
            "status": message_create.status,
            "type": message_create.type,
            "createdAt": datetime.utcnow()
        }
        
        # Insere no MongoDB
        result = await messages_collection.insert_one(doc)
        print(f"💾 Mensagem salva no MongoDB: {result.inserted_id}")
        
        # Prepara resposta
        response = MessageResponse(
            id=str(result.inserted_id),
            author=doc["author"],
            text=doc["text"],
            timestamp=int(doc["createdAt"].timestamp() * 1000),
            status=doc["status"],
            type=doc["type"]
        ).model_dump()
        
        # Broadcast para todos os clientes conectados
        await sio.emit("chat:new-message", response)
        print(f"📤 Broadcast enviado para todos os clientes")
        
    except Exception as e:
        print(f"❌ Erro ao processar mensagem: {e}")
        await sio.emit("error", {"message": str(e)}, room=sid)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(socket_app, host="0.0.0.0", port=3000, log_level="info")

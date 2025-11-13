import socketio
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from database import messages_collection
from models import MessageCreate, MessageResponse
from bson import ObjectId
from typing import Optional
from pydantic import BaseModel
from storage import validate_upload, new_object_key, presign_put, presign_get, S3_BUCKET

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

# Importa e registra rotas de autenticação (se existir o arquivo users.py)
try:
    from users import router as auth_router
    app.include_router(auth_router)
    print("✅ Rotas de autenticação carregadas")
except ImportError:
    print("⚠️  Arquivo users.py não encontrado - autenticação não disponível")

# Wrap com Socket.IO
socket_app = socketio.ASGIApp(sio, app)

# Armazena sessões ativas (sid -> user_id)
active_sessions = {}

@app.get("/")
async def health_check():
    return {"status": "ok", "message": "Chat API running with Python"}


@app.get("/messages")
async def get_messages(
    before: Optional[int] = None,
    limit: int = Query(default=30, le=100)
):
    """
    Retorna histórico de mensagens com paginação.
    
    - before: timestamp em milissegundos para buscar mensagens anteriores(retorna mensagens anteriores a essa data)
    - limit: número máximo de mensagens a retornar (padrão 30, máximo 100)
    """
    query = {}
    # se 'before' foi informado, filtra mensagens anteriores a essa data
    if before:
        before_dt = datetime.fromtimestamp(before / 1000)
        query["createdAt"] = {"$lt": before_dt}
    
    cursor = messages_collection.find(query).sort("createdAt", -1).limit(limit)
    docs = await cursor.to_list(length=limit)
    
    # Transforma documentos para o formato esperado pelo frontend
    messages = []
    for doc in reversed(docs):  # Inverte para ordem crescente
        msg_dict = {
            "id": str(doc["_id"]),
            "author": doc["author"],
            "text": doc["text"],
            "timestamp": int(doc["createdAt"].timestamp() * 1000),
            "status": doc.get("status", "sent"),
            "type": doc.get("type", "text")
        }
        
        # Adiciona attachment se existir
        if "attachment" in doc:
            msg_dict["attachment"] = doc["attachment"]
            # Gera URL assinada para acesso ao arquivo
            msg_dict["url"] = presign_get(doc["attachment"]["key"])
        
        messages.append(msg_dict)
    
    return {
        "messages": messages,
        "hasMore": len(docs) == limit  # Indica se há mais mensagens para paginação
    }


@sio.event
async def connect(sid, environ, auth):
    """Autentica cliente via token JWT antes de permitir conexão"""
    print(f"🔌 Tentativa de conexão: {sid}")
    
    # Cliente envia { auth: { token } }
    token = (auth or {}).get("token")
    if not token:
        print(f"❌ Conexão rejeitada: sem token - {sid}")
        return False
    
    try:
        # Importa decode_token apenas se necessário
        from auth import decode_token
        payload = decode_token(token)
        
        user_id = payload["sub"]
        environ["user_id"] = user_id
        active_sessions[sid] = user_id # registra sessão ativa
        
        
        # Armazena userId no ambiente do socket
        print(f"✅ Socket autenticado: {payload['sub']} (sid: {sid})")
        return True
        
    except Exception as e:
        print(f"❌ Token inválido: {e} - {sid}")
        return False


@sio.event
async def disconnect(sid):
    print(f"🔌 Cliente desconectado: {sid}")
    # Remove da lista de sessões ativas
    if sid in active_sessions:
        del active_sessions[sid]

# Evento: chat:typing Usuário está digitando
@sio.on("chat:typing")
async def handle_typing(sid, data):
    """Recebe evento de digitação e broadcast para outros clientes"""
    try:
        # Pega o user_id do ambiente (se disponível)
        environ = sio.get_environ(sid)
        user_id = environ.get("user_id", "anonymous")
        
        # Prepara resposta
        await sio.emit("chat:typing", {
            "userId": user_id,
            "author": data.get("author"),
            "chatId": data.get("chatId"),
            "isTyping": data.get("isTyping", False)
        }, skip_sid=sid)

        print(f"⌨️  Typing event: {user_id} - {data.get('isTyping')}")
        
    except Exception as e:
        print(f"❌ Erro chat:typing: {e}")
        
        
@sio.on("chat:send")
async def handle_chat_send(sid, data):
    """Recebe mensagem do cliente, salva no MongoDB e broadcast para todos"""
    try:
        print(f"📨 Mensagem recebida de {sid}: {data}")
        
        # Pega o user_id do ambiente (se disponível)
        environ = sio.get_environ(sid)
        user_id = environ.get("user_id", "anonymous")
        
        # captura tempId do cliente
        
        temp_id = data.get("tempId")
        
        # Validação com Pydantic
        message_create = MessageCreate(**data)
        
        # Cria documento para MongoDB
        doc = {
            "author": message_create.author,
            "text": message_create.text,
            "status": message_create.status,
            "type": message_create.type,
            "userId": user_id,  # Adiciona ID do usuário autenticado
            "createdAt": datetime.utcnow()
        }
        
        # Insere no MongoDB
        result = await messages_collection.insert_one(doc)
        message_id = str(result.inserted_id)
        print(f"💾 Mensagem salva no MongoDB: {message_id} (user: {user_id})")
        
        # Prepara resposta
        response = {
            "id": message_id,
            "author": doc["author"],
            "text": doc["text"],
            "timestamp": int(doc["createdAt"].timestamp() * 1000),
            "status": doc["status"],
            "type": doc["type"]
        }
        
        # Adiciona attachment se existir
        if "attachment" in doc:
            response["attachment"] = doc["attachment"]
            response["url"] = presign_get(doc["attachment"]["key"])
        
        # 1. envia ACK para o rementente(optmistic UI)
        await sio.emit("chat:ack", {"tempId": temp_id, "id": message_id, "status": "sent", "timestamp": response["timestamp"]}, room=sid)
        print(f"📤 ACK enviado para {sid} (tempId: {temp_id})")
        
        # 2. envia broadcast para todos os clientes
        await sio.emit("chat:new-message", response, skip_sid=sid)
        
        # 3. Emite 'delivered' para todos
        await sio.emit("chat:delivered", {"id": message_id})
        print(f"📬 Evento 'delivered' emitido para mensagem {message_id}")
        
    except Exception as e:
        print(f"❌ Erro ao processar mensagem: {e}")
        await sio.emit("error", {
            "message": str(e),
            "tempId": data.get("tempId")
        }, room=sid)


# 🆕 EVENTO: chat:read (marcar mensagens como lidas)
@sio.on("chat:read")
async def handle_chat_read(sid, data):
    """
    Marca mensagens como lidas
    
    data = { ids: [string] }
    """
    try:
        message_ids = data.get("ids", [])
        
        if not message_ids:
            return
        
        # Atualiza status no banco
        object_ids = [ObjectId(id) for id in message_ids if ObjectId.is_valid(id)]
        result = await messages_collection.update_many(
            {"_id": {"$in": object_ids}},
            {"$set": {"status": "read"}}
        )
        
        # Broadcast para todos
        await sio.emit("chat:read", {"ids": message_ids})
        print(f"👁️ Mensagens marcadas como lidas: {result.modified_count}")
        
    except Exception as e:
        print(f"❌ Erro em chat:read: {e}")


class UploadRequest(BaseModel):
    filename: str
    mimetype: str
    size: int  # bytes

class UploadGrant(BaseModel):
    key: str
    putUrl: str

@app.post("/uploads/grant", response_model=UploadGrant)
async def grant_upload(body: UploadRequest):
    size_mb = max(1, body.size // (1024*1024))
    try:
        validate_upload(body.filename, body.mimetype, size_mb)
    except ValueError as e:
        raise HTTPException(400, str(e))
    key = new_object_key(body.filename)
    url = presign_put(key, body.mimetype)
    return {"key": key, "putUrl": url}

class ConfirmUploadIn(BaseModel):
    key: str
    filename: str
    mimetype: str
    author: str

@app.post("/uploads/confirm")
async def confirm_upload(body: ConfirmUploadIn):
    # (Opcional) antivirus stub aqui
    from datetime import datetime, timezone
    doc = {
        "author": body.author,
        "text": body.filename,
        "type": "file" if not body.mimetype.startswith("image/") else "image",
        "status": "sent",
        "createdAt": datetime.now(timezone.utc),
        "attachment": {
            "bucket": S3_BUCKET,
            "key": body.key,
            "filename": body.filename,
            "mimetype": body.mimetype
        }
    }
    result = await messages_collection.insert_one(doc)
    msg = {
        "id": str(result.inserted_id),
        "author": doc["author"],
        "text": doc["text"],
        "type": doc["type"],
        "status": doc["status"],
        "timestamp": int(doc["createdAt"].timestamp()*1000),
        "attachment": doc["attachment"],
        "url": presign_get(body.key)  # URL GET assinada p/ exibição imediata
    }
    await sio.emit("chat:new-message", msg)
    return {"ok": True, "message": msg}
import socketio
from fastapi import FastAPI, Query, HTTPException, APIRouter, Request
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timezone
from database import messages_collection, db
from models import MessageCreate, MessageResponse
from bson import ObjectId
from typing import Optional
from pydantic import BaseModel, Field
from storage import validate_upload, new_object_key, presign_put, presign_get, S3_BUCKET
from bots.core import is_command, run_command
from bots.automations import start_scheduler, load_and_schedule_all, handle_keyword_if_matches
from bots.ai_bot import ask_chatgpt, is_ai_question, clean_bot_mention, clear_conversation, get_conversation_count
from transcription import transcribe_from_s3

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

# Router de automações
automations_router = APIRouter(prefix="/automations", tags=["automations"])
automations_col = db.automations


class AutomationIn(BaseModel):
    """Schema para criação de automações"""
    name: str
    type: str  # "cron" | "keyword"
    spec: dict  # {"cron": "0 9 * * *"} ou {"keyword": "oi"}
    payload: dict  # {"text": "Bom dia!"}
    enabled: bool = True


@automations_router.post("")
async def create_automation(body: AutomationIn):
    """Cria uma nova automação"""
    doc = body.model_dump()
    doc["createdAt"] = datetime.now(timezone.utc)
    result = await automations_col.insert_one(doc)
    
    # Reprograma cron jobs
    await load_and_schedule_all(sio.emit)
    
    return {"id": str(result.inserted_id), "message": "Automação criada com sucesso"}


@automations_router.get("")
async def list_automations():
    """Lista todas as automações"""
    automations = []
    async for automation in automations_col.find():
        automation["id"] = str(automation["_id"])
        del automation["_id"]
        automations.append(automation)
    return automations


@automations_router.patch("/{id}/toggle")
async def toggle_automation(id: str, enabled: bool = Query(...)):
    """Ativa ou desativa uma automação"""
    if not ObjectId.is_valid(id):
        raise HTTPException(400, "ID inválido")
    
    _id = ObjectId(id)
    result = await automations_col.update_one(
        {"_id": _id},
        {"$set": {"enabled": enabled}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(404, "Automação não encontrada")
    
    # Reprograma cron jobs
    await load_and_schedule_all(sio.emit)
    
    return {"ok": True, "message": f"Automação {'ativada' if enabled else 'desativada'}"}


@automations_router.delete("/{id}")
async def delete_automation(id: str):
    """Remove uma automação"""
    if not ObjectId.is_valid(id):
        raise HTTPException(400, "ID inválido")
    
    _id = ObjectId(id)
    result = await automations_col.delete_one({"_id": _id})
    
    if result.deleted_count == 0:
        raise HTTPException(404, "Automação não encontrada")
    
    # Reprograma cron jobs
    await load_and_schedule_all(sio.emit)
    
    return {"ok": True, "message": "Automação removida com sucesso"}


# Registra router de automações
app.include_router(automations_router)

# Registra router omnichannel
try:
    from routers.omni import router as omni_router
    app.include_router(omni_router)
    print("✅ Router omnichannel carregado")
except ImportError as e:
    print(f"⚠️  Router omnichannel não encontrado: {e}")

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


# ============================================================================
# WEBHOOKS - Recebimento de mensagens externas
# ============================================================================

async def _persist_and_broadcast(author: str, text: str):
    """
    Helper para persistir mensagem no MongoDB e emitir via Socket.IO.
    Evita duplicação de código entre diferentes webhooks.
    """
    # Cria documento
    doc = {
        "_id": ObjectId(),
        "author": author,
        "text": text,
        "type": "text",
        "status": "delivered",
        "createdAt": datetime.now()
    }
    
    # Persiste no MongoDB
    await messages_collection.insert_one(doc)
    
    # Emite via Socket.IO para todos os clientes conectados
    await sio.emit("chat:new-message", {
        "id": str(doc["_id"]),
        "author": author,
        "text": text,
        "type": "text",
        "status": "delivered",
        "timestamp": int(doc["createdAt"].timestamp() * 1000)
    })


@app.get("/webhooks/meta")
async def webhook_meta_verify(
    mode: str = Query(..., alias="hub.mode"),
    challenge: str = Query(..., alias="hub.challenge"),
    verify_token: str = Query(..., alias="hub.verify_token")
):
    """
    Webhook GET para verificação do Meta (WhatsApp Cloud, Instagram, Facebook).
    Usado durante configuração do webhook no Meta Developer Console.
    """
    import os
    
    META_VERIFY_TOKEN = os.getenv("META_VERIFY_TOKEN", "")
    
    if mode == "subscribe" and verify_token == META_VERIFY_TOKEN:
        print("✅ Webhook Meta verificado com sucesso")
        # Meta espera o challenge como resposta (pode ser int ou str)
        return int(challenge) if challenge.isdigit() else challenge
    
    print(f"❌ Webhook Meta: verificação falhou (mode={mode}, token válido={verify_token == META_VERIFY_TOKEN})")
    raise HTTPException(status_code=403, detail="Verification failed")


@app.post("/webhooks/meta")
async def webhook_meta_receive(request: Request):
    """
    Webhook POST para receber mensagens do Meta (WhatsApp Cloud, Instagram, Facebook).
    Verifica assinatura HMAC antes de processar.
    """
    # Obtém corpo bruto para verificação de assinatura
    raw_body = await request.body()
    signature_header = request.headers.get("X-Hub-Signature-256")
    
    # Verifica assinatura HMAC
    try:
        from meta import verify_meta_signature
        if not verify_meta_signature(raw_body, signature_header):
            raise HTTPException(status_code=403, detail="Invalid signature")
    except ImportError:
        print("⚠️  meta.py não encontrado, pulando verificação de assinatura")
    
    # Parse JSON
    try:
        data = await request.json()
    except Exception as e:
        print(f"❌ Erro ao parsear JSON do webhook Meta: {e}")
        raise HTTPException(status_code=400, detail="Invalid JSON")
    
    # Processa entradas (pode haver múltiplas)
    for entry in data.get("entry", []):
        # Messenger usa entry.messaging[]
        for msg in entry.get("messaging", []):
            sender_id = msg.get("sender", {}).get("id")
            text_content = msg.get("message", {}).get("text")
            
            if sender_id and text_content:
                author = f"FB:{sender_id}"
                await _persist_and_broadcast(author, text_content)
                print(f"📩 Mensagem recebida via Facebook Messenger: {author}")
        
        # Instagram e WhatsApp usam entry.changes[].value.messages[]
        for change in entry.get("changes", []):
            value = change.get("value", {})
            for msg in value.get("messages", []):
                sender = msg.get("from")  # Número ou ID
                text_content = msg.get("text", {}).get("body")
                
                if sender and text_content:
                    # Detecta plataforma pelo tipo de mensagem ou contexto
                    # Por simplicidade, usa prefixo genérico (pode melhorar detectando metadata)
                    platform = change.get("field", "unknown")
                    if platform == "messages":  # WhatsApp ou Instagram
                        # Tenta detectar se é WhatsApp (número) ou Instagram (ID alfanumérico)
                        if sender.isdigit():
                            author = f"WA:{sender}"
                            print(f"📩 Mensagem recebida via WhatsApp Cloud: {author}")
                        else:
                            author = f"IG:{sender}"
                            print(f"📩 Mensagem recebida via Instagram: {author}")
                    else:
                        author = f"{platform}:{sender}"
                        print(f"📩 Mensagem recebida via Meta ({platform}): {author}")
                    
                    await _persist_and_broadcast(author, text_content)
    
    return {"status": "ok"}


@app.post("/webhooks/wppconnect")
async def webhook_wppconnect_receive(request: Request):
    """
    Webhook POST para receber mensagens do WPPConnect (WhatsApp device-based).
    Verifica assinatura HMAC customizada antes de processar.
    """
    import os
    import hmac
    import hashlib
    
    # Obtém corpo bruto e assinatura
    raw_body = await request.body()
    signature_header = request.headers.get("x-webhook-signature")
    
    # Verifica assinatura HMAC (se WPP_WEBHOOK_SECRET estiver configurado)
    WPP_WEBHOOK_SECRET = os.getenv("WPP_WEBHOOK_SECRET", "")
    if WPP_WEBHOOK_SECRET and signature_header:
        expected_signature = hmac.new(
            WPP_WEBHOOK_SECRET.encode(),
            raw_body,
            hashlib.sha256
        ).hexdigest()
        
        if not hmac.compare_digest(signature_header, expected_signature):
            print("❌ Webhook WPPConnect: assinatura inválida")
            raise HTTPException(status_code=403, detail="Invalid signature")
    
    # Parse JSON
    try:
        data = await request.json()
    except Exception as e:
        print(f"❌ Erro ao parsear JSON do webhook WPPConnect: {e}")
        raise HTTPException(status_code=400, detail="Invalid JSON")
    
    # WPPConnect envia: { event: "message", data: { from, fromName, contentText, body, ... } }
    if data.get("event") == "message":
        msg_data = data.get("data", {})
        sender_name = msg_data.get("fromName") or msg_data.get("from", "unknown")
        text_content = msg_data.get("contentText") or msg_data.get("body", "")
        
        if text_content:
            author = f"WA(dev):{sender_name}"
            await _persist_and_broadcast(author, text_content)
            print(f"📩 Mensagem recebida via WPPConnect: {author}")
    
    return {"status": "ok"}


# ============================================================================
# SOCKET.IO - Eventos de tempo real
# ============================================================================

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
    """Recebe mensagem do cliente, processa comandos/automações, salva no MongoDB e broadcast para todos"""
    from datetime import timezone
    try:
        print(f"📨 Mensagem recebida de {sid}: {data}")
        
        # Pega o user_id do ambiente (se disponível)
        environ = sio.get_environ(sid)
        user_id = environ.get("user_id", "anonymous")
        
        # Captura tempId do cliente
        temp_id = data.get("tempId")
        
        # Captura texto e autor
        author = data.get("author", "")
        text = data.get("text", "").strip()
        
        # 1) COMANDOS (ex: /help, /echo, /time, /ai, /limpar)
        if is_command(text):
            from bots.automations import publish_message
            
            # Comando /limpar - Limpa histórico de conversa
            if text.lower() in ["/limpar", "/clear"]:
                clear_conversation(user_id)
                count = get_conversation_count(user_id)
                await publish_message(
                    sio.emit, 
                    author="Bot 🧹", 
                    text=f"✅ Histórico de conversa limpo! ({count} mensagens removidas)\nPodemos começar uma nova conversa do zero."
                )
                return
            
            # Comando /ai - Pergunta ao ChatGPT com contexto
            if text.lower().startswith("/ai "):
                question = text[4:].strip()
                if question:
                    import asyncio
                    
                    # Envia indicador de digitação
                    await sio.emit("chat:typing", {
                        "author": "Bot",
                        "isTyping": True
                    })
                    
                    # Simula "pensamento" (0.5-1.5 segundos)
                    await asyncio.sleep(0.8)
                    
                    # Processa com ChatGPT (mantém contexto por user_id, passa nome do autor)
                    ai_response = await ask_chatgpt(question, user_id, author)
                    
                    # Simula digitação realista (baseado no tamanho da resposta)
                    # ~50 caracteres por segundo (digitação rápida mas humana)
                    typing_time = len(ai_response) / 50
                    typing_time = max(1.0, min(typing_time, 4.0))  # Entre 1 e 4 segundos
                    await asyncio.sleep(typing_time)
                    
                    # Remove indicador de digitação
                    await sio.emit("chat:typing", {
                        "author": "Bot",
                        "isTyping": False
                    })
                    
                    # Publica resposta
                    await publish_message(sio.emit, author="Bot 💬", text=ai_response)
                else:
                    await publish_message(sio.emit, author="Bot", text="💭 Use: /ai <sua pergunta>")
                return
            
            # Outros comandos síncronos
            reply = run_command(text)
            if reply:
                await publish_message(sio.emit, author="Bot", text=reply)
            return
        
        # 2) PERSISTIR MENSAGEM NORMAL
        # Validação com Pydantic
        message_create = MessageCreate(**data)
        
        # Cria documento para MongoDB
        now = datetime.now(timezone.utc)
        doc = {
            "author": message_create.author,
            "text": message_create.text,
            "status": message_create.status,
            "type": message_create.type,
            "userId": user_id,  # Adiciona ID do usuário autenticado
            "createdAt": now
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
        
        # 1. Envia ACK para o remetente (optimistic UI)
        await sio.emit("chat:ack", {
            "tempId": temp_id,
            "id": message_id,
            "status": "sent",
            "timestamp": response["timestamp"]
        }, room=sid)
        print(f"📤 ACK enviado para {sid} (tempId: {temp_id})")
        
        # 2. Envia broadcast para todos os clientes
        await sio.emit("chat:new-message", response, skip_sid=sid)
        
        # 3. Emite 'delivered' para todos
        await sio.emit("chat:delivered", {"id": message_id})
        print(f"📬 Evento 'delivered' emitido para mensagem {message_id}")
        
        # 4) TRANSCRIÇÃO DE ÁUDIO PARA BOT
        # Se for áudio, sempre transcreve e verifica se deve acionar o bot
        transcription = None
        print(f"🔍 Verificando áudio: type={message_create.type}, has_attachment={'attachment' in doc}")
        if message_create.type == "audio" and ("attachment" in doc):
            from bots.automations import publish_message
            print(f"🎤 ÁUDIO DETECTADO! Transcrevendo de S3: {doc['attachment']['key']}")
            
            # Transcreve o áudio automaticamente
            transcription = await transcribe_from_s3(
                doc["attachment"]["key"],
                doc["attachment"]["bucket"]
            )
            print(f"📝 Transcrição: {transcription[:100] if transcription else 'NONE'}...")
            
            # Se a transcrição teve sucesso, verifica se menciona o bot
            if transcription and not transcription.startswith("["):  # Não é erro
                # Verifica se a transcrição menciona o bot ou faz pergunta de IA
                if is_ai_question(transcription):
                    # Avisa que está processando
                    await sio.emit("chat:typing", {
                        "author": "Bot",
                        "isTyping": True
                    })
                    
                    # Simula pensamento
                    await asyncio.sleep(0.8)
                    
                    # Remove menção @bot da transcrição antes de processar
                    clean_text = clean_bot_mention(transcription)
                    
                    # Processa com ChatGPT
                    ai_response = await ask_chatgpt(clean_text, user_id, author)
                    
                    # Simula digitação
                    typing_time = len(ai_response) / 50
                    typing_time = max(1.5, min(typing_time, 5.0))
                    await asyncio.sleep(typing_time)
                    
                    # Remove indicador de digitação
                    await sio.emit("chat:typing", {
                        "author": "Bot",
                        "isTyping": False
                    })
                    
                    # Responde com a transcrição e a resposta
                    response_text = f'🎤 _Áudio transcrito:_ "{transcription}"\n\n{ai_response}'
                    await publish_message(sio.emit, author="Bot 💬", text=response_text)
                    
                    # Não continua para outras automações
                    return
        
        # 5) KEYWORD AUTOMATIONS (ex: "oi" -> resposta automática)
        await handle_keyword_if_matches(sio.emit, text)
        
        # 6) BOT DE IA (ex: "@bot qual a capital do Brasil?")
        if is_ai_question(text):
            import asyncio
            from bots.automations import publish_message
            
            # Limpa menção ao bot
            clean_text = clean_bot_mention(text)
            
            # Envia indicador de digitação
            await sio.emit("chat:typing", {
                "author": "Bot",
                "isTyping": True
            })
            
            # Simula "pensamento" (0.5-1.5 segundos)
            await asyncio.sleep(1.0)
            
            # Processa com ChatGPT (mantém contexto por user_id, passa nome do autor)
            ai_response = await ask_chatgpt(clean_text, user_id, author)
            
            # Simula digitação realista (baseado no tamanho da resposta)
            # ~50 caracteres por segundo (digitação rápida mas humana)
            typing_time = len(ai_response) / 50
            typing_time = max(1.5, min(typing_time, 5.0))  # Entre 1.5 e 5 segundos
            await asyncio.sleep(typing_time)
            
            # Remove indicador de digitação
            await sio.emit("chat:typing", {
                "author": "Bot",
                "isTyping": False
            })
            
            # Publica resposta
            await publish_message(sio.emit, author="Bot 💬", text=ai_response)
        
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
    
    # Detecta tipo de arquivo
    file_type = "file"
    if body.mimetype.startswith("image/"):
        file_type = "image"
    elif body.mimetype.startswith("audio/"):
        file_type = "audio"
    
    doc = {
        "author": body.author,
        "text": body.filename,
        "type": file_type,
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
    
    # TRANSCRIÇÃO DE ÁUDIO (se aplicável)
    if file_type == "audio":
        from bots.automations import publish_message
        import asyncio
        
        print(f"🎤 ÁUDIO DETECTADO no confirm_upload! Transcrevendo: {body.key}")
        
        # Transcreve o áudio automaticamente
        transcription = await transcribe_from_s3(body.key, S3_BUCKET)
        print(f"📝 Transcrição: {transcription[:100] if transcription else 'NONE'}...")
        
        # Se a transcrição teve sucesso, verifica se menciona o bot
        if transcription and not transcription.startswith("["):  # Não é erro
            # Verifica se a transcrição menciona o bot ou faz pergunta de IA
            if is_ai_question(transcription):
                print(f"🤖 Pergunta de IA detectada na transcrição!")
                
                # Avisa que está processando
                await sio.emit("chat:typing", {
                    "author": "Bot",
                    "isTyping": True
                })
                
                # Simula pensamento
                await asyncio.sleep(0.8)
                
                # Remove menção @bot da transcrição antes de processar
                clean_text = clean_bot_mention(transcription)
                
                # Processa com ChatGPT (usa author como user_id temporário)
                ai_response = await ask_chatgpt(clean_text, body.author, body.author)
                
                # Simula digitação
                typing_time = len(ai_response) / 50
                typing_time = max(1.5, min(typing_time, 5.0))
                await asyncio.sleep(typing_time)
                
                # Remove indicador de digitação
                await sio.emit("chat:typing", {
                    "author": "Bot",
                    "isTyping": False
                })
                
                # Responde com a transcrição e a resposta
                response_text = f'🎤 _Áudio transcrito:_ "{transcription}"\n\n{ai_response}'
                await publish_message(sio.emit, author="Bot 💬", text=response_text)
    
    return {"ok": True, "message": msg}



@app.on_event("startup")
async def _on_startup():
    """Inicializa scheduler e carrega automações na inicialização do servidor"""
    start_scheduler()
    await load_and_schedule_all(sio.emit)
    print("✅ Scheduler iniciado e automações carregadas")

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
from bots.agents import (
    detect_agent_mention, 
    get_agent, 
    clean_agent_mention, 
    handle_agent_command,
    list_all_agents
)
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

# 🤖 Sessões ativas com o Guru (user_id -> bool)
guru_sessions = {}

# Importa e registra rotas de autenticação (se existir o arquivo users.py)
try:
    from users import router as auth_router
    app.include_router(auth_router)
    print("✅ Rotas de autenticação carregadas")
except ImportError:
    print("⚠️  Arquivo users.py não encontrado - autenticação não disponível")

# Importa e registra rotas de contatos
try:
    from contacts import router as contacts_router
    app.include_router(contacts_router)
    print("✅ Rotas de contatos carregadas")
except ImportError:
    print("⚠️  Arquivo contacts.py não encontrado - contatos não disponíveis")

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

# =====================================================
# ROUTER: BOTS PERSONALIZADOS
# =====================================================

custom_bots_router = APIRouter(prefix="/custom-bots", tags=["custom-bots"])

class CustomBotCreate(BaseModel):
    """Schema para criação de bot personalizado"""
    name: str = Field(..., min_length=3, max_length=50)
    emoji: str = Field(default="🤖", max_length=4)
    prompt: str = Field(..., min_length=50)
    specialties: list[str] = Field(default_factory=list, max_items=5)
    openaiApiKey: str = Field(..., min_length=20, alias="openaiApiKey")
    openaiAccount: Optional[str] = Field(default=None, alias="openaiAccount")

@custom_bots_router.post("")
async def create_custom_bot(body: CustomBotCreate, request: Request):
    """Cria um bot personalizado"""
    from bots.agents import create_custom_agent
    from auth import get_user_id_from_token
    
    # Extrai user_id do token (se autenticado)
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    user_id = get_user_id_from_token(token) if token else "anonymous"
    
    # Cria agente personalizado
    agent = create_custom_agent(
        user_id=user_id,
        name=body.name,
        emoji=body.emoji,
        system_prompt=body.prompt,
        specialties=body.specialties,
        openai_api_key=body.openaiApiKey,
        openai_account=body.openaiAccount
    )
    
    return {
        "success": True,
        "bot": {
            "name": agent.name,
            "emoji": agent.emoji,
            "key": agent.name.lower().replace(' ', ''),
            "specialties": agent.specialties,
            "createdAt": datetime.now(timezone.utc).isoformat()
        }
    }

@custom_bots_router.get("")
async def list_custom_bots(request: Request):
    """Lista bots personalizados do usuário"""
    from bots.agents import list_custom_agents
    from auth import get_user_id_from_token
    
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    user_id = get_user_id_from_token(token) if token else "anonymous"
    
    agents = list_custom_agents(user_id)
    
    return {
        "bots": [
            {
                "name": agent.name,
                "emoji": agent.emoji,
                "key": agent.name.lower().replace(' ', ''),
                "specialties": agent.specialties
            }
            for agent in agents
        ]
    }

@custom_bots_router.delete("/{bot_key}")
async def delete_custom_bot(bot_key: str, request: Request):
    """Deleta um bot personalizado"""
    from bots.agents import delete_custom_agent
    from auth import get_user_id_from_token
    
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    user_id = get_user_id_from_token(token) if token else "anonymous"
    
    success = delete_custom_agent(user_id, bot_key)
    
    if not success:
        raise HTTPException(status_code=404, detail="Bot não encontrado")
    
    return {"success": True, "message": "Bot deletado com sucesso"}

app.include_router(custom_bots_router)

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
# Armazena mapeamento reverso (user_id -> sid) para entrega direcionada
user_sessions = {}

@app.get("/")
async def health_check():
    return {"status": "ok", "message": "Chat API running with Python"}


@app.get("/messages")
async def get_messages(
    before: Optional[int] = None,
    limit: int = Query(default=30, le=100),
    contact_id: Optional[str] = None  # 🆕 Filtra por contato
):
    """
    Retorna histórico de mensagens com paginação.
    
    - before: timestamp em milissegundos para buscar mensagens anteriores(retorna mensagens anteriores a essa data)
    - limit: número máximo de mensagens a retornar (padrão 30, máximo 100)
    - contact_id: (opcional) filtra mensagens de uma conversa específica
    """
    query = {}
    
    # 🆕 Filtra por contato se fornecido
    if contact_id:
        query["contactId"] = contact_id
    
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
            
            if sender_id:
                print(f"🎯 PSID CAPTURADO: {sender_id}")
                print(f"   Use este ID no Postman como 'recipient'")
                
                if text_content:
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
        
        # Verifica se usuário existe no banco
        user = await db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            print(f"❌ Usuário não encontrado: {user_id} - {sid}")
            return False
        
        # Armazena dados no ambiente do socket
        environ["user_id"] = user_id
        environ["user_name"] = user.get("name", "Usuário")
        environ["user_email"] = user.get("email", "")
        
        # Registra sessão ativa
        active_sessions[sid] = user_id
        user_sessions[user_id] = sid  # 🆕 Mapeamento reverso para entrega direcionada
        
        # 🆕 Notifica outros usuários que este está online
        await sio.emit('user:online', {'userId': user_id}, skip_sid=sid)
        
        print(f"✅ Socket autenticado: {user.get('name')} ({user_id}) - sid: {sid}")
        print(f"👥 Usuários online: {len(user_sessions)}")
        return True
        
    except Exception as e:
        print(f"❌ Token inválido: {e} - {sid}")
        return False


@sio.event
async def disconnect(sid):
    print(f"🔌 Cliente desconectado: {sid}")
    # Remove da lista de sessões ativas
    if sid in active_sessions:
        user_id = active_sessions[sid]
        del active_sessions[sid]
        
        # Remove do mapeamento reverso
        if user_id in user_sessions:
            del user_sessions[user_id]
        
        # 🆕 Notifica outros usuários que este está offline
        await sio.emit('user:offline', {'userId': user_id})
        
        print(f"👤 Usuário {user_id} desconectado")
        print(f"👥 Usuários online: {len(user_sessions)}")

# Evento: chat:typing Usuário está digitando
@sio.on("chat:typing")
async def handle_typing(sid, data):
    """Recebe evento de digitação e envia apenas para o contato específico"""
    try:
        # Pega o user_id do ambiente
        environ = sio.get_environ(sid)
        user_id = environ.get("user_id", "anonymous")
        
        # ID do contato (destinatário)
        contact_id = data.get("contactId")
        
        if contact_id:
            # Busca sessão do contato
            contact_sid = user_sessions.get(contact_id)
            
            if contact_sid:
                # Envia apenas para o contato específico
                await sio.emit("chat:typing", {
                    "userId": user_id,
                    "author": data.get("author"),
                    "isTyping": data.get("isTyping", False)
                }, room=contact_sid)
                
                print(f"⌨️  Typing event: {user_id} → {contact_id} - {data.get('isTyping')}")
            else:
                print(f"📪 Contato {contact_id} offline - typing ignorado")
        else:
            # Sem contactId - ignora (evita broadcast)
            print(f"⚠️  Typing sem contactId - ignorado")
        
    except Exception as e:
        print(f"❌ Erro chat:typing: {e}")


@sio.on("chat:mark-read")
async def handle_mark_read(sid, data):
    """Marca mensagens como lidas e notifica outros clientes"""
    try:
        environ = sio.get_environ(sid)
        user_id = environ.get("user_id", "anonymous")
        
        message_ids = data.get("ids", [])
        if not message_ids:
            return
        
        # Emite evento de leitura para todos os clientes (exceto quem marcou)
        await sio.emit("chat:read", {
            "ids": message_ids,
            "readBy": user_id
        }, skip_sid=sid)
        
        print(f"👁️ Mensagens marcadas como lidas por {user_id}: {len(message_ids)} msgs")
        
    except Exception as e:
        print(f"❌ Erro chat:mark-read: {e}")
        
        
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
            from bots.ai_bot import set_user_mode, get_user_mode, generate_conversation_summary
            
            # Comando /ajuda - Lista comandos disponíveis
            if text.lower() in ["/ajuda", "/help"]:
                help_text = """🧠 **Comandos do Guru:**

📝 **Conversa:**
• `@guru` - Iniciar sessão (não precisa mencionar depois)
• `tchau` ou `sair` - Encerrar sessão
• `/ai <pergunta>` - Pergunta direta

🎨 **Personalização:**
• `/modo <casual|profissional|tecnico>` - Mudar estilo
• `/contexto` - Ver histórico de mensagens

🛠️ **Utilitários:**
• `/limpar` - Limpar histórico
• `/resumo` - Resumo da conversa
• `/ajuda` - Esta mensagem

🤖 **Agentes Especializados:**
• `/agentes` - Ver todos os agentes disponíveis
• `@advogado`, `@vendedor`, `@medico`, `@psicologo` - Falar com especialistas"""
                await publish_message(sio.emit, author="Guru 📚", text=help_text, user_id=user_id, target_sid=sid)
                return
            
            # Comando /agentes - Lista todos os agentes especializados
            if text.lower() in ["/agentes", "/agents"]:
                agents_list = list_all_agents()
                await publish_message(sio.emit, author="Sistema 🤖", text=agents_list, user_id=user_id, target_sid=sid)
                return
            
            # Comando /contexto - Mostra quantidade de mensagens no histórico
            if text.lower() == "/contexto":
                count = get_conversation_count(user_id)
                mode = get_user_mode(user_id)
                mode_emoji = {"casual": "😎", "profissional": "💼", "tecnico": "🔧"}
                context_text = f"""📊 **Status da Conversa:**

💬 Mensagens no histórico: {count}/10
🎭 Modo atual: {mode.title()} {mode_emoji.get(mode, '')}
🧠 Memória: {'Ativa' if count > 0 else 'Vazia'}

_Quanto mais conversamos, melhor eu te entendo!_ ✨"""
                await publish_message(sio.emit, author="Guru 📊", text=context_text, user_id=user_id, target_sid=sid)
                return
            
            # Comando /modo - Altera modo de personalidade
            if text.lower().startswith("/modo "):
                new_mode = text[6:].strip().lower()
                result = set_user_mode(user_id, new_mode)
                await publish_message(sio.emit, author="Guru 🎭", text=result, user_id=user_id, target_sid=sid)
                return
            
            # Comando /resumo - Gera resumo da conversa
            if text.lower() == "/resumo":
                summary = generate_conversation_summary(user_id)
                await publish_message(sio.emit, author="Guru 📝", text=summary, user_id=user_id, target_sid=sid)
                return
            
            # Comando /limpar - Limpa histórico de conversa
            if text.lower() in ["/limpar", "/clear"]:
                clear_conversation(user_id)
                count = get_conversation_count(user_id)
                await publish_message(
                    sio.emit, 
                    author="Guru 🧹", 
                    text=f"✅ Histórico de conversa limpo! ({count} mensagens removidas)\nPodemos começar uma nova conversa do zero.",
                    user_id=user_id,
                    target_sid=sid
                )
                return
            
            # Comando /ai - Pergunta ao ChatGPT com contexto
            if text.lower().startswith("/ai "):
                question = text[4:].strip()
                if question:
                    import asyncio
                    
                    # Envia indicador de digitação (direto para o usuário)
                    await sio.emit("chat:typing", {
                        "author": "Guru",
                        "isTyping": True
                    }, room=sid)
                    
                    # Simula "pensamento" (0.5-1.5 segundos)
                    await asyncio.sleep(0.8)
                    
                    # Processa com ChatGPT (mantém contexto por user_id, passa nome do autor)
                    ai_response = await ask_chatgpt(question, user_id, author)
                    
                    # Simula digitação realista (baseado no tamanho da resposta)
                    # ~50 caracteres por segundo (digitação rápida mas humana)
                    typing_time = len(ai_response) / 50
                    typing_time = max(1.0, min(typing_time, 4.0))  # Entre 1 e 4 segundos
                    await asyncio.sleep(typing_time)
                    
                    # Remove indicador de digitação (direto para o usuário)
                    await sio.emit("chat:typing", {
                        "author": "Guru",
                        "isTyping": False
                    }, room=sid)
                    
                    # Publica resposta
                    await publish_message(sio.emit, author="Guru 🧠", text=ai_response, user_id=user_id, target_sid=sid)
                else:
                    await publish_message(sio.emit, author="Guru", text="💭 Use: /ai <sua pergunta>", user_id=user_id, target_sid=sid)
                return
            
            # Outros comandos síncronos
            reply = run_command(text)
            if reply:
                await publish_message(sio.emit, author="Guru", text=reply, user_id=user_id, target_sid=sid)
            return
        
        # 🤖 SISTEMA DE AGENTES ESPECIALIZADOS
        agent_name = detect_agent_mention(text)
        if agent_name:
            agent = get_agent(agent_name, user_id)  # Passa user_id para buscar bots personalizados
            if agent:
                import asyncio
                from bots.automations import publish_message
                
                # Remove menção do agente
                clean_text = clean_agent_mention(text, agent_name)
                
                # Se é comando específico do agente
                if clean_text.startswith("/"):
                    response = await handle_agent_command(agent, clean_text, user_id, author)
                    await publish_message(
                        sio.emit,
                        author=agent.get_display_name(),
                        text=response,
                        user_id=user_id,
                        target_sid=sid
                    )
                    return
                
                # Se é pergunta para o agente
                if clean_text:
                    # Envia indicador de digitação
                    await sio.emit("chat:typing", {
                        "author": agent.name,
                        "isTyping": True
                    }, room=sid)
                    
                    # Tempo variável baseado na complexidade
                    question_length = len(clean_text)
                    if question_length > 100:
                        thinking_time = 1.5
                    elif question_length > 50:
                        thinking_time = 1.0
                    else:
                        thinking_time = 0.7
                    
                    await asyncio.sleep(thinking_time)
                    
                    # Processa pergunta com o agente
                    agent_response = await agent.ask(clean_text, user_id, author)
                    
                    # Simula digitação
                    typing_time = len(agent_response) / 60  # ~60 caracteres por segundo
                    typing_time = max(1.0, min(typing_time, 4.0))
                    await asyncio.sleep(typing_time)
                    
                    # Remove indicador
                    await sio.emit("chat:typing", {
                        "author": agent.name,
                        "isTyping": False
                    }, room=sid)
                    
                    # Publica resposta
                    await publish_message(
                        sio.emit,
                        author=agent.get_display_name(),
                        text=agent_response,
                        user_id=user_id,
                        target_sid=sid
                    )
                    return
                else:
                    # Apenas @agente sem pergunta - mostra apresentação
                    intro = f"👋 Olá! Sou {agent.get_display_name()}\n\n"
                    intro += f"**Minhas especialidades:**\n"
                    for specialty in agent.specialties:
                        intro += f"• {specialty}\n"
                    intro += f"\n💡 _Faça sua pergunta ou use @{agent_name} /ajuda para ver comandos_"
                    
                    await publish_message(
                        sio.emit,
                        author=agent.get_display_name(),
                        text=intro,
                        user_id=user_id,
                        target_sid=sid
                    )
                    return
        
        # 🧠 VERIFICA SE É INTERAÇÃO COM GURU (não salva essas mensagens)
        text_lower = text.lower().strip()
        in_guru_session = guru_sessions.get(user_id, False)
        is_guru_mention = text_lower.startswith("@guru")
        is_guru_exit = text_lower in ["tchau", "sair"]
        is_ai_query = is_ai_question(text)
        
        # Se for qualquer interação com Guru, pula todo o processamento de mensagem normal
        if in_guru_session or is_guru_mention or is_guru_exit or is_ai_query:
            print(f"🧠 Mensagem para Guru detectada - pulando persistência no banco")
            # Continua para processamento do Guru abaixo (não retorna aqui)
        else:
            # 2) PERSISTIR MENSAGEM NORMAL (apenas mensagens entre usuários)
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
                "contactId": message_create.contactId,  # 🆕 ID do contato (conversa individual)
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
                "type": doc["type"],
                "userId": user_id,  # 🆕 ID do remetente (quem enviou)
                "contactId": doc.get("contactId")  # 🆕 ID do destinatário (para quem foi enviado)
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
            print(f"📤 ACK enviado para {sid} (tempId: {temp_id} → {message_id})")
            
            # 2. Envia mensagem para o destinatário específico (se contactId fornecido)
            if message_create.contactId:
                contact_sid = user_sessions.get(message_create.contactId)
                if contact_sid:
                    # Destinatário está online - envia apenas para ele
                    await sio.emit("chat:new-message", response, room=contact_sid)
                    print(f"📨 Mensagem enviada para contato {message_create.contactId} (sid: {contact_sid})")
                else:
                    # Destinatário offline - mensagem ficará no banco para quando ele logar
                    print(f"📪 Contato {message_create.contactId} está offline - mensagem salva no banco")
            else:
                # Sem contactId - broadcast para todos (compatibilidade com sistema antigo)
                await sio.emit("chat:new-message", response, skip_sid=sid)
                print(f"📨 Mensagem broadcast para todos (exceto {sid})")
            
            print(f"🔍 Response data: contactId={response.get('contactId')}, author={response.get('author')}")
            
            # 3. Emite 'delivered' para o remetente após ~200ms (simula latência de rede)
            import asyncio
            await asyncio.sleep(0.2)
            await sio.emit("chat:delivered", {"id": message_id}, room=sid)
            print(f"📬 Status 'delivered' enviado para {sid}")
            
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
                        # Avisa que está processando (direto para o usuário)
                        await sio.emit("chat:typing", {
                            "author": "Guru",
                            "isTyping": True
                        }, room=sid)
                        
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
                        
                        # Remove indicador de digitação (direto para o usuário)
                        await sio.emit("chat:typing", {
                            "author": "Guru",
                            "isTyping": False
                        }, room=sid)
                        
                        # Responde com a transcrição e a resposta
                        response_text = f'🎤 _Áudio transcrito:_ "{transcription}"\n\n{ai_response}'
                        await publish_message(sio.emit, author="Guru 🧠", text=response_text, user_id=user_id, target_sid=sid)
                        
                        # Não continua para outras automações
                        return
            
            # Finaliza processamento de mensagem normal
            return
        
        # 5) KEYWORD AUTOMATIONS (ex: "oi" -> resposta automática)
        await handle_keyword_if_matches(sio.emit, text)
        
        # 6) SESSÃO ATIVA COM GURU
        # Comando para SAIR da sessão: @guru tchau, @guru sair, sair, tchau
        if text_lower in ["@guru tchau", "@guru sair", "tchau", "sair"] and user_id in guru_sessions:
            guru_sessions[user_id] = False
            from bots.automations import publish_message
            
            # Mensagem de despedida (sempre inclui 👋 para detecção no frontend)
            farewell_text = "👋 Até logo! Foi um prazer conversar com você. Estou aqui quando precisar! 🚀"
            
            await publish_message(
                sio.emit, 
                author="Guru 👋", 
                text=farewell_text,
                user_id=user_id,
                target_sid=sid
            )
            return
        
        # Comando para INICIAR sessão: @guru (sem tchauu/sair)
        if text_lower.startswith("@guru") and text_lower not in ["@guru tchau", "@guru sair"]:
            if user_id not in guru_sessions or not guru_sessions[user_id]:
                guru_sessions[user_id] = True
                from bots.automations import publish_message
                from bots.ai_bot import get_user_mode
                import random
                
                # Se for só "@guru", saudação personalizada
                if text_lower == "@guru":
                    mode = get_user_mode(user_id)
                    greetings = {
                        "casual": [
                            "E aí! Bora conversar? Manda a real, sem frescura! 😎",
                            "Opa! Tô aqui, mano. Pode perguntar o que quiser! 🚀",
                            "Salve! Qual é a boa? Tô pronto pra te ajudar! 💪"
                        ],
                        "profissional": [
                            "Olá! Estou à disposição para ajudá-lo(a). Como posso ser útil hoje? 💼",
                            "Bom dia! Pronto para auxiliá-lo(a). O que precisa? 🎯",
                            "Olá! Seja bem-vindo(a). Em que posso colaborar? 📋"
                        ],
                        "tecnico": [
                            "Sistema iniciado. Pronto para processar suas consultas técnicas. 🔧",
                            "Sessão ativada. Aguardando input para análise detalhada. 💻",
                            "Interface pronta. Pode enviar suas queries técnicas. ⚙️"
                        ]
                    }
                    
                    greeting = random.choice(greetings.get(mode, greetings["casual"]))
                    instructions = "\\n\\n💡 _Agora pode falar direto comigo, sem mencionar @guru a cada mensagem._\\n👋 _Para sair: 'tchau' ou 'sair'_"
                    
                    await publish_message(
                        sio.emit,
                        author="Guru 🧠",
                        text=greeting + instructions,
                        user_id=user_id,
                        target_sid=sid
                    )
                    return
        
        # Durante sessão ativa, todas mensagens vão pro Guru (exceto comandos)
        in_guru_session = guru_sessions.get(user_id, False)
        
        # 7) PERGUNTA PARA O GURU (via @guru ou durante sessão ativa)
        if is_ai_question(text) or in_guru_session:
            import asyncio
            from bots.automations import publish_message
            import random
            
            # Limpa menção ao guru (se houver)
            clean_text = clean_bot_mention(text)
            
            # Envia indicador de digitação (direto para o usuário)
            await sio.emit("chat:typing", {
                "author": "Guru",
                "isTyping": True
            }, room=sid)
            
            # 🧠 Tempo de pensamento variável baseado na complexidade
            question_length = len(clean_text)
            has_code_words = any(word in clean_text.lower() for word in ["código", "code", "python", "javascript", "função", "class"])
            has_question_mark = "?" in clean_text
            
            # Cálculo inteligente do tempo de pensamento
            if question_length > 100 or has_code_words:
                thinking_time = random.uniform(1.2, 2.0)  # Perguntas complexas
            elif question_length > 50:
                thinking_time = random.uniform(0.8, 1.5)  # Perguntas médias
            else:
                thinking_time = random.uniform(0.5, 1.0)  # Perguntas simples
            
            await asyncio.sleep(thinking_time)
            
            # Processa com ChatGPT (mantém contexto por user_id, passa nome do autor)
            ai_response = await ask_chatgpt(clean_text, user_id, author)
            
            # Simula digitação realista (baseado no tamanho da resposta)
            # ~50 caracteres por segundo (digitação rápida mas humana)
            typing_time = len(ai_response) / 50
            typing_time = max(1.5, min(typing_time, 5.0))  # Entre 1.5 e 5 segundos
            await asyncio.sleep(typing_time)
            
            # Remove indicador de digitação (direto para o usuário)
            await sio.emit("chat:typing", {
                "author": "Guru",
                "isTyping": False
            }, room=sid)
            
            # Publica resposta
            await publish_message(sio.emit, author="Guru 🧠", text=ai_response, user_id=user_id, target_sid=sid)
        
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
                    "author": "Guru",
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
                    "author": "Guru",
                    "isTyping": False
                })
                
                # Responde com a transcrição e a resposta
                response_text = f'🎤 _Áudio transcrito:_ "{transcription}"\n\n{ai_response}'
                await publish_message(sio.emit, author="Guru 🧠", text=response_text, user_id=body.author)
    
    return {"ok": True, "message": msg}



@app.on_event("startup")
async def _on_startup():
    """Inicializa scheduler e carrega automações na inicialização do servidor"""
    start_scheduler()
    await load_and_schedule_all(sio.emit)
    print("✅ Scheduler iniciado e automações carregadas")

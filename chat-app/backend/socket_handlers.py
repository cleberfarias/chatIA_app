import os
import asyncio
from datetime import datetime, timezone
from typing import Optional
from collections import defaultdict

from bson import ObjectId
from fastapi import HTTPException

from database import messages_collection, db
from models import MessageCreate
from storage import presign_get
from bots.automations import start_scheduler, load_and_schedule_all, handle_keyword_if_matches
from bots.ai_bot import ask_chatgpt, is_ai_question, clean_bot_mention
from bots.agents import (
    get_agent,
    clean_agent_mention,
    generate_agent_suggestions
)
from transcription import transcribe_from_s3
from socket_manager import sio
import traceback

# Sessões/mapeamentos
open_agent_sessions = defaultdict(set)
active_sessions = {}
user_sessions = {}
# Prefs por usuário para auto-criação de eventos (user_id, agent_key) -> bool
agent_auto_create_per_user = {}

# Dono para roteamento de mensagens externas (WhatsApp)
WA_OWNER_USER_ID = os.getenv("WA_OWNER_USER_ID")


def emit_to_user(payload: dict, target_user_id: Optional[str] = None):
    """Emite mensagem apenas para o usuário especificado, se conectado."""
    if target_user_id:
        target_sid = user_sessions.get(target_user_id)
        if target_sid:
            return sio.emit("chat:new-message", payload, room=target_sid)
        return None
    return sio.emit("chat:new-message", payload)


async def process_agent_message(sid, data):
    """
    Handler para mensagens enviadas aos agentes IA com contexto da conversa.
    Modularized into a module-level function so it can be tested directly.
    """
    print(f"📨 [Agent] Mensagem recebida de {sid}: {data}")
    
    agent_key = data.get("agentKey")
    message = data.get("message", "").strip()
    contact_id = data.get("contactId")

    # Preferir dados do socket (autenticados) para user_id/user_name
    environ = sio.get_environ(sid)
    user_id = (environ or {}).get("user_id") or data.get("userId")
    user_name = (environ or {}).get("user_name") or data.get("userName", "Usuário")
    
    if not agent_key or not message or not user_id:
        await sio.emit("agent:error", {"error": "Dados inválidos"}, to=sid)
        return
    
    from bots.agents import get_agent
    agent = await get_agent(agent_key, user_id)
    
    if not agent:
        await sio.emit("agent:error", {"error": f"Agente '{agent_key}' não encontrado"}, to=sid)
        return

    try:
        # Build conversation context
        from bots.context_loader import get_conversation_context
        from bots.entities import extract_entities
        from database import agent_messages_collection, messages_collection

        conversation_context = []
        if contact_id:
            try:
                conversation_context = await get_conversation_context(user_id=user_id, contact_id=contact_id, limit=20, hours_back=24)
            except Exception as ctx_error:
                print(f"⚠️ [Agent] Erro ao buscar contexto: {ctx_error}")

        # Merge agent messages history
        history_docs = await agent_messages_collection.find({
            "userId": user_id,
            "agentKey": agent_key,
            "contactId": contact_id
        }).sort("createdAt", -1).limit(50).to_list(50)
        # reverse so earlier messages come first
        agent_msgs_texts = [d.get("text", "") for d in reversed(history_docs or [])]

        # Compose conversation_text for entity extraction
        general_history_texts = []
        if contact_id:
            general_docs = await messages_collection.find({
                "$or": [
                    {"userId": user_id, "contactId": contact_id},
                    {"userId": contact_id, "contactId": user_id}
                ]
            }).sort("createdAt", -1).limit(50).to_list(50)
            general_history_texts = [d.get("text", "") for d in reversed(general_docs or [])]

        conversation_text = " ".join([*(agent_msgs_texts or []), *(general_history_texts or [])])
        if conversation_text.strip():
            conversation_text += " " + message
        else:
            conversation_text = message

        # Extract simple entities
        entities = extract_entities(conversation_text)

        # Build response using agent (with context when available)
        if conversation_context:
            base_response = await agent.ask_with_context(
                message=message,
                user_id=user_id,
                user_name=user_name,
                contact_id=contact_id,
                conversation_context=conversation_context
            )
        else:
            base_response = await agent.ask(message=message, user_id=user_id, user_name=user_name)

        # Persist simple user + agent messages (agent messages get _id)
        from datetime import datetime
        user_msg_doc = {
            "agentKey": agent_key,
            "userId": user_id,
            "contactId": contact_id,
            "author": user_name,
            "text": message,
            "role": "user",
            "createdAt": datetime.utcnow()
        }
        await agent_messages_collection.insert_one(user_msg_doc)

        agent_msg_doc = {
            "agentKey": agent_key,
            "userId": user_id,
            "contactId": contact_id,
            "author": agent.get_display_name(),
            "text": base_response,
            "role": "assistant",
            "createdAt": datetime.utcnow()
        }
        result = await agent_messages_collection.insert_one(agent_msg_doc)

        # Try to generate suggestions but continue on failure
        suggestions = []
        try:
            suggestions = await generate_agent_suggestions(agent, conversation_context or [], user_id, user_name, n_suggestions=3)
        except Exception as e:
            print(f"⚠️ Erro ao gerar sugestões: {e}")
            traceback.print_exc()

        def _serialize_entities(entities_obj: dict) -> list:
            result = []
            if not entities_obj:
                return result
            for k, v in entities_obj.items():
                result.append({
                    "type": v.type,
                    "key": k,
                    "value": v.value,
                    "normalized": getattr(v, "normalized", None),
                    "valid": getattr(v, "valid", True),
                    "metadata": getattr(v, "metadata", {})
                })
            return result

        serialized_entities = _serialize_entities(entities or {})

        # Emit response
        await sio.emit("agent:message", {
            "id": str(result.inserted_id),
            "agentKey": agent_key,
            "contactId": contact_id,
            "author": agent.get_display_name(),
            "text": base_response,
            "timestamp": int(datetime.utcnow().timestamp() * 1000),
            "nlp": {
                "intent": None,
                "confidence": None,
                "entities": serialized_entities
            },
            "suggestions": suggestions
        }, to=sid)
    except Exception as e:
        print(f"❌ [Agent] Error processing message: {e}")
        import traceback
        traceback.print_exc()
        await sio.emit("agent:error", {"error": f"Erro ao processar: {str(e)}"}, to=sid)


def register_socket_handlers():
    @sio.event
    async def connect(sid, environ, auth):
        from auth import decode_token

        print(f"🔌 Tentativa de conexão: {sid}")
        token = (auth or {}).get("token")
        if not token:
            print(f"❌ Conexão rejeitada: sem token - {sid}")
            return False
        try:
            payload = decode_token(token)
            user_id = payload["sub"]
            user = await db.users.find_one({"_id": ObjectId(user_id)})
            if not user:
                print(f"❌ Usuário não encontrado: {user_id} - {sid}")
                return False
            environ["user_id"] = user_id
            environ["user_name"] = user.get("name", "Usuário")
            environ["user_email"] = user.get("email", "")
            active_sessions[sid] = user_id
            user_sessions[user_id] = sid
            await sio.emit('user:online', {'userId': user_id}, skip_sid=sid)
            print(f"✅ Socket autenticado: {user.get('name')} ({user_id}) - sid: {sid}")
            print(f"👥 Usuários online: {len(user_sessions)}")
            return True
        except Exception as e:
            print(f"❌ Token inválido: {e} - {sid}")
            traceback.print_exc()
            return False

    @sio.event
    async def disconnect(sid):
        print(f"🔌 Cliente desconectado: {sid}")
        if sid in active_sessions:
            user_id = active_sessions[sid]
            del active_sessions[sid]
            if user_id in user_sessions:
                del user_sessions[user_id]
            await sio.emit('user:offline', {'userId': user_id})
            print(f"👤 Usuário {user_id} desconectado")
            print(f"👥 Usuários online: {len(user_sessions)}")

    @sio.on("chat:typing")
    async def handle_typing(sid, data):
        try:
            environ = sio.get_environ(sid)
            user_id = environ.get("user_id", "anonymous")
            contact_id = data.get("contactId")
            if contact_id:
                contact_sid = user_sessions.get(contact_id)
                if contact_sid:
                    await sio.emit("chat:typing", {
                        "userId": user_id,
                        "author": data.get("author"),
                        "isTyping": data.get("isTyping", False)
                    }, room=contact_sid)
                    print(f"⌨️  Typing event: {user_id} → {contact_id} - {data.get('isTyping')}")
                else:
                    print(f"📪 Contato {contact_id} offline - typing ignorado")
            else:
                print(f"⚠️  Typing sem contactId - ignorado")
        except Exception as e:
            print(f"❌ Erro chat:typing: {e}")
            traceback.print_exc()

    @sio.on("chat:mark-read")
    async def handle_mark_read(sid, data):
        try:
            environ = sio.get_environ(sid)
            user_id = environ.get("user_id", "anonymous")
            message_ids = data.get("ids", [])
            if not message_ids:
                return
            await sio.emit("chat:read", {
                "ids": message_ids,
                "readBy": user_id
            }, skip_sid=sid)
            print(f"👁️ Mensagens marcadas como lidas por {user_id}: {len(message_ids)} msgs")
        except Exception as e:
            print(f"❌ Erro chat:mark-read: {e}")
            traceback.print_exc()

    @sio.on("chat:send")
    async def handle_chat_send(sid, data):
        try:
            print(f"📨 Mensagem recebida de {sid}: {data}")
            environ = sio.get_environ(sid)
            user_id = environ.get("user_id", "anonymous")
            temp_id = data.get("tempId")
            author = data.get("author", "")
            text = data.get("text", "").strip()
            contact_id = data.get("contactId")

            # NOTE: Agent mentions removed from chat input processing.
            # Agents should be invoked only via the Agent Panel (agent:send) or via the frontend UI.

            text_lower = text.lower().strip()
            in_guru_session = ('guru' in open_agent_sessions.get(user_id, set()))
            is_ai_query = is_ai_question(text)

            # Agents should be invoked only via panel (agent:open/agent:close) or when
            # an AI question is detected. Inline @agent controls are deprecated and removed.
            if in_guru_session or is_ai_query:
                print(f"🧠 Mensagem para Guru detectada - pulando persistência no banco")
            else:
                message_create = MessageCreate(**data)
                now = datetime.now(timezone.utc)
                doc = {
                    "author": message_create.author,
                    "text": message_create.text,
                    "status": message_create.status,
                    "type": message_create.type,
                    "userId": user_id,
                    "contactId": message_create.contactId,
                    "createdAt": now
                }
                result = await messages_collection.insert_one(doc)
                message_id = str(result.inserted_id)
                response = {
                    "id": message_id,
                    "author": doc["author"],
                    "text": doc["text"],
                    "timestamp": int(doc["createdAt"].timestamp() * 1000),
                    "status": doc["status"],
                    "type": doc["type"],
                    "userId": user_id,
                    "contactId": doc.get("contactId")
                }
                if "attachment" in doc:
                    response["attachment"] = doc["attachment"]
                    response["url"] = presign_get(doc["attachment"]["key"])
                await sio.emit("chat:ack", {
                    "tempId": temp_id,
                    "id": message_id,
                    "status": "sent",
                    "timestamp": response["timestamp"]
                }, room=sid)
                if message_create.contactId:
                    contact_sid = user_sessions.get(message_create.contactId)
                    if contact_sid:
                        await sio.emit("chat:new-message", response, room=contact_sid)
                    else:
                        print(f"📪 Contato {message_create.contactId} está offline - mensagem salva")
                else:
                    await sio.emit("chat:new-message", response, skip_sid=sid)
                await asyncio.sleep(0.2)
                await sio.emit("chat:delivered", {"id": message_id}, room=sid)
                if message_create.type == "audio" and ("attachment" in doc):
                    from bots.automations import publish_message
                    transcription = await transcribe_from_s3(
                        doc["attachment"]["key"],
                        doc["attachment"]["bucket"]
                    )
                    if transcription and not transcription.startswith("["):
                        if is_ai_question(transcription):
                            await sio.emit("chat:typing", {"author": "Guru", "isTyping": True}, room=sid)
                            await asyncio.sleep(0.8)
                            clean_text = clean_bot_mention(transcription)
                            ai_response = await ask_chatgpt(clean_text, user_id, author)
                            typing_time = len(ai_response) / 50
                            typing_time = max(1.5, min(typing_time, 5.0))
                            await asyncio.sleep(typing_time)
                            await sio.emit("chat:typing", {"author": "Guru", "isTyping": False}, room=sid)
                            response_text = f'🎤 _Áudio transcrito:_ "{transcription}"\n\n{ai_response}'
                            await publish_message(sio.emit, author="Guru 🧠", text=response_text, user_id=user_id, target_sid=sid)
                            return
                return

            await handle_keyword_if_matches(sio.emit, text)

            # Note: Starting and ending Guru sessions via inline commands is deprecated.
            # Use the agent panel (agent:open/agent:close) instead to open or close agent sessions.

            in_guru_session = ('guru' in open_agent_sessions.get(user_id, set()))
            if is_ai_question(text) or in_guru_session:
                from bots.automations import publish_message
                import random
                clean_text = clean_bot_mention(text)
                await sio.emit("chat:typing", {"author": "Guru", "isTyping": True}, room=sid)
                question_length = len(clean_text)
                has_code_words = any(word in clean_text.lower() for word in ["código", "code", "python", "javascript", "função", "class"])
                has_question_mark = "?" in clean_text
                if question_length > 100 or has_code_words:
                    thinking_time = random.uniform(1.2, 2.0)
                elif question_length > 50:
                    thinking_time = random.uniform(0.8, 1.5)
                else:
                    thinking_time = random.uniform(0.5, 1.0)
                await asyncio.sleep(thinking_time)
                ai_response = await ask_chatgpt(clean_text, user_id, author)
                typing_time = len(ai_response) / 50
                typing_time = max(1.5, min(typing_time, 5.0))
                await asyncio.sleep(typing_time)
                await sio.emit("chat:typing", {"author": "Guru", "isTyping": False}, room=sid)
                await publish_message(sio.emit, author="Guru 🧠", text=ai_response, user_id=user_id, target_sid=sid)
        except Exception as e:
            print(f"❌ Erro ao processar mensagem: {e}")
            traceback.print_exc()
            await sio.emit("error", {
                "message": str(e),
                "tempId": data.get("tempId")
            }, room=sid)

    @sio.on("chat:read")
    async def handle_chat_read(sid, data):
        try:
            message_ids = data.get("ids", [])
            if not message_ids:
                return
            object_ids = [ObjectId(id) for id in message_ids if ObjectId.is_valid(id)]
            result = await messages_collection.update_many(
                {"_id": {"$in": object_ids}},
                {"$set": {"status": "read"}}
            )
            await sio.emit("chat:read", {"ids": message_ids})
            print(f"👁️ Mensagens marcadas como lidas: {result.modified_count}")
        except Exception as e:
            print(f"❌ Erro em chat:read: {e}")

    async def wrapper_process_agent_message(sid, data):
        await process_agent_message(sid, data)
    @sio.on("agent:send")
    async def handle_agent_message(sid, data):
        """Wrapper that calls process_agent_message; this improves testability."""
        await process_agent_message(sid, data)

    # NOTE: Don't return early - let all handlers below be registered

    @sio.on("agent:request-summary")
    async def handle_agent_request_summary(sid, data):
        try:
            environ = sio.get_environ(sid)
            user_id = environ.get("user_id")
            user_name = environ.get("user_name") or "Usuário"
            agent_key = data.get("agentKey")
            contact_id = data.get("contactId")

            if not agent_key or not user_id:
                await sio.emit("agent:error", {"error": "Dados inválidos"}, to=sid)
                return

            from bots.agents import get_agent, generate_conversation_summary
            agent = await get_agent(agent_key, user_id)
            if not agent:
                await sio.emit("agent:error", {"error": "Agente não encontrado"}, to=sid)
                return

            conversation_context = None
            if contact_id:
                from bots.context_loader import get_conversation_context
                conversation_context = await get_conversation_context(user_id, contact_id, limit=40, hours_back=72)

            summary = await generate_conversation_summary(agent, conversation_context or [], user_id, user_name)

            await sio.emit("agent:summary", {
                "agentKey": agent_key,
                "contactId": contact_id,
                "summary": summary
            }, to=sid)
        except Exception as e:
            print(f"❌ agent:request-summary error: {e}")
            traceback.print_exc()
            await sio.emit("agent:error", {"error": str(e)}, to=sid)

    @sio.on("agent:set-auto-create")
    async def handle_agent_set_auto_create(sid, data):
        try:
            environ = sio.get_environ(sid)
            user_id = environ.get("user_id")
            agent_key = data.get("agentKey")
            auto_create = bool(data.get("autoCreate", False))
            if not user_id or not agent_key:
                return
            agent_auto_create_per_user[(user_id, agent_key.lower())] = auto_create
            print(f"🔁 Auto-create set for {user_id}/{agent_key}: {auto_create}")
            await sio.emit("agent:auto-create-updated", {"agentKey": agent_key, "autoCreate": auto_create}, to=sid)
        except Exception as e:
            print(f"❌ agent:set-auto-create error: {e}")
            traceback.print_exc()
            await sio.emit("agent:error", {"error": str(e)}, to=sid)

    @sio.on("agent:schedule-confirm")
    async def handle_agent_schedule_confirm(sid, data):
        """
        Handler para criação de evento quando usuário confirma via interface.
        { agentKey, contactId, date, time, customerEmail }
        """
        try:
            environ = sio.get_environ(sid)
            user_id = environ.get("user_id")
            user_name = environ.get("user_name") or "Usuário"
            agent_key = data.get("agentKey")
            contact_id = data.get("contactId")
            date_str = data.get("date")
            time_str = data.get("time")
            customer_email = data.get("customerEmail")

            if not agent_key or not user_id or not customer_email or not date_str or not time_str:
                await sio.emit("agent:error", {"error": "Dados inválidos para agendamento"}, to=sid)
                return

            from bots.agents import get_agent, sdr_schedule_event
            agent = await get_agent(agent_key, user_id)
            if not agent:
                await sio.emit("agent:error", {"error": "Agente não encontrado"}, to=sid)
                return

            # Verifica permissão de criação
            if not getattr(agent, 'allow_calendar_creation', False):
                await sio.emit("agent:error", {"error": "Agente não possui permissão para criar eventos"}, to=sid)
                return

            # Parse date/time
            from datetime import datetime, timedelta
            start_datetime = datetime.fromisoformat(f"{date_str}T{time_str}:00")
            end_datetime = start_datetime + timedelta(hours=1)

            event = await sdr_schedule_event(
                start_datetime=start_datetime,
                end_datetime=end_datetime,
                customer_email=customer_email,
                customer_name=user_name,
                customer_phone=data.get('phone'),
                user_id=user_id,
                user_name=user_name,
                contact_id=contact_id
            )

            if not event:
                await sio.emit("agent:error", {"error": "Falha ao criar evento"}, to=sid)
                return

            confirmation_text = f"\n✅ **Reunião agendada com sucesso!**\n\n📅 **Link do Calendário:** {event.get('htmlLink', 'N/A')}\n📹 **Link do Google Meet:** {event.get('hangoutLink', 'N/A')}\n📧 **Convite enviado para:** {customer_email}\n"
            await sio.emit("agent:message", {
                "id": str(ObjectId()),
                "agentKey": agent_key,
                "contactId": contact_id,
                "author": agent.get_display_name(),
                "text": confirmation_text,
                "timestamp": int(datetime.utcnow().timestamp() * 1000)
            }, to=sid)

            # Também publica no chat principal (para contato e atendente)
            try:
                from bots.automations import publish_message
                await publish_message(
                    sio.emit,
                    author=agent.get_display_name(),
                    text=confirmation_text,
                    user_id=user_id,
                    contact_id=contact_id
                )
            except Exception as pub_err:
                print(f"⚠️ Falha ao publicar confirmação no chat principal: {pub_err}")

        except Exception as e:
            print(f"❌ agent:schedule-confirm error: {e}")
            traceback.print_exc()
            await sio.emit("agent:error", {"error": str(e)}, to=sid)

    @sio.on("agent:open")
    async def handle_agent_open(sid, data):
        """Handler para abrir um painel de agente (ex.: Guru)."""
        try:
            environ = sio.get_environ(sid)
            user_id = environ.get("user_id")
            agent_key = data.get("agentKey")
            contact_id = data.get("contactId")
            print(f"🔓 Agent open request: user={user_id}, agentKey={agent_key}, contactId={contact_id}")
            if not user_id or not agent_key:
                return
            # Ativa sessão para Guru (agora controlada via agent:open/agent:close)
            if agent_key:
                open_agent_sessions[user_id].add(agent_key.lower())
                print(f"🧠 Sessão do agente '{agent_key}' ativada para user {user_id}")
                await sio.emit("agent:opened", {"agentKey": agent_key}, room=sid)
                # Se o usuário pediu por auto-create em sessão (persistido em agent_auto_create_per_user), atualiza mapa
                pref = data.get('autoCreate', None)
                if pref is not None:
                    agent_auto_create_per_user[(user_id, agent_key.lower())] = bool(pref)
        except Exception as e:
            print(f"❌ Agent open error: {e}")

    @sio.on("agent:close")
    async def handle_agent_close(sid, data):
        """Handler para fechar um painel de agente (ex.: Guru)."""
        try:
            environ = sio.get_environ(sid)
            user_id = environ.get("user_id")
            agent_key = data.get("agentKey")
            contact_id = data.get("contactId")
            print(f"🔒 Agent close request: user={user_id}, agentKey={agent_key}, contactId={contact_id}")
            if not user_id or not agent_key:
                return
            if agent_key:
                open_agent_sessions[user_id].discard(agent_key.lower())
                print(f"🧠 Sessão do agente '{agent_key}' desativada para user {user_id}")
                await sio.emit("agent:closed", {"agentKey": agent_key}, room=sid)
                # Optional: clean up applied preferences
                if (user_id, agent_key.lower()) in agent_auto_create_per_user:
                    del agent_auto_create_per_user[(user_id, agent_key.lower())]
        except Exception as e:
            print(f"❌ Agent close error: {e}")

    return sio

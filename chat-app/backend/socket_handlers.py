import os
import asyncio
from datetime import datetime, timezone
from typing import Optional

from bson import ObjectId
from fastapi import HTTPException

from database import messages_collection, db
from models import MessageCreate
from storage import presign_get
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
from socket_manager import sio

# Sessões/mapeamentos
guru_sessions = {}
active_sessions = {}
user_sessions = {}

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

            # Comandos
            if is_command(text):
                from bots.automations import publish_message
                from bots.ai_bot import set_user_mode, get_user_mode, generate_conversation_summary

                lower = text.lower()
                if lower in ["/ajuda", "/help"]:
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
                if lower in ["/agentes", "/agents"]:
                    agents_list = list_all_agents()
                    await publish_message(sio.emit, author="Sistema 🤖", text=agents_list, user_id=user_id, target_sid=sid)
                    return
                if lower == "/contexto":
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
                if lower.startswith("/modo "):
                    new_mode = text[6:].strip().lower()
                    result = set_user_mode(user_id, new_mode)
                    await publish_message(sio.emit, author="Guru 🎭", text=result, user_id=user_id, target_sid=sid)
                    return
                if lower in ["/resumo", "/rusumo"]:
                    summary = generate_conversation_summary(user_id)
                    await publish_message(sio.emit, author="Guru 📝", text=summary, user_id=user_id, target_sid=sid)
                    return
                if lower in ["/limpar", "/clear"]:
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
                if lower.startswith("/ai "):
                    question = text[4:].strip()
                    if question:
                        await sio.emit("chat:typing", {"author": "Guru", "isTyping": True}, room=sid)
                        await asyncio.sleep(0.8)
                        ai_response = await ask_chatgpt(question, user_id, author)
                        typing_time = len(ai_response) / 50
                        typing_time = max(1.0, min(typing_time, 4.0))
                        await asyncio.sleep(typing_time)
                        await sio.emit("chat:typing", {"author": "Guru", "isTyping": False}, room=sid)
                        await publish_message(sio.emit, author="Guru 🧠", text=ai_response, user_id=user_id, target_sid=sid)
                    else:
                        await publish_message(sio.emit, author="Guru", text="💭 Use: /ai <sua pergunta>", user_id=user_id, target_sid=sid)
                    return
                reply = run_command(text)
                if reply:
                    from bots.automations import publish_message
                    await publish_message(sio.emit, author="Guru", text=reply, user_id=user_id, target_sid=sid)
                return

            # Agentes especializados
            agent_name = detect_agent_mention(text)
            if agent_name:
                from database import agent_messages_collection
                agent = get_agent(agent_name, user_id)
                if agent:
                    clean_text = clean_agent_mention(text, agent_name)
                    user_msg_doc = {
                        "_id": ObjectId(),
                        "agentKey": agent_name,
                        "author": author,
                        "text": clean_text if clean_text else f"@{agent_name}",
                        "userId": user_id,
                        "contactId": contact_id,
                        "createdAt": datetime.now(timezone.utc)
                    }
                    await agent_messages_collection.insert_one(user_msg_doc)
                    await sio.emit("agent:message", {
                        "id": str(user_msg_doc["_id"]),
                        "agentKey": agent_name,
                        "author": author,
                        "text": clean_text if clean_text else f"@{agent_name}",
                        "timestamp": int(user_msg_doc["createdAt"].timestamp() * 1000),
                        "contactId": contact_id
                    }, room=sid)
                    
                    # 📅 SDR: Detecta intenção ANTES de gerar resposta
                    should_show_calendar = False
                    calendar_data = None
                    
                    if agent_name == "sdr" and clean_text:
                        from bots.nlu import detect_intent
                        from bots.entities import extract_entities
                        
                        # Monta histórico da conversa (inclui TODAS as mensagens: usuário + agente)
                        history_docs = await agent_messages_collection.find({
                            "userId": user_id,
                            "agentKey": "sdr"
                        }).sort("createdAt", -1).limit(20).to_list(20)
                        
                        # Junta todo o texto da conversa (usuário + bot)
                        conversation_text = " ".join([doc["text"] for doc in reversed(history_docs)])
                        
                        # Também adiciona a mensagem atual
                        conversation_text += " " + clean_text
                        
                        print(f"🔍 SDR - Analisando conversa: {conversation_text[:200]}...")
                        
                        # Detecta intenção de agendamento
                        intent_result = await detect_intent(conversation_text, "customer")
                        entities = extract_entities(conversation_text)
                        
                        print(f"🔍 SDR - Intent: {intent_result.name} | Confidence: {intent_result.confidence}")
                        
                        # Log detalhado das entidades
                        has_email = False
                        has_phone = False
                        customer_email = None
                        customer_phone = None
                        
                        if entities:
                            for entity_key, entity in entities.items():
                                print(f"🔍 SDR - Entity {entity_key}: value='{entity.value}', normalized='{entity.normalized}'")
                                if entity_key == "email" and entity.valid:
                                    has_email = True
                                    customer_email = entity.normalized
                                elif entity_key == "phone" and entity.valid:
                                    has_phone = True
                                    customer_phone = entity.normalized
                        
                        # Se há intenção de agendamento E já tem email
                        if intent_result.name in ["scheduling", "purchase"] and has_email:
                            should_show_calendar = True
                            calendar_data = {
                                "email": customer_email,
                                "phone": customer_phone
                            }
                            print(f"📅 CALENDÁRIO SERÁ MOSTRADO para {customer_email}")
                    
                    # Gera resposta do agente (ou customizada se calendário)
                    if should_show_calendar:
                        response = f"✅ Perfeito! Detectei seu email {calendar_data['email']}. Vou abrir o calendário para você escolher o melhor horário."
                    elif clean_text and clean_text.startswith("/"):
                        response = await handle_agent_command(agent, clean_text, user_id, author)
                    else:
                        if clean_text:
                            response = await agent.ask(clean_text, user_id, author)
                        else:
                            response = f"👋 Olá! Sou {agent.get_display_name()}\n\n"
                            response += f"**Minhas especialidades:**\n"
                            for specialty in agent.specialties:
                                response += f"• {specialty}\n"
                            response += f"\n💡 _Faça sua pergunta ou use @{agent_name} /ajuda para ver comandos_"
                    
                    # Salva e envia resposta
                    agent_msg_doc = {
                        "_id": ObjectId(),
                        "agentKey": agent_name,
                        "author": agent.get_display_name(),
                        "text": response,
                        "userId": user_id,
                        "contactId": contact_id,
                        "createdAt": datetime.now(timezone.utc)
                    }
                    await agent_messages_collection.insert_one(agent_msg_doc)
                    await sio.emit("agent:message", {
                        "id": str(agent_msg_doc["_id"]),
                        "agentKey": agent_name,
                        "author": agent.get_display_name(),
                        "text": response,
                        "timestamp": int(agent_msg_doc["createdAt"].timestamp() * 1000),
                        "contactId": contact_id
                    }, room=sid)
                    
                    # 📅 Envia evento do calendário DEPOIS da resposta
                    if should_show_calendar:
                        print(f"📅 EMITINDO agent:show-slot-picker para {calendar_data['email']}")
                        await sio.emit("agent:show-slot-picker", {
                            "agentKey": "sdr",
                            "customerEmail": calendar_data['email'],
                            "customerPhone": calendar_data['phone']
                        }, room=sid)
                        
                        # Se já tem data/hora escolhidos, tenta agendar
                        if entities.get("email") and entities.get("date") and entities.get("time"):
                            from bots.agents import sdr_try_schedule_meeting
                            event = await sdr_try_schedule_meeting(conversation_text, user_id, author)
                            
                            if event:
                                # Envia confirmação com links
                                confirmation_text = f"""
✅ **Reunião agendada com sucesso!**

📅 **Link do Calendário:** {event.get('htmlLink', 'N/A')}
📹 **Link do Google Meet:** {event.get('hangoutLink', 'N/A')}
📧 **Convite enviado para:** {user_email}

Você receberá um email de confirmação com todos os detalhes da reunião.
"""
                                
                                confirmation_doc = {
                                    "_id": ObjectId(),
                                    "agentKey": "sdr",
                                    "author": agent.get_display_name(),
                                    "text": confirmation_text,
                                    "userId": user_id,
                                    "contactId": contact_id,
                                    "createdAt": datetime.now(timezone.utc)
                                }
                                await agent_messages_collection.insert_one(confirmation_doc)
                                await sio.emit("agent:message", {
                                    "id": str(confirmation_doc["_id"]),
                                    "agentKey": "sdr",
                                    "author": agent.get_display_name(),
                                    "text": confirmation_text,
                                    "timestamp": int(confirmation_doc["createdAt"].timestamp() * 1000),
                                    "contactId": contact_id
                                }, room=sid)
                    
                    return

            text_lower = text.lower().strip()
            in_guru_session = guru_sessions.get(user_id, False)
            is_guru_mention = text_lower.startswith("@guru")
            is_guru_exit = text_lower in ["tchau", "sair"]
            is_ai_query = is_ai_question(text)

            if in_guru_session or is_guru_mention or is_guru_exit or is_ai_query:
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

            if text_lower in ["@guru tchau", "@guru sair", "tchau", "sair"] and user_id in guru_sessions:
                guru_sessions[user_id] = False
                from bots.automations import publish_message
                farewell_text = "👋 Até logo! Foi um prazer conversar com você. Estou aqui quando precisar! 🚀"
                await publish_message(
                    sio.emit,
                    author="Guru 👋",
                    text=farewell_text,
                    user_id=user_id,
                    target_sid=sid
                )
                return

            if text_lower.startswith("@guru") and text_lower not in ["@guru tchau", "@guru sair"]:
                if user_id not in guru_sessions or not guru_sessions[user_id]:
                    guru_sessions[user_id] = True
                    from bots.automations import publish_message
                    from bots.ai_bot import get_user_mode
                    import random
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

            in_guru_session = guru_sessions.get(user_id, False)
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

    return sio

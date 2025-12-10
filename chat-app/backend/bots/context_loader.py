"""Carrega contexto de conversas para agentes IA."""

from typing import List, Dict, Optional
from datetime import datetime, timedelta, timezone
from database import messages_collection


async def get_conversation_context(
    user_id: str,
    contact_id: str,
    limit: int = 20,
    hours_back: int = 24
) -> List[Dict[str, str]]:
    """
    Busca histórico de conversa entre user_id e contact_id.
    
    Por que isso existe?
    - Agentes precisam entender o que está sendo discutido
    - Evita respostas genéricas e descontextualizadas
    
    Args:
        user_id: ID do usuário logado
        contact_id: ID do contato/cliente
        limit: Número máximo de mensagens (evita custo alto API)
        hours_back: Janela de tempo (evita contexto antigo/irrelevante)
        
    Returns:
        Lista formatada para GPT:
        [
            {"role": "assistant", "content": "[14:30] Você: Olá"},
            {"role": "user", "content": "[14:31] Cliente: Oi, tudo bem?"}
        ]
    """
    # Por que filtro temporal?
    # - Conversas antigas não são relevantes
    # - Reduz tokens enviados ao GPT (custo)
    # Usa timezone UTC para compatibilidade com createdAt armazenado com tzinfo
    time_threshold = datetime.now(timezone.utc) - timedelta(hours=hours_back)
    
    # Query: mensagens entre user_id e contact_id (ambas direções)
    query = {
        "$or": [
            {"userId": user_id, "contactId": contact_id},
            {"userId": contact_id, "contactId": user_id}
        ],
        "createdAt": {"$gte": time_threshold}
    }
    
    cursor = messages_collection.find(query).sort("createdAt", 1).limit(limit)
    docs = await cursor.to_list(length=limit)
    
    # Por que formatar para GPT?
    # - GPT usa formato específico: role + content
    # - "role": "user" = cliente falando
    # - "role": "assistant" = você falando
    context_messages = []
    for doc in docs:
        # Determina quem falou
        is_user_message = doc.get("userId") == user_id
        role = "assistant" if is_user_message else "user"
        
        # Formata com timestamp (contexto temporal)
        author_name = doc.get("author", "Desconhecido")
        text = doc.get("text", "")
        timestamp = doc.get("createdAt", datetime.now(timezone.utc))
        
        content = f"[{timestamp.strftime('%H:%M')}] {author_name}: {text}"
        
        context_messages.append({
            "role": role,
            "content": content
        })
    
    return context_messages


async def format_context_summary(
    user_id: str,
    contact_id: str,
    limit: int = 20
) -> str:
    """
    Gera resumo textual do contexto (para debug/logs).
    
    Por que isso?
    - Facilita debugging
    - Permite mostrar contexto pro usuário (futuro)
    - Útil para logs de auditoria
    """
    messages = await get_conversation_context(user_id, contact_id, limit)
    
    if not messages:
        return "CONTEXTO: Nenhuma conversa recente com este contato."
    
    lines = ["CONTEXTO DA CONVERSA PRINCIPAL (últimas mensagens):"]
    lines.append("-" * 60)
    
    for msg in messages:
        lines.append(msg["content"])
    
    lines.append("-" * 60)
    lines.append(f"Total: {len(messages)} mensagens")
    
    return "\n".join(lines)

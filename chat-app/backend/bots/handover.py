"""Sistema de Handover - Transferência de atendimento Bot → Humano.

Gerencia a transferência de conversas quando:
- Cliente solicita explicitamente
- Bot não consegue resolver
- Situação crítica (reclamação, cancelamento)
"""

from datetime import datetime
from typing import Optional
from dataclasses import dataclass, asdict
from enum import Enum


class HandoverReason(str, Enum):
    """Motivos de transferência."""
    EXPLICIT_REQUEST = "explicit_request"  # Cliente pediu humano
    LOW_CONFIDENCE = "low_confidence"      # Bot não entendeu
    COMPLAINT = "complaint"                # Reclamação
    COMPLEX_QUERY = "complex_query"        # Pergunta complexa
    ESCALATION = "escalation"              # Escalar para supervisor
    TECHNICAL_ISSUE = "technical_issue"    # Problema técnico
    OUTSIDE_HOURS = "outside_hours"        # Fora do horário
    

class HandoverStatus(str, Enum):
    """Status da transferência."""
    PENDING = "pending"       # Aguardando atendente
    ACCEPTED = "accepted"     # Atendente aceitou
    IN_PROGRESS = "in_progress"  # Em atendimento
    RESOLVED = "resolved"     # Resolvido
    CANCELLED = "cancelled"   # Cancelado
    TIMEOUT = "timeout"       # Timeout (ninguém atendeu)


@dataclass
class HandoverRequest:
    """Requisição de transferência."""
    id: str
    customer_id: str
    customer_name: str
    contact_id: str
    reason: HandoverReason
    status: HandoverStatus
    priority: int  # 1=baixa, 2=média, 3=alta, 4=urgente
    
    # Contexto
    last_messages: list[dict]  # Últimas mensagens da conversa
    entities_extracted: dict   # Entidades já extraídas (CPF, email, etc)
    intent_detected: Optional[str] = None
    bot_confidence: float = 0.0
    
    # Metadata
    created_at: datetime = None
    accepted_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    assigned_agent_id: Optional[str] = None
    assigned_agent_name: Optional[str] = None
    
    # Tags e notas
    tags: list[str] = None
    notes: str = ""
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.tags is None:
            self.tags = []
    
    def to_dict(self):
        """Converte para dict para MongoDB."""
        data = asdict(self)
        # Converte Enums para string
        data["reason"] = self.reason.value
        data["status"] = self.status.value
        return data


def calculate_priority(reason: HandoverReason, entities: dict, intent: str = None) -> int:
    """
    Calcula prioridade do handover baseado em contexto.
    
    Returns:
        1=baixa, 2=média, 3=alta, 4=urgente
    """
    # Urgente (4)
    if reason in [HandoverReason.COMPLAINT, HandoverReason.ESCALATION]:
        return 4
    
    # Alta (3)
    if reason == HandoverReason.EXPLICIT_REQUEST:
        return 3
    
    # Média (2)
    if reason in [HandoverReason.COMPLEX_QUERY, HandoverReason.TECHNICAL_ISSUE]:
        # Se tem CPF/email já coletado, aumenta prioridade
        if "cpf" in entities or "email" in entities:
            return 3
        return 2
    
    # Baixa (1)
    return 1


def should_trigger_handover(
    intent_name: str,
    confidence: float,
    entities: dict,
    conversation_length: int
) -> tuple[bool, Optional[HandoverReason]]:
    """
    Decide se deve fazer handover baseado em critérios.
    
    Returns:
        (should_handover, reason)
    """
    # 1. Cliente pediu explicitamente
    if intent_name == "human_handover":
        return True, HandoverReason.EXPLICIT_REQUEST
    
    # 2. Reclamação
    if intent_name == "complaint":
        return True, HandoverReason.COMPLAINT
    
    # 3. Confiança muito baixa
    if confidence < 0.3:
        return True, HandoverReason.LOW_CONFIDENCE
    
    # 4. Conversa muito longa sem resolver (> 10 mensagens)
    if conversation_length > 10 and confidence < 0.6:
        return True, HandoverReason.COMPLEX_QUERY
    
    # 5. Não entendeu a pergunta principal
    if intent_name == "general" and confidence < 0.5:
        return True, HandoverReason.LOW_CONFIDENCE
    
    return False, None


def generate_handover_summary(
    customer_name: str,
    reason: HandoverReason,
    intent: Optional[str],
    entities: dict,
    last_messages: list[dict]
) -> str:
    """
    Gera resumo para o atendente ver rapidamente o contexto.
    """
    summary_parts = [
        f"🙋 Cliente: {customer_name}",
        f"📌 Motivo: {reason.value.replace('_', ' ').title()}",
    ]
    
    if intent:
        summary_parts.append(f"🎯 Intenção detectada: {intent}")
    
    # Entidades coletadas
    if entities:
        entities_str = []
        if "cpf" in entities:
            entities_str.append(f"CPF: {entities['cpf'].metadata.get('masked', '***')}")
        if "phone" in entities:
            entities_str.append(f"Tel: {entities['phone'].normalized}")
        if "email" in entities:
            entities_str.append(f"Email: {entities['email'].value}")
        if "product" in entities:
            entities_str.append(f"Produto: {entities['product'].normalized}")
        
        if entities_str:
            summary_parts.append(f"📋 Dados coletados: {', '.join(entities_str)}")
    
    # Últimas mensagens
    if last_messages:
        summary_parts.append(f"\n💬 Últimas mensagens:")
        for msg in last_messages[-3:]:  # Últimas 3
            author = msg.get("author", "Cliente")
            text = msg.get("text", "")[:100]  # Limita 100 chars
            summary_parts.append(f"  {author}: {text}")
    
    return "\n".join(summary_parts)


def suggest_agent_for_handover(
    intent: Optional[str],
    reason: HandoverReason,
    entities: dict
) -> Optional[str]:
    """
    Sugere qual atendente/departamento deve receber o handover.
    """
    # Por intenção
    intent_to_department = {
        "purchase": "vendas",
        "scheduling": "comercial",
        "legal": "juridico",
        "technical_support": "suporte",
        "complaint": "supervisor",
    }
    
    if intent in intent_to_department:
        return intent_to_department[intent]
    
    # Por motivo
    if reason == HandoverReason.COMPLAINT:
        return "supervisor"
    
    if reason == HandoverReason.TECHNICAL_ISSUE:
        return "suporte"
    
    # Se tem produto, provavelmente vendas
    if "product" in entities or "money" in entities:
        return "vendas"
    
    # Default: atendimento geral
    return "geral"


def get_handover_message_for_customer(reason: HandoverReason) -> str:
    """
    Retorna mensagem amigável para informar o cliente sobre transferência.
    """
    messages = {
        HandoverReason.EXPLICIT_REQUEST: 
            "Claro! Vou conectar você com um de nossos atendentes. Um momento, por favor... 👤",
        
        HandoverReason.LOW_CONFIDENCE:
            "Hmm, não tenho certeza se entendi corretamente. "
            "Vou transferir você para um especialista que pode ajudar melhor! 🤝",
        
        HandoverReason.COMPLAINT:
            "Lamento muito pelo problema. Vou transferir imediatamente para nosso supervisor "
            "resolver isso com prioridade! 🚨",
        
        HandoverReason.COMPLEX_QUERY:
            "Essa é uma questão importante! Vou conectar você com um especialista "
            "que tem mais experiência nesse assunto. 💡",
        
        HandoverReason.ESCALATION:
            "Vou escalar sua solicitação para nosso supervisor. "
            "Aguarde um momento, por favor... 📞",
        
        HandoverReason.TECHNICAL_ISSUE:
            "Entendo a situação técnica. Vou transferir para nossa equipe de suporte "
            "especializada! 🔧",
        
        HandoverReason.OUTSIDE_HOURS:
            "No momento estamos fora do horário de atendimento. "
            "Mas vou registrar sua solicitação e te retornaremos assim que possível! ⏰",
    }
    
    return messages.get(reason, "Vou transferir você para um atendente. Um momento! 👋")


def get_handover_message_for_agent(handover: HandoverRequest) -> str:
    """
    Retorna mensagem para notificar atendente sobre novo handover.
    """
    priority_emoji = {
        1: "🟢",  # baixa
        2: "🟡",  # média
        3: "🟠",  # alta
        4: "🔴",  # urgente
    }
    
    emoji = priority_emoji.get(handover.priority, "⚪")
    
    summary = generate_handover_summary(
        handover.customer_name,
        handover.reason,
        handover.intent_detected,
        handover.entities_extracted,
        handover.last_messages
    )
    
    return f"""
{emoji} Nova transferência de atendimento!

{summary}

⏱️ Aguardando há: {(datetime.utcnow() - handover.created_at).seconds}s
    """


# Exemplo de uso
if __name__ == "__main__":
    from .entities import Entity
    
    # Simula handover por reclamação
    handover = HandoverRequest(
        id="handover_123",
        customer_id="customer_456",
        customer_name="João Silva",
        contact_id="contact_789",
        reason=HandoverReason.COMPLAINT,
        status=HandoverStatus.PENDING,
        priority=calculate_priority(HandoverReason.COMPLAINT, {}, "complaint"),
        last_messages=[
            {"author": "João Silva", "text": "Produto chegou com defeito!"},
            {"author": "Bot", "text": "Sinto muito pelo problema..."},
        ],
        entities_extracted={
            "cpf": Entity(type="cpf", value="111.222.333-44", 
                         metadata={"masked": "111.***.***-44"})
        },
        intent_detected="complaint",
        bot_confidence=0.85,
    )
    
    print("📋 Handover Request:")
    print(f"Priority: {handover.priority}")
    print(f"Status: {handover.status.value}")
    
    print("\n💬 Mensagem para cliente:")
    print(get_handover_message_for_customer(handover.reason))
    
    print("\n👨‍💼 Mensagem para atendente:")
    print(get_handover_message_for_agent(handover))

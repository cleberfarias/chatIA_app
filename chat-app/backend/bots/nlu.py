"""Natural Language Understanding - Detecção de Intenções.

Este módulo detecta automaticamente a intenção do usuário sem necessidade
de comandos explícitos como @agente ou /comando.

Suporta dois modos:
1. Pattern matching (rápido, sem custo, offline)
2. GPT (mais preciso, requer API key, online)
"""

import os
import re
import json
import httpx
from typing import Optional
from dataclasses import dataclass, asdict
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_NLU_MODEL", "gpt-4o-mini")  # Modelo mais barato para NLU
USE_GPT_NLU = os.getenv("USE_GPT_NLU", "false").lower() == "true"


@dataclass
class Intent:
    """Representa uma intenção detectada."""
    name: str
    confidence: float
    keywords_matched: list[str]
    suggested_agent: Optional[str] = None
    suggested_action: Optional[str] = None
    method: str = "pattern"  # "pattern" ou "gpt"
    
    def dict(self):
        """Converte para dicionário."""
        return asdict(self)


# Padrões de intenção para CLIENTES
CUSTOMER_INTENTS = {
    "greeting": {
        "keywords": ["olá", "oi", "bom dia", "boa tarde", "boa noite", "hey", "opa"],
        "agent": None,
        "action": "greet_customer"
    },
    "purchase": {
        "keywords": ["quero comprar", "preciso comprar", "quanto custa", "preço", 
                     "valor", "orçamento", "produto", "vender"],
        "agent": "vendedor",
        "action": "start_purchase_flow"
    },
    "scheduling": {
        "keywords": ["agendar", "marcar", "reunião", "meeting", "consulta", 
                     "horário disponível", "agenda", "disponibilidade"],
        "agent": "sdr",
        "action": "start_scheduling_flow"
    },
    "legal": {
        "keywords": ["advogado", "jurídico", "contrato", "processo", "ação judicial",
                     "direito", "lei", "legal"],
        "agent": "advogado",
        "action": "forward_to_legal"
    },
    "technical_support": {
        "keywords": ["erro", "bug", "não funciona", "problema técnico", "código",
                     "programação", "sistema caiu", "travou"],
        "agent": "tech",
        "action": "start_support_ticket"
    },
    "complaint": {
        "keywords": ["reclamação", "insatisfeito", "péssimo", "ruim", "problema",
                     "não gostei", "decepcionado"],
        "agent": "supervisor",
        "action": "escalate_to_supervisor"
    },
    "cancel": {
        "keywords": ["cancelar", "desistir", "não quero mais", "remover pedido"],
        "agent": "vendedor",
        "action": "cancel_order"
    },
    "human_handover": {
        "keywords": ["falar com humano", "atendente", "pessoa real", "humano",
                     "transferir", "não entendi"],
        "agent": None,
        "action": "handover_to_human"
    },
}

# Padrões de intenção para ATENDENTES (uso interno)
AGENT_INTENTS = {
    "search_info": {
        "keywords": ["@guru", "buscar", "informação sobre", "consultar", "verificar"],
        "action": "query_bot"
    },
    "create_order": {
        "keywords": ["criar pedido", "registrar venda", "novo pedido", "fechar venda"],
        "action": "create_order"
    },
    "check_status": {
        "keywords": ["status", "andamento", "verificar pedido", "acompanhar"],
        "action": "check_order_status"
    },
    "schedule_meeting": {
        "keywords": ["agendar reunião", "marcar meeting", "agendar demo"],
        "action": "schedule_with_calendar"
    },
    "escalate": {
        "keywords": ["escalar", "supervisor", "gerente", "urgente"],
        "action": "escalate"
    },
}


async def detect_intent_with_gpt(text: str, speaker: str = "customer") -> Optional[Intent]:
    """
    Detecta intenção usando GPT (mais preciso, requer API key).
    
    Args:
        text: Texto a ser analisado
        speaker: "customer" ou "agent"
        
    Returns:
        Intent detectado ou None se houver erro
    """
    if not OPENAI_API_KEY:
        return None
    
    intents = CUSTOMER_INTENTS if speaker == "customer" else AGENT_INTENTS
    intent_names = list(intents.keys())
    
    # Monta descrição das intenções para o GPT
    intent_descriptions = []
    for name, data in intents.items():
        keywords = ", ".join(data["keywords"][:5])  # Primeiras 5 keywords
        intent_descriptions.append(f"- {name}: {keywords}")
    
    prompt = f"""Analise a seguinte mensagem e identifique a intenção do usuário.

Mensagem: "{text}"

Intenções possíveis:
{chr(10).join(intent_descriptions)}

Retorne APENAS um JSON válido no formato:
{{
  "intent": "nome_da_intencao",
  "confidence": 0.95,
  "reasoning": "breve explicação"
}}

Se a mensagem não se encaixar em nenhuma intenção, use "general" com confidence baixa."""
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENAI_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": OPENAI_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.3,  # Mais determinístico
                    "max_tokens": 150
                }
            )
            
            if response.status_code != 200:
                print(f"❌ GPT NLU error: {response.status_code} - {response.text}")
                return None
            
            result = response.json()
            content = result["choices"][0]["message"]["content"].strip()
            
            # Remove markdown se houver
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            
            data = json.loads(content)
            intent_name = data.get("intent", "general")
            confidence = float(data.get("confidence", 0.5))
            reasoning = data.get("reasoning", "")
            
            # Valida se a intenção existe
            if intent_name not in intents and intent_name != "general":
                intent_name = "general"
                confidence = 0.3
            
            intent_data = intents.get(intent_name, {})
            
            return Intent(
                name=intent_name,
                confidence=round(confidence, 2),
                keywords_matched=[reasoning] if reasoning else [],
                suggested_agent=intent_data.get("agent"),
                suggested_action=intent_data.get("action"),
                method="gpt"
            )
            
    except json.JSONDecodeError as e:
        print(f"❌ GPT NLU JSON parse error: {e} - Content: {content}")
        return None
    except Exception as e:
        print(f"❌ GPT NLU error: {e}")
        return None


def detect_intent_with_patterns(text: str, speaker: str = "customer") -> Intent:
    """
    Detecta a intenção do texto baseado em palavras-chave (pattern matching).
    
    Args:
        text: Texto a ser analisado
        speaker: "customer" (cliente) ou "agent" (atendente)
        
    Returns:
        Intent object com intenção detectada e confiança
    """
    text_lower = text.lower().strip()
    
    # Escolhe conjunto de intenções baseado no speaker
    intents = CUSTOMER_INTENTS if speaker == "customer" else AGENT_INTENTS
    
    best_match = None
    max_matches = 0
    matched_keywords = []
    
    # Procura por matches de keywords
    for intent_name, intent_data in intents.items():
        keywords = intent_data["keywords"]
        matches = [kw for kw in keywords if kw in text_lower]
        
        if len(matches) > max_matches:
            max_matches = len(matches)
            best_match = intent_name
            matched_keywords = matches
    
    # Se não encontrou nenhum match, retorna intent genérico
    if not best_match:
        return Intent(
            name="general",
            confidence=0.0,
            keywords_matched=[],
            suggested_agent="guru" if speaker == "customer" else None,
            suggested_action="general_query"
        )
    
    # Calcula confiança (simples: quantidade de keywords / total de palavras)
    words_count = len(text_lower.split())
    confidence = min(1.0, (max_matches / max(words_count, 1)) * 2)
    
    intent_data = intents[best_match]
    
    return Intent(
        name=best_match,
        confidence=round(confidence, 2),
        keywords_matched=matched_keywords,
        suggested_agent=intent_data.get("agent"),
        suggested_action=intent_data.get("action"),
        method="pattern"
    )


async def detect_intent(text: str, speaker: str = "customer", use_gpt: Optional[bool] = None) -> Intent:
    """
    Detecta intenção do texto. Usa GPT se configurado, senão usa pattern matching.
    
    Args:
        text: Texto a ser analisado
        speaker: "customer" ou "agent"
        use_gpt: Force usar GPT (True) ou patterns (False). None = usa configuração
        
    Returns:
        Intent detectado
    """
    # Determina qual método usar
    should_use_gpt = use_gpt if use_gpt is not None else USE_GPT_NLU
    
    # Tenta GPT primeiro se habilitado
    if should_use_gpt and OPENAI_API_KEY:
        gpt_intent = await detect_intent_with_gpt(text, speaker)
        if gpt_intent:
            print(f"🤖 NLU via GPT: {gpt_intent.name} (confidence: {gpt_intent.confidence})")
            return gpt_intent
        else:
            print(f"⚠️  GPT NLU falhou, usando pattern matching como fallback")
    
    # Fallback para pattern matching
    pattern_intent = detect_intent_with_patterns(text, speaker)
    print(f"🔍 NLU via patterns: {pattern_intent.name} (confidence: {pattern_intent.confidence})")
    return pattern_intent


def requires_human_handover(intent: Intent, confidence_threshold: float = 0.3) -> bool:
    """
    Verifica se a mensagem requer transferência para humano.
    
    Args:
        intent: Intent detectado
        confidence_threshold: Confiança mínima para bot continuar
        
    Returns:
        True se deve transferir para humano
    """
    # Intenções que sempre vão para humano
    critical_intents = ["human_handover", "complaint"]
    
    if intent.name in critical_intents:
        return True
    
    # Se confiança muito baixa, transfere para humano
    if intent.confidence < confidence_threshold:
        return True
    
    return False


def suggest_response_template(intent: Intent) -> str:
    """
    Sugere template de resposta baseado na intenção.
    
    Útil para atendentes humanos terem sugestões rápidas.
    """
    templates = {
        "greeting": "Olá! Como posso ajudar você hoje?",
        "purchase": "Ótimo! Vou ajudar com sua compra. Qual produto te interessa?",
        "scheduling": "Vou verificar os horários disponíveis. Qual seria o melhor dia/horário para você?",
        "legal": "Entendo sua questão jurídica. Vou conectar você com nosso departamento legal.",
        "technical_support": "Vou ajudar a resolver seu problema técnico. Pode descrever o erro em mais detalhes?",
        "complaint": "Lamento pelo problema. Vou transferir para nosso supervisor resolver isso com prioridade.",
        "cancel": "Entendo que deseja cancelar. Pode me informar o número do pedido?",
    }
    
    return templates.get(intent.name, "Como posso ajudar?")


# Exemplo de uso
if __name__ == "__main__":
    import asyncio
    
    async def test_nlu():
        # Teste com mensagens de cliente
        test_messages = [
            ("Olá, quero comprar notebooks", "customer"),
            ("Preciso agendar uma reunião para amanhã", "customer"),
            ("Meu código deu erro 500", "customer"),
            ("Quero falar com um humano", "customer"),
            ("@guru qual a política de garantia?", "agent"),
        ]
        
        print(f"\n{'='*60}")
        print(f"🧪 TESTANDO NLU - Modo: {'GPT' if USE_GPT_NLU else 'Pattern Matching'}")
        print(f"{'='*60}\n")
        
        for msg, speaker in test_messages:
            intent = await detect_intent(msg, speaker)
            print(f"\n📨 Mensagem: '{msg}'")
            print(f"👤 Speaker: {speaker}")
            print(f"🎯 Intent: {intent.name}")
            print(f"📊 Confidence: {intent.confidence}")
            print(f"🔧 Method: {intent.method}")
            print(f"🤖 Agent: {intent.suggested_agent}")
            print(f"⚡ Action: {intent.suggested_action}")
            print(f"🔑 Keywords: {intent.keywords_matched}")
            print(f"👨 Handover: {requires_human_handover(intent)}")
    
    asyncio.run(test_nlu())

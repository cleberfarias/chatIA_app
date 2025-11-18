"""Módulo de integração com ChatGPT/OpenAI."""

import os
from typing import Optional
from collections import defaultdict, deque
import httpx
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"

# Contexto do Guru
SYSTEM_PROMPT = """Você é o Guru 🧠, um assistente de chat muito amigável e sábio, conversando em um grupo de mensagens.

COMPORTAMENTO:
- Seja caloroso, empático e use uma linguagem natural e informal
- Use emojis de forma moderada para expressar emoção 😊
- Chame as pessoas pelo nome quando apropriado (o nome será fornecido)
- Responda como se estivesse digitando naturalmente, não como uma IA formal
- Use expressões coloquiais brasileiras (tipo: "beleza?", "massa!", "que legal!", etc)
- Às vezes use interjeições: "Ah!", "Hmmm...", "Opa!", "Caramba!"
- Mantenha respostas concisas mas completas (2-4 linhas geralmente)
- Lembre-se do contexto da conversa para respostas mais naturais
- Se não souber algo, admita de forma amigável: "Poxa, essa eu não sei..." 

ESTILO DE ESCRITA:
- Natural e conversacional, como uma pessoa real
- Evite ser muito formal ou robotizado
- Não use "Claro!", "Com certeza!" em excesso
- Varie suas expressões e formas de responder
- Seja autêntico e genuíno nas respostas

FORMATAÇÃO DE CÓDIGO:
Quando precisar mostrar código, SEMPRE use blocos de código markdown com a linguagem especificada.
Para códigos de múltiplas linhas, use:
```python
def exemplo():
    return "código bem formatado"
```

Para códigos inline de 1 linha, use backticks simples: `variavel = valor`

NUNCA envie código em uma única linha corrida sem formatação.
SEMPRE mantenha a indentação e quebras de linha do código."""

# Armazena histórico de conversa por usuário (máximo 10 mensagens)
# user_id -> deque de {"role": "user"/"assistant", "content": "texto"}
conversation_history: dict[str, deque] = defaultdict(lambda: deque(maxlen=10))

# Modos de personalidade do Guru
GURU_MODES = {
    "casual": """Seja super descontraído, use gírias, emojis frequentes e linguagem bem informal. 
Fale como um amigo próximo em uma conversa de bar. Use expressões tipo: "mano", "cara", "brother", "vlw", "tmj".""",
    
    "profissional": """Seja educado, formal mas ainda amigável. Use linguagem técnica quando apropriado.
Evite gírias excessivas. Mantenha tom respeitoso e corporativo, mas não robotizado.""",
    
    "tecnico": """Seja preciso, detalhado e técnico. Forneça explicações aprofundadas com terminologia adequada.
Use exemplos de código quando útil. Foque em precisão e completude das respostas."""
}

# Preferências do usuário: modo, idioma, etc
# user_id -> {"mode": "casual", "language": "pt"}
user_preferences: dict[str, dict] = defaultdict(lambda: {"mode": "casual", "language": "pt"})


async def ask_chatgpt(message: str, user_id: str = "anonymous", user_name: str = "Amigo") -> str:
    """
    Envia uma mensagem para o ChatGPT e retorna a resposta.
    Mantém histórico de conversa por usuário.
    
    Args:
        message: Mensagem do usuário
        user_id: ID do usuário (para manter contexto separado)
        user_name: Nome do usuário (para personalizar resposta)
        
    Returns:
        Resposta do ChatGPT
    """
    if not OPENAI_API_KEY:
        return "❌ Bot de IA não configurado. Configure OPENAI_API_KEY nas variáveis de ambiente."
    
    # Obtém preferências do usuário
    prefs = user_preferences[user_id]
    mode_instruction = GURU_MODES.get(prefs["mode"], GURU_MODES["casual"])
    
    # Prepara as mensagens com modo personalizado
    system_prompt = f"{SYSTEM_PROMPT}\n\nMODO ATUAL: {prefs['mode'].upper()}\n{mode_instruction}"
    messages = [{"role": "system", "content": system_prompt}]
    
    # Adiciona histórico do usuário (últimas mensagens)
    user_history = conversation_history[user_id]
    messages.extend(list(user_history))
    
    # Adiciona contexto do nome do usuário na mensagem
    contextualized_message = f"[Usuário: {user_name}] {message}"
    messages.append({"role": "user", "content": contextualized_message})
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                OPENAI_API_URL,
                headers={
                    "Authorization": f"Bearer {OPENAI_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": OPENAI_MODEL,
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": 500
                }
            )
            
            if response.status_code != 200:
                error_msg = response.json().get("error", {}).get("message", "Erro desconhecido")
                return f"❌ Erro na API OpenAI: {error_msg}"
            
            data = response.json()
            ai_response = data["choices"][0]["message"]["content"].strip()
            
            # Armazena no histórico do usuário
            user_history.append({"role": "user", "content": message})
            user_history.append({"role": "assistant", "content": ai_response})
            
            return ai_response
            
    except httpx.TimeoutException:
        return "⏱️ Timeout ao conectar com ChatGPT. Tente novamente."
    except Exception as e:
        return f"❌ Erro ao processar resposta: {str(e)}"


def clear_conversation(user_id: str) -> None:
    """
    Limpa o histórico de conversa de um usuário.
    
    Args:
        user_id: ID do usuário
    """
    if user_id in conversation_history:
        conversation_history[user_id].clear()


def get_conversation_count(user_id: str) -> int:
    """
    Retorna o número de mensagens no histórico do usuário.
    
    Args:
        user_id: ID do usuário
        
    Returns:
        Número de mensagens no histórico
    """
    return len(conversation_history[user_id])


def is_ai_question(text: str) -> bool:
    """
    Verifica se a mensagem é uma pergunta para o Guru.
    
    Detecta padrões como:
    - @guru <pergunta>
    - guru, <pergunta>
    - Mensagens com "?" direcionadas ao guru
    
    Args:
        text: Texto da mensagem
        
    Returns:
        True se for uma pergunta para o Guru
    """
    text_lower = text.lower().strip()
    
    # Padrões que indicam uma pergunta ao Guru (incluindo variações de pronúncia)
    triggers = [
        text_lower.startswith("@guru"),
        text_lower.startswith("guru,"),
        text_lower.startswith("guru "),
        text_lower.startswith("hey guru"),
        text_lower.startswith("ei guru"),
        text_lower.startswith("oi guru"),
        # Variações de pronúncia (áudio pode não transcrever perfeitamente)
        text_lower.startswith("@gugu"),
        text_lower.startswith("gugu"),
        # Mantém compatibilidade com @bot (legado)
        text_lower.startswith("@bot"),
        text_lower.startswith("bot,"),
        text_lower.startswith("bot "),
    ]
    
    return any(triggers)


def clean_bot_mention(text: str) -> str:
    """
    Remove menções ao Guru do texto.
    
    Args:
        text: Texto original
        
    Returns:
        Texto limpo sem menções
    """
    text = text.strip()
    
    # Remove prefixos comuns (incluindo variações de transcrição)
    prefixes = [
        "@guru", "guru,", "hey guru", "ei guru", "oi guru", "guru",
        "@gugu", "gugu,", "gugu",
        # Mantém compatibilidade com @bot (legado)
        "@bot", "bot,", "hey bot", "ei bot", "oi bot", "bot",
    ]
    
    for prefix in prefixes:
        if text.lower().startswith(prefix):
            text = text[len(prefix):].strip()
            # Remove vírgula ou dois pontos após o prefixo
            if text.startswith((",", ":")):
                text = text[1:].strip()
            break
    
    return text


def set_user_mode(user_id: str, mode: str) -> str:
    """
    Define o modo de personalidade do Guru para um usuário.
    
    Args:
        user_id: ID do usuário
        mode: Modo desejado (casual, profissional, tecnico)
        
    Returns:
        Mensagem de confirmação
    """
    mode = mode.lower()
    if mode not in GURU_MODES:
        return f"❌ Modo inválido. Escolha: {', '.join(GURU_MODES.keys())}"
    
    user_preferences[user_id]["mode"] = mode
    mode_names = {"casual": "Casual 😎", "profissional": "Profissional 💼", "tecnico": "Técnico 🔧"}
    return f"✅ Modo alterado para: {mode_names[mode]}"


def get_user_mode(user_id: str) -> str:
    """
    Retorna o modo atual do usuário.
    
    Args:
        user_id: ID do usuário
        
    Returns:
        Nome do modo atual
    """
    return user_preferences[user_id]["mode"]


def generate_conversation_summary(user_id: str) -> str:
    """
    Gera um resumo da conversa do usuário.
    
    Args:
        user_id: ID do usuário
        
    Returns:
        Resumo da conversa
    """
    history = conversation_history[user_id]
    if not history:
        return "📭 Não há histórico de conversa ainda."
    
    user_msgs = [msg for msg in history if msg["role"] == "user"]
    assistant_msgs = [msg for msg in history if msg["role"] == "assistant"]
    
    summary = f"📊 **Resumo da Conversa:**\n\n"
    summary += f"💬 Total de mensagens: {len(history)}\n"
    summary += f"❓ Suas perguntas: {len(user_msgs)}\n"
    summary += f"💡 Minhas respostas: {len(assistant_msgs)}\n\n"
    
    if user_msgs:
        summary += "🔍 Últimos tópicos discutidos:\n"
        for i, msg in enumerate(list(user_msgs)[-3:], 1):
            preview = msg["content"][:50] + "..." if len(msg["content"]) > 50 else msg["content"]
            summary += f"{i}. {preview}\n"
    
    return summary


def suggest_follow_up_questions(last_response: str, topic: str) -> list[str]:
    """
    Gera sugestões de perguntas relacionadas ao tópico.
    
    Args:
        last_response: Última resposta do Guru
        topic: Tópico da conversa
        
    Returns:
        Lista de perguntas sugeridas
    """
    # Sugestões genéricas baseadas em contexto
    suggestions = [
        f"Pode explicar mais sobre {topic}?",
        "Tem algum exemplo prático?",
        "Quais são as melhores práticas?"
    ]
    
    return suggestions[:2]  # Retorna apenas 2 sugestões

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

# Contexto do bot
SYSTEM_PROMPT = """Você é um assistente de chat muito amigável e humano, conversando em um grupo de mensagens.

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
    
    # Prepara as mensagens
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    
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
    Verifica se a mensagem é uma pergunta para o bot de IA.
    
    Detecta padrões como:
    - @bot <pergunta>
    - bot, <pergunta>
    - Mensagens com "?" direcionadas ao bot
    
    Args:
        text: Texto da mensagem
        
    Returns:
        True se for uma pergunta para o bot
    """
    text_lower = text.lower().strip()
    
    # Padrões que indicam uma pergunta ao bot (incluindo variações de pronúncia)
    triggers = [
        text_lower.startswith("@bot"),
        text_lower.startswith("bot,"),
        text_lower.startswith("bot "),
        text_lower.startswith("hey bot"),
        text_lower.startswith("ei bot"),
        text_lower.startswith("oi bot"),
        # Variações de pronúncia (áudio pode não transcrever perfeitamente)
        text_lower.startswith("bod"),
        text_lower.startswith("@bod"),
        text_lower.startswith("bod,"),
        text_lower.startswith("bote"),
        text_lower.startswith("@bote"),
    ]
    
    return any(triggers)


def clean_bot_mention(text: str) -> str:
    """
    Remove menções ao bot do texto.
    
    Args:
        text: Texto original
        
    Returns:
        Texto limpo sem menções
    """
    text = text.strip()
    
    # Remove prefixos comuns (incluindo variações de transcrição)
    prefixes = [
        "@bot", "bot,", "hey bot", "ei bot", "oi bot", "bot",
        "@bod", "bod,", "bod", "@bote", "bote,", "bote"
    ]
    
    for prefix in prefixes:
        if text.lower().startswith(prefix):
            text = text[len(prefix):].strip()
            # Remove vírgula ou dois pontos após o prefixo
            if text.startswith((",", ":")):
                text = text[1:].strip()
            break
    
    return text

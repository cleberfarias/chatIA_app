"""Sistema de Agentes IA Especializados.

Cada agente tem personalidade, expertise e comandos específicos.
Uso: @advogado, @vendedor, @guru, etc.
"""

import os
from typing import Optional
from collections import defaultdict, deque
import httpx
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"


class Agent:
    """Classe base para agentes IA especializados."""
    
    def __init__(
        self,
        name: str,
        emoji: str,
        system_prompt: str,
        specialties: list[str],
        commands: dict[str, str],
        openai_api_key: Optional[str] = None,
        openai_account: Optional[str] = None
    ):
        self.name = name
        self.emoji = emoji
        self.system_prompt = system_prompt
        self.specialties = specialties
        self.commands = commands
        self.openai_api_key = openai_api_key or OPENAI_API_KEY
        self.openai_account = openai_account
        # Histórico de conversa por usuário (máximo 10 mensagens)
        self.conversation_history: dict[str, deque] = defaultdict(lambda: deque(maxlen=10))
    
    def get_display_name(self) -> str:
        """Retorna nome com emoji para exibição."""
        return f"{self.name} {self.emoji}"
    
    def clear_history(self, user_id: str) -> None:
        """Limpa histórico de conversa do usuário."""
        if user_id in self.conversation_history:
            self.conversation_history[user_id].clear()
    
    def get_history_count(self, user_id: str) -> int:
        """Retorna número de mensagens no histórico."""
        return len(self.conversation_history[user_id])
    
    async def ask(self, message: str, user_id: str, user_name: str) -> str:
        """
        Envia pergunta ao agente e retorna resposta.
        
        Args:
            message: Mensagem do usuário
            user_id: ID do usuário
            user_name: Nome do usuário
            
        Returns:
            Resposta do agente
        """
        if not self.openai_api_key:
            return f"❌ {self.name} não configurado. Configure OPENAI_API_KEY."
        
        # Prepara mensagens
        messages = [{"role": "system", "content": self.system_prompt}]
        
        # Adiciona histórico
        user_history = self.conversation_history[user_id]
        messages.extend(list(user_history))
        
        # Adiciona contexto do usuário
        contextualized_message = f"[Usuário: {user_name}] {message}"
        messages.append({"role": "user", "content": contextualized_message})
        
        try:
            headers = {
                "Authorization": f"Bearer {self.openai_api_key}",
                "Content-Type": "application/json"
            }
            
            # Adiciona Organization ID se fornecido
            if self.openai_account:
                headers["OpenAI-Organization"] = self.openai_account
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    OPENAI_API_URL,
                    headers=headers,
                    json={
                        "model": OPENAI_MODEL,
                        "messages": messages,
                        "temperature": 0.7,
                        "max_tokens": 600
                    }
                )
                
                if response.status_code != 200:
                    error_msg = response.json().get("error", {}).get("message", "Erro desconhecido")
                    return f"❌ Erro na API: {error_msg}"
                
                data = response.json()
                ai_response = data["choices"][0]["message"]["content"].strip()
                
                # Armazena no histórico
                user_history.append({"role": "user", "content": message})
                user_history.append({"role": "assistant", "content": ai_response})
                
                return ai_response
                
        except httpx.TimeoutException:
            return f"⏱️ {self.name} demorou para responder. Tente novamente."
        except Exception as e:
            return f"❌ Erro: {str(e)}"


# =====================================================
# DEFINIÇÃO DOS AGENTES ESPECIALIZADOS
# =====================================================

AGENT_GURU = Agent(
    name="Guru",
    emoji="🧠",
    system_prompt="""Você é o Guru 🧠, um assistente técnico e educacional muito sábio.

EXPERTISE:
- Programação e desenvolvimento de software
- Explicações técnicas detalhadas
- Resolução de problemas de código
- Arquitetura e design patterns
- Melhores práticas de desenvolvimento

COMPORTAMENTO:
- Seja didático e paciente ao explicar
- Use exemplos práticos e código quando apropriado
- Forneça referências e fontes quando possível
- Admita quando não souber algo
- Use emojis de forma moderada 🤓

FORMATAÇÃO:
- Use blocos de código markdown com linguagem especificada
- Mantenha respostas concisas mas completas (3-5 linhas)
- Para código: sempre use ```linguagem e mantenha indentação""",
    specialties=[
        "Programação",
        "Arquitetura de Software",
        "Debugging",
        "Code Review",
        "Documentação Técnica"
    ],
    commands={
        "/ajuda": "Lista comandos do Guru",
        "/codigo": "Gera exemplo de código",
        "/debug": "Ajuda a debugar problema",
        "/review": "Faz review de código",
        "/docs": "Gera documentação"
    }
)

AGENT_ADVOGADO = Agent(
    name="Dr. Advocatus",
    emoji="⚖️",
    system_prompt="""Você é Dr. Advocatus ⚖️, um advogado especializado e consultor jurídico.

EXPERTISE:
- Direito Civil, Trabalhista e Consumidor
- Análise de contratos e documentos
- Orientação sobre processos legais
- Direitos e deveres do cidadão
- Legislação brasileira

COMPORTAMENTO:
- Seja formal, preciso e profissional
- Sempre cite a legislação aplicável (CLT, Código Civil, CDC, etc)
- Use linguagem técnica mas acessível
- Sempre avise que é orientação geral, não substitui advogado pessoal
- Seja ético e imparcial

DISCLAIMER:
Sempre inclua: "_Importante: Esta é uma orientação geral. Para casos específicos, consulte um advogado pessoalmente._"

FORMATAÇÃO:
- Use parágrafos curtos para facilitar leitura
- Cite artigos de lei quando aplicável
- Use emojis legais moderadamente ⚖️📜""",
    specialties=[
        "Direito do Consumidor",
        "Direito Trabalhista",
        "Contratos",
        "Direito Civil",
        "Orientação Jurídica Geral"
    ],
    commands={
        "/ajuda": "Lista comandos do Dr. Advocatus",
        "/analise": "Analisa situação jurídica",
        "/contrato": "Revisa pontos de contrato",
        "/direitos": "Explica direitos sobre tema",
        "/legislacao": "Busca legislação aplicável"
    }
)

AGENT_VENDEDOR = Agent(
    name="Sales Pro",
    emoji="💼",
    system_prompt="""Você é Sales Pro 💼, um especialista em vendas e negociação de alta performance.

EXPERTISE:
- Técnicas de vendas consultivas (SPIN, BANT, Challenger)
- Prospecção e qualificação de leads
- Negociação e fechamento de deals
- Gestão de objeções
- CRM e pipeline de vendas

COMPORTAMENTO:
- Seja motivador, energético e positivo 🚀
- Forneça dicas práticas e acionáveis
- Use exemplos reais de situações de venda
- Ensine frameworks e metodologias comprovadas
- Seja direto e focado em resultados

ESTILO:
- Use linguagem corporativa mas acessível
- Inclua perguntas reflexivas para o usuário
- Sugira scripts e abordagens práticas
- Compartilhe métricas e KPIs importantes

FORMATAÇÃO:
- Use bullet points para listas de dicas
- Negrito para destacar conceitos-chave
- Emojis de negócios: 💼 📊 🎯 💰 🤝""",
    specialties=[
        "Prospecção B2B",
        "Técnicas de Fechamento",
        "Gestão de Objeções",
        "Follow-up Estratégico",
        "Vendas Consultivas"
    ],
    commands={
        "/ajuda": "Lista comandos do Sales Pro",
        "/script": "Gera script de vendas",
        "/objecao": "Como lidar com objeção",
        "/pitch": "Melhora seu pitch",
        "/followup": "Estratégia de follow-up"
    }
)

AGENT_MEDICO = Agent(
    name="Dr. Health",
    emoji="🩺",
    system_prompt="""Você é Dr. Health 🩺, um assistente médico educacional.

EXPERTISE:
- Informações gerais sobre saúde e bem-estar
- Explicações sobre sintomas comuns
- Orientações sobre hábitos saudáveis
- Primeiros socorros básicos
- Prevenção de doenças

COMPORTAMENTO:
- Seja cauteloso e responsável
- SEMPRE recomende procurar médico para diagnóstico real
- Forneça informações educacionais, não diagnósticos
- Use linguagem acessível, evite jargões excessivos
- Seja empático e acolhedor

DISCLAIMER OBRIGATÓRIO:
SEMPRE inclua: "⚠️ _Esta é uma informação educacional. Consulte um médico para diagnóstico e tratamento adequados. Em emergências, ligue 192 (SAMU)._"

LIMITAÇÕES:
- NÃO faça diagnósticos
- NÃO prescreva medicamentos
- NÃO substitua consulta médica
- Encoraje sempre a busca por profissional

FORMATAÇÃO:
- Use emojis médicos: 🩺 💊 🏥 🚑
- Separe informações em tópicos claros""",
    specialties=[
        "Educação em Saúde",
        "Hábitos Saudáveis",
        "Primeiros Socorros",
        "Prevenção",
        "Bem-estar"
    ],
    commands={
        "/ajuda": "Lista comandos do Dr. Health",
        "/sintoma": "Informações sobre sintoma",
        "/prevencao": "Dicas de prevenção",
        "/emergencia": "Primeiros socorros",
        "/habitos": "Hábitos saudáveis"
    }
)

AGENT_PSICOLOGO = Agent(
    name="MindCare",
    emoji="🧘",
    system_prompt="""Você é MindCare 🧘, um assistente de apoio emocional e bem-estar mental.

EXPERTISE:
- Técnicas de gerenciamento de ansiedade e estresse
- Mindfulness e meditação
- Inteligência emocional
- Comunicação não-violenta
- Autocuidado e autoconhecimento

COMPORTAMENTO:
- Seja empático, acolhedor e não-julgador
- Use escuta ativa e validação emocional
- Faça perguntas reflexivas gentis
- Ofereça técnicas práticas de respiração/relaxamento
- Respeite os limites éticos

ABORDAGEM:
- Baseie-se em CBT (Terapia Cognitivo-Comportamental)
- Sugira técnicas validadas cientificamente
- Normalize sentimentos e experiências
- Encoraje busca por ajuda profissional quando necessário

DISCLAIMER:
SEMPRE inclua quando detectar sofrimento intenso: "💚 _Se estiver em crise emocional, ligue CVV 188 (24h). Considere procurar um psicólogo ou psiquiatra._"

LIMITAÇÕES:
- NÃO faça diagnósticos de transtornos mentais
- NÃO substitua terapia profissional
- Encoraje ajuda profissional em casos sérios

FORMATAÇÃO:
- Use tom calmo e pausado
- Emojis gentis: 🧘 💚 🌱 🌈 ☮️""",
    specialties=[
        "Gestão de Ansiedade",
        "Mindfulness",
        "Autoconhecimento",
        "Comunicação Assertiva",
        "Autocuidado"
    ],
    commands={
        "/ajuda": "Lista comandos do MindCare",
        "/respiracao": "Exercício de respiração",
        "/ansiedade": "Técnicas para ansiedade",
        "/diario": "Dicas de journaling",
        "/autocuidado": "Práticas de autocuidado"
    }
)


# =====================================================
# REGISTRO DE AGENTES
# =====================================================

AGENTS_REGISTRY: dict[str, Agent] = {
    "guru": AGENT_GURU,
    "advogado": AGENT_ADVOGADO,
    "vendedor": AGENT_VENDEDOR,
    "medico": AGENT_MEDICO,
    "psicologo": AGENT_PSICOLOGO,
}


# =====================================================
# CUSTOM BOTS (Criados pelo usuário)
# =====================================================

# Armazena bots personalizados em memória (user_id -> {bot_name -> Agent})
custom_bots_registry: dict[str, dict[str, Agent]] = {}


def create_custom_agent(
    user_id: str,
    name: str,
    emoji: str,
    system_prompt: str,
    specialties: list[str],
    openai_api_key: str,
    openai_account: Optional[str] = None
) -> Agent:
    """
    Cria um agente personalizado para o usuário.
    
    Args:
        user_id: ID do usuário criador
        name: Nome do bot
        emoji: Emoji do bot
        system_prompt: Prompt customizado
        specialties: Lista de especialidades
        openai_api_key: Chave de API da OpenAI
        openai_account: ID da organização OpenAI (opcional)
        
    Returns:
        Instância do agente customizado
    """
    # Cria comandos padrão
    commands = {
        "/ajuda": f"Lista comandos do {name}",
        "/limpar": "Limpar histórico",
        "/contexto": "Ver status da conversa"
    }
    
    # Cria agente com credenciais personalizadas
    agent = Agent(
        name=name,
        emoji=emoji,
        system_prompt=system_prompt,
        specialties=specialties,
        commands=commands,
        openai_api_key=openai_api_key,
        openai_account=openai_account
    )
    
    # Armazena no registro do usuário
    if user_id not in custom_bots_registry:
        custom_bots_registry[user_id] = {}
    
    bot_key = name.lower().replace(' ', '')
    custom_bots_registry[user_id][bot_key] = agent
    
    print(f"✅ Bot personalizado criado: {name} {emoji} (user: {user_id})")
    return agent


def get_custom_agent(user_id: str, agent_name: str) -> Optional[Agent]:
    """
    Retorna bot personalizado do usuário.
    
    Args:
        user_id: ID do usuário
        agent_name: Nome do bot
        
    Returns:
        Instância do bot ou None
    """
    if user_id not in custom_bots_registry:
        return None
    
    bot_key = agent_name.lower().replace(' ', '')
    return custom_bots_registry[user_id].get(bot_key)


def list_custom_agents(user_id: str) -> list[Agent]:
    """
    Lista todos os bots personalizados do usuário.
    
    Args:
        user_id: ID do usuário
        
    Returns:
        Lista de agentes personalizados
    """
    if user_id not in custom_bots_registry:
        return []
    
    return list(custom_bots_registry[user_id].values())


def delete_custom_agent(user_id: str, agent_name: str) -> bool:
    """
    Deleta bot personalizado.
    
    Args:
        user_id: ID do usuário
        agent_name: Nome do bot
        
    Returns:
        True se deletado com sucesso
    """
    if user_id not in custom_bots_registry:
        return False
    
    bot_key = agent_name.lower().replace(' ', '')
    if bot_key in custom_bots_registry[user_id]:
        del custom_bots_registry[user_id][bot_key]
        print(f"🗑️ Bot personalizado deletado: {agent_name} (user: {user_id})")
        return True
    
    return False


# =====================================================
# FUNÇÕES AUXILIARES
# =====================================================

def get_agent(agent_name: str, user_id: str = None) -> Optional[Agent]:
    """
    Retorna agente pelo nome (global ou personalizado).
    
    Args:
        agent_name: Nome do agente (guru, advogado, vendedor, etc)
        user_id: ID do usuário (para buscar bots personalizados)
        
    Returns:
        Instância do agente ou None se não encontrado
    """
    # Primeiro tenta bot personalizado do usuário
    if user_id:
        custom_agent = get_custom_agent(user_id, agent_name)
        if custom_agent:
            return custom_agent
    
    # Depois tenta agentes globais
    return AGENTS_REGISTRY.get(agent_name.lower())


def list_all_agents() -> str:
    """
    Lista todos os agentes disponíveis.
    
    Returns:
        String formatada com lista de agentes
    """
    result = "🤖 **Agentes IA Especializados Disponíveis:**\n\n"
    
    for agent in AGENTS_REGISTRY.values():
        result += f"**@{agent.name.lower().replace(' ', '')}** {agent.emoji}\n"
        result += f"└─ Especialidades: {', '.join(agent.specialties[:3])}\n\n"
    
    result += "\n💡 _Use @agente para iniciar conversa_\n"
    result += "📋 _Use @agente /ajuda para ver comandos_"
    
    return result


def detect_agent_mention(text: str) -> Optional[str]:
    """
    Detecta se mensagem menciona algum agente.
    
    Args:
        text: Texto da mensagem
        
    Returns:
        Nome do agente mencionado ou None
    """
    text_lower = text.lower().strip()
    
    # Verifica menções diretas com @
    for agent_key in AGENTS_REGISTRY.keys():
        if text_lower.startswith(f"@{agent_key}"):
            return agent_key
    
    # Verifica nomes alternativos
    aliases = {
        "advogado": ["@advogada", "@dr", "@dra", "@advocatus"],
        "vendedor": ["@vendedora", "@sales", "@comercial"],
        "medico": ["@medica", "@doutor", "@doutora", "@health"],
        "psicologo": ["@psicologa", "@terapeuta", "@mindcare"],
    }
    
    for agent_key, agent_aliases in aliases.items():
        if any(text_lower.startswith(alias) for alias in agent_aliases):
            return agent_key
    
    return None


def clean_agent_mention(text: str, agent_name: str) -> str:
    """
    Remove menção do agente do texto.
    
    Args:
        text: Texto original
        agent_name: Nome do agente para remover
        
    Returns:
        Texto limpo
    """
    text = text.strip()
    
    # Remove @agente do início
    prefixes = [f"@{agent_name}", f"@{agent_name.replace(' ', '')}"]
    
    for prefix in prefixes:
        if text.lower().startswith(prefix):
            text = text[len(prefix):].strip()
            if text.startswith((",", ":")):
                text = text[1:].strip()
            break
    
    return text


async def handle_agent_command(
    agent: Agent,
    command: str,
    user_id: str,
    user_name: str
) -> str:
    """
    Processa comando específico de um agente.
    
    Args:
        agent: Instância do agente
        command: Comando a executar
        user_id: ID do usuário
        user_name: Nome do usuário
        
    Returns:
        Resposta do comando
    """
    command_lower = command.lower().strip()
    
    # Comando universal: /ajuda
    if command_lower == "/ajuda":
        result = f"📚 **Comandos do {agent.get_display_name()}:**\n\n"
        for cmd, desc in agent.commands.items():
            result += f"**{cmd}** - {desc}\n"
        result += f"\n💡 _Exemplo: @{agent.name.lower()} {list(agent.commands.keys())[1]} sua pergunta_"
        return result
    
    # Comando universal: /limpar
    if command_lower == "/limpar":
        agent.clear_history(user_id)
        return f"🗑️ Histórico limpo! Começando conversa do zero com {agent.get_display_name()}"
    
    # Comando universal: /contexto
    if command_lower == "/contexto":
        count = agent.get_history_count(user_id)
        return f"📊 **Contexto {agent.get_display_name()}:**\n\n💬 Mensagens no histórico: {count}/10\n🎯 Especialidades: {', '.join(agent.specialties)}"
    
    # Comandos específicos: delega para o agente
    if command_lower in agent.commands:
        prompt = f"O usuário solicitou o comando {command_lower}. {agent.commands[command_lower]}"
        return await agent.ask(prompt, user_id, user_name)
    
    return f"❓ Comando desconhecido. Use **@{agent.name.lower()} /ajuda** para ver comandos disponíveis."

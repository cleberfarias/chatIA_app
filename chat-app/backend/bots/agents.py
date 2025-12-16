"""Sistema de Agentes IA Especializados.

Cada agente tem personalidade, expertise e comandos específicos.
Uso: via Agent Panels (ex.: advogado, vendedor, guru). Inline @agent usages are deprecated.
"""

import os
from typing import Optional, List, Dict, Any
from collections import defaultdict, deque
from datetime import datetime, timezone
import httpx
from dotenv import load_dotenv

from database import custom_bots_collection

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
        # Permite que este agente crie eventos diretamente no Google Calendar
        # (padrão: False). O SDR deve ter True.
        self.allow_calendar_creation: bool = False
        # Se True, este agente pode criar eventos automaticamente sem confirmação do atendente
        self.allow_calendar_auto_create: bool = False
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
    
    async def ask_with_context(
        self,
        message: str,
        user_id: str,
        user_name: str,
        contact_id: Optional[str] = None,
        conversation_context: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        Envia pergunta ao agente COM contexto da conversa principal.
        
        Por que criar método separado?
        - Mantém compatibilidade com ask() original
        - Permite usar contexto opcionalmente
        - Facilita A/B testing (com/sem contexto)
        
        Args:
            message: Pergunta do usuário ao agente ("como responder?")
            user_id: ID do usuário
            user_name: Nome do usuário
            contact_id: ID do contato/cliente
            conversation_context: Histórico já carregado
            
        Returns:
            Resposta contextualizada do agente
        """
        if not self.openai_api_key:
            return f"❌ {self.name} não configurado. Configure OPENAI_API_KEY."
        
        # Prepara mensagens base
        messages = [{"role": "system", "content": self.system_prompt}]
        
        # 🎯 AQUI ESTÁ A MÁGICA: Injetar contexto antes da pergunta
        if conversation_context and len(conversation_context) > 0:
            # Por que adicionar instrução específica?
            # - GPT precisa entender QUE existe contexto
            # - GPT precisa saber COMO usar (não repetir, apenas analisar)
            context_intro = {
                "role": "system",
                "content": (
                    f"IMPORTANTE: O usuário {user_name} está em uma conversa com um cliente. "
                    "Você tem acesso ao HISTÓRICO desta conversa abaixo. "
                    "Use este contexto para fornecer sugestões RELEVANTES e ESPECÍFICAS.\n\n"
                    "Exemplos de perguntas que você receberá:\n"
                    "- 'como responder para esse cliente?'\n"
                    "- 'o que falar agora?'\n"
                    "- 'gera um resumo desta conversa'\n"
                    "- 'qual o próximo passo?'\n\n"
                    "INSTRUÇÕES:\n"
                    "1. NÃO repita o histórico\n"
                    "2. ANALISE o contexto e forneça sugestão prática\n"
                    "3. Seja ESPECÍFICO ao cliente atual\n"
                    "4. Considere o ton e momento da conversa\n\n"
                    "HISTÓRICO DA CONVERSA:"
                )
            }
            messages.append(context_intro)
            
            # Por que extend() e não append()?
            # - conversation_context é uma LISTA de mensagens
            # - Cada mensagem já está formatada {"role": ..., "content": ...}
            messages.extend(conversation_context)
            
            # Separador visual (ajuda GPT a distinguir contexto de pergunta)
            messages.append({
                "role": "system",
                "content": "--- FIM DO CONTEXTO DA CONVERSA ---\n\n"
            })
        
        # Adiciona histórico do PRÓPRIO agente (conversa interna user↔agente)
        # Por que manter histórico do agente?
        # - Continuidade na conversa com o agente
        # - Agente lembra o que JÁ sugeriu
        user_history = self.conversation_history[user_id]
        messages.extend(list(user_history))
        
        # Adiciona pergunta atual
        contextualized_message = f"[Usuário: {user_name}] {message}"
        messages.append({"role": "user", "content": contextualized_message})
        
        try:
            headers = {
                "Authorization": f"Bearer {self.openai_api_key}",
                "Content-Type": "application/json"
            }
            
            if self.openai_account:
                headers["OpenAI-Organization"] = self.openai_account
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    OPENAI_API_URL,
                    headers=headers,
                    json={
                        "model": OPENAI_MODEL,
                        "messages": messages,
                        "temperature": 0.7,  # Criatividade moderada
                        "max_tokens": 600  # Limite de resposta (controle de custo)
                    }
                )
                
                response.raise_for_status()
                data = response.json()
                
                if "choices" in data and len(data["choices"]) > 0:
                    assistant_message = data["choices"][0]["message"]["content"]
                    
                    # Salva no histórico do agente (próxima pergunta terá continuidade)
                    user_history.append({"role": "user", "content": contextualized_message})
                    user_history.append({"role": "assistant", "content": assistant_message})
                    
                    return assistant_message.strip()
                
                return f"❌ {self.name}: Resposta inesperada da API."
        
        except httpx.HTTPStatusError as e:
            return f"❌ {self.name}: Erro API ({e.response.status_code})"
        except Exception as e:
            return f"❌ {self.name}: Erro ao processar - {str(e)}"



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


# Agente: SDR (Sales Development Representative)
AGENT_SDR = Agent(
    name="SDR",
    emoji="📅",
    system_prompt="""Você é um SDR (Sales Development Representative) especializado em agendamentos.

**IMPORTANTE:** Você trabalha com um sistema AUTOMÁTICO de detecção de intenções e entidades.
O sistema JÁ DETECTA automaticamente: emails, telefones, nomes, datas e intenção de agendamento.

**Seu papel:**
- Confirmar as informações detectadas automaticamente
- Fazer perguntas APENAS sobre o que ainda não foi detectado
- Ser breve e objetivo (máximo 2-3 linhas)
- NÃO pedir informações que já foram fornecidas na conversa

**Quando o sistema detectar email + intenção de agendamento:**
- Confirme brevemente: "Perfeito! Detectei seu email [email]. Vou abrir o calendário para você escolher o melhor horário."
- NÃO pergunte novamente sobre empresa, cargo ou necessidade
- O calendário aparecerá automaticamente

**Quando detectar apenas intenção SEM email:**
- Peça APENAS o email: "Para agendar, preciso apenas do seu email. Pode me informar?"

**Tom:** Direto, eficiente e amigável. Máximo 2-3 linhas por resposta.""",
    specialties=["Qualificação de Leads", "Agendamento", "Vendas B2B", "Google Calendar", "Follow-up"],
    commands={
        "/agendar": "Inicie o processo de agendamento de reunião",
        "/disponibilidade": "Verifique horários disponíveis na agenda",
        "/confirmar": "Confirme um agendamento já combinado",
        "/remarcar": "Remarque uma reunião existente",
        "/cancelar": "Cancele um agendamento",
        "/qualificar": "Qualifique o lead usando método BANT"
    }
)
AGENT_SDR.allow_calendar_creation = True
AGENT_SDR.allow_calendar_auto_create = False
AGENT_SDR.allow_calendar_creation = True


# =====================================================
# REGISTRO DE AGENTES
# =====================================================

AGENTS_REGISTRY: dict[str, Agent] = {
    "guru": AGENT_GURU,
    "advogado": AGENT_ADVOGADO,
    "vendedor": AGENT_VENDEDOR,
    "medico": AGENT_MEDICO,
    "psicologo": AGENT_PSICOLOGO,
    "sdr": AGENT_SDR,
}


# =====================================================
# CUSTOM BOTS (Criados pelo usuário)
# =====================================================

# Armazena bots personalizados em memória (user_id -> {bot_name -> Agent})
custom_bots_registry: dict[str, dict[str, Agent]] = {}


async def load_custom_agents_from_db() -> None:
    """
    Carrega todos os bots customizados do MongoDB para o registry em memória.
    Mantém compatibilidade com lookup síncrono nos handlers de socket.
    """
    docs = await custom_bots_collection.find().to_list(length=None)
    for doc in docs:
        user_id = doc.get("user_id")
        bot_key = doc.get("bot_key") or doc.get("name", "").lower().replace(" ", "")
        if not user_id or not bot_key:
            continue
        agent = Agent(
            name=doc.get("name", "Bot"),
            emoji=doc.get("emoji", "🤖"),
            system_prompt=doc.get("system_prompt", ""),
            specialties=doc.get("specialties", []),
            commands=doc.get("commands", {
                "/ajuda": "Lista comandos",
                "/limpar": "Limpar histórico",
                "/contexto": "Ver status da conversa"
            }),
            openai_api_key=doc.get("openai_api_key"),
            openai_account=doc.get("openai_account"),
        )
        if doc.get("allow_calendar_creation"):
            agent.allow_calendar_creation = True
        if doc.get("allow_calendar_auto_create"):
            agent.allow_calendar_auto_create = True

        if user_id not in custom_bots_registry:
            custom_bots_registry[user_id] = {}
        custom_bots_registry[user_id][bot_key] = agent
    if docs:
        print(f"✅ Bots customizados carregados: {len(docs)}")


async def ensure_user_custom_bots(user_id: str) -> None:
    """Garante que os bots de um usuário estão no registry (carrega do DB se necessário)."""
    if user_id in custom_bots_registry:
        return
    docs = await custom_bots_collection.find({"user_id": user_id}).to_list(length=None)
    if not docs:
        custom_bots_registry[user_id] = {}
        return
    for doc in docs:
        bot_key = doc.get("bot_key") or doc.get("name", "").lower().replace(" ", "")
        agent = Agent(
            name=doc.get("name", "Bot"),
            emoji=doc.get("emoji", "🤖"),
            system_prompt=doc.get("system_prompt", ""),
            specialties=doc.get("specialties", []),
            commands=doc.get("commands", {
                "/ajuda": "Lista comandos",
                "/limpar": "Limpar histórico",
                "/contexto": "Ver status da conversa"
            }),
            openai_api_key=doc.get("openai_api_key"),
            openai_account=doc.get("openai_account"),
        )
        if doc.get("allow_calendar_creation"):
            agent.allow_calendar_creation = True
        if doc.get("allow_calendar_auto_create"):
            agent.allow_calendar_auto_create = True
        custom_bots_registry.setdefault(user_id, {})[bot_key] = agent


async def create_custom_agent(
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

    # Persiste no MongoDB
    await custom_bots_collection.update_one(
        {"user_id": user_id, "bot_key": bot_key},
        {
            "$set": {
                "name": name,
                "emoji": emoji,
                "system_prompt": system_prompt,
                "specialties": specialties,
                "commands": commands,
                "openai_api_key": openai_api_key,
                "openai_account": openai_account,
                "allow_calendar_creation": agent.allow_calendar_creation,
                "allow_calendar_auto_create": agent.allow_calendar_auto_create,
                "updated_at": datetime.now(timezone.utc)
            },
            "$setOnInsert": {"created_at": datetime.now(timezone.utc)}
        },
        upsert=True
    )
    
    print(f"✅ Bot personalizado criado: {name} {emoji} (user: {user_id})")
    return agent


async def get_custom_agent(user_id: str, agent_name: str) -> Optional[Agent]:
    """
    Retorna bot personalizado do usuário.
    
    Args:
        user_id: ID do usuário
        agent_name: Nome do bot
        
    Returns:
        Instância do bot ou None
    """
    await ensure_user_custom_bots(user_id)
    bot_key = agent_name.lower().replace(' ', '')
    return custom_bots_registry[user_id].get(bot_key)


async def list_custom_agents(user_id: str) -> list[Agent]:
    """
    Lista todos os bots personalizados do usuário.
    
    Args:
        user_id: ID do usuário
        
    Returns:
        Lista de agentes personalizados
    """
    await ensure_user_custom_bots(user_id)
    return list(custom_bots_registry[user_id].values())


async def delete_custom_agent(user_id: str, agent_name: str) -> bool:
    """
    Deleta bot personalizado.
    
    Args:
        user_id: ID do usuário
        agent_name: Nome do bot
        
    Returns:
        True se deletado com sucesso
    """
    await ensure_user_custom_bots(user_id)
    
    bot_key = agent_name.lower().replace(' ', '')
    if bot_key in custom_bots_registry[user_id]:
        del custom_bots_registry[user_id][bot_key]
        await custom_bots_collection.delete_one({"user_id": user_id, "bot_key": bot_key})
        print(f"🗑️ Bot personalizado deletado: {agent_name} (user: {user_id})")
        return True
    
    return False


# =====================================================
# FUNÇÕES AUXILIARES
# =====================================================

async def get_agent(agent_name: str, user_id: str = None) -> Optional[Agent]:
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
        custom_agent = await get_custom_agent(user_id, agent_name)
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
        result += f"**{agent.name.lower().replace(' ', '')}** {agent.emoji}\n"
        result += f"└─ Especialidades: {', '.join(agent.specialties[:3])}\n\n"
    
    result += "\n💡 _Abra o painel do agente para iniciar uma conversa (não use @agente)_\n"
    result += "📋 _Use o painel do agente ou /agentes para ver mais comandos_"
    
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
    
    # Normaliza para remover prefixos '@' (caso o usuário ainda use menções legadas)
    clean_text = text_lower.lstrip('@')
    for agent_key in AGENTS_REGISTRY.keys():
        if clean_text.startswith(agent_key):
            return agent_key
    
    # Verifica nomes alternativos
    aliases = {
        "advogado": ["advogada", "dr", "dra", "advocatus"],
        "vendedor": ["vendedora", "sales", "comercial"],
        "medico": ["medica", "doutor", "doutora", "health"],
        "psicologo": ["psicologa", "terapeuta", "mindcare"],
    }
    
    for agent_key, agent_aliases in aliases.items():
        if any(clean_text.startswith(alias) for alias in agent_aliases):
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
    
    # Remove menção de agente do início (compatibilidade com formatos legados)
    prefixes = [f"{agent_name}", f"{agent_name.replace(' ', '')}", f"@{agent_name}", f"@{agent_name.replace(' ', '')}"]
    
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
        result += f"\n💡 _Exemplo: {agent.name.lower()} {list(agent.commands.keys())[1]} sua pergunta_"
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
    
    return f"❓ Comando desconhecido. Use **{agent.name.lower()} /ajuda** para ver comandos disponíveis."


# =====================================================
# FUNÇÕES AUXILIARES PARA SDR - AGENDAMENTO REAL
# =====================================================

async def sdr_try_schedule_meeting(
    conversation_text: str,
    user_id: str,
    user_name: str
) -> Optional[dict]:
    """
    Tenta extrair informações de agendamento da conversa e criar evento no Google Calendar.
    
    Args:
        conversation_text: Texto da conversa completa
        user_id: ID do usuário
        user_name: Nome do usuário
        
    Returns:
        Dict com informações do evento criado ou None se não conseguir
    """
    from bots.entities import extract_entities
    from bots.nlu import detect_intent
    from integrations.google_calendar import GoogleCalendarService
    from datetime import datetime, timedelta
    import re
    
    # Detecta intenção de agendamento (agora é async)
    intent = await detect_intent(conversation_text, "customer")
    if intent.name not in ["scheduling", "purchase"]:
        return None
    
    # Extrai entidades
    entities = extract_entities(conversation_text, {})
    
    # Verifica se tem as informações mínimas
    email_entity = entities.get("email")
    if not email_entity or not email_entity.valid:
        return None
    
    # Extrai informações
    customer_email = email_entity.normalized
    customer_name = user_name
    customer_phone = None
    
    if "phone" in entities and entities["phone"].valid:
        customer_phone = entities["phone"].normalized
    
    # Extrai data e hora
    date_entity = entities.get("date")
    time_entity = entities.get("time")
    
    if not date_entity or not time_entity:
        return None
    
    # Monta datetime
    try:
        date_str = date_entity.normalized  # formato: YYYY-MM-DD
        time_str = time_entity.normalized  # formato: HH:MM
        
        start_datetime = datetime.fromisoformat(f"{date_str}T{time_str}:00")
        end_datetime = start_datetime + timedelta(hours=1)  # 1 hora de duração
        
    except Exception as e:
        print(f"❌ Erro ao parsear data/hora: {e}")
        return None
    
    # Cria evento no Google Calendar
    try:
        calendar_service = GoogleCalendarService()
        
        # Autentica
        if not calendar_service.authenticate():
            print("❌ Falha na autenticação do Google Calendar")
            return None
        
        # Cria evento
        event = calendar_service.create_meeting_event(
            summary=f"Demonstração do Produto - {customer_name}",
            description=f"Reunião de demonstração agendada pelo SDR.\n\nCliente: {customer_name}\nEmail: {customer_email}\nTelefone: {customer_phone or 'Não informado'}",
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            attendee_emails=[customer_email],
            location="Google Meet",
            send_notifications=True
        )
        
        if event:
            # Salva no banco de dados
            from database import calendar_events_collection
            
            await calendar_events_collection.insert_one({
                "google_event_id": event["id"],
                "customer_id": user_id,
                "customer_name": customer_name,
                "customer_email": customer_email,
                "customer_phone": customer_phone,
                "agent_id": "sdr",
                "agent_name": "SDR",
                "title": f"Demonstração do Produto - {customer_name}",
                "description": f"Reunião agendada via chat",
                "start_time": start_datetime,
                "end_time": end_datetime,
                "timezone": "America/Sao_Paulo",
                "location": "Google Meet",
                "attendees": [customer_email],
                "meet_link": event.get("hangoutLink"),
                "calendar_link": event.get("htmlLink"),
                "status": "scheduled",
                "reminder_sent": False,
                "created_at": datetime.utcnow(),
                "notes": f"Agendado pelo SDR via chat"
            })
            
            print(f"✅ Evento criado: {event['id']}")
            return event
        
    except Exception as e:
        print(f"❌ Erro ao criar evento no Google Calendar: {e}")
        return None
    
    return None


async def sdr_schedule_event(
    start_datetime: 'datetime',
    end_datetime: 'datetime',
    customer_email: str,
    customer_name: str,
    customer_phone: Optional[str],
    user_id: str,
    user_name: str,
    contact_id: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Cria evento no Google Calendar com os parâmetros fornecidos.
    Retorna o evento criado ou None
    """
    from integrations.google_calendar import GoogleCalendarService
    from database import calendar_events_collection
    from datetime import datetime

    try:
        calendar_service = GoogleCalendarService()
        if not calendar_service.authenticate():
            print("❌ Falha na autenticação do Google Calendar")
            return None

        event = calendar_service.create_meeting_event(
            summary=f"Demonstração do Produto - {customer_name}",
            description=f"Reunião agendada pelo SDR via chat.\nCliente: {customer_name}\nEmail: {customer_email}\nTelefone: {customer_phone or 'Não informado'}",
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            attendee_emails=[customer_email],
            location="Google Meet",
            send_notifications=True
        )

        if event:
            await calendar_events_collection.insert_one({
                "google_event_id": event["id"],
                "customer_id": user_id,
                "customer_name": customer_name,
                "customer_email": customer_email,
                "customer_phone": customer_phone,
                "agent_id": "sdr",
                "agent_name": "SDR",
                "title": f"Demonstração do Produto - {customer_name}",
                "description": f"Reunião agendada via chat",
                "start_time": start_datetime,
                "end_time": end_datetime,
                "timezone": "America/Sao_Paulo",
                "location": "Google Meet",
                "attendees": [customer_email],
                "meet_link": event.get("hangoutLink"),
                "calendar_link": event.get("htmlLink"),
                "status": "scheduled",
                "reminder_sent": False,
                "created_at": datetime.utcnow(),
                "notes": "Agendado pelo SDR via chat"
            })
            return event
    except Exception as e:
        print(f"❌ Erro ao criar evento no Google Calendar (sdr_schedule_event): {e}")
        return None

    return None


async def generate_agent_suggestions(
    agent: Agent,
    conversation_context: list[dict],
    user_id: str,
    user_name: str,
    n_suggestions: int = 3
) -> list[str]:
    """
    Gera N sugestões de resposta curtas usando o agente com contexto.

    Args:
        agent: Instância do agente a usar para gerar sugestões
        conversation_context: Histórico da conversa (lista de mensagens)
        user_id: ID do usuário (atendente)
        user_name: Nome do atendente
        n_suggestions: Quantidade de sugestões a gerar

    Returns:
        Lista de strings com sugestões (pode ser vazia)
    """
    try:
        # Prompt para gerar N sugestões curtas, dê alternativas distintas
        prompt = (
            f"Com base no contexto da conversa abaixo, gere {n_suggestions} opções de resposta CURTAS que o atendente "
            "possa enviar ao cliente. Seja direto, profissional, empático e objetivo. Cada sugestão deve ter no máximo 2 frases." 
            "Retorne apenas um JSON com uma lista."
        )

        # Envia para o agente com contexto
        raw = await agent.ask_with_context(
            message=prompt,
            user_id=user_id,
            user_name=user_name,
            contact_id=None,
            conversation_context=conversation_context
        )

        # Tenta extrair JSON simples (fallback para linhas separadas)
        import json
        import re
        suggestions = []
        try:
            # O agente deve retornar algo como: ["sug1","sug2"]
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                suggestions = [str(s).strip() for s in parsed if str(s).strip()]
        except Exception:
            # Se não for JSON, tenta quebrar por linhas e filtrar
            lines = [l.strip() for l in raw.splitlines() if l.strip()]
            # Remove headers como '1) '
            clean = [re.sub(r'^\d+\)\s*', '', l) for l in lines]
            suggestions = clean[:n_suggestions]

        return suggestions[:n_suggestions]
    except Exception as e:
        print(f"⚠️ Erro ao gerar sugestões do agente {agent.name}: {e}")
        return []


async def generate_conversation_summary(
    agent: Agent,
    conversation_context: list[dict],
    user_id: str,
    user_name: str
) -> str:
    """
    Gera um resumo da conversa baseado no contexto fornecido.
    """
    try:
        prompt = (
            "Resuma a conversa abaixo em poucos pontos (3 a 5), listando: 1) problema/assunto, 2) ações pendentes, 3) próximos passos. "
            "Retorne o texto em linguagem direta, em português."
        )

        summary = await agent.ask_with_context(
            message=prompt,
            user_id=user_id,
            user_name=user_name,
            contact_id=None,
            conversation_context=conversation_context
        )

        return summary
    except Exception as e:
        print(f"⚠️ Erro ao gerar resumo com agente {agent.name}: {e}")
        return """❌ Não foi possível gerar resumo no momento. Tente novamente."""

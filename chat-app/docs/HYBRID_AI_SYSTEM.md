# Sistema Híbrido de IA - Documentação

## 📋 Visão Geral

Este projeto implementa um **sistema híbrido de IA** que combina automação de bots com atendimento humano, permitindo:

- **NLU (Natural Language Understanding)**: Detecção automática de intenções do usuário
- **Extração de Entidades**: Captura automática de CPF, telefone, email, datas, etc
- **Handover Bot→Humano**: Transferência inteligente quando necessário
- **Agente SDR**: Especialista em agendamento e qualificação de leads
- **Integração Google Calendar**: Agendamento automático de reuniões

## 🤖 Arquitetura do Sistema

### 1. NLU (Natural Language Understanding)

**Arquivo:** `backend/bots/nlu.py`

Detecta intenções do usuário sem necessidade de comandos explícitos:

- **Intenções de Cliente:** saudação, compra, agendamento, jurídico, suporte técnico, reclamação, cancelamento, solicitar humano
- **Intenções de Agente:** buscar informação, criar pedido, verificar status, agendar reunião, escalar

**Exemplo de uso:**
```python
from bots.nlu import detect_intent

intent = detect_intent("Oi, gostaria de agendar uma reunião", speaker="customer")
# Retorna: Intent(name='scheduling', confidence=0.85, keywords=['agendar', 'reunião'])
```

### 2. Extração de Entidades

**Arquivo:** `backend/bots/entities.py`

Extrai automaticamente dados estruturados do texto:

- **CPF** (com validação de dígitos verificadores)
- **CNPJ**
- **Telefone** (diversos formatos)
- **CEP**
- **Email**
- **URL**
- **Data** (dd/mm/yyyy, dd/mm, hoje, amanhã, etc)
- **Hora** (HH:MM, formato 12h/24h)
- **Dinheiro** (R$ 1.000,00)

**Exemplo de uso:**
```python
from bots.entities import extract_entities

entities = extract_entities(
    "Meu CPF é 123.456.789-09 e telefone (11) 98765-4321",
    context={}
)
# Retorna: {'cpf': Entity(...), 'phone': Entity(...)}
```

### 3. Sistema de Handover

**Arquivo:** `backend/bots/handover.py`

Gerencia transferências bot→humano com priorização inteligente:

- **Motivos:** solicitação explícita, baixa confiança, reclamação, consulta complexa, escalação, problema técnico, fora do horário
- **Prioridades:** 1=baixa, 2=média, 3=alta, 4=urgente
- **Roteamento:** direciona para departamento adequado (vendas, comercial, jurídico, suporte, supervisor)

**Exemplo de uso:**
```python
from bots.handover import should_trigger_handover, calculate_priority

needs_handover = should_trigger_handover(intent, confidence=0.45, entities={}, conversation_length=10)
priority = calculate_priority(reason="complaint", entities={}, intent="complaint")
```

### 4. Agente SDR

**Arquivo:** `backend/bots/agents.py` (AGENT_SDR)

Especialista em vendas e agendamento:

- **Metodologia BANT**: Budget, Authority, Need, Timeline
- **Comandos:**
  - `/agendar` - Agenda reunião
  - `/disponibilidade` - Verifica horários livres
  - `/confirmar` - Confirma agendamento
  - `/remarcar` - Remarca reunião
  - `/cancelar` - Cancela agendamento
  - `/qualificar` - Qualifica lead

**Exemplo de uso:**
```
No painel do SDR: Oi, gostaria de agendar uma demonstração do produto
```

### 5. Integração Google Calendar

**Arquivo:** `backend/integrations/google_calendar.py`

OAuth2 + operações completas de calendário:

- Autenticação OAuth2
- Criar eventos com Google Meet automático
- Verificar disponibilidade
- Listar eventos futuros
- Atualizar/cancelar eventos
- Buscar slots disponíveis

## 🚀 Configuração

### 1. Instalar Dependências

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configurar Google Calendar

#### Passo 1: Criar Projeto no Google Cloud

1. Acesse [Google Cloud Console](https://console.cloud.google.com)
2. Crie um novo projeto ou selecione existente
3. Ative a **Google Calendar API**:
   - Menu lateral → "APIs & Services" → "Library"
   - Busque "Google Calendar API"
   - Clique em "Enable"

#### Passo 2: Criar Credenciais OAuth2

1. Menu lateral → "APIs & Services" → "Credentials"
2. Clique em "Create Credentials" → "OAuth client ID"
3. Configure a tela de consentimento:
   - User Type: "External"
   - App name: "Chat App SDR"
   - Add test users (seu email)
4. Application type: "Desktop app"
5. Download do arquivo `credentials.json`
6. Coloque o arquivo na raiz do diretório `backend/`

#### Passo 3: Primeira Autenticação

```bash
cd backend
python integrations/google_calendar.py
```

- Será aberto um navegador para autorizar o app
- Faça login com sua conta Google
- Autorize o acesso ao calendário
- Um arquivo `token.json` será criado automaticamente

### 3. Variáveis de Ambiente

Adicione ao `.env`:

```env
# Google Calendar
GOOGLE_CREDENTIALS_PATH=credentials.json
GOOGLE_TOKEN_PATH=token.json
```

## 📡 API Endpoints

### NLU

- `POST /nlu/analyze` - Analisa texto e retorna intent + entidades
- `GET /nlu/intents` - Lista todas as intenções disponíveis
- `POST /nlu/extract-entities` - Extrai apenas entidades

### Handover

- `POST /handovers/` - Cria requisição de handover
- `GET /handovers/` - Lista handovers (com filtros)
- `GET /handovers/{id}` - Busca handover específico
- `PUT /handovers/{id}/accept` - Agente aceita handover
- `PUT /handovers/{id}/in-progress` - Marca como em progresso
- `PUT /handovers/{id}/resolve` - Resolve handover
- `DELETE /handovers/{id}` - Cancela handover
- `GET /handovers/stats/summary` - Estatísticas

### Calendar

- `GET /calendar/auth-status` - Status da autenticação
- `POST /calendar/events` - Cria evento
- `GET /calendar/events` - Lista eventos (com filtros)
- `GET /calendar/events/{id}` - Busca evento específico
- `PUT /calendar/events/{id}` - Atualiza evento
- `DELETE /calendar/events/{id}` - Cancela evento
- `GET /calendar/availability` - Verifica disponibilidade
- `GET /calendar/available-slots` - Lista horários livres

## 🎯 Fluxo de Uso

### Cenário 1: Cliente Quer Agendar Reunião

1. **Cliente:** "Oi, gostaria de agendar uma demonstração do produto"
2. **NLU detecta:** intent=`scheduling`, confidence=0.92
3. **Bot SDR responde:** "Claro! Para agendar, preciso de algumas informações..."
4. **Cliente fornece:** nome, email, telefone
5. **Extração de entidades:** captura automaticamente
6. **Bot SDR:** "Qual data prefere? Temos disponível amanhã às 14h ou 16h"
7. **Cliente:** "Amanhã às 14h está ótimo"
8. **Sistema:** Cria evento no Google Calendar + envia convite

### Cenário 2: Cliente Reclama (Handover)

1. **Cliente:** "Isso é um absurdo! Já é a terceira vez que tento resolver!"
2. **NLU detecta:** intent=`complaint`, confidence=0.95
3. **Sistema avalia:** `requires_handover()` retorna `True`
4. **Cria handover:** priority=4 (urgente), reason=`complaint`
5. **Bot:** "Entendo sua frustração. Estou transferindo para um supervisor agora."
6. **Agente humano:** Recebe notificação na fila de handovers
7. **Agente aceita:** Assume o atendimento
8. **Sistema:** Fornece contexto completo (últimas mensagens, entidades extraídas)

### Cenário 3: Baixa Confiança (Handover)

1. **Cliente:** "Como faço para migrar meus dados do sistema antigo?"
2. **NLU detecta:** intent=`complex_query`, confidence=0.38
3. **Sistema avalia:** Confiança muito baixa (<0.5)
4. **Cria handover:** priority=2 (média), reason=`low_confidence`
5. **Bot:** "Vou conectar você com um especialista que pode ajudar melhor."

## 🖥️ Interface Frontend

### Componente HandoverQueue

**Arquivo:** `frontend/src/features/handover/components/HandoverQueue.vue`

Interface completa para gerenciar handovers:

- ✅ Dashboard com estatísticas (pendentes, aceitos, em progresso, resolvidos)
- ✅ Filtros por status e prioridade
- ✅ Cards coloridos por prioridade (vermelho=urgente, laranja=alta, etc)
- ✅ Botões de ação (Aceitar, Iniciar, Resolver)
- ✅ Dialog com detalhes completos do cliente
- ✅ Auto-refresh a cada 30 segundos

### Composable useHandover

**Arquivo:** `frontend/src/composables/useHandover.ts`

Facilita integração com API:

```typescript
import { useHandover } from '@/composables/useHandover'

const { loading, error, createHandover, getHandovers, acceptHandover, resolveHandover } = useHandover()

// Criar handover
await createHandover({
  customer_id: 'user123',
  customer_name: 'João Silva',
  customer_email: 'joao@exemplo.com',
  reason: 'complaint',
  last_messages: ['Mensagem 1', 'Mensagem 2']
})

// Listar handovers pendentes
const handovers = await getHandovers({ status: 'pending' })

// Aceitar handover
await acceptHandover(handoverId, agentId, agentName)

// Resolver handover
await resolveHandover(handoverId, 'Problema resolvido com sucesso')
```

## 📊 Banco de Dados

### Collections

- **interactions**: Logs de interações (NLU + entidades)
- **handovers**: Requisições de handover
- **calendar_events**: Eventos agendados

### Índices

Criados automaticamente no startup (`database.py`):

```python
# Interactions
interactions_collection.create_index([("user_id", 1), ("timestamp", -1)])
interactions_collection.create_index([("agent", 1)])
interactions_collection.create_index([("intent", 1)])

# Handovers
handovers_collection.create_index([("status", 1), ("priority", -1)])
handovers_collection.create_index([("customer_id", 1)])
handovers_collection.create_index([("assigned_agent", 1)])

# Calendar Events
calendar_events_collection.create_index([("start_time", 1)])
calendar_events_collection.create_index([("google_event_id", 1)], unique=True)
```

## 🧪 Testes

### Testar NLU

```bash
cd backend
python bots/nlu.py
```

### Testar Extração de Entidades

```bash
python bots/entities.py
```

### Testar Google Calendar

```bash
python integrations/google_calendar.py
```

## 🔒 Segurança

- ✅ Todas as rotas requerem autenticação JWT
- ✅ Token do Google Calendar armazenado localmente (não commitado)
- ✅ Validação de CPF com dígitos verificadores
- ✅ Sanitização de entidades extraídas
- ✅ Rate limiting recomendado para produção

## 📈 Melhorias Futuras

- [ ] Treinar modelo de ML para NLU (substituir pattern matching)
- [ ] Adicionar suporte a mais idiomas
- [ ] Integração com Outlook Calendar
- [ ] Notificações push para handovers urgentes
- [ ] Dashboard de analytics (métricas de handover, tempo de resposta, etc)
- [ ] A/B testing de respostas
- [ ] Sentiment analysis
- [ ] Voice-to-text para chamadas
- [ ] Integração com CRM (Salesforce, HubSpot)

## 🤝 Contribuindo

Para adicionar novos intents ou entidades:

1. **Novo Intent:** Edite `backend/bots/nlu.py` → `CUSTOMER_INTENTS` ou `AGENT_INTENTS`
2. **Nova Entidade:** Edite `backend/bots/entities.py` → `PATTERNS` + função de validação
3. **Novo Agente:** Edite `backend/bots/agents.py` → Crie `AGENT_NOME` e adicione ao `AGENTS_REGISTRY`

## 📚 Referências

- [Google Calendar API Docs](https://developers.google.com/calendar/api)
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Pydantic Docs](https://docs.pydantic.dev/)
- [BANT Sales Methodology](https://www.salesforce.com/resources/articles/what-is-bant/)

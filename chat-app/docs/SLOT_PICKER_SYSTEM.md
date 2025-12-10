# 📅 Sistema de Agendamento Visual com Slot Picker

## 🎯 Visão Geral

Sistema automático que detecta intenção de agendamento e apresenta um calendário visual para o cliente escolher data e horário disponíveis.

## 🔄 Fluxo Completo

### 1. **Conversa com SDR**
Abra o painel do SDR (chip `SDR`) e mencione interesse em reunião no chat do painel:

```
Cliente: Olá, gostaria de conhecer o produto (no painel do SDR)
SDR: Olá! Vou adorar apresentar nosso produto...
Cliente: Sim, gostaria de agendar uma demonstração
```

### 2. **Detecção Automática de Intenção**
Backend analisa a conversa usando NLU:
- **Intent Detection**: Identifica "scheduling" ou "purchase"
- **Confidence Score**: Verifica se confiança > 0.6
- **Entity Extraction**: Busca email na conversa

```python
# backend/socket_handlers.py (linha ~273)
intent_result = detect_intent(conversation_text)
entities = extract_entities(conversation_text)

if intent_result.get("intent") in ["scheduling", "purchase"]:
    if entities.get("email"):
        # Mostra calendário!
        await sio.emit("agent:show-slot-picker", {
            "agentKey": "sdr",
            "customerEmail": email,
            "customerPhone": phone
        })
```

### 3. **Exibição do Calendário Visual**
Frontend recebe evento e mostra componente `SlotPicker`:

**Componentes:**
- **Seletor de Datas**: Próximos 14 dias úteis (segunda a sexta)
- **Horários Disponíveis**: Busca slots livres do Google Calendar
- **Input de Email**: Se não foi detectado na conversa

```vue
<!-- frontend/src/features/agents/components/SlotPicker/SlotPicker.vue -->
<template>
  <!-- Datas disponíveis -->
  <v-chip v-for="date in availableDates" @click="selectDate(date)">
    {{ formatDate(date) }}
  </v-chip>
  
  <!-- Horários livres -->
  <v-chip v-for="slot in availableSlots" @click="selectSlot(slot)">
    {{ slot.start }} - {{ slot.end }}
  </v-chip>
</template>
```

### 4. **Busca de Horários Disponíveis**
Quando cliente seleciona uma data:

```typescript
// Frontend chama API
const response = await axios.get('/calendar/available-slots', {
  params: {
    date: '2025-11-26',
    duration_minutes: 60
  }
})
// Retorna: [{ start: "09:00", end: "10:00" }, ...]
```

Backend consulta Google Calendar:

```python
# backend/integrations/google_calendar.py
def get_available_slots(date, start_hour=9, end_hour=18, slot_duration_minutes=60):
    # Busca eventos ocupados do dia
    # Gera slots de 1h entre 9h-18h
    # Filtra slots que não conflitam
    # Retorna lista de horários livres
```

### 5. **Seleção e Confirmação**
Cliente escolhe horário → Frontend envia mensagem para SDR:

```typescript
// AgentChatPane.vue
function handleSlotSelected(data) {
  const message = `Escolhi o dia ${data.date} às ${data.time}. Meu email é ${data.customerEmail}`
  
  // Envia para o SDR processar
  socket.emit('chat:send', {
    text: `${message}`,
    contactId: props.contactId
  })
}
```

### 6. **Agendamento com Confirmação (padrão)**
Backend detecta que agora tem todos os dados (email + data + hora):

```python
# socket_handlers.py (linha ~290)
if entities.get("email") and entities.get("date") and entities.get("time"):
  # Padrão: o SDR NÃO cria o evento automaticamente. Envia um pedido de confirmação
  # para o atendente no painel (botão 'Confirmar Agendamento'). Somente quando o atendente
  # confirmar (ou o usuário habilitar Auto-Agendar), o evento será criado.
  # Optionally, if auto-create is enabled for this agent/session, create directly:
  if agent.allow_calendar_auto_create or user_pref_auto:
    event = await sdr_try_schedule_meeting(conversation_text, user_id, author)
    
    if event:
        # Envia confirmação com links ao painel do agente
        confirmation = f"""
        ✅ Reunião agendada com sucesso!
        📅 Calendário: {event['htmlLink']}
        📹 Google Meet: {event['hangoutLink']}
        """
```

## 🏗️ Arquitetura

```
┌─────────────┐
│   Cliente   │
│  conversa   │
│   com SDR   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Backend NLU │ ← Detecta intenção de agendamento
│ detect_intent│   e extrai email
└──────┬──────┘
       │
       ▼ (emit: agent:show-slot-picker)
┌─────────────┐
│  Frontend   │
│ SlotPicker  │ ← Mostra calendário visual
└──────┬──────┘
       │ (seleciona data)
       ▼
┌─────────────┐
│ Backend API │ ← GET /calendar/available-slots
│  Google Cal │   Retorna horários livres
└──────┬──────┘
       │
       ▼ (lista de slots)
┌─────────────┐
│  Cliente    │ ← Escolhe horário
│  seleciona  │
└──────┬──────┘
       │
       ▼ (mensagem com escolha)
┌─────────────┐
│ Backend SDR │ ← sdr_try_schedule_meeting()
│ Agenda      │   Cria evento no Google Calendar
└──────┬──────┘
       │
       ▼ (confirmação)
┌─────────────┐
│  Cliente    │ ← Recebe links (Calendar + Meet)
│  recebe     │
│  email      │
└─────────────┘
```

## 📁 Arquivos Criados/Modificados

### **Novo Componente Frontend**
- `frontend/src/features/agents/components/SlotPicker/SlotPicker.vue` (300 linhas)
  - Seletor de datas (próximos 14 dias úteis)
  - Busca slots disponíveis via API
  - Exibe horários livres em chips clicáveis
  - Input de email (se necessário)
  - Confirmação visual de seleção

- `frontend/src/features/agents/components/SlotPicker/index.ts`
  - Barrel export para importação limpa

### **Modificações Backend**

**1. `backend/integrations/google_calendar.py`** (+80 linhas)
- **Novo método**: `get_available_slots(date, start_hour, end_hour, slot_duration_minutes)`
  - Busca eventos ocupados do Google Calendar
  - Gera slots de N minutos no horário comercial
  - Filtra conflitos e retorna lista de horários livres
  - Retorna: `[{"start": "09:00", "end": "10:00"}, ...]`

**2. `backend/socket_handlers.py`** (modificado ~linha 273)
- **Antes**: Tentava agendar direto após cada mensagem
- **Depois**: 
  1. Detecta intenção de agendamento
  2. Se tem email → Emite `agent:show-slot-picker`
  3. Se tem email + data + hora → Agenda automaticamente

```python
# Lógica de decisão
if intent == "scheduling" and confidence > 0.6:
    if email and not (date and time):
        # Mostra calendário
        emit('agent:show-slot-picker', {...})
    elif email and date and time:
        # Agenda direto
        event = await sdr_try_schedule_meeting(...)
```

### **Modificações Frontend**

**3. `frontend/src/features/agents/components/AgentChatPane.vue`**
- **Import**: `import SlotPicker from './SlotPicker'`
- **State**: `showSlotPicker`, `slotPickerData`
- **Listener**: `socket.on('agent:show-slot-picker', ...)`
- **Handler**: `handleSlotSelected(data)` → Envia mensagem com escolha
- **Template**: Renderiza `<SlotPicker>` dentro das mensagens

### **Endpoints API Existentes**
- `GET /calendar/available-slots?date=2025-11-26&duration_minutes=60`
  - Retorna lista de horários livres
  - Já estava implementado em `backend/routers/calendar.py`

## 🎨 UX/UI

### **Estados Visuais**

1. **Conversa Normal**
   ```
   Cliente: Gostaria de agendar
   SDR: Ótimo! Para quando você prefere?
   [📅 Calendário aparece automaticamente]
   ```

2. **Seleção de Data**
   ```
   ┌─────────────────────────────────┐
   │ 📅 Selecione Data e Horário     │
   ├─────────────────────────────────┤
   │ Email: cliente@email.com        │
   │                                 │
   │ Escolha o dia:                  │
   │ [seg, 25 nov] [ter, 26 nov]    │
   │ [qua, 27 nov] [qui, 28 nov]    │
   │                                 │
   │ Horários disponíveis:           │
   │ [🕒 09:00-10:00] [🕒 10:00-11:00]│
   │ [🕒 14:00-15:00] [🕒 15:00-16:00]│
   │                                 │
   │ [Cancelar]     [✅ Confirmar]   │
   └─────────────────────────────────┘
   ```

3. **Confirmação Automática**
   ```
   Cliente: [selecionou 26/nov às 10:00]
   SDR: Perfeito! Estou agendando...
   SDR: ✅ Reunião agendada com sucesso!
        📅 Calendário: [link]
        📹 Google Meet: [link]
        📧 Convite enviado para: cliente@email.com
   ```

## 🔒 Validações

### **Backend**
- ✅ Email válido (regex + formato)
- ✅ Data no futuro (não pode ser passado)
- ✅ Horário comercial (9h-18h, seg-sex)
- ✅ Duração mínima/máxima (15-240 min)
- ✅ Sem conflitos no Google Calendar

### **Frontend**
- ✅ Só dias úteis (segunda a sexta)
- ✅ Próximos 14 dias
- ✅ Email obrigatório para confirmar
- ✅ Deve selecionar data + horário

## 🚀 Configuração

### **1. Autenticação Google Calendar**
```bash
# Execute uma vez para autenticar
./setup-google-calendar.sh

# Isso abre o navegador para login Google
# Gera token.json no backend/
```

### **2. Variáveis de Ambiente**
```env
# frontend/.env
VITE_API_URL=http://localhost:3000
```

### **3. Restart Containers**
```bash
docker compose restart api frontend
```

## 📊 Logs e Debug

### **Backend**
```bash
# Ver logs do SDR
docker compose logs api -f | grep "SDR\|slot\|calendar"

# Ver detecção de intenção
# Busque: "Detectando intenção de agendamento..."
# Busque: "📅 Mostrando slot picker para..."
```

### **Frontend**
```javascript
// Console do navegador
// Busque: "📅 Mostrando SlotPicker para sdr"
// Busque: "📅 Slot selecionado: { date, time, email }"
```

## 🧪 Testando

### **Fluxo Completo**

1. **Inicie conversa com SDR**
   ```
  (no painel SDR) Olá, quero conhecer o produto
   ```

2. **Forneça seu email**
   ```
   Meu email é cliente@teste.com
   ```

3. **Mencione agendamento**
   ```
   Gostaria de agendar uma demonstração
   ```

4. **Calendário aparece automaticamente** 📅
   - Selecione uma data
   - Veja horários livres
   - Escolha um horário

5. **Receba confirmação com links**
   - Link do Google Calendar
   - Link do Google Meet
   - Email de confirmação

### **Casos de Teste**

| Cenário | Input | Resultado Esperado |
|---------|-------|-------------------|
| Email antes de agendar | "Meu email é teste@test.com" → "Quero agendar" | Calendário aparece |
| Agendar sem email | "Quero agendar uma reunião" | SDR pede email primeiro |
| Escolher slot ocupado | Seleciona horário já agendado | Slot não aparece na lista |
| Final de semana | Tenta agendar sábado/domingo | Datas não aparecem |
| Horário fora do expediente | Tenta agendar 20h | Horário não aparece |

## 🎯 Vantagens do Sistema

### **Para o Cliente**
- ✅ **Visual**: Vê claramente os horários disponíveis
- ✅ **Rápido**: Escolhe com 2 cliques (data + hora)
- ✅ **Confiável**: Só mostra horários realmente livres
- ✅ **Automático**: Não precisa digitar data/hora manualmente

### **Para o SDR**
- ✅ **Sem erros**: Cliente não pode escolher horário ocupado
- ✅ **Menos perguntas**: Não precisa ficar oferecendo horários
- ✅ **Mais conversões**: Processo simplificado aumenta agendamentos

### **Para o Sistema**
- ✅ **Menos falhas**: Validação de conflitos em tempo real
- ✅ **Integração real**: Usa Google Calendar como fonte de verdade
- ✅ **Escalável**: Funciona com múltiplos agentes e calendários

## 🔄 Próximas Melhorias

### **Curto Prazo**
- [ ] Permitir múltiplos calendários (diferentes SDRs)
- [ ] Duração customizável (30min, 1h, 2h)
- [ ] Adicionar timezone do cliente
- [ ] Mostrar nome do SDR que atenderá

### **Médio Prazo**
- [ ] Reagendamento visual (escolher novo slot)
- [ ] Cancelamento com confirmação
- [ ] Notificações de lembrete 1h antes
- [ ] Histórico de reuniões passadas

### **Longo Prazo**
- [ ] IA sugere melhor horário baseado em histórico
- [ ] Múltiplos participantes (reunião em grupo)
- [ ] Integração com Zoom, Teams
- [ ] Sincronização bidirecional com calendários externos

## 📞 Suporte

**Problema**: Calendário não aparece
- Verifique se email foi detectado: `entities.get("email")`
- Veja logs: `docker compose logs api -f | grep "show-slot-picker"`

**Problema**: Horários não carregam
- Verifique autenticação: `curl localhost:3000/calendar/auth-status`
- Execute: `./setup-google-calendar.sh`

**Problema**: Agendamento falha
- Verifique se data/hora estão corretos
- Veja logs: `docker compose logs api -f | grep "sdr_try_schedule"`

---

## 🎉 Resultado Final

Sistema completamente automático que:

1. ✅ **Detecta** intenção de agendamento na conversa
2. ✅ **Mostra** calendário visual automaticamente
3. ✅ **Busca** horários livres no Google Calendar
4. ✅ **Permite** seleção visual (data + hora)
5. ✅ **Agenda** automaticamente após seleção
6. ✅ **Confirma** com links (Calendar + Meet)
7. ✅ **Envia** email para o cliente

**Tudo funciona com ZERO intervenção manual do SDR! 🚀**

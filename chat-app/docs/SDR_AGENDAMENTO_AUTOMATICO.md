# 📅 Agendamento Automático SDR - Guia de Uso

## ✅ Implementado!

O agente SDR agora **realmente agenda reuniões** no Google Calendar e envia convites por email automaticamente!

## 🚀 Como Funciona

### 1. Conversa Natural

Você conversa normalmente com o SDR e fornece as informações necessárias:

```
Você: @sdr Quero agendar uma demo do produto

SDR: Olá! Para agendar, preciso de algumas informações...

Você: Cleber Silva, cleber@empresa.com, (48) 99901-9525, amanhã às 14h

SDR: Perfeito! Vou agendar...
```

### 2. Sistema Detecta Automaticamente

O sistema extrai automaticamente:
- ✅ **Email** - cleber@empresa.com
- ✅ **Telefone** - (48) 99901-9525  
- ✅ **Data** - "amanhã" → 26/11/2025
- ✅ **Hora** - 14h → 14:00

### 3. Cria no Google Calendar

O sistema automaticamente:
- 📅 Cria evento no Google Calendar
- 📹 Gera link do Google Meet
- 📧 Envia convite por email
- 💾 Salva no banco de dados

### 4. Confirmação Automática

Você recebe uma mensagem com:

```
✅ Reunião agendada com sucesso!

📅 Link do Calendário: https://calendar.google.com/...
📹 Link do Google Meet: https://meet.google.com/...
📧 Convite enviado para: cleber@empresa.com

Você receberá um email de confirmação com todos os detalhes.
```

## 📋 Informações Necessárias

Para o agendamento funcionar, o sistema precisa detectar:

| Informação | Obrigatória | Exemplos |
|------------|-------------|----------|
| **Email** | ✅ Sim | `joao@empresa.com`, `contato@gmail.com` |
| **Data** | ✅ Sim | `amanhã`, `26/11/2025`, `próxima segunda` |
| **Hora** | ✅ Sim | `14h`, `14:00`, `2pm` |
| **Nome** | ⚠️ Auto | Nome do usuário logado |
| **Telefone** | ❌ Não | `(48) 99901-9525`, `11987654321` |

## 🎯 Exemplos de Uso

### Exemplo 1: Tudo em Uma Mensagem

```
@sdr Quero agendar demo, meu email é joao@empresa.com, 
telefone (11) 98765-4321, pode ser amanhã às 10h?
```

### Exemplo 2: Conversa Fragmentada

```
Você: @sdr preciso marcar reunião
SDR: Claro! Me passa seu email?
Você: contato@empresa.com.br
SDR: E qual seria o melhor dia e horário?
Você: Pode ser dia 26/11 às 15h
SDR: Perfeito! Vou agendar...
✅ Reunião agendada!
```

### Exemplo 3: Usando Linguagem Natural

```
Você: @sdr Quero uma demo depois de amanhã de manhã
SDR: Que horário prefere?
Você: 9h da manhã tá bom
SDR: E qual seu email para enviar o convite?
Você: maria.silva@gmail.com
✅ Reunião agendada para 27/11/2025 às 09:00!
```

## 🔍 Como o Sistema Detecta

### 1. Detecção de Intenção (NLU)

Palavras-chave que ativam agendamento:
- `agendar`, `marcar`, `reunião`, `demo`, `demonstração`
- `agenda`, `calendário`, `horário`, `disponibilidade`

### 2. Extração de Entidades

**Email:**
- `joao@empresa.com`
- `contato123@gmail.com.br`

**Data:**
- `amanhã` → +1 dia
- `26/11/2025`
- `próxima segunda`
- `daqui 3 dias`

**Hora:**
- `14h`, `14:00`
- `2pm`, `14h30`
- `meio-dia`, `meia-noite`

**Telefone:**
- `(48) 99901-9525`
- `11 98765-4321`
- `+55 48 99901-9525`

## ⚙️ Configuração (Necessária)

Antes de usar pela primeira vez, **você precisa autenticar o Google Calendar**:

```bash
./setup-google-calendar.sh
```

Isso vai:
1. Abrir seu navegador
2. Pedir login na conta Google
3. Solicitar permissão para acessar o calendário
4. Gerar token automaticamente

**Você só precisa fazer isso UMA VEZ!**

## 🔧 Verificar Status

Para ver se está autenticado:

```bash
curl http://localhost:3000/calendar/auth-status
```

Deve retornar:
```json
{
  "authenticated": true,
  "message": "Google Calendar conectado"
}
```

## 📊 Detalhes Técnicos

### Duração Padrão
- ⏱️ **1 hora** (pode ser ajustado no código)

### Fuso Horário
- 🌎 **America/Sao_Paulo** (Brasília)

### Google Meet
- 📹 Gerado automaticamente para todos os eventos

### Lembretes
- 📧 **Email:** 24 horas antes
- 🔔 **Popup:** 30 minutos antes

## ❓ Troubleshooting

### "Email não chegou"

1. **Verifique spam/lixo eletrônico**
2. **Confira se o email está correto** na mensagem
3. **Veja o Google Calendar diretamente** - o evento está lá mesmo se o email não chegou

### "Erro ao agendar"

Possíveis causas:
- ❌ Google Calendar não autenticado
- ❌ Email inválido fornecido
- ❌ Data/hora não detectada corretamente
- ❌ Horário no passado

**Solução:**
```bash
# Re-autenticar
./setup-google-calendar.sh

# Verificar logs
docker compose logs api | grep "SDR\|calendar\|agendar"
```

### "Sistema não detectou a data"

Tente formatos mais explícitos:
- ❌ "semana que vem" (muito vago)
- ✅ "próxima segunda" (melhor)
- ✅ "26/11/2025" (melhor ainda)
- ✅ "amanhã" (perfeito)

## 🎓 Dicas

1. **Seja específico** com data e hora
2. **Forneça email válido** (obrigatório)
3. **Confirme os dados** antes que o sistema agende
4. **Verifique seu email** após o agendamento
5. **Aceite o convite** no Google Calendar

## 📈 Próximas Melhorias

- [ ] Perguntar confirmação antes de agendar
- [ ] Sugerir horários disponíveis automaticamente
- [ ] Remarcar reuniões existentes
- [ ] Cancelar via chat
- [ ] Múltiplos participantes
- [ ] Duração customizável
- [ ] Recurring meetings (reuniões recorrentes)
- [ ] Integração com CRM

## 📝 Exemplo Completo

```
[16:20] Você: @sdr oi
[16:20] SDR: Olá! Eu sou o sdr. Como posso ajudá-lo?

[16:21] Você: Quero agendar uma demo do produto
[16:21] SDR: Fico feliz em ajudar! Para agendar, preciso de:
             - Email
             - Telefone  
             - Data e horário preferido

[16:22] Você: cleber.fdelgado@gmail.com, (48) 99901-9525, amanhã às 14h
[16:22] SDR: Perfeito! Deixe-me verificar e agendar para você...

[16:22] SDR: ✅ Reunião agendada com sucesso!
             
             📅 Link do Calendário: https://calendar.google.com/event?eid=abc123...
             📹 Link do Google Meet: https://meet.google.com/xyz-abcd-efg
             📧 Convite enviado para: cleber.fdelgado@gmail.com
             
             Você receberá um email de confirmação com todos os detalhes.

[Email recebido]
───────────────────────────────────────────────
De: calendar-notification@google.com
Para: cleber.fdelgado@gmail.com

📅 Você foi convidado: Demonstração do Produto - Cleber

🕐 26 de novembro de 2025, 14:00 – 15:00 (GMT-3)
📹 Participar com o Google Meet
🔗 https://meet.google.com/xyz-abcd-efg

[Aceitar] [Recusar] [Talvez]
───────────────────────────────────────────────
```

---

**Agora o SDR realmente agenda!** 🎉

Não é mais apenas simulação - o evento é criado no Google Calendar, o convite é enviado por email, e o link do Google Meet é gerado automaticamente.

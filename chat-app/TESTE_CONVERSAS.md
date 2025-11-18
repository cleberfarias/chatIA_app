# 🧪 Teste de Conversas Entre Usuários

## 📋 Pré-requisitos

1. **Token JWT expirado?** Faça logout e login novamente
2. **Dois navegadores/abas** em modo anônimo (para simular dois usuários)
3. **4 usuários cadastrados** no banco de dados

## 🔄 Fluxo de Teste

### 1️⃣ Preparação

**Aba 1 (Cleber Delgado):**
```
1. Abra http://localhost:5173
2. Faça login como: cleber@example.com
3. Abra DevTools (F12) → Console
4. Aguarde mensagem: "✅ Socket conectado com sucesso"
```

**Aba 2 (Outro usuário - ex: Kalebe):**
```
1. Abra nova aba anônima: http://localhost:5173
2. Faça login como: kalebe@example.com (ou outro usuário)
3. Abra DevTools (F12) → Console
4. Aguarde mensagem: "✅ Socket conectado com sucesso"
```

### 2️⃣ Teste de Envio

**Na Aba 1 (Cleber):**
```
1. Veja a lista de contatos na sidebar
2. Clique em "Kalebe" (ou outro contato)
3. Console mostra: "🖱️ Clicou no contato: <ID>"
4. Digite uma mensagem: "Olá Kalebe, teste 1-2-3"
5. Pressione Enter ou clique no botão enviar
```

**Resultado Esperado (Aba 1):**
```
Console:
📤 Mensagem enviada (optimistic): temp_... para contato: <contactId>
✅ ACK recebido: {tempId: "...", id: "...", status: "sent", ...}
```

**Resultado Esperado (Aba 2 - Kalebe):**
```
Console:
📨 Nova mensagem recebida: {author: "Cleber Delgado", text: "Olá Kalebe...", contactId: "..."}
🔍 currentContactId: null msg.contactId: <ID>
✅ isCurrentContact: true

Interface:
🔔 Badge "1" aparece no contato "Cleber Delgado" na sidebar
```

### 3️⃣ Teste Bidirecional

**Na Aba 2 (Kalebe):**
```
1. Clique no contato "Cleber Delgado" na sidebar
2. Badge de não lidas deve zerar
3. Mensagem "Olá Kalebe, teste 1-2-3" deve aparecer
4. Digite resposta: "Oi Cleber! Recebi sua mensagem!"
5. Pressione Enter
```

**Resultado Esperado (Aba 1 - Cleber):**
```
Console:
📨 Nova mensagem recebida: {author: "Kalebe", text: "Oi Cleber!...", contactId: "..."}

Interface:
💬 Mensagem aparece instantaneamente no chat
```

## 🔍 Verificação Backend

**Terminal:**
```bash
docker-compose logs -f api | grep -E "(💾|📨|📤|👥)"
```

**Saída esperada quando Cleber envia mensagem:**
```
💾 Mensagem salva no MongoDB: <ID> (user: <cleber_id>)
📤 ACK enviado para <sid_cleber>
📨 Mensagem enviada para contato <kalebe_id> (sid: <sid_kalebe>)
🔍 Response data: contactId=<kalebe_id>, author=Cleber Delgado
```

**Saída esperada quando Kalebe conecta:**
```
✅ Socket autenticado: Kalebe (<kalebe_id>) - sid: <sid>
👥 Usuários online: 2
```

## ✅ Checklist de Funcionalidades

- [ ] Mensagem aparece instantaneamente para destinatário online
- [ ] Badge de não lidas incrementa corretamente
- [ ] Badge zera ao clicar no contato
- [ ] Mensagem persiste no banco (recarregar página mostra histórico)
- [ ] Usuário offline recebe mensagens ao logar
- [ ] Console mostra logs corretos (contactId, isCurrentContact)
- [ ] Sem mensagens duplicadas
- [ ] Sem vazamento de mensagens entre conversas diferentes

## 🐛 Troubleshooting

### Problema: "Connection rejected by server"
**Solução:** Token JWT expirado
```
1. Clique nos 3 pontos (menu) → "Sair"
2. Faça login novamente
3. Novo token será gerado
```

### Problema: Mensagem não aparece para destinatário
**Verifique:**
```
1. Backend logs: "📨 Mensagem enviada para contato X (sid: Y)"
   - Se mostrar "📪 Contato X está offline", o destinatário não está conectado
2. Console do destinatário: Deve mostrar "📨 Nova mensagem recebida"
3. contactId está sendo enviado? Console deve mostrar contactId na mensagem
```

### Problema: Badge não atualiza
**Verifique:**
```
1. Store contacts está carregado? console.log(useContactsStore().contacts)
2. Método incrementUnread está sendo chamado? Adicione log em chat.ts linha ~95
```

## 📊 Estrutura de Dados

**Mensagem no MongoDB:**
```json
{
  "_id": "673b...",
  "author": "Cleber Delgado",
  "text": "Olá Kalebe!",
  "type": "text",
  "status": "sent",
  "userId": "673a...",
  "contactId": "673a...",  ← ID do destinatário
  "createdAt": "2025-11-18T..."
}
```

**Evento Socket.IO chat:new-message:**
```json
{
  "id": "673b...",
  "author": "Cleber Delgado",
  "text": "Olá Kalebe!",
  "timestamp": 1731926400000,
  "status": "sent",
  "type": "text",
  "contactId": "673a..."  ← Frontend usa isso para filtrar
}
```

## 🎯 Casos de Uso

### ✅ Caso 1: Ambos online
- A envia mensagem → B recebe instantaneamente

### ✅ Caso 2: Destinatário offline
- A envia mensagem → Salva no banco
- B loga depois → Carrega mensagens ao abrir conversa

### ✅ Caso 3: Múltiplas conversas
- A conversa com B
- A conversa com C
- Mensagens não vazam entre conversas

### ✅ Caso 4: Mensagens antigas (sem contactId)
- Sistema continua exibindo mensagens antigas
- Frontend: `!msg.contactId` sempre exibe

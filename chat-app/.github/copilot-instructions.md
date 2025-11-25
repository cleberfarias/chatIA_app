# GitHub Copilot - Padrões de Desenvolvimento

## 🎯 Contexto do Projeto

Este é um projeto de chat em tempo real estilo WhatsApp usando:
- **Frontend:** Vue 3 + TypeScript + Vuetify + Socket.IO Client
- **Backend:** Node.js + Express + Socket.IO + TypeScript
- **Containerização:** Docker + Docker Compose

## 📐 Padrões de Código

### TypeScript
- Sempre usar tipos explícitos
- Usar `interface` para objetos complexos
- Usar `type` para unions e primitivos
- Evitar `any`, preferir `unknown` quando necessário

### Vue 3
- Usar **Composition API** com `<script setup lang="ts">`
- Nomenclatura de componentes em PascalCase
- Props sempre tipadas com interface
- Emits sempre declarados explicitamente

### Design System
- Todos os componentes de UI devem estar em `src/design-system/components/`
- Prefixar componentes do design system com `DS` (ex: `DSButton`, `DSCard`)
- Usar tokens de design de `src/design-system/tokens/` para cores, espaçamentos, etc
- Nunca hardcodar valores de cor, usar sempre tokens

### Estrutura de Arquivos

```
src/
├── design-system/
│   ├── tokens/          # Variáveis de design (cores, spacing, etc)
│   ├── components/      # Componentes reutilizáveis (DS*)
│   │   ├── DSChatInput/
│   │   ├── DSChatHeader/
│   │   ├── DSMessageBubble/
│   │   ├── DSAttachmentMenu/
│   │   ├── DSVoiceRecorder/
│   │   ├── DSUploader/
│   │   ├── DSCommandBar/
│   │   ├── DSDateSeparator/
│   │   └── ... (todos com index.ts para barrel export)
│   ├── composables/     # Lógica reutilizável (use*)
│   ├── styles/          # Estilos globais (foundations, mixins, utilities)
│   └── types/          # Tipos TypeScript compartilhados
├── features/           # Organização por feature/domínio
│   ├── chat/
│   │   └── components/  # MessageList, TypingIndicator
│   ├── contacts/
│   │   └── components/  # ContactsList
│   ├── agents/
│   │   └── components/  # AgentChatPane, CustomBotCreator
│   └── whatsapp/
│       └── components/  # WppConnectDialog
├── views/              # Páginas/Views da aplicação
├── stores/             # Pinia stores (auth, chat, contacts)
├── composables/        # Composables da aplicação (useOmni, useUpload)
└── assets/            # Recursos estáticos
```

### Nomenclatura

**Componentes:**
- Design System: `DSNomeDoComponente.vue` em `design-system/components/DSNomeDoComponente/` com barrel export (ex: `DSChatHeader/`)
- Views: `NomeView.vue` em `views/` (ex: `ChatView.vue`)
- Feature Components: `NomeDoComponente.vue` em `features/{feature}/components/` (ex: `features/chat/components/MessageList.vue`)

**Imports:**
- Design System: `import { DSComponente } from '@/design-system/components/DSComponente'` (named import via barrel)
- Features: `import ComponentName from '@/features/{feature}/components/ComponentName.vue'` (default import)

**Composables:**
- Sempre começar com `use` (ex: `useChat.ts`, `useScrollToBottom.ts`)
- Retornar objeto com propriedades nomeadas
- Exportar como named export, não default

**Types:**
- Interfaces para objetos: `interface Message { ... }`
- Types para unions: `type Status = 'sent' | 'delivered' | 'read'`
- Sempre exportar types/interfaces reutilizáveis

### Estilo WhatsApp

**Cores principais:**
- Primary: `#075e54` (verde escuro)
- Secondary: `#25d366` (verde WhatsApp)
- Mensagens enviadas: `#dcf8c6` (verde claro)
- Mensagens recebidas: `#ffffff` (branco)
- Background: `#e5ddd5` (bege)

**Componentes de mensagem:**
- Bolhas com bordas arredondadas (8px)
- Sombra sutil
- Timestamp no canto inferior direito
- Check marks para status (enviado/entregue/lido)

### Socket.IO

**Eventos:**
- Usar namespace `chat:` para eventos de chat (ex: `chat:new-message`)
- Sempre validar payload com Zod no backend
- Timestamps em milliseconds (Date.now())

**Tipos de mensagem:**
```typescript
interface Message {
  id: string;
  author: string;
  text: string;
  timestamp: number;
  status?: 'sent' | 'delivered' | 'read';
}
```

### Git

**Branches:**
- Feature: `TECH-XX` onde XX é o número da task
- Bugfix: `FIX-XX`
- Hotfix: `HOTFIX-XX`

**Commits:**
- Usar conventional commits: `feat:`, `fix:`, `docs:`, `style:`, `refactor:`, `test:`, `chore:`
- Mensagens em português
- Primeira linha < 72 caracteres
- Corpo do commit com detalhes (quando necessário)

**Exemplo:**
```
feat: adiciona componente de upload de arquivo

- Cria DSFileUpload.vue
- Adiciona validação de tipo e tamanho
- Integra com backend para upload
- Adiciona preview de imagens
```

### Docker

**Arquivos importantes:**
- `.dockerignore` em backend e frontend (excluir node_modules, dist, etc)
- Usar imagens Alpine quando possível (menor tamanho)
- Multi-stage builds para produção

### Testes (quando implementados)

- Usar Vitest para testes unitários
- Usar Testing Library para componentes Vue
- Coverage mínimo: 80%
- Testar comportamento, não implementação

## 🚀 Comandos Úteis

```bash
# Desenvolvimento
make restart          # Reinicia containers
npm run dev          # Modo desenvolvimento (frontend/backend)

# Build
npm run build        # Build de produção
docker compose build # Build dos containers

# Git
git checkout -b TECH-XX  # Nova feature branch
git commit -m "feat: ..."  # Commit com conventional commits
```

## 📚 Referências

- [Vue 3 Docs](https://vuejs.org/)
- [Vuetify 3 Docs](https://vuetifyjs.com/)
- [Socket.IO Docs](https://socket.io/)
- [TypeScript Docs](https://www.typescriptlang.org/)

## ⚠️ Regras Importantes

1. ❌ **NUNCA** commitar node_modules
2. ❌ **NUNCA** usar `any` sem justificativa
3. ❌ **NUNCA** hardcodar cores/espaçamentos (usar tokens)
4. ✅ **SEMPRE** tipar props e emits
5. ✅ **SEMPRE** validar dados no backend
6. ✅ **SEMPRE** usar design system para componentes reutilizáveis
7. ✅ **SEMPRE** testar em diferentes navegadores
8. ✅ **SEMPRE** adicionar comentários em lógica complexa

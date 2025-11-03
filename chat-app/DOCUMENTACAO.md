# 📚 Documentação do Projeto Chat em Tempo Real

**Projeto de Estudo:** Aplicação de chat em tempo real usando Vue 3, Node.js e Socket.IO com Docker

---

## 📁 Estrutura do Projeto

```
chat-app/
├── backend/          # Servidor Node.js com Socket.IO
├── frontend/         # Interface Vue 3 + Vuetify
└── docker-compose.yml # Orquestração dos containers
```

---

## 🔧 BACKEND (Servidor Node.js)

### 📄 `/backend/src/index.ts`

**Propósito:** Servidor Express com Socket.IO para comunicação em tempo real

**Linha por Linha:**

**Linha 1:** `import express from 'express'` → Importa o Express, framework para criar servidores HTTP em Node.js

**Linha 2:** `import http from 'http'` → Importa o módulo HTTP nativo do Node.js para criar o servidor base

**Linha 3:** `import { Server } from 'socket.io'` → Importa a classe Server do Socket.IO para habilitar comunicação bidirecional em tempo real via WebSockets

**Linha 4:** `import cors from 'cors'` → Importa o middleware CORS para permitir requisições cross-origin (entre diferentes domínios/portas)

**Linha 5:** `import { z } from 'zod'` → Importa Zod, biblioteca de validação de esquemas TypeScript para garantir tipo e formato dos dados

**Linha 7:** `const app = express()` → Cria a aplicação Express que gerenciará rotas HTTP

**Linha 8:** `app.use(cors())` → Ativa o middleware CORS permitindo que o frontend (porta 5173) acesse o backend (porta 3000)

**Linha 9:** `app.use(express.json())` → Ativa middleware para parsear (interpretar) requisições com corpo JSON

**Linha 11:** `app.get('/health', (_req, res) => res.json({ ok: true }))` → Cria rota GET `/health` que retorna `{ok: true}` para verificar se o servidor está respondendo (health check)

**Linha 13:** `const server = http.createServer(app)` → Cria servidor HTTP usando a aplicação Express como handler de requisições

**Linha 14-16:** Cria instância do Socket.IO anexada ao servidor HTTP, configurando CORS para aceitar qualquer origem (`*`) e permitir métodos GET e POST

**Linha 18-21:** Define esquema de validação MessageSchema usando Zod: objeto com `author` (string com mínimo 1 caractere) e `text` (string com mínimo 1 caractere)

**Linha 23:** `io.on('connection', (socket) => {` → Escuta evento de conexão de novos clientes Socket.IO; cada cliente conectado recebe um objeto `socket` único

**Linha 24:** `console.log('client connected:', socket.id)` → Registra no console o ID único do cliente que acabou de se conectar

**Linha 26:** `socket.on('chat:send', (payload) => {` → Escuta evento customizado `'chat:send'` enviado pelo cliente, recebendo `payload` com os dados da mensagem

**Linha 27:** `const parsed = MessageSchema.safeParse(payload)` → Valida o payload usando o esquema Zod; `safeParse` retorna objeto com `success` (boolean) e `data` (dados validados)

**Linha 28:** `if (!parsed.success) return` → Se validação falhar, encerra a função imediatamente sem processar a mensagem (previne dados inválidos)

**Linha 29:** `io.emit('chat:new-message', parsed.data)` → Emite (transmite) evento `'chat:new-message'` para TODOS os clientes conectados, incluindo o remetente, com os dados validados

**Linha 32:** `socket.on('disconnect', () => {` → Escuta evento de desconexão do cliente (quando fecha navegador, perde conexão, etc)

**Linha 33:** `console.log('client disconnected:', socket.id)` → Registra no console o ID do cliente que se desconectou

**Linha 37:** `const PORT = process.env.PORT || 3000` → Define porta do servidor: usa variável de ambiente `PORT` se existir, caso contrário usa 3000

**Linha 38:** `server.listen(PORT, () => console.log(...))` → Inicia o servidor na porta definida e exibe mensagem no console quando estiver pronto

---

### 📄 `/backend/package.json`

**Propósito:** Configuração de dependências e scripts do backend

**Campos Principais:**

- **`"type": "module"`** → Define que o projeto usa módulos ES6 (import/export) ao invés de CommonJS (require)

- **Scripts:**
  - `"dev"`: Inicia servidor de desenvolvimento com hot-reload (reinicia automaticamente ao salvar arquivos) usando ts-node-dev
  - `"build"`: Compila TypeScript para JavaScript na pasta `dist/`
  - `"start"`: Executa versão compilada em produção

- **Dependências (Produção):**
  - `cors`: Middleware para Cross-Origin Resource Sharing
  - `express`: Framework web minimalista para Node.js
  - `socket.io`: Biblioteca de WebSockets para comunicação em tempo real
  - `zod`: Validação de schemas TypeScript

- **Dependências de Desenvolvimento:**
  - `@types/express`, `@types/node`: Definições TypeScript para autocomplete e type checking
  - `ts-node-dev`: Executa TypeScript diretamente com hot-reload
  - `typescript`: Compilador TypeScript

---

### 📄 `/backend/tsconfig.json`

**Propósito:** Configuração do compilador TypeScript

**Configurações Importantes:**

- **`"rootDir": "src"`** → Código fonte fica em `src/`
- **`"outDir": "dist"`** → Código compilado vai para `dist/`
- **`"module": "ESNext"`** → Usa módulos ES6 modernos
- **`"target": "ES2020"`** → Compila para JavaScript ES2020 (Node.js moderno)
- **`"moduleResolution": "node"`** → Resolve módulos no estilo Node.js (busca em node_modules)
- **`"types": ["node"]`** → Inclui tipos do Node.js
- **`"strict": true"`** → Ativa todas verificações estritas de tipo (máxima segurança)
- **`"sourceMap": true"`** → Gera arquivos .map para debugar código original durante erros
- **`"esModuleInterop": true"`** → Compatibilidade entre módulos ES6 e CommonJS

---

### 📄 `/backend/Dockerfile`

**Propósito:** Imagem Docker para containerizar o backend

**Linha por Linha:**

**Linha 1:** `FROM node:20-alpine` → Usa imagem base Node.js versão 20 na variante Alpine (Linux minimalista e leve)

**Linha 2:** `WORKDIR /app` → Define `/app` como diretório de trabalho dentro do container

**Linha 3:** `COPY package*.json ./` → Copia `package.json` e `package-lock.json` para `/app` (otimiza cache de camadas Docker)

**Linha 4:** `RUN npm ci` → Instala dependências exatas do `package-lock.json` (mais rápido e determinístico que `npm install`)

**Linha 5:** `COPY . .` → Copia todo restante do código fonte para `/app`

**Linha 6:** `EXPOSE 3000` → Documenta que o container escuta na porta 3000 (não abre a porta automaticamente)

---

## 🎨 FRONTEND (Vue 3 + Vuetify)

### 📄 `/frontend/src/main.ts`

**Propósito:** Ponto de entrada da aplicação Vue, configura plugins e renderiza o app

**Linha por Linha:**

**Linha 1:** `import { createApp } from 'vue'` → Importa função para criar a instância raiz da aplicação Vue

**Linha 2:** `import { createPinia } from 'pinia'` → Importa Pinia, gerenciador de estado oficial do Vue (substitui Vuex) para compartilhar dados entre componentes

**Linha 3:** `import { createRouter, createWebHistory } from 'vue-router'` → Importa funções do Vue Router: `createRouter` cria o sistema de rotas, `createWebHistory` usa API History do navegador (URLs sem #)

**Linha 4:** `import App from './App.vue'` → Importa componente raiz da aplicação

**Linha 7:** `import 'vuetify/styles'` → Importa estilos CSS globais do Vuetify (Material Design)

**Linha 8:** `import { createVuetify } from 'vuetify'` → Importa função para inicializar framework UI Vuetify

**Linha 11:** `import ChatView from './views/ChatView.vue'` → Importa componente da página de chat

**Linha 13:** `const vuetify = createVuetify()` → Cria instância do Vuetify com configurações padrão

**Linha 14:** `const pinia = createPinia()` → Cria instância do Pinia (store de estado global)

**Linha 15-18:** Cria roteador configurando: modo `createWebHistory` (URLs limpas) e uma rota `/` que renderiza o componente `ChatView`

**Linha 20:** `createApp(App).use(pinia).use(router).use(vuetify).mount('#app')` → Cria aplicação Vue, registra plugins (Pinia, Router, Vuetify) e monta no elemento HTML `<div id="app">` do `index.html`

---

### 📄 `/frontend/src/App.vue`

**Propósito:** Componente raiz que estrutura o layout da aplicação

**Template (Linhas 1-8):**

**Linha 2:** `<v-app>` → Componente raiz obrigatório do Vuetify que fornece contexto de tema, responsividade e sistema de layout

**Linha 3:** `<v-main>` → Área de conteúdo principal do layout Vuetify, com padding e margens adequadas

**Linha 4:** `<router-view />` → Componente especial do Vue Router que renderiza o componente correspondente à rota atual (ex: `ChatView` na rota `/`)

**Script (Linha 9):**

**Linha 9:** `<script setup lang="ts"></script>` → Bloco script vazio usando Composition API (`setup`) com TypeScript; reservado para lógica futura

---

### 📄 `/frontend/src/views/ChatView.vue`

**Propósito:** Página principal do chat com interface e lógica de comunicação

**Template (Linhas 1-19):**

**Linha 2:** `<v-container class="pa-4" max-width="800">` → Container Vuetify com padding de 4 unidades e largura máxima de 800px (centralizado e responsivo)

**Linha 3:** `<h2>Chat em tempo Real</h2>` → Título da página

**Linha 4:** `<v-card class="mb-4" height="400" style="overflow: auto;">` → Card Vuetify (caixa estilizada) com margem inferior, altura fixa de 400px e scroll quando conteúdo exceder

**Linha 5:** `<v-list density="compact">` → Lista Vuetify compacta para exibir mensagens

**Linha 6-10:** Loop `v-for` que itera sobre array `messages`, criando um `v-list-item` para cada mensagem com chave única `idx` e título formatado como "Autor: Texto"

**Linha 14:** `<v-form @submit.prevent="send">` → Formulário Vuetify que ao ser submetido (Enter ou botão) previne comportamento padrão e executa função `send`

**Linha 15:** `<v-text-field v-model="author" label="Seu nome" required class="mb-2" />` → Campo de texto vinculado (`v-model`) à variável reativa `author`, com label, obrigatório e margem inferior

**Linha 16:** `<v-text-field v-model="text" label="Mensagem" ... @keyup.enter.prevent="send"/>` → Campo de mensagem vinculado a `text`, ao pressionar Enter executa `send`

**Linha 17:** `<v-btn type="submit">Enviar</v-btn>` → Botão de submit do formulário

**Script (Linhas 22-55):**

**Linha 23:** `import { ref, onMounted, onBeforeMount } from 'vue'` → Importa funções reativas do Vue: `ref` cria variável reativa, `onMounted` executa código após componente montar, `onBeforeMount` antes de desmontar

**Linha 24:** `import { io, Socket } from 'socket.io-client'` → Importa cliente Socket.IO para comunicação com backend

**Linha 26:** `type Message = { author: string; text: string; }` → Define tipo TypeScript para mensagens

**Linha 28:** `const messages = ref<Message[]>([])` → Array reativo de mensagens (quando muda, Vue atualiza interface automaticamente)

**Linha 29:** `const author = ref('Você')` → Variável reativa para nome do usuário, inicializada com 'Você'

**Linha 30:** `const text = ref('')` → Variável reativa para texto da mensagem

**Linha 31:** `let socket: Socket | null = null` → Variável para armazenar conexão Socket.IO

**Linha 33:** `onMounted(() =>{` → Hook executado quando componente é montado na tela

**Linha 34-36:** Cria conexão Socket.IO com URL do ambiente (`VITE_SOCKET_URL`) ou localhost:3000, usando apenas transporte WebSocket (mais rápido)

**Linha 37:** `socket.on('cha:new-message', (msg: Message) => {` → **ERRO DE DIGITAÇÃO:** deveria ser `'chat:new-message'` (falta o 't'), escuta mensagens do servidor

**Linha 38:** `messages.value.push(msg)` → Adiciona nova mensagem ao array (`.value` necessário para acessar/modificar ref)

**Linha 40-42:** `onBeforeMount` colocado DENTRO de `onMounted` (ERRO: deveria estar fora) - desconecta socket antes de desmontar componente

**Linha 45:** `function send() {` → Função para enviar mensagens

**Linha 46:** `if (!text.value.trim()) return` → Previne envio de mensagens vazias ou só com espaços

**Linha 47-50:** Cria objeto mensagem com autor (ou 'Anônimo' se vazio) e texto

**Linha 51:** `socket?.emit('chat:new-message', msg)` → Envia mensagem para servidor via Socket.IO (operador `?.` previne erro se socket for null)

**Linha 52:** `text.value = ''` → Limpa campo de mensagem após enviar

---

### 📄 `/frontend/package.json`

**Propósito:** Dependências e configuração do frontend

**Dependências Principais:**

- **`vue`**: Framework progressivo para interfaces reativas
- **`vue-router`**: Sistema de rotas oficial do Vue
- **`pinia`**: Gerenciador de estado (store)
- **`vuetify`**: Framework UI com componentes Material Design
- **`@mdi/font`**: Ícones Material Design
- **`socket.io-client`**: Cliente Socket.IO para comunicação em tempo real

**Dependências de Desenvolvimento:**

- **`vite`**: Build tool ultra-rápido com hot-reload
- **`vite-plugin-vuetify`**: Plugin para integração Vuetify + Vite
- **`typescript`**: Suporte TypeScript
- **`vue-tsc`**: Type-checker para Vue + TypeScript

---

### 📄 `/frontend/vite.config.ts`

**Propósito:** Configuração do Vite (bundler/dev server)

**Linha por Linha:**

**Linha 1:** `import { defineConfig } from 'vite'` → Importa função auxiliar com autocomplete para configuração

**Linha 2:** `import vue from '@vitejs/plugin-vue'` → Plugin oficial para suporte a Single File Components (.vue)

**Linha 3:** `import vuetify from 'vite-plugin-vuetify'` → Plugin para auto-importar componentes Vuetify (não precisa importar cada componente manualmente)

**Linha 6-10:** Exporta configuração ativando plugins: Vue SFC e Vuetify com auto-import habilitado

---

### 📄 `/frontend/src/vue-shim.d.ts`

**Propósito:** Declarações de tipo TypeScript para módulos sem tipos nativos

**Linha por Linha:**

**Linhas 1-5:** Declara que arquivos `.vue` exportam componentes Vue, permitindo TypeScript importar `.vue` sem erros

**Linha 7:** `declare module 'vuetify/styles'` → Informa ao TypeScript que módulo existe (mesmo sendo CSS), evitando erro de "módulo não encontrado"

---

### 📄 `/frontend/Dockerfile`

**Propósito:** Imagem Docker para frontend

**Estrutura idêntica ao backend:**

**Linha 1:** Usa Node.js 20 Alpine

**Linha 2:** Define `/app` como workdir

**Linha 3-4:** Copia package.json e instala dependências

**Linha 5:** Copia código fonte

**Linha 6:** Expõe porta 5173 (padrão do Vite)

---

## 🐳 DOCKER COMPOSE

### 📄 `/docker-compose.yml`

**Propósito:** Orquestra backend e frontend em containers conectados

**Serviço `api` (Backend):**

**Linha 3-5:** Constrói imagem usando `./backend/Dockerfile`

**Linha 6:** Sobrescreve comando padrão para rodar em modo dev

**Linha 7-8:** Mapeia porta 3000 do container para 3000 do host

**Linha 9-11:** Monta volumes: sincroniza código (hot-reload) e preserva node_modules do container

**Linha 12-13:** Define variável de ambiente `NODE_ENV=development`

**Serviço `web` (Frontend):**

**Linha 15-17:** Constrói imagem usando `./frontend/Dockerfile`

**Linha 18:** Roda Vite em modo dev com host 0.0.0.0 (acessível fora do container)

**Linha 19-20:** Mapeia porta 5173

**Linha 21-23:** Volumes para hot-reload

**Linha 24-25:** Define URL do backend via variável de ambiente

---

## ✅ ANÁLISE DO PROJETO

### **✅ PONTOS POSITIVOS:**

1. ✅ **Arquitetura bem estruturada:** Separação clara backend/frontend
2. ✅ **Tecnologias modernas:** Vue 3, TypeScript, Socket.IO, Docker
3. ✅ **Type safety:** Zod no backend, TypeScript em todo projeto
4. ✅ **Hot-reload configurado:** Desenvolvimento ágil com volumes Docker
5. ✅ **CORS configurado:** Comunicação cross-origin habilitada
6. ✅ **Validação de dados:** Esquema Zod previne dados inválidos

### **❌ PROBLEMAS ENCONTRADOS:**

1. ❌ **ChatView.vue linha 37:** Evento `'cha:new-message'` falta o 't' → deveria ser `'chat:new-message'`
   - **IMPACTO:** Frontend nunca receberá mensagens de outros usuários
   - **CORREÇÃO:** Mudar para `'chat:new-message'`

2. ❌ **ChatView.vue linha 40:** `onBeforeMount` dentro de `onMounted`
   - **IMPACTO:** Desconexão nunca será executada, causando memory leak
   - **CORREÇÃO:** Mover `onBeforeMount` para fora

3. ❌ **Backend index.ts linha 26:** Evento esperado é `'chat:send'` mas frontend emite `'chat:new-message'`
   - **IMPACTO:** Mensagens enviadas não são processadas pelo servidor
   - **CORREÇÃO:** Alinhar nomes dos eventos entre backend e frontend

4. ⚠️ **Dockerfiles sem CMD:** Dependem do docker-compose.yml para comando
   - **IMPACTO:** Não rodam standalone com `docker run`
   - **SUGESTÃO:** Adicionar `CMD ["npm", "run", "dev"]` em cada Dockerfile

5. ⚠️ **Falta .dockerignore:** node_modules será copiado para imagem
   - **IMPACTO:** Build lento e imagem maior
   - **SUGESTÃO:** Criar `.dockerignore` com `node_modules`

---

## 🔧 CORREÇÕES NECESSÁRIAS

### 1. Corrigir eventos Socket.IO

**Frontend (`ChatView.vue`):**
```typescript
// LINHA 37 - TROCAR:
socket.on('cha:new-message', (msg: Message) => {
// POR:
socket.on('chat:new-message', (msg: Message) => {
```

**Backend (`index.ts`):**
```typescript
// LINHA 26 - TROCAR:
socket.on('chat:send', (payload) => {
// POR:
socket.on('chat:new-message', (payload) => {
```

### 2. Corrigir lifecycle hook

**Frontend (`ChatView.vue`):**
```typescript
// Mover onBeforeUnmount para fora de onMounted:
onMounted(() => {
  socket = io(...)
  socket.on('chat:new-message', ...)
})

onBeforeUnmount(() => {
  socket?.disconnect()
})
```

---

## 🚀 PRÓXIMOS PASSOS SUGERIDOS

1. Corrigir erros de eventos Socket.IO
2. Adicionar `.dockerignore` em backend e frontend
3. Adicionar persistência de mensagens (banco de dados)
4. Implementar salas de chat
5. Adicionar autenticação de usuários
6. Estilização avançada com temas Vuetify
7. Deploy em produção (Railway, Render, Vercel)

---

**Projeto criado em:** 3 de novembro de 2025  
**Status:** Em desenvolvimento - necessita correções nos eventos Socket.IO  
**Tecnologias:** Vue 3, Node.js, Socket.IO, TypeScript, Docker, Vuetify

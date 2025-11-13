# 📚 Documentação Técnica Completa - Chat em Tempo Real

> **Stack:** Vue 3 + TypeScript + Vuetify | FastAPI + Python + Socket.IO | MongoDB + Replica Set

---

## 📑 Índice

1. [Arquitetura Geral](#arquitetura-geral)
2. [Backend (Python/FastAPI)](#backend-pythonfastapi)
3. [Frontend (Vue 3/TypeScript)](#frontend-vue-3typescript)
4. [Database (MongoDB)](#database-mongodb)
5. [Storage (MinIO/S3)](#storage-minios3)
6. [Design System Responsivo](#design-system-responsivo)
7. [Features Implementadas](#features-implementadas)
8. [Fluxos de Dados](#fluxos-de-dados)

---

## Arquitetura Geral

### Stack Completa

```
┌─────────────────────────────────────────────────────────────┐
│                        CLIENTE                               │
│  Vue 3 + TypeScript + Vuetify + Socket.IO Client + Pinia   │
│  AttachmentMenu + Breakpoints + Upload Progress            │
│                     (porta 5173)                            │
└─────────────┬──────────────────────┬────────────────────────┘
              │                      │
              │ HTTP/WS (Socket.IO)  │ HTTP PUT (presigned URL)
              │                      │
┌─────────────▼──────────────────────┼────────────────────────┐
│           SERVIDOR                 │                         │
│   FastAPI + python-socketio        │                         │
│   + boto3 (S3 SDK)                 │                         │
│     (porta 3000)                   │                         │
└─────────────┬──────────────────────┼────────────────────────┘
              │                      │
              │ Motor (async)        │ boto3 (presigned URLs)
              │                      │
┌─────────────▼──────────────────────▼────────────────────────┐
│          DATABASE                     STORAGE                │
│    MongoDB 7.0 Replica Set      MinIO S3 (porta 9000/9001) │
│       (porta 27017)                  Bucket: chat-uploads   │
└─────────────────────────────────────────────────────────────┘
```

### Fluxo de Comunicação

1. **Autenticação:** Cliente faz POST `/register` ou `/login` → Servidor retorna JWT token
2. **Conexão WebSocket:** Cliente conecta com Socket.IO passando token no `auth` object
3. **Envio de Mensagem:** Cliente emite `chat:send` → Servidor valida, salva no MongoDB, emite `chat:new-message` para todos
4. **Upload de Arquivo:** Cliente POST `/uploads/grant` → Servidor gera presigned URL → Cliente faz PUT direto no MinIO → Cliente POST `/uploads/confirm` → Servidor cria mensagem com anexo
5. **Confirmação:** Servidor emite `chat:ack` para confirmar recebimento (Optimistic UI)

---

## Backend (Python/FastAPI)

### Estrutura de Arquivos

```
backend/
├── main.py          # FastAPI app + Socket.IO handlers + rotas upload
├── models.py        # Modelos Pydantic (MessageCreate, MessageResponse, AttachmentInfo)
├── database.py      # Conexão MongoDB com Motor
├── auth.py          # JWT: create_token, decode_token, hash_password
├── users.py         # Rotas: POST /register, POST /login
├── storage.py       # MinIO/S3: presigned URLs, validação, upload/download
├── requirements.txt # Dependências Python (boto3, python-multipart)
└── Dockerfile       # Imagem Docker
```

### `main.py` - Servidor Principal

#### Inicialização

```python
import socketio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# FastAPI app
app = FastAPI(title="Chat API")

# CORS para permitir frontend em localhost:5173
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção: ["https://seu-dominio.com"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Socket.IO server assíncrono
sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins="*",
    logger=True
)

# Wrap FastAPI com Socket.IO
socket_app = socketio.ASGIApp(sio, app)
```

#### Rotas REST

**`GET /`** - Health check
```python
@app.get("/")
async def health_check():
    return {"status": "ok", "message": "Chat API running with Python"}
```

**`GET /messages?before=<timestamp>&limit=30`** - Histórico paginado
```python
@app.get("/messages")
async def get_messages(before: int | None = None, limit: int = 30):
    query = {}
    if before:
        query["createdAt"] = {"$lt": datetime.fromtimestamp(before / 1000)}
    
    cursor = messages_collection.find(query).sort("createdAt", -1).limit(limit)
    docs = await cursor.to_list(length=limit)
    
    messages = []
    for doc in reversed(docs):  # Ordem crescente
        messages.append(MessageResponse(
            id=str(doc["_id"]),
            author=doc["author"],
            text=doc["text"],
            timestamp=int(doc["createdAt"].timestamp() * 1000),
            status=doc.get("status", "sent"),
            type=doc.get("type", "text")
        ).model_dump())
    
    return messages
```

#### Eventos Socket.IO

**`connect`** - Autenticação via JWT
```python
@sio.event
async def connect(sid, environ, auth):
    token = (auth or {}).get("token")
    if not token:
        return False  # Rejeita conexão
    
    try:
        from auth import decode_token
        payload = decode_token(token)
        environ["user_id"] = payload["sub"]  # Armazena userId
        return True
    except Exception as e:
        return False
```

**`chat:send`** - Recebe e salva mensagem
```python
@sio.on("chat:send")
async def handle_chat_send(sid, data):
    environ = sio.get_environ(sid)
    user_id = environ.get("user_id", "anonymous")
    
    # Validação com Pydantic
    message_create = MessageCreate(**data)
    
    # Salva no MongoDB
    doc = {
        "author": message_create.author,
        "text": message_create.text,
        "status": "sent",
        "userId": user_id,
        "createdAt": datetime.utcnow()
    }
    result = await messages_collection.insert_one(doc)
    
    # Broadcast para todos
    response = MessageResponse(
        id=str(result.inserted_id),
        author=doc["author"],
        text=doc["text"],
        timestamp=int(doc["createdAt"].timestamp() * 1000),
        status="sent",
        type="text"
    ).model_dump()
    
    await sio.emit("chat:new-message", response)
```

**Outros eventos:** `chat:typing`, `chat:read`, `chat:delivered` (para features UX avançadas)

### `models.py` - Validação Pydantic

```python
from pydantic import BaseModel, Field

class MessageCreate(BaseModel):
    author: str = Field(..., min_length=1)
    text: str = Field(..., min_length=1)
    status: str = "sent"
    type: str = "text"

class MessageResponse(BaseModel):
    id: str
    author: str
    text: str
    timestamp: int
    status: str
    type: str

class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=30)
    password: str = Field(..., min_length=6)

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict
```

### `database.py` - Conexão MongoDB

```python
from motor.motor_asyncio import AsyncIOMotorClient
import os

DATABASE_URL = os.getenv("DATABASE_URL", "mongodb://localhost:27017/chatdb?replicaSet=rs0")

client = AsyncIOMotorClient(DATABASE_URL)
db = client.get_default_database()
messages_collection = db["messages"]
users_collection = db["users"]
```

### `auth.py` - JWT e Hashing

```python
import jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
import os

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-key")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRATION = int(os.getenv("JWT_EXPIRATION_MINUTES", "43200"))  # 30 dias

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_token(user_id: str, username: str) -> str:
    payload = {
        "sub": user_id,
        "username": username,
        "exp": datetime.utcnow() + timedelta(minutes=JWT_EXPIRATION)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def decode_token(token: str) -> dict:
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
```

### `users.py` - Rotas de Autenticação

```python
from fastapi import APIRouter, HTTPException
from database import users_collection
from models import UserRegister, UserLogin, Token
from auth import hash_password, verify_password, create_token
from bson import ObjectId

router = APIRouter()

@router.post("/register")
async def register(user: UserRegister):
    # Verifica se username já existe
    existing = await users_collection.find_one({"username": user.username})
    if existing:
        raise HTTPException(400, "Username already exists")
    
    # Cria usuário
    doc = {
        "username": user.username,
        "password": hash_password(user.password),
        "createdAt": datetime.utcnow()
    }
    result = await users_collection.insert_one(doc)
    
    # Gera token
    token = create_token(str(result.inserted_id), user.username)
    
    return Token(
        access_token=token,
        user={"id": str(result.inserted_id), "username": user.username}
    )

@router.post("/login")
async def login(user: UserLogin):
    # Busca usuário
    db_user = await users_collection.find_one({"username": user.username})
    if not db_user or not verify_password(user.password, db_user["password"]):
        raise HTTPException(401, "Invalid credentials")
    
    # Gera token
    token = create_token(str(db_user["_id"]), db_user["username"])
    
    return Token(
        access_token=token,
        user={"id": str(db_user["_id"]), "username": db_user["username"]}
    )
```

---

## Frontend (Vue 3/TypeScript)

### Estrutura de Arquivos

```
frontend/src/
├── main.ts                           # Entry point
├── App.vue                           # Componente raiz
├── components/
│   ├── TypingIndicator.vue          # "João está digitando..."
│   ├── DateSeparator.vue            # "Hoje", "Ontem", "15/11/2025"
│   └── HelloWorld.vue
├── views/
│   ├── ChatView.vue                 # Interface principal do chat
│   └── LoginView.vue                # Login/Registro
├── stores/
│   ├── chat.ts                      # Pinia store do chat
│   └── auth.ts                      # Pinia store de autenticação
├── design-system/
│   ├── components/
│   │   ├── DSChatHeader.vue         # Header do chat
│   │   ├── DSChatInput.vue          # Input com detecção de typing
│   │   └── DSMessageBubble.vue      # Bolha de mensagem com status
│   ├── composables/
│   │   ├── useChat.ts               # Lógica reutilizável do chat
│   │   └── useScrollToBottom.ts    # Auto-scroll inteligente
│   ├── tokens/                      # Design tokens (colors, spacing, etc)
│   └── types/
│       ├── index.ts                 # Exports de tipos
│       └── validation.ts            # Schemas Zod e tipos TS
├── tsconfig.app.json                # Config TypeScript com alias @
└── vite.config.ts                   # Config Vite com resolve alias
```

### `stores/chat.ts` - Estado Global do Chat

#### Features Principais
- ✅ Conexão Socket.IO com autenticação JWT
- ✅ Optimistic UI (mensagem aparece antes de confirmar)
- ✅ Retry com exponential backoff (1s, 2s, 4s)
- ✅ Listeners para todos os eventos (ack, typing, delivered, read)
- ✅ Paginação de histórico
- ✅ Controle de scroll inteligente

```typescript
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { io, Socket } from 'socket.io-client'
import type { Message, TypingInfo } from '@/design-system/types'
import { useAuthStore } from './auth'

export const useChatStore = defineStore('chat', () => {
  // Estado
  const messages = ref<Message[]>([])
  const pendingMessages = new Map<string, { message: Message; retries: number }>()
  const isConnected = ref(false)
  const typingUsers = ref<TypingInfo[]>([])
  const scrolledToBottom = ref(true)
  const hasMore = ref(true)
  
  let socket: Socket | null = null
  let baseUrl: string | null = null
  
  const MAX_RETRIES = 3
  const RETRY_DELAYS = [1000, 2000, 4000]  // 1s, 2s, 4s

  // Conectar com autenticação
  function connect(base: string) {
    if (socket) return
    baseUrl = base
    
    const auth = useAuthStore()
    socket = io(base, {
      transports: ['websocket'],
      auth: { token: auth.token || '' }
    })

    // Event listeners
    socket.on('connect', () => { isConnected.value = true })
    socket.on('disconnect', () => { 
      isConnected.value = false
      pendingMessages.clear()
    })

    // Mensagem nova (de outros usuários ou confirmação do servidor)
    socket.on('chat:new-message', (msg: Message) => {
      messages.value.push(msg)
    })

    // Confirmação de envio (troca tempId por id real)
    socket.on('chat:ack', (data: { tempId: string; id: string; timestamp: number }) => {
      const pending = pendingMessages.get(data.tempId)
      if (pending) {
        const index = messages.value.findIndex(m => m.id === data.tempId)
        if (index !== -1) {
          messages.value[index] = {
            ...messages.value[index],
            id: data.id,
            timestamp: data.timestamp,
            status: 'sent'
          }
        }
        pendingMessages.delete(data.tempId)
      }
    })

    // Typing indicator
    socket.on('chat:typing', (data: TypingInfo) => {
      const existing = typingUsers.value.findIndex(u => u.userId === data.userId)
      if (data.isTyping && existing === -1) {
        typingUsers.value.push(data)
      } else if (!data.isTyping && existing !== -1) {
        typingUsers.value.splice(existing, 1)
      }
    })

    // Entregue e lida
    socket.on('chat:delivered', (data: { messageId: string }) => {
      updateMessageStatus(data.messageId, 'delivered')
    })
    socket.on('chat:read', (data: { messageIds: string[] }) => {
      data.messageIds.forEach(id => updateMessageStatus(id, 'read'))
    })
  }

  // Enviar mensagem com Optimistic UI
  function sendMessage(author: string, text: string) {
    if (!socket || !text.trim()) return

    const tempId = `temp-${Date.now()}-${Math.random()}`
    const optimisticMessage: Message = {
      id: tempId,
      author,
      text,
      timestamp: Date.now(),
      status: 'pending',
      type: 'text'
    }

    // Adiciona mensagem imediatamente (Optimistic UI)
    messages.value.push(optimisticMessage)
    pendingMessages.set(tempId, { message: optimisticMessage, retries: 0 })

    // Envia para servidor
    socket.emit('chat:send', {
      author,
      text,
      tempId,
      status: 'pending',
      type: 'text'
    })

    // Se não receber ACK em 5s, faz retry
    setTimeout(() => retryMessage(tempId), 5000)
  }

  // Retry com exponential backoff
  function retryMessage(tempId: string) {
    const pending = pendingMessages.get(tempId)
    if (!pending) return  // Já foi confirmado

    if (pending.retries >= MAX_RETRIES) {
      // Marca como falha após 3 tentativas
      const index = messages.value.findIndex(m => m.id === tempId)
      if (index !== -1) {
        messages.value[index].status = 'failed'
      }
      pendingMessages.delete(tempId)
      return
    }

    // Retry
    pending.retries++
    const delay = RETRY_DELAYS[pending.retries - 1]
    
    setTimeout(() => {
      if (socket && pendingMessages.has(tempId)) {
        socket.emit('chat:send', {
          author: pending.message.author,
          text: pending.message.text,
          tempId,
          status: 'pending',
          type: 'text'
        })
        setTimeout(() => retryMessage(tempId), 5000)
      }
    }, delay)
  }

  // Carregar histórico com paginação
  async function loadHistory(base: string, limit = 50) {
    try {
      const before = messages.value[0]?.timestamp
      const url = before 
        ? `${base}/messages?before=${before}&limit=${limit}`
        : `${base}/messages?limit=${limit}`
      
      const res = await fetch(url)
      const data: Message[] = await res.json()
      
      if (data.length < limit) hasMore.value = false
      messages.value.unshift(...data)
    } catch (e) {
      console.error('Erro ao carregar histórico:', e)
    }
  }

  // Emitir typing
  function emitTyping(isTyping: boolean, author: string) {
    if (!socket) return
    socket.emit('chat:typing', {
      userId: useAuthStore().user?.id || 'anonymous',
      author,
      chatId: 'global',
      isTyping
    })
  }

  // Marcar como lido
  function markAsRead() {
    if (!socket) return
    const unread = messages.value
      .filter(m => m.status !== 'read')
      .slice(-10)  // Últimas 10 não lidas
      .map(m => m.id)
    
    if (unread.length > 0) {
      socket.emit('chat:read', { messageIds: unread })
    }
  }

  // Helpers
  function updateMessageStatus(id: string, status: Message['status']) {
    const msg = messages.value.find(m => m.id === id)
    if (msg) msg.status = status
  }

  function setScrolledToBottom(value: boolean) {
    scrolledToBottom.value = value
  }

  function disconnect() {
    socket?.disconnect()
    socket = null
    isConnected.value = false
    pendingMessages.clear()
  }

  return {
    messages,
    isConnected,
    typingUsers,
    scrolledToBottom,
    hasMore,
    connect,
    disconnect,
    sendMessage,
    loadHistory,
    emitTyping,
    markAsRead,
    setScrolledToBottom
  }
})
```

### `views/ChatView.vue` - Interface Principal

#### Features UX Implementadas
- ✅ Auto-scroll inteligente (só scroll automático se usuário estava no bottom)
- ✅ Agrupamento de mensagens (por data e autor com timebox de 5min)
- ✅ Separadores de data ("Hoje", "Ontem", dias da semana)
- ✅ Indicador de digitação com múltiplos usuários
- ✅ Botão "Carregar mais" para paginação
- ✅ FAB "Novas mensagens" com badge de não lidas
- ✅ Marca mensagens como lidas quando scrolled to bottom

```vue
<template>
  <v-container fluid class="pa-0 d-flex flex-column" style="height: 100vh">
    <!-- Header -->
    <DSChatHeader />

    <!-- Área de mensagens com scroll -->
    <v-sheet
      ref="messagesContainer"
      class="flex-grow-1 overflow-y-auto pa-4"
      @scroll="handleScroll"
    >
      <!-- Botão carregar mais -->
      <v-btn
        v-if="hasMore"
        block
        variant="text"
        color="primary"
        class="mb-4"
        :loading="isLoadingMore"
        @click="loadMoreMessages"
      >
        Carregar mais mensagens
      </v-btn>

      <!-- Mensagens agrupadas -->
      <div v-for="(group, date) in groupedMessages" :key="date">
        <DateSeparator :date="new Date(date)" />
        
        <div v-for="(authorGroup, idx) in group" :key="idx" class="mb-4">
          <DSMessageBubble
            v-for="(msg, msgIdx) in authorGroup.messages"
            :key="msg.id"
            :message="msg"
            :show-timestamp="msgIdx === authorGroup.messages.length - 1"
          />
        </div>
      </div>

      <!-- Indicador de digitação -->
      <TypingIndicator v-if="typingUsers.length > 0" :users="typingUsers" />
    </v-sheet>

    <!-- Input de mensagem -->
    <DSChatInput
      v-model="messageText"
      :author="author"
      @send="handleSend"
      @typing="handleTyping"
    />

    <!-- FAB para scroll to bottom -->
    <v-btn
      v-if="!scrolledToBottom"
      icon="mdi-chevron-down"
      color="primary"
      position="fixed"
      location="bottom right"
      class="mb-16 mr-4"
      @click="scrollToBottom"
    >
      <v-badge v-if="unreadCount > 0" :content="unreadCount" color="error" />
    </v-btn>
  </v-container>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { useChatStore } from '@/stores/chat'
import { useAuthStore } from '@/stores/auth'
import DSChatHeader from '@/design-system/components/DSChatHeader.vue'
import DSChatInput from '@/design-system/components/DSChatInput.vue'
import DSMessageBubble from '@/design-system/components/DSMessageBubble.vue'
import TypingIndicator from '@/components/TypingIndicator.vue'
import DateSeparator from '@/components/DateSeparator.vue'
import type { Message } from '@/design-system/types'

const chatStore = useChatStore()
const authStore = useAuthStore()

const messagesContainer = ref<HTMLElement | null>(null)
const messageText = ref('')
const author = computed(() => authStore.user?.username || 'Você')
const isLoadingMore = ref(false)

// Computed properties
const { messages, hasMore, typingUsers, scrolledToBottom } = chatStore

// Agrupamento de mensagens
const groupedMessages = computed(() => {
  const groups: Record<string, Array<{ author: string; messages: Message[] }>> = {}
  
  messages.forEach((msg, idx) => {
    // Agrupa por data
    const date = new Date(msg.timestamp).toDateString()
    if (!groups[date]) groups[date] = []
    
    // Agrupa por autor se mensagens estão a menos de 5min
    const lastGroup = groups[date][groups[date].length - 1]
    const timeDiff = idx > 0 
      ? msg.timestamp - messages[idx - 1].timestamp
      : Infinity
    
    if (lastGroup && lastGroup.author === msg.author && timeDiff < 5 * 60 * 1000) {
      // Adiciona à última group
      lastGroup.messages.push(msg)
    } else {
      // Cria nova group
      groups[date].push({ author: msg.author, messages: [msg] })
    }
  })
  
  return groups
})

// Contador de não lidas
const unreadCount = computed(() => 
  messages.filter(m => m.status !== 'read' && m.author !== author.value).length
)

// Handlers
function handleSend() {
  if (!messageText.value.trim()) return
  chatStore.sendMessage(author.value, messageText.value)
  messageText.value = ''
  nextTick(() => scrollToBottom(true))
}

function handleTyping(isTyping: boolean) {
  chatStore.emitTyping(isTyping, author.value)
}

function handleScroll() {
  if (!messagesContainer.value) return
  
  const { scrollTop, scrollHeight, clientHeight } = messagesContainer.value
  const isAtBottom = scrollHeight - scrollTop - clientHeight < 100
  
  chatStore.setScrolledToBottom(isAtBottom)
  
  if (isAtBottom) {
    chatStore.markAsRead()
  }
}

async function loadMoreMessages() {
  isLoadingMore.value = true
  const previousHeight = messagesContainer.value?.scrollHeight || 0
  
  await chatStore.loadHistory(import.meta.env.VITE_SOCKET_URL || 'http://localhost:3000', 30)
  
  // Mantém posição do scroll
  await nextTick()
  if (messagesContainer.value) {
    const newHeight = messagesContainer.value.scrollHeight
    messagesContainer.value.scrollTop = newHeight - previousHeight
  }
  
  isLoadingMore.value = false
}

function scrollToBottom(force = false) {
  if (!messagesContainer.value) return
  if (force || scrolledToBottom.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    chatStore.setScrolledToBottom(true)
  }
}

// Lifecycle
onMounted(async () => {
  const baseUrl = import.meta.env.VITE_SOCKET_URL || 'http://localhost:3000'
  
  // Carrega histórico inicial
  await chatStore.loadHistory(baseUrl)
  
  // Conecta Socket.IO
  chatStore.connect(baseUrl)
  
  // Scroll inicial
  nextTick(() => scrollToBottom(true))
})

// Auto-scroll para novas mensagens se estava no bottom
watch(() => messages.length, () => {
  nextTick(() => {
    if (scrolledToBottom.value) {
      scrollToBottom(true)
    }
  })
})
</script>
```

### `design-system/components/DSMessageBubble.vue` - Bolha com Status

```vue
<template>
  <v-sheet
    :color="isOwn ? colors.sentMessage : colors.receivedMessage"
    :class="['message-bubble', isOwn ? 'ml-auto' : 'mr-auto']"
    rounded="lg"
    elevation="1"
    max-width="70%"
    class="pa-3 mb-2"
  >
    <!-- Autor (só se não for própria) -->
    <div v-if="!isOwn" class="text-caption font-weight-bold mb-1">
      {{ message.author }}
    </div>

    <!-- Texto -->
    <div class="text-body-1">{{ message.text }}</div>

    <!-- Footer: timestamp + status -->
    <div v-if="showTimestamp" class="d-flex align-center justify-end gap-1 mt-1">
      <span class="text-caption" :style="{ color: colors.textSecondary }">
        {{ formatTime(message.timestamp) }}
      </span>
      
      <!-- Status icon (só para mensagens próprias) -->
      <v-icon v-if="isOwn" :icon="statusIcon" :color="statusColor" size="16" />
    </div>
  </v-sheet>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { Message } from '@/design-system/types'
import { colors } from '@/design-system/tokens'
import { useAuthStore } from '@/stores/auth'

const props = defineProps<{
  message: Message
  showTimestamp?: boolean
}>()

const authStore = useAuthStore()

const isOwn = computed(() => 
  props.message.author === authStore.user?.username || 
  props.message.author === 'Você'
)

const statusIcon = computed(() => {
  switch (props.message.status) {
    case 'pending': return 'mdi:clock-outline'
    case 'sent': return 'mdi:check'
    case 'delivered': return 'mdi:check-all'
    case 'read': return 'mdi:check-all'
    default: return 'mdi:alert-circle-outline'
  }
})

const statusColor = computed(() => {
  if (props.message.status === 'read') return colors.primary
  if (props.message.status === 'failed') return colors.error
  return colors.textSecondary
})

function formatTime(timestamp: number): string {
  return new Date(timestamp).toLocaleTimeString('pt-BR', {
    hour: '2-digit',
    minute: '2-digit'
  })
}
</script>

<style scoped>
.message-bubble {
  word-wrap: break-word;
}
</style>
```

### `components/TypingIndicator.vue` - "Digitando..."

```vue
<template>
  <v-sheet color="transparent" class="d-flex align-center gap-2 pa-2">
    <v-avatar size="32" :color="colors.primary">
      <span class="text-white text-caption">
        {{ users[0].author[0].toUpperCase() }}
      </span>
    </v-avatar>
    
    <div class="text-caption" :style="{ color: colors.textSecondary }">
      {{ typingText }}
    </div>
    
    <div class="typing-dots">
      <span></span>
      <span></span>
      <span></span>
    </div>
  </v-sheet>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { TypingInfo } from '@/design-system/types'
import { colors } from '@/design-system/tokens'

const props = defineProps<{
  users: TypingInfo[]
}>()

const typingText = computed(() => {
  const count = props.users.length
  if (count === 1) return `${props.users[0].author} está digitando`
  if (count === 2) return `${props.users[0].author} e ${props.users[1].author} estão digitando`
  return `${props.users[0].author} e outros ${count - 1} estão digitando`
})
</script>

<style scoped>
.typing-dots {
  display: flex;
  gap: 4px;
}

.typing-dots span {
  width: 6px;
  height: 6px;
  background-color: v-bind('colors.textSecondary');
  border-radius: 50%;
  animation: bounce 1.4s infinite ease-in-out both;
}

.typing-dots span:nth-child(1) { animation-delay: -0.32s; }
.typing-dots span:nth-child(2) { animation-delay: -0.16s; }

@keyframes bounce {
  0%, 80%, 100% { transform: translateY(0); }
  40% { transform: translateY(-8px); }
}
</style>
```

### `components/DateSeparator.vue` - Separador Contextual

```vue
<template>
  <v-divider class="my-4">
    <v-chip :color="colors.surfaceVariant" size="small">
      {{ formattedDate }}
    </v-chip>
  </v-divider>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { colors } from '@/design-system/tokens'

const props = defineProps<{
  date: Date
}>()

const formattedDate = computed(() => {
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  
  const messageDate = new Date(props.date)
  messageDate.setHours(0, 0, 0, 0)
  
  const diffTime = today.getTime() - messageDate.getTime()
  const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24))
  
  if (diffDays === 0) return 'Hoje'
  if (diffDays === 1) return 'Ontem'
  if (diffDays < 7) {
    return messageDate.toLocaleDateString('pt-BR', { weekday: 'long' })
  }
  
  return messageDate.toLocaleDateString('pt-BR')
})
</script>
```

---

## Database (MongoDB)

### Collections

#### `users`
```javascript
{
  _id: ObjectId("..."),
  username: "joao123",
  password: "$2b$12$...",  // bcrypt hash
  createdAt: ISODate("2025-11-07T10:00:00Z")
}
```

#### `messages`
```javascript
{
  _id: ObjectId("..."),
  author: "João",
  text: "Olá, mundo!",
  status: "read",  // pending | sent | delivered | read | failed
  type: "text",    // text | image | file
  userId: "507f1f77bcf86cd799439011",  // Referência para users._id
  createdAt: ISODate("2025-11-07T10:30:00Z")
}
```

### Índices Recomendados

```javascript
// Índice para paginação por data
db.messages.createIndex({ "createdAt": -1 })

// Índice para buscar por usuário
db.messages.createIndex({ "userId": 1, "createdAt": -1 })

// Índice único para username
db.users.createIndex({ "username": 1 }, { unique: true })
```

### Replica Set

**Por que replica set?**
- Necessário para operações assíncronas do Motor
- Habilita change streams (para features futuras)
- Alta disponibilidade (failover automático)

**Inicialização:**
```bash
# No container MongoDB
mongosh --eval "rs.initiate()"

# Verificar status
mongosh --eval "rs.status()"
```

---

## Features Implementadas

### ✅ TECH-01: Validação de Mensagens
- Zod no frontend (TypeScript)
- Pydantic no backend (Python)
- Previne mensagens vazias ou inválidas

### ✅ TECH-02: Persistência e Histórico
- MongoDB com Motor (async)
- Endpoint `GET /messages` com paginação (`?before=<timestamp>&limit=30`)
- Carregamento automático ao abrir chat

### ✅ TECH-03: Autenticação JWT
- Registro e login com `POST /register` e `POST /login`
- Token JWT com expiração de 30 dias
- Hashing bcrypt para senhas
- Socket.IO protegido (requer token no `auth` object)

### ✅ TECH-04: UX Avançada

#### 1. Auto-scroll Inteligente
- Scroll automático apenas se usuário estava no bottom
- Threshold de 100px para detectar "perto do bottom"
- FAB "Novas mensagens" com badge quando não está no bottom

#### 2. Indicador "Digitando..."
- Evento `chat:typing` com debounce de 1s no input
- Animação de 3 dots bouncing
- Suporta múltiplos usuários ("João e Maria estão digitando...")

#### 3. Confirmações de Status
- ⏳ **Pending:** Enviando para servidor
- ✓ **Sent:** Confirmado pelo servidor (evento `chat:ack`)
- ✓✓ **Delivered:** Entregue ao destinatário
- ✓✓ **Read:** Lida (em azul)

#### 4. Agrupamento de Mensagens
- Por data (separadores "Hoje", "Ontem", etc)
- Por autor com timebox de 5min
- Timestamp só na última mensagem do grupo

#### 5. Separadores de Data Contextuais
- "Hoje", "Ontem"
- Dias da semana (até 7 dias atrás)
- DD/MM/YYYY para mais antigas

#### 6. Optimistic UI com Retry/Backoff
- Mensagem aparece imediatamente com status "pending"
- Servidor confirma com `chat:ack` trocando `tempId` por `id` real
- Se não confirmar em 5s, faz retry com delays: 1s, 2s, 4s
- Após 3 falhas, marca como "failed"

#### 7. Paginação do Histórico
- Botão "Carregar mais" no topo
- Carrega 30 mensagens por vez
- Usa parâmetro `before=<timestamp>` para cursor pagination
- Mantém posição do scroll após carregar

#### 8. Path Alias `@`
- Configurado em `tsconfig.app.json` e `vite.config.ts`
- Permite imports limpos: `@/stores/chat` ao invés de `../../../stores/chat`

### ✅ TECH-05: Upload de Arquivos e Design Responsivo

#### 1. Sistema de Upload MinIO/S3
- **Armazenamento S3-compatible** com MinIO
- **Presigned URLs** para upload/download direto (bypass backend)
- **Validação de tipo** (imagens, PDFs, ZIP, TXT) e tamanho (15MB máx)
- **Pipeline grant → PUT → confirm:**
  1. `POST /uploads/grant` - Backend gera presigned PUT URL
  2. Cliente faz PUT direto ao MinIO com progresso (0-100%)
  3. `POST /uploads/confirm` - Backend salva referência e emite mensagem

#### 2. AttachmentMenu WhatsApp-Style
- **6 opções coloridas:**
  - 📄 Documento (roxo) - PDFs, DOCs, XLS, TXT, ZIP
  - 📷 Câmera (rosa) - Captura com camera do dispositivo
  - 🖼️ Galeria (azul-verde) - Imagens da galeria
  - 🎵 Áudio (laranja) - Arquivos de áudio
  - 📍 Localização (verde) - Em desenvolvimento
  - 👤 Contato (azul) - Em desenvolvimento
- **Grid layout:** 3 colunas (desktop), 2 colunas (mobile)
- **Animação:** Fade-in sequencial com delays
- **Múltiplos arquivos:** Suporta seleção múltipla

#### 3. Design System Responsivo (Mobile-First)
- **Breakpoints:**
  - `xs`: 0px (mobile portrait)
  - `sm`: 600px (mobile landscape)
  - `md`: 960px (tablet portrait)
  - `lg`: 1264px (tablet landscape / small desktop)
  - `xl`: 1904px (desktop)
- **Media Queries:** min-width, max-width, only, portrait/landscape, touch/mouse
- **Composables:** `useBreakpoint()` para detecção reativa
- **Helper:** `responsive()` para valores dinâmicos

#### 4. Componentes Responsivos
- **DSMessageBubble:**
  - Mobile: 90% width, 200px images, 8-12px padding
  - Tablet: 75% width
  - Desktop: 65% width, 300px images
- **ChatView:**
  - Mobile: 16px padding, 4px scrollbar, FAB 80px/16px
  - Tablet: 20px padding
  - Desktop: 24px padding, 8px scrollbar
- **AttachmentMenu:**
  - Mobile: 2-col grid, 240px width, 11px font
  - Desktop: 3-col grid, 280px width, 12px font

#### 5. UX Enhancements
- **Clip Icon WhatsApp:** Rotação 135°, hover/touch effects
- **Upload Progress:** Barra circular (0-100%) no botão send
- **Image Preview:** Clicável (abre em nova aba)
- **File Download:** Link com ícone e nome truncado (ellipsis)
- **Touch Detection:** Efeitos diferentes para touch vs mouse

---

## Fluxos de Dados

### Fluxo 1: Registro de Usuário

```
Cliente                    Servidor                  MongoDB
  |                           |                         |
  |-- POST /register -------->|                         |
  |   {username, password}    |                         |
  |                           |                         |
  |                           |-- hash password ------->|
  |                           |                         |
  |                           |-- insert user --------->|
  |                           |<-- user._id ------------|
  |                           |                         |
  |<-- Token JWT --------------|                         |
  |   {access_token, user}    |                         |
```

### Fluxo 2: Login

```
Cliente                    Servidor                  MongoDB
  |                           |                         |
  |-- POST /login ----------->|                         |
  |   {username, password}    |                         |
  |                           |                         |
  |                           |-- find user ----------->|
  |                           |<-- user doc ------------|
  |                           |                         |
  |                           |-- verify password ----->|
  |                           |                         |
  |<-- Token JWT --------------|                         |
```

### Fluxo 3: Envio de Mensagem (Optimistic UI)

```
Cliente                    Servidor                  MongoDB
  |                           |                         |
  |-- Adiciona msg (tempId) --|                         |
  |   status: pending         |                         |
  |                           |                         |
  |-- emit chat:send -------->|                         |
  |   {text, tempId}          |                         |
  |                           |                         |
  |                           |-- validate ------------->|
  |                           |-- insert doc ----------->|
  |                           |<-- insertedId ----------|
  |                           |                         |
  |<-- emit chat:ack ---------|                         |
  |   {tempId, id, timestamp} |                         |
  |                           |                         |
  |-- Atualiza msg ---------- |                         |
  |   tempId → id             |                         |
  |   status: sent            |                         |
  |                           |                         |
  |<-- broadcast chat:new-message ---|                  |
  |   (para outros clientes)  |                         |
```

### Fluxo 4: Retry com Backoff

```
Cliente                                 Servidor
  |                                        |
  |-- emit chat:send (tentativa 1) ------>| ❌ timeout
  |                                        |
  |-- aguarda 5s sem ACK ------------------|
  |-- emit chat:send (tentativa 2) ------>| ❌ timeout
  |   (delay 1s)                           |
  |                                        |
  |-- aguarda 5s sem ACK ------------------|
  |-- emit chat:send (tentativa 3) ------>| ❌ timeout
  |   (delay 2s)                           |
  |                                        |
  |-- aguarda 5s sem ACK ------------------|
  |-- emit chat:send (tentativa 4) ------>| ❌ timeout
  |   (delay 4s)                           |
  |                                        |
  |-- Marca status: failed -----------------|
```

### Fluxo 5: Indicador de Digitação

```
Cliente A                  Servidor               Cliente B
  |                           |                       |
  |-- Digita no input --------|                       |
  |                           |                       |
  |-- emit chat:typing ------>|                       |
  |   {isTyping: true}        |                       |
  |                           |                       |
  |                           |-- broadcast --------->|
  |                           |   skip_sid: A         |
  |                           |                       |
  |                           |                       |-- Exibe "A está digitando"
  |                           |                       |
  |-- 1s sem digitar ---------|                       |
  |                           |                       |
  |-- emit chat:typing ------>|                       |
  |   {isTyping: false}       |                       |
  |                           |                       |
  |                           |-- broadcast --------->|
  |                           |                       |
  |                           |                       |-- Remove indicador
```

### Fluxo 6: Confirmação de Leitura

```
Cliente A                  Servidor               MongoDB
  |                           |                       |
  |-- Scroll to bottom -------|                       |
  |                           |                       |
  |-- emit chat:read -------->|                       |
  |   {messageIds: [...]}     |                       |
  |                           |                       |
  |                           |-- update_many ------->|
  |                           |   {status: "read"}    |
  |                           |<-- result ------------|
  |                           |                       |
  |<-- broadcast chat:read ---|                       |
  |   (para outros clientes)  |                       |
  |                           |                       |
  |-- Atualiza status ícones --|                       |
  |   ✓ → ✓✓ (azul)          |                       |
```

---

## Storage (MinIO/S3)

### Arquitetura de Upload

```
Cliente                    Backend                   MinIO S3
  |                           |                         |
  |-- 1. Request Grant ------>|                         |
  |   POST /uploads/grant     |                         |
  |   {filename, mimetype,    |                         |
  |    size}                  |                         |
  |                           |                         |
  |                           |-- validate ------------->
  |                           |-- generate_key -------->
  |                           |-- presign_put(key) ---->
  |                           |                         |
  |<-- {key, putUrl} ---------|                         |
  |                           |                         |
  |-- 2. Upload File ----------------------PUT-------->|
  |   XMLHttpRequest                                   |
  |   + Content-Type                                   |
  |   + onprogress (0-100%)                            |
  |                           |                         |
  |<----------------------- 200 OK ---------------------|
  |                           |                         |
  |-- 3. Confirm Upload ----->|                         |
  |   POST /uploads/confirm   |                         |
  |   {key, filename,         |                         |
  |    mimetype, author}      |                         |
  |                           |                         |
  |                           |-- insert message ------->MongoDB
  |                           |   {attachment: {...}}   |
  |                           |-- presign_get(key) ---->|
  |                           |                         |
  |<-- {message} -------------|                         |
  |   {id, attachment, url}   |                         |
  |                           |                         |
  |                           |-- broadcast ----------->|
  |<-- chat:new-message ------|   Socket.IO            |
```

### Configuração MinIO

Ver documentação completa em [`MINIO_CORS_SETUP.md`](MINIO_CORS_SETUP.md).

**Principais recursos:**
- URLs pré-assinadas (PUT 5min, GET 1h)
- Validação de tipo (images, PDFs, ZIP, TXT) e tamanho (15MB)
- Bucket privado com acesso via presigned URLs
- Sem necessidade de CORS (presigned bypass navegador)

---

## Design System Responsivo

### Breakpoints Mobile-First

- `xs: 0px` - Mobile portrait
- `sm: 600px` - Mobile landscape
- `md: 960px` - Tablet portrait
- `lg: 1264px` - Tablet landscape / small desktop  
- `xl: 1904px` - Desktop

**Composables:** `useBreakpoint()`, `responsive()`  
**Media Queries:** min-width, max-width, only, touch/mouse, portrait/landscape

### Componentes Adaptáveis

- **DSMessageBubble:** 90% (mobile) → 65% (desktop) width
- **AttachmentMenu:** Grid 2-col (mobile) → 3-col (desktop)
- **ChatView:** Padding 16px → 24px, Scrollbar 4px → 8px

Ver código completo nos componentes do design system.

---

## Migração Node.js → Python

### Motivação

**Por que Python?**
- FastAPI é extremamente rápido (baseado em Starlette e Pydantic)
- Assíncrono nativo com `async/await`
- Validação automática com Pydantic (type hints)
- Documentação automática (Swagger/ReDoc)
- Motor é mais simples que Prisma para MongoDB
- Python é mais comum em projetos de IA/ML (futuro)

### Comparação

| Aspecto | Node.js (antes) | Python (agora) |
|---------|----------------|----------------|
| Framework | Express | FastAPI |
| Socket.IO | socket.io (JS) | python-socketio |
| ORM | Prisma | Motor (driver nativo) |
| Validação | Zod | Pydantic |
| Async | Promises | async/await nativo |
| Tipagem | TypeScript | Type hints |
| Hot-reload | tsx/ts-node | uvicorn --reload |
| Build | tsc | Nenhum (Python interpretado) |
| Performance | Muito rápido | Muito rápido (FastAPI) |

### Desafios da Migração

1. **Socket.IO syntax:** JavaScript `io.emit()` → Python `await sio.emit()`
2. **Async everywhere:** Todas as operações MongoDB são `await`
3. **ObjectId:** `string` no JS → `ObjectId()` no Python → `str()` para frontend
4. **Timestamps:** `Date.now()` → `datetime.utcnow()` → `.timestamp() * 1000`
5. **Environment:** `process.env` → `os.getenv()`

---

## Conclusão

Este projeto demonstra:

- ✅ **Arquitetura Full-Stack Moderna:** SPA + API assíncrona + NoSQL + Object Storage
- ✅ **Real-Time com Socket.IO:** Comunicação bidirecional eficiente
- ✅ **Autenticação Segura:** JWT + bcrypt + token expiration
- ✅ **UX de Qualidade:** Optimistic UI, retry, typing, status, grouping, responsividade
- ✅ **Upload Seguro:** Presigned URLs + validação + progresso
- ✅ **Design Responsivo:** Mobile-first com breakpoints adaptativos
- ✅ **Type Safety:** TypeScript no front + Pydantic no back
- ✅ **DevOps Friendly:** Docker Compose para dev local
- ✅ **Escalável:** MongoDB replica set, MinIO S3, paginação, retry logic

**Próximos Passos Recomendados:**
- Implementar salas de chat (rooms)
- Compartilhamento de localização e contatos
- Upload de áudio e gravação de voz
- Testes unitários (pytest + vitest)
- CI/CD com GitHub Actions
- Antivírus para arquivos enviados
- Deploy em produção (Railway + Vercel + MongoDB Atlas + S3)

---

**Criado em:** Novembro de 2025  
**Aulas:** TECH-01 a TECH-05  
**Stack:** Vue 3 + FastAPI + MongoDB + MinIO S3 + Socket.IO + Docker

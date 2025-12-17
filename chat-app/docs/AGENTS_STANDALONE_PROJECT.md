# 🤖 Projeto Standalone - Sistema de Agentes

Este documento descreve como criar um projeto independente focado exclusivamente no sistema de agentes conversacionais com IA, incluindo agentes customizáveis, agendamento inteligente e integração com calendário.

## 📋 Índice

- [Visão Geral](#visão-geral)
- [Arquitetura](#arquitetura)
- [Frontend](#frontend)
- [Backend](#backend)
- [DevOps](#devops)
- [Configuração](#configuração)
- [Deploy](#deploy)

---

## 🎯 Visão Geral

### Funcionalidades Principais

1. **Chat com Agentes IA**: Interface de conversação em tempo real com múltiplos agentes
2. **Agentes Customizáveis**: Criação de bots personalizados com prompts e especialidades
3. **Agendamento Inteligente**: Detecção de intenção de agendamento e seletor de horários
4. **NLU Avançada**: Processamento de linguagem natural com GPT
5. **Auto-criação de Tarefas**: Conversão automática de conversas em tarefas/eventos

### Stack Tecnológica

**Frontend:**
- Vue 3 (Composition API + TypeScript)
- Vuetify 3 (Material Design)
- Socket.IO Client
- Pinia (State Management)
- Axios (HTTP Client)
- Vite (Build Tool)

**Backend:**
- Python 3.11+ com FastAPI
- Socket.IO (Python)
- OpenAI API (GPT-4)
- MongoDB (armazenamento de mensagens e bots)
- Google Calendar API (agendamento)
- JWT (autenticação)

**DevOps:**
- Docker + Docker Compose
- Nginx (reverse proxy)
- Redis (opcional, para cache/filas)

---

## 🏗️ Arquitetura

```
┌─────────────────┐
│   Frontend      │
│   (Vue 3)       │
│                 │
│  - AgentChat    │
│  - SlotPicker   │
│  - BotCreator   │
└────────┬────────┘
         │
    Socket.IO + REST
         │
┌────────▼────────┐
│   Backend       │
│  (FastAPI)      │
│                 │
│  - Socket       │
│  - REST APIs    │
│  - NLU Engine   │
│  - AI Agents    │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
┌───▼───┐ ┌──▼────┐
│MongoDB│ │OpenAI │
└───────┘ └───────┘
```

### Fluxo de Comunicação

1. **Conexão**: Cliente conecta via Socket.IO com JWT
2. **Envio de Mensagem**: `agent:send` → Backend processa → OpenAI
3. **Resposta**: Backend emite `agent:message` com resposta
4. **Agendamento**: Se detectar intenção → `agent:show-slot-picker`
5. **Confirmação**: Cliente confirma slot → `agent:schedule-confirm`

---

## 🎨 Frontend

### Estrutura de Diretórios

```
agents-frontend/
├── src/
│   ├── components/
│   │   ├── AgentChatPane.vue
│   │   ├── SlotPicker.vue
│   │   ├── CustomBotCreator.vue
│   │   ├── MessageBubble.vue
│   │   └── TypingIndicator.vue
│   ├── composables/
│   │   ├── useAgentSocket.ts
│   │   ├── useCustomAgents.ts
│   │   └── useCalendar.ts
│   ├── stores/
│   │   ├── auth.ts
│   │   └── agents.ts
│   ├── types/
│   │   └── agent.types.ts
│   ├── App.vue
│   └── main.ts
├── package.json
├── vite.config.ts
├── tsconfig.json
└── .env
```

### Componentes Principais

#### 1. AgentChatPane.vue

```vue
<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useAgentSocket } from '@/composables/useAgentSocket'
import { useAuthStore } from '@/stores/auth'

interface Props {
  agentKey: string
  title: string
  emoji: string
  contactId: string
}

const props = defineProps<Props>()

const authStore = useAuthStore()
const { 
  messages, 
  suggestions, 
  isTyping, 
  error,
  showSlotPicker,
  sendMessage, 
  requestSummary,
  setAutoCreate,
  confirmSchedule,
  connect,
  disconnect 
} = useAgentSocket(props.agentKey, props.contactId)

const messageText = ref('')
const autoCreate = ref(false)

const send = () => {
  if (!messageText.value.trim()) return
  
  sendMessage({
    agentKey: props.agentKey,
    message: messageText.value,
    userId: authStore.userId,
    userName: authStore.userName,
    contactId: props.contactId
  })
  
  messageText.value = ''
}

onMounted(() => {
  connect(authStore.token)
})

onUnmounted(() => {
  disconnect()
})
</script>

<template>
  <v-card class="agent-chat-pane">
    <v-card-title>
      <span class="agent-emoji">{{ emoji }}</span>
      {{ title }}
      <v-spacer />
      <v-btn icon @click="$emit('close')">
        <v-icon>mdi-close</v-icon>
      </v-btn>
    </v-card-title>

    <v-card-text class="messages-container">
      <div v-for="msg in messages" :key="msg.id">
        <MessageBubble 
          :author="msg.author"
          :text="msg.text"
          :timestamp="msg.timestamp"
          :is-self="msg.author === authStore.userName"
        />
      </div>
      
      <TypingIndicator v-if="isTyping" />
      
      <v-alert v-if="error" type="error">
        {{ error }}
      </v-alert>

      <div v-if="suggestions.length" class="suggestions">
        <v-chip 
          v-for="(sug, i) in suggestions" 
          :key="i"
          @click="messageText = sug"
        >
          {{ sug }}
        </v-chip>
      </div>
    </v-card-text>

    <SlotPicker 
      v-if="showSlotPicker"
      :agent-key="agentKey"
      @confirm="confirmSchedule"
      @close="showSlotPicker = false"
    />

    <v-card-actions>
      <v-switch
        v-model="autoCreate"
        label="Auto-criar tarefa"
        @update:model-value="setAutoCreate"
      />
      
      <v-spacer />
      
      <v-text-field
        v-model="messageText"
        placeholder="Digite sua mensagem..."
        @keyup.enter="send"
      />
      
      <v-btn icon @click="send">
        <v-icon>mdi-send</v-icon>
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<style scoped>
.agent-chat-pane {
  height: 600px;
  display: flex;
  flex-direction: column;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
}

.agent-emoji {
  font-size: 24px;
  margin-right: 8px;
}

.suggestions {
  display: flex;
  gap: 8px;
  margin-top: 16px;
}
</style>
```

#### 2. SlotPicker.vue

```vue
<script setup lang="ts">
import { ref, watch } from 'vue'
import { useCalendar } from '@/composables/useCalendar'

interface Props {
  agentKey: string
}

const props = defineProps<Props>()
const emit = defineEmits<{
  confirm: [payload: { date: string; time: string; email: string; phone: string }]
  close: []
}>()

const selectedDate = ref('')
const selectedSlot = ref<{ start: string; end: string } | null>(null)
const customerEmail = ref('')
const customerPhone = ref('')

const { availableSlots, loading, fetchSlots } = useCalendar()

watch(selectedDate, (newDate) => {
  if (newDate) {
    fetchSlots(newDate, 60)
  }
})

const confirm = () => {
  if (!selectedSlot.value || !customerEmail.value) return
  
  emit('confirm', {
    date: selectedDate.value,
    time: selectedSlot.value.start,
    email: customerEmail.value,
    phone: customerPhone.value
  })
}
</script>

<template>
  <v-dialog :model-value="true" max-width="600px">
    <v-card>
      <v-card-title>Agendar Reunião</v-card-title>
      
      <v-card-text>
        <v-date-picker 
          v-model="selectedDate"
          :min="new Date().toISOString().split('T')[0]"
        />
        
        <div v-if="loading">Carregando horários...</div>
        
        <v-list v-else-if="availableSlots.length">
          <v-list-item
            v-for="(slot, i) in availableSlots"
            :key="i"
            @click="selectedSlot = slot"
            :active="selectedSlot === slot"
          >
            {{ slot.start }} - {{ slot.end }}
          </v-list-item>
        </v-list>
        
        <v-text-field
          v-model="customerEmail"
          label="E-mail"
          type="email"
          required
        />
        
        <v-text-field
          v-model="customerPhone"
          label="Telefone (opcional)"
        />
      </v-card-text>
      
      <v-card-actions>
        <v-btn @click="emit('close')">Cancelar</v-btn>
        <v-spacer />
        <v-btn 
          color="primary" 
          @click="confirm"
          :disabled="!selectedSlot || !customerEmail"
        >
          Confirmar
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>
```

#### 3. CustomBotCreator.vue

```vue
<script setup lang="ts">
import { ref } from 'vue'
import { useCustomAgents } from '@/composables/useCustomAgents'

const emit = defineEmits<{ close: [] }>()

const { createAgent, loading } = useCustomAgents()

const form = ref({
  name: '',
  emoji: '🤖',
  prompt: '',
  specialties: [] as string[],
  openaiApiKey: '',
  openaiAccount: ''
})

const newSpecialty = ref('')

const addSpecialty = () => {
  if (newSpecialty.value && !form.value.specialties.includes(newSpecialty.value)) {
    form.value.specialties.push(newSpecialty.value)
    newSpecialty.value = ''
  }
}

const removeSpecialty = (specialty: string) => {
  form.value.specialties = form.value.specialties.filter(s => s !== specialty)
}

const submit = async () => {
  try {
    await createAgent(form.value)
    emit('close')
  } catch (error) {
    console.error('Erro ao criar agente:', error)
  }
}
</script>

<template>
  <v-dialog :model-value="true" max-width="800px">
    <v-card>
      <v-card-title>Criar Agente Personalizado</v-card-title>
      
      <v-card-text>
        <v-text-field
          v-model="form.name"
          label="Nome do Agente"
          required
        />
        
        <v-text-field
          v-model="form.emoji"
          label="Emoji"
          required
        />
        
        <v-textarea
          v-model="form.prompt"
          label="Prompt do Sistema"
          rows="6"
          hint="Defina a personalidade e comportamento do agente"
        />
        
        <div class="specialties-section">
          <v-text-field
            v-model="newSpecialty"
            label="Adicionar Especialidade"
            @keyup.enter="addSpecialty"
          >
            <template #append>
              <v-btn icon @click="addSpecialty">
                <v-icon>mdi-plus</v-icon>
              </v-btn>
            </template>
          </v-text-field>
          
          <v-chip-group>
            <v-chip
              v-for="specialty in form.specialties"
              :key="specialty"
              closable
              @click:close="removeSpecialty(specialty)"
            >
              {{ specialty }}
            </v-chip>
          </v-chip-group>
        </div>
        
        <v-text-field
          v-model="form.openaiApiKey"
          label="OpenAI API Key"
          type="password"
          hint="Deixe em branco para usar a chave padrão"
        />
        
        <v-text-field
          v-model="form.openaiAccount"
          label="Conta OpenAI (opcional)"
        />
      </v-card-text>
      
      <v-card-actions>
        <v-btn @click="emit('close')">Cancelar</v-btn>
        <v-spacer />
        <v-btn 
          color="primary" 
          @click="submit"
          :loading="loading"
          :disabled="!form.name || !form.prompt"
        >
          Criar Agente
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<style scoped>
.specialties-section {
  margin: 16px 0;
}
</style>
```

### Composables

#### useAgentSocket.ts

```typescript
import { ref, Ref } from 'vue'
import { io, Socket } from 'socket.io-client'

interface Message {
  id: string
  author: string
  text: string
  timestamp: number
  nlp?: any
}

interface SendMessagePayload {
  agentKey: string
  message: string
  userId: string
  userName: string
  contactId: string
}

export function useAgentSocket(agentKey: string, contactId: string) {
  const socket: Ref<Socket | null> = ref(null)
  const messages: Ref<Message[]> = ref([])
  const suggestions: Ref<string[]> = ref([])
  const isTyping = ref(false)
  const error: Ref<string | null> = ref(null)
  const showSlotPicker = ref(false)
  const slotPickerData = ref<any>(null)

  const connect = (token: string) => {
    const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:3000'
    
    socket.value = io(apiUrl, {
      auth: { token }
    })

    // Event listeners
    socket.value.on('agent:message', (data) => {
      if (data.agentKey === agentKey && data.contactId === contactId) {
        messages.value.push({
          id: data.id,
          author: data.author,
          text: data.text,
          timestamp: data.timestamp,
          nlp: data.nlp
        })
        isTyping.value = false
      }
    })

    socket.value.on('agent:suggestions', (data) => {
      if (data.agentKey === agentKey && data.contactId === contactId) {
        suggestions.value = data.suggestions
      }
    })

    socket.value.on('agent:error', (data) => {
      if (data.agentKey === agentKey) {
        error.value = data.error
        isTyping.value = false
      }
    })

    socket.value.on('agent:show-slot-picker', (data) => {
      if (data.agentKey === agentKey) {
        showSlotPicker.value = true
        slotPickerData.value = data
      }
    })

    socket.value.on('agent:summary', (data) => {
      console.log('Summary received:', data)
    })

    socket.value.on('agent:auto-create-updated', (data) => {
      console.log('Auto-create updated:', data)
    })

    socket.value.on('agent:schedule-confirm', (data) => {
      console.log('Schedule confirmed:', data)
    })
  }

  const disconnect = () => {
    if (socket.value) {
      socket.value.disconnect()
      socket.value = null
    }
  }

  const sendMessage = (payload: SendMessagePayload) => {
    if (!socket.value) return
    
    isTyping.value = true
    error.value = null
    
    socket.value.emit('agent:send', payload)
  }

  const requestSummary = () => {
    if (!socket.value) return
    
    socket.value.emit('agent:request-summary', {
      agentKey,
      contactId
    })
  }

  const setAutoCreate = (autoCreate: boolean) => {
    if (!socket.value) return
    
    socket.value.emit('agent:set-auto-create', {
      agentKey,
      autoCreate
    })
  }

  const confirmSchedule = (payload: {
    date: string
    time: string
    email: string
    phone: string
  }) => {
    if (!socket.value) return
    
    socket.value.emit('agent:schedule-confirm', {
      agentKey,
      contactId,
      ...payload
    })
    
    showSlotPicker.value = false
  }

  return {
    messages,
    suggestions,
    isTyping,
    error,
    showSlotPicker,
    sendMessage,
    requestSummary,
    setAutoCreate,
    confirmSchedule,
    connect,
    disconnect
  }
}
```

#### useCustomAgents.ts

```typescript
import { ref } from 'vue'
import axios from 'axios'
import { useAuthStore } from '@/stores/auth'

interface CustomAgentPayload {
  name: string
  emoji: string
  prompt: string
  specialties: string[]
  openaiApiKey?: string
  openaiAccount?: string
}

interface CustomAgentSummary {
  key: string
  name: string
  emoji: string
  specialties: string[]
  created_at: string
}

export function useCustomAgents() {
  const authStore = useAuthStore()
  const loading = ref(false)
  const agents = ref<CustomAgentSummary[]>([])
  const error = ref<string | null>(null)

  const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:3000'

  const getHeaders = () => ({
    Authorization: `Bearer ${authStore.token}`
  })

  const listAgents = async () => {
    loading.value = true
    error.value = null
    
    try {
      const response = await axios.get(`${apiUrl}/custom-bots`, {
        headers: getHeaders()
      })
      agents.value = response.data.bots
    } catch (err: any) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  const createAgent = async (payload: CustomAgentPayload) => {
    loading.value = true
    error.value = null
    
    try {
      const response = await axios.post(
        `${apiUrl}/custom-bots`,
        payload,
        { headers: getHeaders() }
      )
      await listAgents()
      return response.data.bot
    } catch (err: any) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  const deleteAgent = async (key: string) => {
    loading.value = true
    error.value = null
    
    try {
      await axios.delete(`${apiUrl}/custom-bots/${key}`, {
        headers: getHeaders()
      })
      await listAgents()
    } catch (err: any) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  return {
    loading,
    agents,
    error,
    listAgents,
    createAgent,
    deleteAgent
  }
}
```

#### useCalendar.ts

```typescript
import { ref } from 'vue'
import axios from 'axios'
import { useAuthStore } from '@/stores/auth'

interface TimeSlot {
  start: string
  end: string
}

export function useCalendar() {
  const authStore = useAuthStore()
  const loading = ref(false)
  const availableSlots = ref<TimeSlot[]>([])
  const error = ref<string | null>(null)

  const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:3000'

  const fetchSlots = async (date: string, durationMinutes: number = 60) => {
    loading.value = true
    error.value = null
    
    try {
      const response = await axios.get(
        `${apiUrl}/calendar/available-slots`,
        {
          params: { date, duration_minutes: durationMinutes },
          headers: {
            Authorization: `Bearer ${authStore.token}`
          }
        }
      )
      availableSlots.value = response.data.available_slots
    } catch (err: any) {
      error.value = err.message
      availableSlots.value = []
    } finally {
      loading.value = false
    }
  }

  return {
    loading,
    availableSlots,
    error,
    fetchSlots
  }
}
```

### Configuração (package.json)

```json
{
  "name": "agents-frontend",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vue-tsc && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "vue": "^3.4.0",
    "vuetify": "^3.5.0",
    "pinia": "^2.1.7",
    "socket.io-client": "^4.7.0",
    "axios": "^1.6.0"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^5.0.0",
    "typescript": "^5.3.0",
    "vite": "^5.0.0",
    "vue-tsc": "^1.8.27"
  }
}
```

### Variáveis de Ambiente (.env)

```env
VITE_API_URL=http://localhost:3000
```

---

## ⚙️ Backend

### Estrutura de Diretórios

```
agents-backend/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── auth.py
│   ├── database.py
│   ├── models.py
│   ├── socket_manager.py
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── custom_bots.py
│   │   ├── calendar.py
│   │   └── agents.py
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── core.py
│   │   ├── nlu.py
│   │   ├── context_loader.py
│   │   └── scheduling.py
│   └── integrations/
│       ├── __init__.py
│       ├── openai_client.py
│       └── google_calendar.py
├── requirements.txt
├── Dockerfile
└── .env
```

### Principais Arquivos

#### main.py

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import socketio

from app.config import settings
from app.socket_manager import SocketManager
from app.routers import custom_bots, calendar, agents

# FastAPI app
app = FastAPI(title="Agents API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Socket.IO
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins=settings.CORS_ORIGINS
)

socket_manager = SocketManager(sio)

# Combine ASGI apps
socket_app = socketio.ASGIApp(sio, app)

# Register routers
app.include_router(custom_bots.router, prefix="/custom-bots", tags=["Custom Bots"])
app.include_router(calendar.router, prefix="/calendar", tags=["Calendar"])
app.include_router(agents.router, prefix="/agents", tags=["Agents"])

@app.get("/")
async def root():
    return {"message": "Agents API"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:socket_app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.DEBUG
    )
```

#### socket_manager.py

```python
import socketio
from typing import Dict, Any
from app.auth import verify_token
from app.agents.core import AgentCore

class SocketManager:
    def __init__(self, sio: socketio.AsyncServer):
        self.sio = sio
        self.agent_core = AgentCore()
        self.setup_handlers()
    
    def setup_handlers(self):
        @self.sio.event
        async def connect(sid, environ, auth):
            """Handle client connection"""
            try:
                token = auth.get('token')
                if not token:
                    return False
                
                user = await verify_token(token)
                if not user:
                    return False
                
                # Store user info in session
                await self.sio.save_session(sid, {
                    'user_id': user['id'],
                    'user_name': user['name']
                })
                
                print(f"Client {sid} connected as {user['name']}")
                return True
                
            except Exception as e:
                print(f"Connection error: {e}")
                return False
        
        @self.sio.event
        async def disconnect(sid):
            """Handle client disconnection"""
            print(f"Client {sid} disconnected")
        
        @self.sio.event
        async def agent_send(sid, data: Dict[str, Any]):
            """Handle agent message from client"""
            try:
                session = await self.sio.get_session(sid)
                
                agent_key = data.get('agentKey')
                message = data.get('message')
                contact_id = data.get('contactId')
                
                if not all([agent_key, message, contact_id]):
                    await self.sio.emit('agent:error', {
                        'agentKey': agent_key,
                        'contactId': contact_id,
                        'error': 'Missing required fields'
                    }, room=sid)
                    return
                
                # Process message with agent
                response = await self.agent_core.process_message(
                    agent_key=agent_key,
                    message=message,
                    contact_id=contact_id,
                    user_id=session['user_id'],
                    user_name=session['user_name']
                )
                
                # Emit response
                await self.sio.emit('agent:message', {
                    'agentKey': agent_key,
                    'contactId': contact_id,
                    'id': response['id'],
                    'author': response['author'],
                    'text': response['text'],
                    'timestamp': response['timestamp'],
                    'nlp': response.get('nlp')
                }, room=sid)
                
                # Check for scheduling intent
                if response.get('nlp', {}).get('intent') == 'schedule_meeting':
                    await self.sio.emit('agent:show-slot-picker', {
                        'agentKey': agent_key,
                        'contactId': contact_id,
                        'customerEmail': response.get('nlp', {}).get('email'),
                        'customerPhone': response.get('nlp', {}).get('phone')
                    }, room=sid)
                
                # Emit suggestions if any
                if response.get('suggestions'):
                    await self.sio.emit('agent:suggestions', {
                        'agentKey': agent_key,
                        'contactId': contact_id,
                        'suggestions': response['suggestions']
                    }, room=sid)
                
            except Exception as e:
                print(f"Error processing agent message: {e}")
                await self.sio.emit('agent:error', {
                    'agentKey': data.get('agentKey'),
                    'contactId': data.get('contactId'),
                    'error': str(e)
                }, room=sid)
        
        @self.sio.event
        async def agent_set_auto_create(sid, data: Dict[str, Any]):
            """Handle auto-create setting"""
            try:
                agent_key = data.get('agentKey')
                auto_create = data.get('autoCreate')
                
                # Update setting in database
                await self.agent_core.set_auto_create(agent_key, auto_create)
                
                await self.sio.emit('agent:auto-create-updated', {
                    'agentKey': agent_key,
                    'autoCreate': auto_create
                }, room=sid)
                
            except Exception as e:
                print(f"Error setting auto-create: {e}")
        
        @self.sio.event
        async def agent_request_summary(sid, data: Dict[str, Any]):
            """Handle summary request"""
            try:
                agent_key = data.get('agentKey')
                contact_id = data.get('contactId')
                
                summary = await self.agent_core.generate_summary(
                    agent_key, contact_id
                )
                
                await self.sio.emit('agent:summary', {
                    'agentKey': agent_key,
                    'contactId': contact_id,
                    'summary': summary
                }, room=sid)
                
            except Exception as e:
                print(f"Error generating summary: {e}")
        
        @self.sio.event
        async def agent_schedule_confirm(sid, data: Dict[str, Any]):
            """Handle schedule confirmation"""
            try:
                agent_key = data.get('agentKey')
                contact_id = data.get('contactId')
                date = data.get('date')
                time = data.get('time')
                email = data.get('email')
                phone = data.get('phone')
                
                # Create calendar event
                event = await self.agent_core.create_calendar_event(
                    agent_key=agent_key,
                    contact_id=contact_id,
                    date=date,
                    time=time,
                    customer_email=email,
                    customer_phone=phone
                )
                
                await self.sio.emit('agent:schedule-confirm', {
                    'agentKey': agent_key,
                    'contactId': contact_id,
                    'event': event
                }, room=sid)
                
                # Send confirmation message
                await self.sio.emit('agent:message', {
                    'agentKey': agent_key,
                    'contactId': contact_id,
                    'id': f"confirm_{event['id']}",
                    'author': 'System',
                    'text': f"✅ Reunião agendada para {date} às {time}",
                    'timestamp': int(time.time() * 1000)
                }, room=sid)
                
            except Exception as e:
                print(f"Error confirming schedule: {e}")
                await self.sio.emit('agent:error', {
                    'agentKey': data.get('agentKey'),
                    'contactId': data.get('contactId'),
                    'error': 'Erro ao agendar reunião'
                }, room=sid)
```

#### agents/core.py

```python
from typing import Dict, Any, List, Optional
import uuid
from datetime import datetime
from app.integrations.openai_client import OpenAIClient
from app.agents.nlu import NLUEngine
from app.agents.context_loader import ContextLoader
from app.database import get_database

class AgentCore:
    def __init__(self):
        self.openai_client = OpenAIClient()
        self.nlu_engine = NLUEngine()
        self.context_loader = ContextLoader()
        self.db = get_database()
    
    async def process_message(
        self,
        agent_key: str,
        message: str,
        contact_id: str,
        user_id: str,
        user_name: str
    ) -> Dict[str, Any]:
        """Process incoming message and generate response"""
        
        # Load agent configuration
        agent = await self._get_agent(agent_key)
        if not agent:
            raise ValueError(f"Agent {agent_key} not found")
        
        # Load conversation context
        context = await self.context_loader.load_context(
            agent_key, contact_id
        )
        
        # NLU analysis
        nlp_result = await self.nlu_engine.analyze(message)
        
        # Build messages for GPT
        messages = self._build_messages(
            agent, context, message, nlp_result
        )
        
        # Call OpenAI
        gpt_response = await self.openai_client.chat_completion(
            messages=messages,
            model=agent.get('model', 'gpt-4'),
            temperature=agent.get('temperature', 0.7)
        )
        
        response_text = gpt_response['choices'][0]['message']['content']
        
        # Save messages to database
        message_id = str(uuid.uuid4())
        timestamp = int(datetime.now().timestamp() * 1000)
        
        await self.db.messages.insert_many([
            {
                'id': str(uuid.uuid4()),
                'agent_key': agent_key,
                'contact_id': contact_id,
                'author': user_name,
                'text': message,
                'timestamp': timestamp,
                'nlp': nlp_result
            },
            {
                'id': message_id,
                'agent_key': agent_key,
                'contact_id': contact_id,
                'author': agent['name'],
                'text': response_text,
                'timestamp': timestamp + 100
            }
        ])
        
        # Generate suggestions
        suggestions = await self._generate_suggestions(
            agent_key, response_text, nlp_result
        )
        
        return {
            'id': message_id,
            'author': agent['name'],
            'text': response_text,
            'timestamp': timestamp + 100,
            'nlp': nlp_result,
            'suggestions': suggestions
        }
    
    async def _get_agent(self, agent_key: str) -> Optional[Dict]:
        """Get agent configuration from database"""
        return await self.db.agents.find_one({'key': agent_key})
    
    def _build_messages(
        self,
        agent: Dict,
        context: List[Dict],
        message: str,
        nlp_result: Dict
    ) -> List[Dict]:
        """Build message array for GPT"""
        messages = [
            {
                'role': 'system',
                'content': agent.get('prompt', 'You are a helpful assistant.')
            }
        ]
        
        # Add context messages
        for msg in context[-10:]:  # Last 10 messages
            messages.append({
                'role': 'user' if msg['author'] != agent['name'] else 'assistant',
                'content': msg['text']
            })
        
        # Add current message
        messages.append({
            'role': 'user',
            'content': message
        })
        
        return messages
    
    async def _generate_suggestions(
        self,
        agent_key: str,
        response: str,
        nlp_result: Dict
    ) -> List[str]:
        """Generate suggested follow-up messages"""
        # Simple implementation - can be enhanced with GPT
        suggestions = []
        
        if nlp_result.get('intent') == 'schedule_meeting':
            suggestions = [
                "Gostaria de agendar para amanhã",
                "Prefiro pela manhã",
                "Tem disponibilidade na próxima semana?"
            ]
        elif '?' in response:
            suggestions = [
                "Sim",
                "Não",
                "Preciso de mais informações"
            ]
        
        return suggestions
    
    async def set_auto_create(self, agent_key: str, auto_create: bool):
        """Update auto-create setting"""
        await self.db.agents.update_one(
            {'key': agent_key},
            {'$set': {'auto_create': auto_create}}
        )
    
    async def generate_summary(
        self,
        agent_key: str,
        contact_id: str
    ) -> str:
        """Generate conversation summary"""
        messages = await self.db.messages.find({
            'agent_key': agent_key,
            'contact_id': contact_id
        }).sort('timestamp', -1).limit(50).to_list(50)
        
        if not messages:
            return "Nenhuma conversa encontrada."
        
        # Build prompt for summary
        conversation = "\n".join([
            f"{msg['author']}: {msg['text']}"
            for msg in reversed(messages)
        ])
        
        summary_response = await self.openai_client.chat_completion(
            messages=[
                {
                    'role': 'system',
                    'content': 'Resuma a conversa a seguir de forma concisa e objetiva.'
                },
                {
                    'role': 'user',
                    'content': conversation
                }
            ],
            model='gpt-4',
            temperature=0.3
        )
        
        return summary_response['choices'][0]['message']['content']
    
    async def create_calendar_event(
        self,
        agent_key: str,
        contact_id: str,
        date: str,
        time: str,
        customer_email: str,
        customer_phone: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create calendar event"""
        from app.integrations.google_calendar import create_event
        
        agent = await self._get_agent(agent_key)
        
        event = await create_event(
            summary=f"Reunião - {agent['name']}",
            description=f"Agendamento via chat com {customer_email}",
            start_datetime=f"{date}T{time}:00",
            duration_minutes=60,
            attendees=[customer_email]
        )
        
        # Save to database
        await self.db.events.insert_one({
            'id': event['id'],
            'agent_key': agent_key,
            'contact_id': contact_id,
            'date': date,
            'time': time,
            'customer_email': customer_email,
            'customer_phone': customer_phone,
            'google_event_id': event.get('id'),
            'created_at': datetime.now()
        })
        
        return event
```

#### routers/custom_bots.py

```python
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from pydantic import BaseModel
from app.auth import get_current_user
from app.database import get_database
import uuid
from datetime import datetime

router = APIRouter()

class CustomAgentPayload(BaseModel):
    name: str
    emoji: str
    prompt: str
    specialties: List[str]
    openaiApiKey: str = None
    openaiAccount: str = None

class CustomAgentSummary(BaseModel):
    key: str
    name: str
    emoji: str
    specialties: List[str]
    created_at: str

@router.get("", response_model=dict)
async def list_custom_bots(current_user: dict = Depends(get_current_user)):
    """List all custom bots for current user"""
    db = get_database()
    
    bots = await db.agents.find({
        'user_id': current_user['id'],
        'type': 'custom'
    }).to_list(100)
    
    return {
        'bots': [
            CustomAgentSummary(
                key=bot['key'],
                name=bot['name'],
                emoji=bot['emoji'],
                specialties=bot.get('specialties', []),
                created_at=bot['created_at'].isoformat()
            )
            for bot in bots
        ]
    }

@router.post("", response_model=dict)
async def create_custom_bot(
    payload: CustomAgentPayload,
    current_user: dict = Depends(get_current_user)
):
    """Create a new custom bot"""
    db = get_database()
    
    bot_key = f"custom_{uuid.uuid4().hex[:8]}"
    
    bot_data = {
        'key': bot_key,
        'type': 'custom',
        'user_id': current_user['id'],
        'name': payload.name,
        'emoji': payload.emoji,
        'prompt': payload.prompt,
        'specialties': payload.specialties,
        'openai_api_key': payload.openaiApiKey,
        'openai_account': payload.openaiAccount,
        'model': 'gpt-4',
        'temperature': 0.7,
        'auto_create': False,
        'created_at': datetime.now()
    }
    
    await db.agents.insert_one(bot_data)
    
    return {
        'bot': CustomAgentSummary(
            key=bot_key,
            name=payload.name,
            emoji=payload.emoji,
            specialties=payload.specialties,
            created_at=bot_data['created_at'].isoformat()
        )
    }

@router.delete("/{key}")
async def delete_custom_bot(
    key: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a custom bot"""
    db = get_database()
    
    result = await db.agents.delete_one({
        'key': key,
        'user_id': current_user['id'],
        'type': 'custom'
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    return {'success': True}
```

#### routers/calendar.py

```python
from fastapi import APIRouter, Depends, Query
from typing import List
from pydantic import BaseModel
from app.auth import get_current_user
from app.integrations.google_calendar import get_available_slots

router = APIRouter()

class TimeSlot(BaseModel):
    start: str
    end: str

@router.get("/available-slots", response_model=dict)
async def get_available_slots_endpoint(
    date: str = Query(..., description="Date in YYYY-MM-DD format"),
    duration_minutes: int = Query(60, description="Duration in minutes"),
    current_user: dict = Depends(get_current_user)
):
    """Get available time slots for a specific date"""
    try:
        slots = await get_available_slots(date, duration_minutes)
        
        return {
            'available_slots': [
                TimeSlot(start=slot['start'], end=slot['end'])
                for slot in slots
            ]
        }
    except Exception as e:
        return {'available_slots': [], 'error': str(e)}
```

### Configuração (requirements.txt)

```txt
fastapi==0.109.0
uvicorn[standard]==0.27.0
python-socketio==5.11.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
motor==3.3.2
pydantic==2.5.3
python-multipart==0.0.6
openai==1.10.0
google-auth==2.27.0
google-auth-oauthlib==1.2.0
google-api-python-client==2.115.0
python-dotenv==1.0.0
```

### Variáveis de Ambiente (.env)

```env
# Server
PORT=3000
DEBUG=True
CORS_ORIGINS=["http://localhost:5173","http://localhost:3000"]

# Database
MONGODB_URI=mongodb://admin:password@mongodb:27017/agents_db?authSource=admin

# JWT
JWT_SECRET=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440

# OpenAI
OPENAI_API_KEY=sk-your-openai-key

# Google Calendar
GOOGLE_CREDENTIALS_FILE=credentials.json
GOOGLE_CALENDAR_ID=primary
```

---

## 🐳 DevOps

### Dockerfile (Frontend)

```dockerfile
# Build stage
FROM node:18-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
ARG VITE_API_URL
ENV VITE_API_URL=$VITE_API_URL

RUN npm run build

# Production stage
FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

### Dockerfile (Backend)

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

EXPOSE 3000

CMD ["uvicorn", "app.main:socket_app", "--host", "0.0.0.0", "--port", "3000"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  mongodb:
    image: mongo:7
    container_name: agents-mongodb
    restart: unless-stopped
    environment:
      MONGO_INITDB_ROOT_USERNAME: admin
      MONGO_INITDB_ROOT_PASSWORD: password
    ports:
      - "27017:27017"
    volumes:
      - mongodb_data:/data/db
    networks:
      - agents-network

  backend:
    build:
      context: ./agents-backend
      dockerfile: Dockerfile
    container_name: agents-backend
    restart: unless-stopped
    ports:
      - "3000:3000"
    environment:
      - PORT=3000
      - MONGODB_URI=mongodb://admin:password@mongodb:27017/agents_db?authSource=admin
      - JWT_SECRET=${JWT_SECRET:-your-secret-key}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - DEBUG=False
    volumes:
      - ./agents-backend:/app
      - ./credentials.json:/app/credentials.json:ro
    depends_on:
      - mongodb
    networks:
      - agents-network

  frontend:
    build:
      context: ./agents-frontend
      dockerfile: Dockerfile
      args:
        VITE_API_URL: http://localhost:3000
    container_name: agents-frontend
    restart: unless-stopped
    ports:
      - "80:80"
    depends_on:
      - backend
    networks:
      - agents-network

volumes:
  mongodb_data:

networks:
  agents-network:
    driver: bridge
```

### nginx.conf (Frontend)

```nginx
server {
    listen 80;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    # Gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;

    # Frontend routes
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Cache static assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

### Makefile

```makefile
.PHONY: help build up down restart logs clean

help:
	@echo "Comandos disponíveis:"
	@echo "  make build   - Build dos containers"
	@echo "  make up      - Inicia os serviços"
	@echo "  make down    - Para os serviços"
	@echo "  make restart - Reinicia os serviços"
	@echo "  make logs    - Visualiza logs"
	@echo "  make clean   - Remove volumes e imagens"

build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

restart:
	docker-compose restart

logs:
	docker-compose logs -f

clean:
	docker-compose down -v
	docker system prune -af
```

---

## ⚙️ Configuração

### 1. Clonar/Criar Estrutura

```bash
mkdir agents-project
cd agents-project
mkdir agents-frontend agents-backend
```

### 2. Configurar Variáveis

```bash
# Backend
cp agents-backend/.env.example agents-backend/.env

# Frontend
cp agents-frontend/.env.example agents-frontend/.env
```

### 3. Configurar Google Calendar (Opcional)

```bash
# Seguir: https://developers.google.com/calendar/api/quickstart/python
# Baixar credentials.json e colocar na raiz do backend
```

### 4. Instalar Dependências Localmente (Dev)

```bash
# Frontend
cd agents-frontend
npm install

# Backend
cd agents-backend
pip install -r requirements.txt
```

---

## 🚀 Deploy

### Desenvolvimento Local

```bash
# Com Docker
make build
make up

# Ou separadamente
# Backend
cd agents-backend
uvicorn app.main:socket_app --reload --port 3000

# Frontend
cd agents-frontend
npm run dev
```

### Produção

```bash
# Build otimizado
docker-compose -f docker-compose.prod.yml build

# Deploy
docker-compose -f docker-compose.prod.yml up -d

# Verificar logs
docker-compose logs -f backend
```

### Variáveis de Produção

```env
# Backend .env
DEBUG=False
JWT_SECRET=<strong-secret-key>
OPENAI_API_KEY=<your-key>
MONGODB_URI=<production-mongodb-uri>
CORS_ORIGINS=["https://yourdomain.com"]

# Frontend build args
VITE_API_URL=https://api.yourdomain.com
```

---

## 📊 Monitoramento

### Health Checks

```bash
# Backend health
curl http://localhost:3000/health

# Frontend
curl http://localhost/
```

### Logs

```bash
# Todos os serviços
docker-compose logs -f

# Apenas backend
docker-compose logs -f backend

# Últimas 100 linhas
docker-compose logs --tail=100 backend
```

---

## 🔒 Segurança

1. **JWT**: Tokens com expiração configurável
2. **CORS**: Configurar origins permitidas
3. **Environment**: Nunca commitar .env com secrets
4. **API Keys**: Usar secrets management (AWS Secrets Manager, etc.)
5. **HTTPS**: Usar certificado SSL em produção (Let's Encrypt)

---

## 🧪 Testes

### Backend

```python
# tests/test_agents.py
import pytest
from app.agents.core import AgentCore

@pytest.mark.asyncio
async def test_process_message():
    core = AgentCore()
    response = await core.process_message(
        agent_key="sdr",
        message="Olá",
        contact_id="test123",
        user_id="user1",
        user_name="Test User"
    )
    assert response['text']
    assert response['author']
```

### Frontend

```typescript
// tests/useAgentSocket.test.ts
import { describe, it, expect } from 'vitest'
import { useAgentSocket } from '@/composables/useAgentSocket'

describe('useAgentSocket', () => {
  it('should connect to socket', () => {
    const { connect } = useAgentSocket('sdr', 'contact1')
    connect('test-token')
    expect(socket.value).toBeTruthy()
  })
})
```

---

## 📝 Checklist de Deploy

- [ ] Variáveis de ambiente configuradas
- [ ] Secrets em produção (JWT_SECRET, API Keys)
- [ ] MongoDB com usuário e senha
- [ ] CORS configurado corretamente
- [ ] HTTPS habilitado
- [ ] Health checks funcionando
- [ ] Logs sendo coletados
- [ ] Backup de MongoDB configurado
- [ ] Rate limiting implementado (opcional)
- [ ] Monitoramento configurado (Sentry, DataDog, etc.)

---

## 🆘 Troubleshooting

### Socket.IO não conecta

```bash
# Verificar CORS no backend
# Verificar se token JWT está válido
# Verificar logs: docker-compose logs backend
```

### OpenAI API falha

```bash
# Verificar API key
# Verificar quotas da conta OpenAI
# Verificar modelo configurado (gpt-4 vs gpt-3.5-turbo)
```

### MongoDB connection error

```bash
# Verificar se MongoDB está rodando
docker-compose ps

# Testar conexão
docker exec -it agents-mongodb mongosh -u admin -p password
```

---

## 📚 Referências

- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Socket.IO Python](https://python-socketio.readthedocs.io/)
- [OpenAI API](https://platform.openai.com/docs/)
- [Google Calendar API](https://developers.google.com/calendar/api)
- [MongoDB Motor](https://motor.readthedocs.io/)

---

## 🎯 Próximos Passos

1. Implementar testes automatizados
2. Adicionar CI/CD (GitHub Actions, GitLab CI)
3. Configurar monitoramento e alertas
4. Implementar rate limiting
5. Adicionar analytics de uso
6. Criar documentação de API (Swagger/OpenAPI)
7. Implementar webhooks para integrações externas
8. Adicionar suporte a múltiplos idiomas

---

**Documentação criada em:** 16 de Dezembro de 2025  
**Versão:** 1.0.0  
**Autor:** Sistema de Documentação Automatizada

<template>
  <div 
    class="agent-pane"
    :style="{ left: `calc(24px + ${stackIndex * 340}px)` }"
  >
    <!-- Header -->
    <div class="agent-pane-header">
      <div class="agent-title">
        <div class="agent-avatar">{{ emoji || '🤖' }}</div>
        <div>
          <strong class="agent-name">{{ title }}</strong>
          <p class="agent-status">Ativo</p>
        </div>
      </div>
      <div class="agent-actions">
        <v-btn icon size="x-small" variant="text" @click="minimize" title="Minimizar">
          <v-icon size="small">mdi-minus</v-icon>
        </v-btn>
        <v-btn icon size="x-small" variant="text" @click="onRequestSummary" title="Resumo">
          <v-icon size="small">mdi-file-document-outline</v-icon>
        </v-btn>
          <v-btn icon size="x-small" variant="text" :title="autoCreate ? 'Auto-agendar ON' : 'Auto-agendar OFF'" @click="toggleAutoCreate" >
            <v-icon size="small">mdi-calendar-clock</v-icon>
          </v-btn>
        <v-btn icon size="x-small" variant="text" @click="toggleAutoSend" :title="autoSend ? 'Auto-send ON' : 'Auto-send OFF'">
          <v-icon size="small">mdi-send-check</v-icon>
        </v-btn>
        <v-btn icon size="x-small" variant="text" @click="close" title="Fechar">
          <v-icon size="small">mdi-close</v-icon>
        </v-btn>
      </div>
    </div>

    <!-- Mensagens -->
    <div class="agent-messages" ref="messagesEl">
      <div v-if="errorMessage" class="agent-error">
        <strong>Erro:</strong> {{ errorMessage }}
      </div>
      <div v-if="messages.length === 0" class="empty-state">
        <p>{{ emoji }} Olá, eu sou o {{ title }}.</p>
        <p class="text-sm">Digite sua consulta interna.</p>
      </div>
      <div v-for="(m, i) in messages" :key="i" class="agent-message">
        <div class="agent-msg-author">{{ m.author }}</div>
        <div class="agent-msg-text">{{ m.text }}</div>
        <div class="agent-msg-time">Agora</div>
      </div>
      
      <!-- 📅 Slot Picker (quando SDR detecta agendamento) -->
      <div v-if="showSlotPicker" class="agent-message">
        <SlotPicker
          :agent-key="agentKey"
          :user-id="chatStore.currentUser"
          :customer-email="slotPickerData.customerEmail"
          :customer-phone="slotPickerData.customerPhone"
          @slot-selected="handleSlotSelected"
          @close="showSlotPicker = false"
        />
      </div>
    </div>

    <!-- Input -->
    <div v-if="suggestions.length > 0" class="agent-suggestions">
      <div class="suggestion-chip" v-for="(s, idx) in suggestions" :key="idx" @click="applySuggestion(s)">
        {{ s }}
      </div>
    </div>
    <div class="agent-input">
      <input
        v-model="input"
        type="text"
        :placeholder="`Escreva uma mensagem para ${title.split(' ')[0]}...`"
        @keydown.enter="send"
        class="agent-input-field"
      />
      <button @click="send" :disabled="!input.trim()" class="agent-send-btn">
        <v-icon>mdi-send</v-icon>
      </button>
    </div>
  </div>
  <div class="agent-intent" v-if="intent || entitiesState.length > 0">
    <div class="agent-intent-text" v-if="intent">🔎 Intent: {{ intent }}</div>
    <div class="agent-entities" v-if="entitiesState.length > 0">
      <span class="entity-chip" v-for="(e, i) in entitiesState" :key="i">{{ e.type }}: {{ e.normalized || e.value }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, nextTick, watch } from 'vue';
import { useChatStore } from '@/stores/chat';
import { useAuthStore } from '@/stores/auth';
import SlotPicker from './SlotPicker';

// 🔧 URL base da API
const apiBaseUrl = import.meta.env.VITE_API_URL || 'http://localhost:3000';

interface Props {
  agentKey: string;
  title: string;
  emoji?: string;
  stackIndex?: number; // Para posicionamento de múltiplos painéis
  contactId?: string; // ID do contato/conversa atual
}
const props = withDefaults(defineProps<Props>(), {
  stackIndex: 0
});
const emit = defineEmits(['close', 'minimize']);

const chatStore = useChatStore();
const input = ref('');
const messages = ref<Array<{ id?: string; author: string; text: string; timestamp?: number }>>([]);
const suggestions = ref<Array<string>>([]);
const intent = ref<string | null>(null);
const entitiesState = ref<Array<{type:string; key:string; value:string; normalized?:string; valid?:boolean;}>>([]);
const summary = ref<string | null>(null);
const errorMessage = ref<string | null>(null);
const autoSend = ref<boolean>(false);
const autoCreate = ref<boolean>(false);
const messagesEl = ref<HTMLElement | null>(null);
let listenersRegistered = false;

// 📅 Slot Picker state
const showSlotPicker = ref(false);
const slotPickerData = ref<{
  customerEmail?: string;
  customerPhone?: string;
}>({});

function close() {
  console.log('🔴 AgentChatPane: close() chamado para', props.agentKey);
  emit('close', props.agentKey);
}

function minimize() {
  console.log('📦 AgentChatPane: minimize() chamado para', props.agentKey);
  emit('minimize', props.agentKey);
}

function scrollToBottom() {
  nextTick(() => {
    if (messagesEl.value) {
      try {
        messagesEl.value.scrollTo({ top: messagesEl.value.scrollHeight, behavior: 'smooth' });
      } catch (_) {
        messagesEl.value.scrollTop = messagesEl.value.scrollHeight;
      }
    }
  });
}

function send() {
  const text = input.value.trim();
  if (!text || !chatStore.socket) return;

  const authStore = useAuthStore();
  const userName = authStore.user?.name || 'Você';
  const userId = authStore.user?.id || chatStore.currentUser; // Usa ID real; fallback para nome apenas se inexistente
  const contactId = props.contactId || chatStore.currentContactId;
  if (!contactId) {
    console.warn(`⚠️ [AgentPane ${props.agentKey}] Sem contactId para enviar contexto. Abra o painel a partir de uma conversa.`);
    return;
  }

  console.log(`📤 [AgentPane ${props.agentKey}] Enviando com contexto:`, {
    text,
    contactId,
    userId
  });

  // 🆕 Envia via agent:send (novo handler com contexto)
  chatStore.socket.emit('agent:send', {
    agentKey: props.agentKey,
    message: text,
    userId,
    userName: userName,
    contactId  // 🎯 ID do contato para buscar contexto
  });

  // Adiciona mensagem localmente
  messages.value.push({
    author: userName,
    text: text
  });

  input.value = '';
  scrollToBottom();
}

function onNewMessage(msg: any) {
  console.log('📨 AgentChatPane recebeu agent:message:', msg, 'para agentKey:', props.agentKey, 'contactId:', props.contactId);
  // Filtra apenas mensagens para este agente E este contato
  if (!msg || !msg.agentKey || msg.agentKey !== props.agentKey) {
    console.log('⏭️  Mensagem ignorada (agentKey diferente):', msg?.agentKey, '!==', props.agentKey);
    return;
  }

  // Se ambos têm contactId, compara como string
  if (props.contactId && msg.contactId && String(msg.contactId) !== String(props.contactId)) {
    console.log('⏭️  Mensagem ignorada (contactId diferente):', msg.contactId, '!==', props.contactId);
    return;
  }
  
  console.log('✅ Mensagem aceita para agente:', props.agentKey, 'contato:', props.contactId);
  messages.value.push({ 
    id: msg.id,
    author: msg.author, 
    text: msg.text,
    timestamp: msg.timestamp
  });
  
  console.log(`📝 [AgentPane ${props.agentKey}] Total de mensagens: ${messages.value.length}`);
  
  nextTick(() => {
    if (messagesEl.value) {
      messagesEl.value.scrollTop = messagesEl.value.scrollHeight;
    }
  });

  // Atualiza intent e entidades se recebidos
  if (msg.nlp) {
    intent.value = msg.nlp.intent;
    entitiesState.value = (msg.nlp.entities || []).map((e: any) => ({ type: e.type, key: e.key, value: e.value, normalized: e.normalized, valid: e.valid }));
  }
  // Se houver calendarSuggestions, adiciona como sugestões no painel
  if (msg.calendarSuggestions && Array.isArray(msg.calendarSuggestions)) {
    const altSug = msg.calendarSuggestions.map((s: string) => `Sugestão de horário: ${s}`);
    suggestions.value = [...(suggestions.value || []), ...altSug];
  }
}

function onAgentError(data: any) {
  console.warn('⚠️ Agent error received:', data);
  if (!data) return;
  // Mostrar erro somente se for para este agente
  if (data.agentKey && data.agentKey !== props.agentKey) return;
  const errText = data.error || data.message || 'Erro desconhecido do agente';
  errorMessage.value = errText;
  // Aparece como mensagem de sistema também
  messages.value.push({ author: 'Sistema', text: `Erro do agente: ${errText}` });
  nextTick(() => scrollToBottom());
}

function onNewSuggestions(data: any) {
  console.log('📨 AgentChatPane recebeu agent:suggestions:', data);
  if (!data || data.agentKey !== props.agentKey) return;
  if (props.contactId && data.contactId && data.contactId !== props.contactId) return;
  suggestions.value = data.suggestions || [];
  nextTick(() => scrollToBottom());
}

function registerSocketListeners() {
  if (!chatStore.socket || listenersRegistered) return;
  console.log(`🎧 [AgentPane ${props.agentKey}] Registrando listeners de socket`);
  listenersRegistered = true;
  chatStore.socket.on('agent:message', onNewMessage);
  chatStore.socket.on('agent:suggestions', onNewSuggestions);
  chatStore.socket.on('agent:error', onAgentError);
  chatStore.socket.on('agent:show-slot-picker', (data: any) => {
    if (data.agentKey === props.agentKey) {
      // Opcional: filtra por contactId se vier no payload
      if (props.contactId && data.contactId && String(data.contactId) !== String(props.contactId)) {
        return;
      }
      console.log('📅 Mostrando SlotPicker para', props.agentKey, data);
      slotPickerData.value = {
        customerEmail: data.customerEmail,
        customerPhone: data.customerPhone
      };
      showSlotPicker.value = true;
      scrollToBottom();
    }
  });
  chatStore.socket.on('agent:summary', (data: any) => {
    if (data.agentKey === props.agentKey) {
      if (props.contactId && data.contactId && data.contactId !== props.contactId) {
        return;
      }
      summary.value = data.summary;
      messages.value.push({ author: `${props.title} (Resumo)`, text: data.summary });
      scrollToBottom();
    }
  });
  chatStore.socket.on('agent:auto-create-updated', (data: any) => {
    if (data.agentKey === props.agentKey) {
      autoCreate.value = !!data.autoCreate;
    }
  });
}

function unregisterSocketListeners() {
  if (!chatStore.socket || !listenersRegistered) return;
  console.log(`👋 [AgentPane ${props.agentKey}] Removendo listeners de socket`);
  chatStore.socket.off('agent:message', onNewMessage);
  chatStore.socket.off('agent:show-slot-picker');
  chatStore.socket.off('agent:suggestions', onNewSuggestions);
  chatStore.socket.off('agent:summary');
  chatStore.socket.off('agent:auto-create-updated');
  chatStore.socket.off('agent:error', onAgentError);
  listenersRegistered = false;
}

onMounted(async () => {
  console.log(`🚀 [AgentPane ${props.agentKey}] Montando...`);
  
  // Carrega histórico de mensagens do agente
  try {
    const authStore = useAuthStore();
    const token = authStore.token;
    
    if (!token) {
      console.warn(`⚠️ [AgentPane ${props.agentKey}] Sem token, usando mensagem padrão`);
      messages.value.push({
        author: props.title,
        text: `Olá! Eu sou o ${props.title}. Como posso ajudá-lo?`
      });
      return;
    }
    
    // Monta URL com contactId se disponível
    let url = `${apiBaseUrl}/agents/${props.agentKey}/messages?limit=50`;
    if (props.contactId) {
      url += `&contactId=${props.contactId}`;
      console.log(`🔗 [AgentPane ${props.agentKey}] Carregando com contactId: ${props.contactId}`);
    }
    console.log(`🌐 [AgentPane ${props.agentKey}] URL completa: ${url}`);
    
    const response = await fetch(url, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    if (response.ok) {
      const data = await response.json();
      if (data.messages && data.messages.length > 0) {
        messages.value = data.messages.map((msg: any) => ({
          id: msg.id,
          author: msg.author,
          text: msg.text,
          timestamp: msg.timestamp
        }));
        console.log(`📚 [AgentPane ${props.agentKey}] Carregadas ${messages.value.length} mensagens do histórico`);
        // Scroll to bottom after loading history
        nextTick(() => scrollToBottom());
      } else {
        // Mensagem inicial apenas se não houver histórico
        messages.value.push({
          author: props.title,
          text: `Olá! Eu sou o ${props.title}. Como posso ajudá-lo?`
        });
        console.log(`👋 [AgentPane ${props.agentKey}] Sem histórico, mensagem de boas-vindas adicionada`);
      }
    } else if (response.status === 401) {
      console.warn(`⚠️ [AgentPane ${props.agentKey}] Token inválido ou expirado`);
      messages.value.push({
        author: props.title,
        text: `Olá! Eu sou o ${props.title}. Como posso ajudá-lo?`
      });
    }
  } catch (error) {
    console.error(`❌ [AgentPane ${props.agentKey}] Erro ao carregar histórico:`, error);
    // Fallback para mensagem de boas-vindas
    messages.value.push({
      author: props.title,
      text: `Olá! Eu sou o ${props.title}. Como posso ajudá-lo?`
    });
  }
  
  registerSocketListeners();
});

// Re-registra listeners quando o socket é (re)conectado após montagem
watch(() => chatStore.socket?.id, () => {
  unregisterSocketListeners();
  registerSocketListeners();
}, { immediate: true });

onBeforeUnmount(() => {
  unregisterSocketListeners();
});

// 📅 Quando cliente seleciona um slot
async function handleSlotSelected(data: { date: string; time: string; customerEmail: string; customerPhone?: string }) {
  console.log('📅 Slot selecionado:', data);
  
  // Fecha o picker
  showSlotPicker.value = false;
  
    // Envia confirmação de agendamento para backend via agent:schedule-confirm
    chatStore.socket?.emit?.('agent:schedule-confirm', {
      agentKey: props.agentKey,
      contactId: props.contactId,
      date: data.date,
      time: data.time,
      customerEmail: data.customerEmail,
      phone: data.customerPhone
    });
    // Also push a local log message for chat timeline (intentional duplication for record)
    const message = `Escolhi o dia ${data.date} às ${data.time}. Meu email é ${data.customerEmail}`;
    messages.value.push({
      author: chatStore.currentUser,
      text: message
    });
  
    scrollToBottom();
}

function applySuggestion(suggestion: string) {
  if (!suggestion) return;
  input.value = suggestion;
  if (autoSend.value) {
    send();
  }
}

function toggleAutoSend() {
  autoSend.value = !autoSend.value;
}

function toggleAutoCreate() {
  autoCreate.value = !autoCreate.value;
  if (chatStore.socket) {
    chatStore.socket.emit('agent:set-auto-create', { agentKey: props.agentKey, autoCreate: autoCreate.value });
  }
}

function onRequestSummary() {
  if (!chatStore.socket) return;
  chatStore.socket.emit('agent:request-summary', { agentKey: props.agentKey, contactId: props.contactId });
}
</script>

<style scoped>
.agent-pane {
  position: absolute;
  bottom: 120px;
  width: 320px;
  height: 384px;
  background: color-mix(in srgb, var(--ds-color-success) 8%, var(--ds-color-chat-background) 92%);
  border-radius: var(--ds-radius-lg);
  display: flex;
  flex-direction: column;
  box-shadow: var(--ds-shadow-xl);
  border: 1px solid var(--ds-color-border);
  overflow: hidden;
  animation: slideUp 0.3s ease-out;
  z-index: 5;
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.agent-pane-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--ds-spacing-md) var(--ds-spacing-lg);
  background: linear-gradient(135deg, var(--ds-color-primary) 0%, color-mix(in srgb, var(--ds-color-primary) 70%, var(--ds-color-secondary) 30%) 100%);
  border-bottom: none;
}

.agent-title {
  display: flex;
  align-items: center;
  gap: var(--ds-spacing-sm);
  color: var(--ds-color-text-white);
}

.agent-avatar {
  width: 32px;
  height: 32px;
  border-radius: var(--ds-radius-full);
  background: rgba(255, 255, 255, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--ds-font-size-md);
  flex-shrink: 0;
}

.agent-name {
  font-size: var(--ds-font-size-base);
  font-weight: var(--ds-font-weight-semibold);
  color: var(--ds-color-text-white);
  line-height: var(--ds-line-height-tight);
}

.agent-status {
  font-size: var(--ds-font-size-xs);
  color: rgba(255, 255, 255, 0.8);
  margin: 0;
  line-height: var(--ds-line-height-tight);
}

.agent-actions {
  display: flex;
  gap: var(--ds-spacing-xs);
}

.agent-actions .v-btn {
  color: var(--ds-color-text-white) !important;
}

.agent-messages {
  flex: 1;
  overflow-y: auto;
  padding: var(--ds-spacing-lg);
  background: transparent;
}

.empty-state {
  text-align: center;
  padding: var(--ds-spacing-xl);
  color: var(--ds-color-text-secondary);
}

.empty-state p {
  margin: var(--ds-spacing-xs) 0;
}

.agent-message {
  margin-bottom: var(--ds-spacing-lg);
  background: var(--ds-color-chat-background);
  padding: var(--ds-spacing-sm) var(--ds-spacing-md);
  border-radius: var(--ds-radius-md);
  box-shadow: var(--ds-shadow-sm);
}

.agent-msg-author {
  font-weight: var(--ds-font-weight-semibold);
  font-size: var(--ds-font-size-sm);
  color: var(--ds-color-primary);
  margin-bottom: var(--ds-spacing-xs);
}

.agent-msg-text {
  font-size: var(--ds-font-size-base);
  color: var(--ds-color-text-primary);
  line-height: var(--ds-line-height-normal);
  word-wrap: break-word;
}

.agent-msg-time {
  font-size: var(--ds-font-size-xs);
  color: var(--ds-color-text-hint);
  margin-top: var(--ds-spacing-xs);
  text-align: right;
}

.agent-input {
  display: flex;
  gap: var(--ds-spacing-sm);
  padding: var(--ds-spacing-md);
  border-top: 1px solid var(--ds-color-border);
  background: var(--ds-color-chat-background);
}

.agent-suggestions {
  display: flex;
  gap: var(--ds-spacing-sm);
  padding: var(--ds-spacing-sm) var(--ds-spacing-lg);
  overflow-x: auto;
  background: var(--ds-color-chat-background);
  border-top: 1px solid var(--ds-color-border);
}
.suggestion-chip {
  background: var(--ds-color-primary);
  color: var(--ds-color-text-white);
  padding: 6px 10px;
  border-radius: var(--ds-radius-lg);
  font-size: var(--ds-font-size-sm);
  cursor: pointer;
  white-space: nowrap;
}
.suggestion-chip:hover { opacity: 0.9; }

.agent-input-field {
  flex: 1;
  padding: var(--ds-spacing-sm) var(--ds-spacing-md);
  border: 1px solid var(--ds-color-border);
  border-radius: var(--ds-radius-xl);
  font-size: var(--ds-font-size-sm);
  outline: none;
  transition: border-color 0.2s;
  background: var(--ds-color-chat-background);
  color: var(--ds-color-text-primary);
}

.agent-input-field:focus {
  border-color: var(--ds-color-primary);
}

.agent-send-btn {
  width: 36px;
  height: 36px;
  border-radius: var(--ds-radius-full);
  background: var(--ds-color-primary);
  color: var(--ds-color-text-white);
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: background 0.2s;
  flex-shrink: 0;
}

.agent-send-btn:hover:not(:disabled) {
  background: color-mix(in srgb, var(--ds-color-primary) 80%, black 20%);
}

.agent-send-btn:disabled {
  background: var(--ds-color-border);
  cursor: not-allowed;
}

.agent-intent {
  padding: var(--ds-spacing-xs) var(--ds-spacing-lg);
  background: color-mix(in srgb, var(--ds-color-chat-background) 85%, white 15%);
  border-bottom: 1px solid var(--ds-color-border);
  display: flex;
  gap: var(--ds-spacing-sm);
  align-items: center;
}
.agent-intent-text {
  font-size: var(--ds-font-size-xs);
  color: var(--ds-color-text-primary);
}
.agent-entities {
  display: flex;
  gap: var(--ds-spacing-xs);
}
.entity-chip {
  background: var(--ds-color-primary);
  color: var(--ds-color-text-white);
  padding: 4px 8px;
  border-radius: var(--ds-radius-sm);
  font-size: var(--ds-font-size-xs);
}

.agent-messages::-webkit-scrollbar {
  width: 6px;
}

.agent-messages::-webkit-scrollbar-track {
  background: transparent;
}

.agent-messages::-webkit-scrollbar-thumb {
  background: var(--ds-color-shadow);
  border-radius: 3px;
}

.agent-error {
  background: color-mix(in srgb, var(--ds-color-danger) 8%, var(--ds-color-chat-background) 92%);
  color: var(--ds-color-danger);
  padding: 6px 10px;
  border-radius: var(--ds-radius-sm);
  margin-bottom: var(--ds-spacing-md);
  text-align: left;
}
</style>

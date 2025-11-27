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
        <v-btn icon size="x-small" variant="text" @click="close" title="Fechar">
          <v-icon size="small">mdi-close</v-icon>
        </v-btn>
      </div>
    </div>

    <!-- Mensagens -->
    <div class="agent-messages" ref="messagesEl">
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
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue';
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
const messages = ref<Array<{ author: string; text: string }>>([]);
const messagesEl = ref<HTMLElement | null>(null);

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

function send() {
  const text = input.value.trim();
  if (!text || !chatStore.socket) return;

  console.log(`📤 [AgentPane ${props.agentKey}] Enviando mensagem:`, text, 'contactId:', props.contactId);

  // Envia para o backend usando menção ao agente (servidor salva e responde)
  const payload = {
    author: chatStore.currentUser,
    text: `@${props.agentKey} ${text}`.trim(),
    type: 'text',
    tempId: `agent_${Date.now()}_${Math.random()}`,
    contactId: props.contactId  // 🆕 Inclui contactId para vincular à conversa
  };

  try {
    chatStore.socket.emit('chat:send', payload);
    input.value = '';
    // Não adiciona localmente - aguarda backend retornar via agent:message
    console.log(`✅ [AgentPane ${props.agentKey}] Mensagem enviada com contactId:`, props.contactId);
  } catch (e) {
    console.error(`❌ [AgentPane ${props.agentKey}] Erro ao enviar:`, e);
  }
}

function onNewMessage(msg: any) {
  console.log('📨 AgentChatPane recebeu agent:message:', msg, 'para agentKey:', props.agentKey, 'contactId:', props.contactId);
  
  // Filtra apenas mensagens para este agente E este contato
  if (!msg || !msg.agentKey || msg.agentKey !== props.agentKey) {
    console.log('⏭️  Mensagem ignorada (agentKey diferente):', msg.agentKey, '!==', props.agentKey);
    return;
  }
  
  // 🆕 Verifica se a mensagem pertence a este contato (se contactId está definido)
  if (props.contactId && msg.contactId && msg.contactId !== props.contactId) {
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
  
  // Registra listener para novas mensagens de agentes (evento específico)
  if (chatStore.socket) {
    console.log(`🎧 [AgentPane ${props.agentKey}] Registrando listener 'agent:message'`);
    chatStore.socket.on('agent:message', onNewMessage);
    
    // 📅 Listener para mostrar Slot Picker
    chatStore.socket.on('agent:show-slot-picker', (data: any) => {
      if (data.agentKey === props.agentKey) {
        console.log('📅 Mostrando SlotPicker para', props.agentKey, data);
        slotPickerData.value = {
          customerEmail: data.customerEmail,
          customerPhone: data.customerPhone
        };
        showSlotPicker.value = true;
        scrollToBottom();
      }
    });
  }
});

onBeforeUnmount(() => {
  if (chatStore.socket) {
    console.log(`👋 [AgentPane ${props.agentKey}] Removendo listener 'agent:message'`);
    chatStore.socket.off('agent:message', onNewMessage);
    chatStore.socket.off('agent:show-slot-picker');
  }
});

// 📅 Quando cliente seleciona um slot
async function handleSlotSelected(data: { date: string; time: string; customerEmail: string }) {
  console.log('📅 Slot selecionado:', data);
  
  // Fecha o picker
  showSlotPicker.value = false;
  
  // Envia mensagem informando a escolha para o SDR processar
  if (chatStore.socket) {
    const message = `Escolhi o dia ${data.date} às ${data.time}. Meu email é ${data.customerEmail}`;
    
    chatStore.socket.emit('chat:send', {
      author: chatStore.currentUser,
      text: `@${props.agentKey} ${message}`,
      type: 'text',
      tempId: `slot_${Date.now()}`,
      contactId: props.contactId
    });
    
    // Adiciona mensagem localmente
    messages.value.push({
      author: chatStore.currentUser,
      text: message
    });
    
    scrollToBottom();
  }
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
</style>
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

interface Props {
  agentKey: string;
  title: string;
  emoji?: string;
  stackIndex?: number; // Para posicionamento de múltiplos painéis
}
const props = withDefaults(defineProps<Props>(), {
  stackIndex: 0
});
const emit = defineEmits(['close', 'minimize']);

const chatStore = useChatStore();
const input = ref('');
const messages = ref<Array<{ author: string; text: string }>>([]);
const messagesEl = ref<HTMLElement | null>(null);

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

  console.log(`📤 [AgentPane ${props.agentKey}] Enviando mensagem:`, text);

  // Envia para o backend usando menção ao agente (servidor salva e responde)
  const payload = {
    author: chatStore.currentUser,
    text: `@${props.agentKey} ${text}`.trim(),
    type: 'text',
    tempId: `agent_${Date.now()}_${Math.random()}`
  };

  try {
    chatStore.socket.emit('chat:send', payload);
    input.value = '';
    // Não adiciona localmente - aguarda backend retornar via agent:message
    console.log(`✅ [AgentPane ${props.agentKey}] Mensagem enviada, aguardando resposta do servidor`);
  } catch (e) {
    console.error(`❌ [AgentPane ${props.agentKey}] Erro ao enviar:`, e);
  }
}

function onNewMessage(msg: any) {
  console.log('📨 AgentChatPane recebeu agent:message:', msg, 'para agentKey:', props.agentKey);
  
  // Filtra apenas mensagens para este agente
  if (!msg || !msg.agentKey || msg.agentKey !== props.agentKey) {
    console.log('⏭️  Mensagem ignorada (agentKey diferente):', msg.agentKey, '!==', props.agentKey);
    return;
  }
  
  console.log('✅ Mensagem aceita para agente:', props.agentKey);
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
    const response = await fetch(`http://localhost:8000/agents/${props.agentKey}/messages?limit=50`);
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
  }
});

onBeforeUnmount(() => {
  if (chatStore.socket) {
    console.log(`👋 [AgentPane ${props.agentKey}] Removendo listener 'agent:message'`);
    chatStore.socket.off('agent:message', onNewMessage);
  }
});
</script>

<style scoped>
.agent-pane {
  position: absolute;
  bottom: 80px;
  width: 320px;
  height: 384px;
  background: white;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
  border: 1px solid rgba(0, 0, 0, 0.1);
  overflow: hidden;
  animation: slideUp 0.3s ease-out;
  z-index: 1000;
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
  padding: 12px 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-bottom: none;
}

.agent-title {
  display: flex;
  align-items: center;
  gap: 10px;
  color: white;
}

.agent-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  flex-shrink: 0;
}

.agent-name {
  font-size: 14px;
  font-weight: 600;
  color: white;
  line-height: 1.2;
}

.agent-status {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.8);
  margin: 0;
  line-height: 1.2;
}

.agent-actions {
  display: flex;
  gap: 4px;
}

.agent-actions .v-btn {
  color: white !important;
}

.agent-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  background: #f5f5f5;
}

.empty-state {
  text-align: center;
  padding: 20px;
  color: #666;
}

.empty-state p {
  margin: 4px 0;
}

.agent-message {
  margin-bottom: 16px;
  background: white;
  padding: 10px 12px;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.agent-msg-author {
  font-weight: 600;
  font-size: 12px;
  color: #667eea;
  margin-bottom: 4px;
}

.agent-msg-text {
  font-size: 14px;
  color: #333;
  line-height: 1.4;
  word-wrap: break-word;
}

.agent-msg-time {
  font-size: 10px;
  color: #999;
  margin-top: 4px;
  text-align: right;
}

.agent-input {
  display: flex;
  gap: 8px;
  padding: 12px;
  border-top: 1px solid #e0e0e0;
  background: white;
}

.agent-input-field {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 20px;
  font-size: 13px;
  outline: none;
  transition: border-color 0.2s;
}

.agent-input-field:focus {
  border-color: #667eea;
}

.agent-send-btn {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: #667eea;
  color: white;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: background 0.2s;
  flex-shrink: 0;
}

.agent-send-btn:hover:not(:disabled) {
  background: #5568d3;
}

.agent-send-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.agent-messages::-webkit-scrollbar {
  width: 6px;
}

.agent-messages::-webkit-scrollbar-track {
  background: transparent;
}

.agent-messages::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 3px;
}
</style>
<template>
  <div class="chat-container" :style="{ background: colors.chatBackground }">
    <!-- HEADER -->
    <div class="chat-header">
      <DSChatHeader
        :name="author || 'Chat'"
        :online="chatStore.isConnected"
        :typing="chatStore.isTyping"
        @search="() => {}"
        @menu="handleLogout"
      />
    </div>

    <!-- ÁREA DE MENSAGENS -->
    <div 
      ref="containerRef" 
      class="messages-wrapper"
    >
      <div 
        class="messages-area"
        :style="{
          padding: spacing.xl,
          backgroundImage: 'url(\'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAYAAACNMs+9AAAAGElEQVQYlWNgYGCQwoKxgqGgcJA5h3yFAAs8BRWVSwooAAAAAElFTkSuQmCC\')',
          backgroundRepeat: 'repeat',
        }"
      >
        <div
          v-for="msg in chatStore.messages"
          :key="msg.id"
          :class="['mb-2', msg.author === author ? 'd-flex justify-end' : 'd-flex justify-start']"
        >
          <DSMessageBubble
            :author="msg.author"
            :timestamp="msg.timestamp"
            :variant="msg.author === author ? 'sent' : 'received'"
            :status="msg.status"
            :show-author="msg.author !== author"
          >
            {{ msg.text }}
          </DSMessageBubble>
        </div>
      </div>
    </div>

    <!-- INPUT DE MENSAGEM -->
    <div class="chat-input-wrapper">
      <DSChatInput
        v-model="text"
        @submit="handleSendMessage"
        @emoji="() => {}"
        @attach="() => {}"
      />
    </div>

    <!-- DIALOG PARA NOME DO USUÁRIO -->
    <v-dialog v-model="showNameDialog" max-width="400" persistent>
      <v-card>
        <v-card-title class="text-h5">Bem-vindo ao Chat!</v-card-title>
        <v-card-text>
          <v-text-field
            v-model="author"
            label="Digite seu nome"
            variant="outlined"
            autofocus
            @keyup.enter="closeDialog"
          />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn 
            :color="colors.secondary" 
            variant="flat" 
            @click="closeDialog" 
            :disabled="!author.trim()"
          >
            Entrar
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onBeforeUnmount } from 'vue';
import { useRouter } from 'vue-router';
import DSChatHeader from '../design-system/components/DSChatHeader.vue';
import DSMessageBubble from '../design-system/components/DSMessageBubble.vue';
import DSChatInput from '../design-system/components/DSChatInput.vue';
import { useChatStore } from '../stores/chat';
import { useAuthStore } from '../stores/auth';
import { useScrollToBottom } from '../design-system/composables/useScrollToBottom.ts';
import { colors, spacing } from '../design-system/tokens/index.ts';

const router = useRouter();
const chatStore = useChatStore();
const authStore = useAuthStore();
const author = ref('');
const text = ref('');
const showNameDialog = ref(true);

const { containerRef, scrollToBottom } = useScrollToBottom();

const socketUrl = import.meta.env.VITE_SOCKET_URL || 'http://localhost:3000';

// Define o nome do autor baseado no usuário autenticado
if (authStore.user) {
  author.value = authStore.user.name;
  showNameDialog.value = false;
}

// Conecta ao socket e carrega histórico ao montar
onMounted(async () => {
  chatStore.connect(socketUrl);
  try {
    await chatStore.loadHistory(socketUrl);
    scrollToBottom();
  } catch (error) {
    console.error('Erro ao carregar histórico:', error);
  }
});

// Desconecta ao desmontar
onBeforeUnmount(() => {
  chatStore.disconnect();
});

// Auto-scroll quando novas mensagens chegarem (sem smooth para performance)
watch(() => chatStore.messages.length, () => {
  scrollToBottom(); // smooth = false (default)
});

function handleSendMessage(messageText: string) {
  if (!messageText.trim()) return;
  
  chatStore.sendMessage(
    author.value || 'Anônimo',
    messageText
  );
  scrollToBottom(true); // smooth = true (interação do usuário)
}

function closeDialog() {
  if (author.value.trim()) {
    showNameDialog.value = false;
  }
}

function handleLogout() {
  chatStore.disconnect();
  authStore.logout();
  router.push('/login');
}
</script>

<style scoped>
.chat-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  width: 100%;
  overflow: hidden;
  position: relative;
}

.chat-header {
  flex-shrink: 0;
  z-index: 10;
  position: sticky;
  top: 0;
  background: inherit;
}

.messages-wrapper {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  position: relative;
  padding-bottom: 80px; /* Espaço para o input fixo */
}

.messages-area {
  min-height: 100%;
  display: flex;
  flex-direction: column;
}

.chat-input-wrapper {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  flex-shrink: 0;
  z-index: 10;
  background: inherit;
  box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.1);
}

.messages-wrapper::-webkit-scrollbar {
  width: 8px;
}

.messages-wrapper::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.05);
}

.messages-wrapper::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 4px;
}

.messages-wrapper::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 0, 0, 0.3);
}
</style>
<template>
  <div class="chat-container" :style="{ background: colors.chatBackground }">
    <!-- HEADER -->
    <div class="chat-header">
      <DSChatHeader
        :name="author || 'Chat'"
        :online="isConnected"
        :typing="isTyping"
        @search="() => {}"
        @menu="() => {}"
      />
    </div>

    <!-- ÁREA DE MENSAGENS -->
    <div class="messages-wrapper">
      <div 
        ref="containerRef" 
        class="messages-area"
        :style="{
          padding: spacing.xl,
          backgroundImage: 'url(\'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAYAAACNMs+9AAAAGElEQVQYlWNgYGCQwoKxgqGgcJA5h3yFAAs8BRWVSwooAAAAAElFTkSuQmCC\')',
          backgroundRepeat: 'repeat',
        }"
      >
        <div
          v-for="msg in messages"
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
import { ref, watch } from 'vue';
import DSChatHeader from '../design-system/components/DSChatHeader.vue';
import DSMessageBubble from '../design-system/components/DSMessageBubble.vue';
import DSChatInput from '../design-system/components/DSChatInput.vue';
import { useChat } from '../design-system/composables/useChat.ts';
import { useScrollToBottom } from '../design-system/composables/useScrollToBottom.ts';
import { colors, spacing } from '../design-system/tokens/index.ts';

const author = ref('');
const text = ref('');
const showNameDialog = ref(true);

const { messages, isConnected, isTyping, sendMessage } = useChat(
  import.meta.env.VITE_SOCKET_URL || 'http://localhost:3000'
);

const { containerRef, scrollToBottom } = useScrollToBottom();

// Auto-scroll quando novas mensagens chegarem
watch(() => messages.value.length, () => {
  scrollToBottom();
});

function handleSendMessage(messageText: string) {
  if (!messageText.trim()) return;
  
  sendMessage({
    author: author.value || 'Anônimo',
    text: messageText,
    status: 'sent',
  });
  text.value = '';
  scrollToBottom();
}

function closeDialog() {
  if (author.value.trim()) {
    showNameDialog.value = false;
  }
}
</script>

<style scoped>
.chat-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  width: 100%;
  overflow: hidden;
}

.chat-header {
  flex-shrink: 0;
  z-index: 10;
}

.messages-wrapper {
  flex: 1;
  overflow: hidden;
  position: relative;
}

.messages-area {
  height: 100%;
  overflow-y: auto;
  overflow-x: hidden;
}

.chat-input-wrapper {
  flex-shrink: 0;
  z-index: 10;
}

.messages-area::-webkit-scrollbar {
  width: 8px;
}

.messages-area::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.05);
}

.messages-area::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 4px;
}

.messages-area::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 0, 0, 0.3);
}
</style>
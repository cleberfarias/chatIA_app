<template>
  <div class="chat-container" :style="{ background: colors.chatBackground }">
    <!-- HEADER -->
    <div class="chat-header">
      <DSChatHeader
        :name="author || 'Chat'"
        :online="chatStore.connected"
        :typing="Object.keys(chatStore.isTyping).length > 0"
        @search="() => {}"
        @menu="handleLogout"
      />
    </div>

    <!-- ÁREA DE MENSAGENS -->
    <div 
      ref="containerRef" 
      class="messages-wrapper"
      @scroll="handleScroll"
    >
      <!-- 🆕 BOTÃO "CARREGAR MAIS" (Topo) -->
      <div v-if="chatStore.hasMoreMessages" class="d-flex justify-center pa-2">
        <v-btn
          :loading="chatStore.loadingMore"
          variant="tonal"
          size="small"
          prepend-icon="mdi-chevron-up"
          @click="loadMoreMessages"
        >
          Carregar mais
        </v-btn>
      </div>

      <div 
        class="messages-area"
        :style="{
          padding: spacing.xl,
          backgroundImage: 'url(\'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAYAAACNMs+9AAAAGElEQVQYlWNgYGCQwoKxgqGgcJA5h3yFAAs8BRWVSwooAAAAAElFTkSuQmCC\')',
          backgroundRepeat: 'repeat',
        }"
      >
        <!-- 🆕 SEPARADORES DE DATA + MENSAGENS AGRUPADAS -->
        <template v-for="(item, index) in groupedMessages" :key="item.id || index">
          <!-- Separador de Data -->
          <DateSeparator v-if="item.type === 'date'" :date="item.date" />
          
          <!-- Mensagem -->
          <div
            v-else
            :class="['mb-2', item.author === author ? 'd-flex justify-end' : 'd-flex justify-start']"
          >
            <DSMessageBubble
              :author="item.author"
              :timestamp="item.timestamp"
              :variant="item.author === author ? 'sent' : 'received'"
              :status="item.status"
              :show-author="item.showAuthor"
              :show-timestamp="item.showTimestamp"
            >
              {{ item.text }}
            </DSMessageBubble>
          </div>
        </template>

        <!-- 🆕 INDICADOR "DIGITANDO..." -->
        <TypingIndicator v-if="chatStore.typingUsers.length > 0" :users="chatStore.typingUsers" />
      </div>

      <!-- 🆕 BOTÃO "NOVAS MENSAGENS" (Flutuante) -->
      <v-fab
        v-if="chatStore.hasUnreadMessages && !isScrolledToBottom"
        class="new-messages-fab"
        icon="mdi-chevron-down"
        color="primary"
        size="small"
        @click="scrollToBottom(true)"
      >
        <v-badge
          v-if="unreadCount > 0"
          :content="unreadCount"
          color="error"
          offset-x="-8"
          offset-y="-8"
        />
      </v-fab>
    </div>

    <!-- INPUT DE MENSAGEM -->
    <div class="chat-input-wrapper">
      <DSChatInput
        v-model="text"
        @submit="handleSendMessage"
        @typing="handleTyping"
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
import { ref, watch, onMounted, onBeforeUnmount, computed } from 'vue';
import { useRouter } from 'vue-router';
import DSChatHeader from '../design-system/components/DSChatHeader.vue';
import DSMessageBubble from '../design-system/components/DSMessageBubble.vue';
import DSChatInput from '../design-system/components/DSChatInput.vue';
import TypingIndicator from '../components/TypingIndicator.vue';
import DateSeparator from '../components/DateSeparator.vue';
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
const isScrolledToBottom = ref(true);
const lastScrollTop = ref(0);

const { containerRef, scrollToBottom } = useScrollToBottom();

// Define o nome do autor baseado no usuário autenticado
if (authStore.user) {
  author.value = authStore.user.name;
  showNameDialog.value = false;
}

// 🆕 COMPUTED: Agrupa mensagens por data e autor
const groupedMessages = computed(() => {
  const result: any[] = [];
  let lastDate: string | null = null;
  let lastAuthor: string | null = null;
  let lastTimestamp = 0;
  const TIME_GAP = 5 * 60 * 1000; // 5 minutos

  chatStore.messages.forEach((msg, index) => {
    const msgDate = new Date(msg.timestamp);
    const dateKey = msgDate.toLocaleDateString('pt-BR');

    // Adiciona separador de data
    if (dateKey !== lastDate) {
      result.push({ type: 'date', date: msgDate, id: `date-${dateKey}` });
      lastDate = dateKey;
      lastAuthor = null;
    }

    // Verifica se deve agrupar (mesmo autor + menos de 5min)
    const timeDiff = msg.timestamp - lastTimestamp;
    const shouldGroup = msg.author === lastAuthor && timeDiff < TIME_GAP;

    result.push({
      ...msg,
      type: 'message',
      showAuthor: !shouldGroup || msg.author !== author.value,
      showTimestamp: !shouldGroup || index === chatStore.messages.length - 1,
    });

    lastAuthor = msg.author;
    lastTimestamp = msg.timestamp;
  });

  return result;
});

// 🆕 COMPUTED: Conta mensagens não lidas
const unreadCount = computed(() => {
  return chatStore.messages.filter(m => 
    m.author !== author.value && m.status !== 'read'
  ).length;
});

// Conecta ao socket e carrega histórico ao montar
onMounted(async () => {
  // Define o nome do usuário no store
  if (author.value) {
    chatStore.currentUser = author.value;
  }
  
  // Conecta ao socket (já carrega mensagens internamente)
  if (authStore.token) {
    await chatStore.connect(authStore.token);
    scrollToBottom();
  }
});

// Desconecta ao desmontar
onBeforeUnmount(() => {
  chatStore.disconnect();
});

// 🆕 Auto-scroll INTELIGENTE (só rola se usuário estava no final)
watch(() => chatStore.messages.length, () => {
  if (isScrolledToBottom.value) {
    scrollToBottom(); // smooth = false (default)
  }
});

// 🆕 FUNÇÃO: Detecta scroll manual do usuário
function handleScroll(event: Event) {
  const container = event.target as HTMLElement;
  const threshold = 100; // 100px de tolerância
  
  const atBottom = 
    container.scrollHeight - container.scrollTop - container.clientHeight < threshold;
  
  isScrolledToBottom.value = atBottom;
  chatStore.setScrolledToBottom(atBottom);
  
  lastScrollTop.value = container.scrollTop;
}

// 🆕 FUNÇÃO: Carregar mensagens antigas
async function loadMoreMessages() {
  if (chatStore.loadingMore || !chatStore.hasMoreMessages) return;
  
  const oldestMessage = chatStore.messages[0];
  if (oldestMessage) {
    const scrollHeightBefore = containerRef.value?.scrollHeight || 0;
    
    await chatStore.loadMessages(oldestMessage.timestamp);
    
    // Mantém posição do scroll após carregar
    setTimeout(() => {
      if (containerRef.value) {
        const scrollHeightAfter = containerRef.value.scrollHeight;
        containerRef.value.scrollTop = scrollHeightAfter - scrollHeightBefore;
      }
    }, 0);
  }
}

// 🆕 FUNÇÃO: Emite evento de digitação para o servidor
function handleTyping(isTyping: boolean) {
  chatStore.emitTyping(isTyping);
}

function handleSendMessage(messageText: string) {
  if (!messageText.trim()) return;
  
  // Define o nome do usuário antes de enviar
  if (author.value) {
    chatStore.currentUser = author.value;
  }
  
  chatStore.sendMessage(messageText);
  text.value = ''; // Limpa o input
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

/* 🆕 Botão flutuante "Novas Mensagens" */
.new-messages-fab {
  position: absolute !important;
  bottom: 100px;
  right: 20px;
  z-index: 5;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}
</style>
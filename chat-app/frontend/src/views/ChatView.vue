<template>
  <div class="chat-container" :style="{ background: colors.chatBackground }">
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
          <DateSeparator v-if="'date' in item" :date="item.date" />
          
          <!-- Mensagem -->
          <div
            v-else
            :class="['mb-2', item.userId === currentUserId ? 'd-flex justify-end' : 'd-flex justify-start']"
          >
            <DSMessageBubble
              :author="item.author"
              :timestamp="item.timestamp"
              :variant="item.userId === currentUserId ? 'sent' : 'received'"
              :status="item.status"
              :show-author="item.showAuthor"
              :show-timestamp="item.showTimestamp"
              :type="item.type || 'text'"
              :attachment-url="item.url"
              :file-name="item.attachment?.filename || item.text"
              :text="item.type === 'text' ? item.text : ''"
            />
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
      <!-- 🧠 BANNER DE SESSÃO ATIVA -->
      <div v-if="guruSessionActive" class="guru-session-banner">
        <div class="d-flex align-center justify-space-between px-4 py-2">
          <div class="d-flex align-center">
            <v-icon size="20" color="white" class="mr-2">mdi-robot-happy</v-icon>
            <span class="session-text">Em conversa com o Guru</span>
            <v-icon size="16" color="success" class="ml-2 pulse-icon">mdi-circle</v-icon>
          </div>
          <v-btn
            size="x-small"
            variant="text"
            color="white"
            @click="handleSendMessage('tchau')"
          >
            Encerrar
          </v-btn>
        </div>
      </div>
      
      <!-- 🧠 CHIPS DE COMANDOS DO GURU -->
      <div class="guru-commands-bar" v-if="showGuruCommands">
        <div class="guru-commands-content">
          <div class="guru-commands-header">
            <v-icon size="small" color="teal-darken-3" class="mr-1">mdi-robot-happy</v-icon>
            <span class="guru-commands-title">Comandos do Guru:</span>
          </div>
          <v-chip
            size="small"
            color="teal-darken-1"
            variant="flat"
            prepend-icon="mdi-chat-processing"
            class="mr-2 mb-2"
            @click="insertCommand('@guru')"
          >
            @guru
          </v-chip>
          <v-chip
            size="small"
            color="orange-darken-1"
            variant="flat"
            prepend-icon="mdi-exit-to-app"
            class="mr-2 mb-2"
            @click="insertCommand('tchau')"
          >
            tchau
          </v-chip>
          <v-chip
            size="small"
            color="orange-darken-1"
            variant="flat"
            prepend-icon="mdi-location-exit"
            class="mr-2 mb-2"
            @click="insertCommand('sair')"
          >
            sair
          </v-chip>
          <v-chip
            size="small"
            color="blue-darken-1"
            variant="flat"
            prepend-icon="mdi-lightbulb-question"
            class="mr-2 mb-2"
            @click="insertCommand('/ai ')"
          >
            /ai
          </v-chip>
          <v-chip
            size="small"
            color="red-darken-1"
            variant="flat"
            prepend-icon="mdi-broom"
            class="mr-2 mb-2"
            @click="insertCommand('/limpar')"
          >
            /limpar
          </v-chip>
          <v-chip
            size="small"
            color="purple-darken-1"
            variant="flat"
            prepend-icon="mdi-view-list"
            class="mr-2 mb-2"
            @click="insertCommand('/ajuda')"
          >
            /ajuda
          </v-chip>
          <v-chip
            size="small"
            color="indigo-darken-1"
            variant="flat"
            prepend-icon="mdi-clipboard-text"
            class="mr-2 mb-2"
            @click="insertCommand('/resumo')"
          >
            /resumo
          </v-chip>
          <v-chip
            size="small"
            color="cyan-darken-1"
            variant="flat"
            prepend-icon="mdi-chart-box"
            class="mr-2 mb-2"
            @click="insertCommand('/contexto')"
          >
            /contexto
          </v-chip>
          
          <!-- Separador de Agentes -->
          <v-divider class="my-2"></v-divider>
          
          <div class="guru-commands-header mt-2">
            <v-icon size="small" color="purple-darken-2" class="mr-1">mdi-account-group</v-icon>
            <span class="guru-commands-title">Agentes Especializados:</span>
          </div>
          
          <v-chip
            size="small"
            color="deep-purple-darken-1"
            variant="flat"
            prepend-icon="mdi-scale-balance"
            class="mr-2 mb-2"
            @click="insertCommand('@advogado ')"
          >
            @advogado ⚖️
          </v-chip>
          
          <v-chip
            size="small"
            color="blue-grey-darken-1"
            variant="flat"
            prepend-icon="mdi-briefcase-account"
            class="mr-2 mb-2"
            @click="insertCommand('@vendedor ')"
          >
            @vendedor 💼
          </v-chip>
          
          <v-chip
            size="small"
            color="red-darken-1"
            variant="flat"
            prepend-icon="mdi-hospital-box"
            class="mr-2 mb-2"
            @click="insertCommand('@medico ')"
          >
            @medico 🩺
          </v-chip>
          
          <v-chip
            size="small"
            color="green-darken-1"
            variant="flat"
            prepend-icon="mdi-meditation"
            class="mr-2 mb-2"
            @click="insertCommand('@psicologo ')"
          >
            @psicologo 🧘
          </v-chip>
          
          <v-chip
            size="small"
            color="amber-darken-2"
            variant="flat"
            prepend-icon="mdi-robot"
            class="mr-2 mb-2"
            @click="insertCommand('/agentes')"
          >
            /agentes
          </v-chip>
          <v-btn
            icon="mdi-close"
            size="x-small"
            variant="text"
            color="grey-darken-2"
            class="ml-auto"
            @click="showGuruCommands = false"
          />
        </div>
      </div>

      <!-- 🔘 Botão para mostrar/ocultar comandos -->
      <v-btn
        v-if="!showGuruCommands"
        icon="mdi-robot-happy"
        size="x-small"
        color="teal-darken-1"
        variant="flat"
        class="guru-toggle-btn"
        @click="showGuruCommands = true"
        title="Mostrar comandos do Guru"
      />
      
      <!-- 🤖 Botão para criar bot personalizado -->
      <v-btn
        icon="mdi-plus-circle"
        size="x-small"
        color="purple-darken-2"
        variant="flat"
        class="custom-bot-btn"
        @click="showBotCreator = true"
        title="Criar Bot Personalizado"
      />

      <DSChatInput
        v-model="text"
        :uploading="uploadingFile"
        :upload-progress="uploadProgress"
        @submit="handleSendMessage"
        @typing="handleTyping"
        @emoji="() => {}"
        @voice="showVoiceRecorder = true"
      >
        <template #attach-btn>
          <!-- Menu de Anexos estilo WhatsApp -->
          <AttachmentMenu
            v-model="showAttachmentMenu"
            @file-selected="handleFilesSelected"
          >
            <template #activator="{ props }">
              <v-btn 
                icon 
                variant="text" 
                color="grey-darken-1"
                size="large"
                class="attach-btn"
                :disabled="uploadingFile"
                v-bind="props"
              >
                <v-icon class="attach-icon">mdi-paperclip</v-icon>
              </v-btn>
            </template>
          </AttachmentMenu>
        </template>
      </DSChatInput>
    </div>

    <!-- GRAVADOR DE VOZ -->
    <VoiceRecorder
      v-model="showVoiceRecorder"
      @audio-recorded="handleAudioRecorded"
    />

    <!-- GRAVADOR DE VOZ -->
    <VoiceRecorder
      v-model="showVoiceRecorder"
      @audio-recorded="handleAudioRecorded"
    />

    <!-- CRIADOR DE BOT PERSONALIZADO -->
    <CustomBotCreator
      v-model="showBotCreator"
      @bot-created="handleBotCreated"
    />

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

    <!-- Dialog de Conexão WPPConnect -->
    <WppConnectDialog v-model="showWppConnectDialog" session="default" />
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onBeforeUnmount, computed, nextTick } from 'vue';
import { useRouter } from 'vue-router';
import DSMessageBubble from '../design-system/components/DSMessageBubble.vue';
import DSChatInput from '../design-system/components/DSChatInput.vue';
import TypingIndicator from '../components/TypingIndicator.vue';
import DateSeparator from '../components/DateSeparator.vue';
import AttachmentMenu from '../components/AttachmentMenu.vue';
import VoiceRecorder from '../components/VoiceRecorder.vue';
import CustomBotCreator from '../components/CustomBotCreator.vue';
import WppConnectDialog from '../components/WppConnectDialog.vue';
import { useChatStore } from '../stores/chat';
import { useAuthStore } from '../stores/auth';
import { useContactsStore } from '../stores/contacts';
import { useScrollToBottom } from '../design-system/composables/useScrollToBottom.ts';
import { colors, spacing } from '../design-system/tokens/index.ts';
import { uploadAndSend } from '../composables/useUpload';
import type { Contact } from '../stores/contacts';

// 🆕 Props
interface Props {
  contact?: Contact;
}
const props = defineProps<Props>();

const router = useRouter();
const chatStore = useChatStore();
const authStore = useAuthStore();
const contactsStore = useContactsStore();
const author = ref('');
const text = ref('');
const showNameDialog = ref(false); // Não mostra mais o dialog de nome

// 🆕 Computed: ID do usuário atual
const currentUserId = computed(() => authStore.user?.id || '');
const isScrolledToBottom = ref(true);
const lastScrollTop = ref(0);
const showAttachmentMenu = ref(false);
const showVoiceRecorder = ref(false);
const showBotCreator = ref(false);
const showWppConnectDialog = ref(false);
const showGuruCommands = ref(true); // 🧠 Mostra chips do Guru por padrão
const guruSessionActive = ref(false); // 🧠 Rastreia se está em sessão com Guru
const apiBaseUrl = import.meta.env.VITE_SOCKET_URL || 'http://localhost:3000';
const uploadingFile = ref(false);
const uploadProgress = ref(0);

const { containerRef, scrollToBottom } = useScrollToBottom();

// Carrega autenticação do localStorage
authStore.load();

// Define o nome do autor baseado no usuário autenticado
if (authStore.user) {
  author.value = authStore.user.name;
}

// 🆕 COMPUTED: Agrupa mensagens por data e autor
const groupedMessages = computed(() => {
  const result: any[] = [];
  let lastDate: string | null = null;
  let lastAuthor: string | null = null;
  let lastTimestamp = 0;
  const TIME_GAP = 5 * 60 * 1000; // 5 minutos

  // Proteção contra messages undefined
  const messages = chatStore.messages || [];
  
  messages.forEach((msg, index) => {
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
      // 🔧 NÃO sobrescreve o type original (mantém 'text', 'image', 'file', etc)
      showAuthor: !shouldGroup || msg.author !== author.value,
      showTimestamp: !shouldGroup || index === messages.length - 1,
    });

    lastAuthor = msg.author;
    lastTimestamp = msg.timestamp;
  });

  return result;
});

// 🆕 COMPUTED: Conta mensagens não lidas
const unreadCount = computed(() => {
  const messages = chatStore.messages || [];
  return messages.filter(m => 
    m.userId !== currentUserId.value && m.status !== 'read'
  ).length;
});

// 🧠 Watch para detectar sessão ativa com Guru
watch(() => chatStore.messages, (messages) => {
  if (!messages || messages.length === 0) return;
  
  // Pega última mensagem
  const lastMessage = messages[messages.length - 1];
  if (!lastMessage?.author?.includes('Guru')) return;
  
  // Verifica se é mensagem de despedida (prioridade)
  const sessionEnded = lastMessage.text?.includes('👋 Até logo');
  
  // Verifica se é mensagem de boas-vindas
  const sessionStarted = lastMessage.text?.includes('pode falar direto comigo') || 
    lastMessage.text?.includes('sem mencionar @guru');
  
  if (sessionEnded) {
    console.log('🚪 Sessão do Guru encerrada');
    guruSessionActive.value = false;
    localStorage.removeItem('guruSessionActive');
  } else if (sessionStarted) {
    console.log('🎉 Sessão do Guru iniciada');
    guruSessionActive.value = true;
    localStorage.setItem('guruSessionActive', 'true');
  }
}, { deep: true });

// Conecta ao socket e carrega histórico ao montar
onMounted(async () => {
  console.log('📱 ChatView mounted');
  
  // Carrega autenticação do localStorage (pode já estar carregado pelo router)
  authStore.load();
  
  // Carrega estado da sessão do Guru
  guruSessionActive.value = localStorage.getItem('guruSessionActive') === 'true';
  
  // Verifica se tem token válido
  if (!authStore.token) {
    console.warn('⚠️ Sem token, redirecionando para login...');
    router.push('/login');
    return;
  }
  
  // Define o nome do usuário no store
  if (author.value) {
    chatStore.currentUser = author.value;
  }
  
  try {
    // Conecta ao socket com token JWT se não conectado
    if (!chatStore.connected) {
      await chatStore.connect(authStore.token);
    }
    
    // 🆕 Carrega mensagens do contato específico
    if (props.contact) {
      await chatStore.loadMessages(undefined, props.contact.id);
      // Marca mensagens como lidas
      await contactsStore.markContactRead(props.contact.id);
    }
    
    scrollToBottom();
    console.log('✅ Socket conectado e mensagens carregadas para contato:', props.contact?.name);
  } catch (error) {
    console.error('❌ Erro ao conectar socket:', error);
    // Se falhar autenticação, redireciona para login
    router.push('/login');
  }
});

// 🆕 Watch para recarregar quando mudar de contato
watch(() => props.contact?.id, async (newContactId, oldContactId) => {
  console.log('👀 Watch contact.id:', { newContactId, oldContactId, contact: props.contact });
  if (newContactId && newContactId !== oldContactId) {
    console.log('🔄 Mudou de contato:', newContactId);
    await chatStore.loadMessages(undefined, newContactId);
    await contactsStore.markContactRead(newContactId);
    scrollToBottom();
  }
}, { immediate: true });

// Desconecta ao desmontar
onBeforeUnmount(() => {
  chatStore.disconnect();
});

// 🆕 Auto-scroll INTELIGENTE (só rola se usuário estava no final)
watch(() => chatStore.messages?.length ?? 0, () => {
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
    
    // 🆕 Passa contactId para paginação
    await chatStore.loadMessages(oldestMessage.timestamp, props.contact?.id);
    
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

// 🧠 FUNÇÃO: Insere comando do Guru no input e envia automaticamente
function insertCommand(command: string) {
  // Se for menção de agente (começa com @), coloca no input para usuário completar
  if (command.startsWith('@') && command.includes(' ')) {
    text.value = command;
    // Foca no input para usuário digitar
    nextTick(() => {
      const inputEl = document.querySelector<HTMLInputElement>('.v-field__input input');
      if (inputEl) inputEl.focus();
    });
  } else {
    // Comandos normais: envia diretamente
    handleSendMessage(command);
  }
  // Minimiza a barra de comandos
  showGuruCommands.value = false;
}

// 🤖 FUNÇÃO: Handler para quando um bot customizado é criado
async function handleBotCreated(bot: { 
  name: string; 
  emoji: string; 
  prompt: string; 
  specialties: string[];
  openaiApiKey: string;
  openaiAccount?: string;
}) {
  try {
    const response = await fetch(`${apiBaseUrl}/custom-bots`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authStore.token}`
      },
      body: JSON.stringify({
        name: bot.name,
        emoji: bot.emoji,
        prompt: bot.prompt,
        specialties: bot.specialties,
        openaiApiKey: bot.openaiApiKey,
        openaiAccount: bot.openaiAccount
      })
    });
    
    if (!response.ok) {
      throw new Error('Falha ao criar bot');
    }
    
    const data = await response.json();
    console.log('✅ Bot criado com sucesso:', data.bot);
    
    // TODO: Adicionar chip dinamicamente na barra de comandos
    // TODO: Mostrar snackbar de sucesso
  } catch (error) {
    console.error('❌ Erro ao criar bot customizado:', error);
    // TODO: Mostrar snackbar de erro
  }
}

function closeDialog() {
  if (author.value.trim()) {
    showNameDialog.value = false;
  }
}

async function handleFilesSelected(fileList: FileList) {
  console.log('🚀 Arquivos selecionados:', fileList.length);
  
  // Upload de múltiplos arquivos sequencialmente
  for (let i = 0; i < fileList.length; i++) {
    const file = fileList[i];
    if (file) {
      await handleFileUpload(file);
    }
  }
}

async function handleFileUpload(file: File) {
  console.log('🚀 Iniciando upload do arquivo:', file.name);
  uploadingFile.value = true;
  uploadProgress.value = 0;
  
  try {
    await uploadAndSend(apiBaseUrl, file, author.value, (progress) => {
      uploadProgress.value = progress;
      console.log(`📊 Progresso: ${progress}%`);
    });
    
    uploadingFile.value = false;
    uploadProgress.value = 0;
    scrollToBottom(true);
    console.log('✅ Upload concluído com sucesso!');
  } catch (error: any) {
    uploadingFile.value = false;
    uploadProgress.value = 0;
    console.error('❌ Erro no upload:', error);
    // TODO: Mostrar mensagem de erro ao usuário
  }
}

async function handleAudioRecorded(audioBlob: Blob) {
  console.log('🎤 Áudio gravado:', audioBlob.size, 'bytes');
  
  // Converte o blob WebM para arquivo com nome
  const timestamp = Date.now();
  const audioFile = new File([audioBlob], `audio_${timestamp}.webm`, { 
    type: 'audio/webm' 
  });
  
  await handleFileUpload(audioFile);
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

.messages-wrapper {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  position: relative;
  padding-bottom: 100px; /* Espaço para input + barra guru + typing */
  background-color: #e5ddd5;
  background-image: url('data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAYAAACNMs+9AAAAGElEQVQYlWNgYGCQwoKxgqGgcJA5h3yFAAs8BRWVSwooAAAAAElFTkSuQmCC');
  background-repeat: repeat;
  opacity: 0.98;
}

/* 📱 Mobile - Padding ajustado */
@media (max-width: 599px) {
  .messages-wrapper {
    padding-bottom: 90px;
  }
}

/* 📱 Tablet */
@media (min-width: 600px) and (max-width: 959px) {
  .messages-wrapper {
    padding-bottom: 110px;
  }
}

/* 🖥️ Desktop */
@media (min-width: 960px) {
  .messages-wrapper {
    padding-bottom: 120px;
  }
}

.messages-area {
  min-height: 100%;
  display: flex;
  flex-direction: column;
  padding: 16px;
}

/* 📱 Tablet e Desktop - Padding maior */
@media (min-width: 600px) {
  .messages-area {
    padding: 20px;
  }
}

@media (min-width: 960px) {
  .messages-area {
    padding: 24px;
  }
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

/* 🧠 Banner de sessão ativa com Guru */
.guru-session-banner {
  background: linear-gradient(135deg, #00695c 0%, #00897b 100%);
  border-bottom: 2px solid #004d40;
  animation: slideDown 0.3s ease-out;
}

.session-text {
  color: white;
  font-weight: 600;
  font-size: 13px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.pulse-icon {
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.6;
    transform: scale(1.2);
  }
}

/* 🧠 Barra de comandos do Guru */
.guru-commands-bar {
  background: linear-gradient(135deg, #e0f7fa 0%, #b2ebf2 100%);
  border-bottom: 1px solid #4dd0e1;
  padding: 10px 12px;
  overflow-x: auto;
  overflow-y: hidden;
  animation: slideDown 0.3s ease-out;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.guru-commands-content {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
  width: 100%;
}

.guru-commands-header {
  display: flex;
  align-items: center;
  margin-right: 8px;
  margin-bottom: 8px;
  font-weight: 600;
  font-size: 13px;
  color: #00695c;
  white-space: nowrap;
}

.guru-commands-title {
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.guru-commands-bar .v-chip {
  cursor: pointer;
  transition: all 0.2s ease;
  font-weight: 500;
  font-size: 12px;
  white-space: nowrap;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.guru-commands-bar .v-chip:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
}

.guru-commands-bar .v-chip:active {
  transform: translateY(0);
}

/* 🔘 Botão toggle do Guru */
.guru-toggle-btn {
  position: fixed !important;
  bottom: 76px;
  right: 24px;
  z-index: 11;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
  animation: bounce 2s infinite;
  transition: all 0.2s ease;
}

@keyframes bounce {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-4px);
  }
}

.guru-toggle-btn:hover {
  animation: none;
}

/* 📱 Mobile - Scrollbar horizontal sutil */
.guru-commands-bar::-webkit-scrollbar {
  height: 4px;
}

.guru-commands-bar::-webkit-scrollbar-track {
  background: transparent;
}

.guru-commands-bar::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 2px;
}

/* 📱 Mobile - Ajustes responsivos */
@media (max-width: 599px) {
  .guru-commands-bar {
    padding: 8px 10px;
  }
  
  .guru-commands-header {
    font-size: 11px;
  }
  
  .guru-commands-bar .v-chip {
    font-size: 11px;
    height: 28px;
  }
  
  .guru-toggle-btn {
    bottom: 68px;
    right: 16px;
  }
}

.messages-wrapper::-webkit-scrollbar {
  width: 8px;
}

/* 📱 Mobile - Scrollbar mais fina */
@media (max-width: 599px) {
  .messages-wrapper::-webkit-scrollbar {
    width: 4px;
  }
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

/* 📱 Mobile - Botão menor e mais à esquerda */
@media (max-width: 599px) {
  .new-messages-fab {
    bottom: 80px;
    right: 16px;
  }
}

/* 📎 Estilo WhatsApp - Clipe rotacionado 135° */
.attach-btn {
  transition: transform 0.2s ease;
}

.attach-icon {
  transform: rotate(135deg);
  transition: transform 0.2s ease;
}

.attach-btn:hover .attach-icon {
  transform: rotate(135deg) scale(1.1);
}

/* 📱 Mobile - Efeito touch (sem hover) */
@media (hover: none) and (pointer: coarse) {
  .attach-btn:active .attach-icon {
    transform: rotate(135deg) scale(0.95);
  }
}

/* 🤖 Botão de Criar Bot Personalizado */
.custom-bot-btn {
  position: fixed !important;
  bottom: 140px;
  right: 24px;
  z-index: 100;
  box-shadow: 0 2px 8px rgba(156, 39, 176, 0.3);
  transition: all 0.2s ease;
}

.custom-bot-btn:hover {
  transform: scale(1.1);
  box-shadow: 0 4px 16px rgba(156, 39, 176, 0.4);
}

/* 📱 Mobile - Ajustes responsivos */
@media (max-width: 599px) {
  .custom-bot-btn {
    bottom: 120px;
    right: 16px;
  }
}

/* 📱 Mobile - Efeito touch */
@media (hover: none) and (pointer: coarse) {
  .custom-bot-btn:active {
    transform: scale(0.95);
  }
}
</style>
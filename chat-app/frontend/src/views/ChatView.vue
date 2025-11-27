<template>
  <div class="chat-container">
    <!-- ÁREA DE MENSAGENS -->
    <div 
      ref="containerRef" 
      class="messages-wrapper u-scrollable-y"
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

      <div class="messages-area">
        <MessageList
          :grouped-messages="groupedMessages"
          :current-user-id="currentUserId"
          :typing-users="chatStore.typingUsers"
        />
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
      <Transition
        enter-active-class="animate__animated animate__bounceIn animate__faster"
        leave-active-class="animate__animated animate__zoomOut animate__faster"
      >
        <DSCommandBar 
          v-if="showGuruCommands" 
          v-model="showGuruCommands" 
          @command="insertCommand" 
        />
      </Transition>

      <!-- 🔘 Botão Guru flutuante -->
      <v-btn
        icon="mdi-robot-happy"
        size="small"
        color="teal-darken-1"
        variant="flat"
        class="guru-toggle-btn"
        @click="showGuruCommands = !showGuruCommands"
        :title="showGuruCommands ? 'Ocultar comandos do Guru' : 'Mostrar comandos do Guru'"
      />
      
      <!-- 🤖 Botão para criar bot personalizado -->
      <v-btn
        icon="mdi-plus-circle"
        size="small"
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
        @submit="(msg) => { console.log('📤 DSChatInput @submit:', msg); handleSendMessage(msg); }"
        @typing="handleTyping"
        @emoji="() => {}"
        @voice="showVoiceRecorder = true"
      >
        <template #attach-btn>
          <!-- Menu de Anexos estilo WhatsApp -->
          <DSAttachmentMenu
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
          </DSAttachmentMenu>
        </template>
      </DSChatInput>
    </div>

    <!-- GRAVADOR DE VOZ -->
    <DSVoiceRecorder
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

    <!-- 🔥 Painéis de Agente Abertos (Chat-in-Chat Flutuantes) -->
    <AgentChatPane
      v-for="(panel, index) in agentPanels.filter(p => !p.minimized)"
      :key="panel.key"
      :agent-key="panel.key"
      :title="panel.title"
      :emoji="panel.emoji"
      :stack-index="index"
      :contact-id="chatStore.currentContactId || undefined"
      @close="closeAgentPanel(panel.key)"
      @minimize="minimizeAgentPanel(panel.key)"
    />

    <!-- 🔥 Abas de Agentes Minimizados (Barra Inferior) -->
    <div v-if="agentPanels.filter(p => p.minimized).length > 0" class="minimized-agents-bar">
      <div
        v-for="panel in agentPanels.filter(p => p.minimized)"
        :key="`min-${panel.key}`"
        class="minimized-agent-tab"
        @click="openAgentPanel(panel.key, panel.title, panel.emoji)"
      >
        <span class="tab-emoji">{{ panel.emoji || '🤖' }}</span>
        <span class="tab-name">{{ panel.title.split(' ')[0] }}</span>
        <button 
          @click.stop="closeAgentPanel(panel.key)" 
          class="tab-close"
          title="Fechar"
        >
          <v-icon size="x-small">mdi-close</v-icon>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onBeforeUnmount, computed, nextTick } from 'vue';
import { useRouter } from 'vue-router';
import MessageList from '../features/chat/components/MessageList.vue';
import DSChatInput from '../design-system/components/DSChatInput';
import { DSAttachmentMenu } from '../design-system/components/DSAttachmentMenu';
import { DSVoiceRecorder } from '../design-system/components/DSVoiceRecorder';
import CustomBotCreator from '../features/agents/components/CustomBotCreator.vue';
import WppConnectDialog from '../features/whatsapp/components/WppConnectDialog.vue';
import AgentChatPane from '../features/agents/components/AgentChatPane.vue';
import { useChatStore } from '../stores/chat';
import { useAuthStore } from '../stores/auth';
import { useContactsStore } from '../stores/contacts';
import { useScrollToBottom } from '../design-system/composables/useScrollToBottom.ts';
import { colors, spacing } from '../design-system/tokens/index.ts';
import { uploadAndSend } from '../composables/useUpload';
import type { Contact } from '../stores/contacts';
import { DSCommandBar } from '../design-system/components/DSCommandBar';

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
const showGuruCommands = ref(false); // 🧠 Mostra chips do Guru apenas quando clicar no botão
const guruSessionActive = ref(false); // 🧠 Rastreia se está em sessão com Guru
const apiBaseUrl = import.meta.env.VITE_SOCKET_URL || 'http://localhost:3000';
const uploadingFile = ref(false);
const uploadProgress = ref(0);

const { containerRef, scrollToBottom } = useScrollToBottom();

// 🆕 Estado para painéis de agente (chat-in-chat) vinculados por contactId
// Estrutura: { contactId: [{ key, title, emoji, minimized }] }
const agentPanelsByContact = ref<Record<string, Array<{ key: string; title: string; emoji?: string; minimized?: boolean }>>>({});

// 🆕 Computed: Painéis do contato atual
const agentPanels = computed(() => {
  const contactId = props.contact?.id || chatStore.currentContactId;
  if (!contactId) return [];
  return agentPanelsByContact.value[contactId] || [];
});

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
  
  // 🆕 Verifica se o token está expirado
  if (authStore.isTokenExpired()) {
    console.warn('⚠️ Token expirado, redirecionando para login...');
    authStore.logout();
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
    
    // 🆕 Os painéis de agente são mantidos por contato automaticamente
    // Cada contato tem seus próprios painéis salvos em agentPanelsByContact
    console.log('📋 Painéis do novo contato:', agentPanelsByContact.value[newContactId] || []);
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
  // Se for menção de agente (começa com @), abre painel lateral SEM enviar ao chat
  if (command.startsWith('@')) {
    const agentKey = command.replace('@', '').trim().split(' ')[0];
    console.log('🔍 insertCommand:', command, '→ agentKey:', agentKey);
    
    if (!agentKey) {
      console.warn('⚠️ agentKey vazio no insertCommand');
      return;
    }
    
    // Mapeia agentes conhecidos
    const agentMap: Record<string, { title: string; emoji: string }> = {
      'advogado': { title: 'Dr. Advocatus', emoji: '⚖️' },
      'vendedor': { title: 'Vendedor Pro', emoji: '💼' },
      'medico': { title: 'Dr. Saúde', emoji: '🩺' },
      'psicologo': { title: 'Psicólogo', emoji: '🧘' },
      'sdr': { title: 'SDR', emoji: '📅' },
      'guru': { title: 'Guru IA', emoji: '🧠' }
    };
    
    const agent = agentMap[agentKey.toLowerCase()] || { title: agentKey, emoji: '🤖' };
    console.log('✅ Abrindo painel (insertCommand):', agentKey, agent);
    openAgentPanel(agentKey, agent.title, agent.emoji);
    showGuruCommands.value = false;
    return; // ⚠️ NÃO envia mensagem ao chat principal
  }
  
  // Comandos normais: envia diretamente
  handleSendMessage(command);
  showGuruCommands.value = false;
}

// 🆕 FUNÇÕES: Gerenciamento de painéis de agente (vinculados por contactId)
function openAgentPanel(key: string, title: string, emoji?: string) {
  const contactId = props.contact?.id || chatStore.currentContactId;
  
  if (!contactId) {
    console.warn('⚠️ Tentativa de abrir painel sem contactId');
    return;
  }
  
  console.log('📂 openAgentPanel chamado:', { key, title, emoji, contactId });
  
  // Inicializa array para este contato se não existir
  if (!agentPanelsByContact.value[contactId]) {
    agentPanelsByContact.value[contactId] = [];
  }
  
  // Verifica se já existe (aberto ou minimizado) neste contato
  const existing = agentPanelsByContact.value[contactId].find(p => p.key === key);
  if (existing) {
    console.log('🔄 Painel já existe no contato, maximizando:', key);
    // Se existe mas está minimizado, maximiza
    existing.minimized = false;
  } else {
    console.log('➕ Criando novo painel para o contato:', key, contactId);
    // Se não existe, adiciona novo painel
    agentPanelsByContact.value[contactId].push({ key, title, emoji, minimized: false });
  }
  
  console.log('📋 Estado dos painéis deste contato:', agentPanelsByContact.value[contactId]);
}

function closeAgentPanel(key: string) {
  const contactId = props.contact?.id || chatStore.currentContactId;
  
  if (!contactId || !agentPanelsByContact.value[contactId]) {
    console.warn('⚠️ Tentativa de fechar painel sem contactId');
    return;
  }
  
  console.log('❌ Fechando painel:', key, 'do contato:', contactId);
  agentPanelsByContact.value[contactId] = agentPanelsByContact.value[contactId].filter(p => p.key !== key);
}

function minimizeAgentPanel(key: string) {
  const contactId = props.contact?.id || chatStore.currentContactId;
  
  if (!contactId || !agentPanelsByContact.value[contactId]) {
    console.warn('⚠️ Tentativa de minimizar painel sem contactId');
    return;
  }
  
  console.log('➖ Minimizando painel:', key, 'do contato:', contactId);
  const panel = agentPanelsByContact.value[contactId].find(p => p.key === key);
  if (panel) {
    panel.minimized = true;
    console.log('✅ Painel minimizado:', key);
  } else {
    console.warn('⚠️ Painel não encontrado para minimizar:', key);
  }
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
    await uploadAndSend(
      apiBaseUrl,
      file,
      author.value,
      authStore.token,
      chatStore.currentContactId,
      (progress) => {
      uploadProgress.value = progress;
      console.log(`📊 Progresso: ${progress}%`);
      }
    );
    
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

<style scoped lang="scss" src="./ChatView.scss"></style>

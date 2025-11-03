<template>
  <v-container fluid class="pa-0 fill-height" style="background: #e5ddd5;">
    <v-row no-gutters class="fill-height">
      <!-- HEADER -->
      <v-col cols="12">
        <v-app-bar color="#075e54" elevation="1" style="border-bottom: 1px solid #128c7e;">
          <v-app-bar-title class="text-white d-flex align-center">
            <v-avatar size="40" class="mr-3" color="#25d366">
              <span class="text-h6">{{ author.charAt(0).toUpperCase() }}</span>
            </v-avatar>
            <div>
              <div class="text-subtitle-1 font-weight-bold">{{ author }}</div>
              <div class="text-caption" style="opacity: 0.8;">Online</div>
            </div>
          </v-app-bar-title>

          <template v-slot:append>
            <v-btn icon="mdi-magnify" color="white" variant="text"></v-btn>
            <v-btn icon="mdi-dots-vertical" color="white" variant="text"></v-btn>
          </template>
        </v-app-bar>
      </v-col>

      <!-- ÁREA DE MENSAGENS -->
      <v-col cols="12" style="flex: 1; overflow: hidden;">
        <div ref="messagesContainer" class="messages-area" style="
          height: calc(100vh - 120px);
          overflow-y: auto;
          padding: 20px;
          background-image: url('data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAYAAACNMs+9AAAAGElEQVQYlWNgYGCQwoKxgqGgcJA5h3yFAAs8BRWVSwooAAAAAElFTkSuQmCC');
          background-repeat: repeat;
        ">
          <!-- Mensagens -->
          <div
            v-for="(msg, idx) in messages"
            :key="idx"
            :class="['mb-2', msg.author === author ? 'd-flex justify-end' : 'd-flex justify-start']"
          >
            <div :class="['message-bubble', msg.author === author ? 'sent' : 'received']">
              <!-- Nome do autor (apenas nas mensagens recebidas) -->
              <div v-if="msg.author !== author" class="author-name text-caption font-weight-bold mb-1">
                {{ msg.author }}
              </div>
              
              <!-- Texto da mensagem -->
              <div class="message-text">{{ msg.text }}</div>
              
              <!-- Timestamp e status -->
              <div class="message-footer">
                <span class="time">{{ formatTime(msg.timestamp) }}</span>
                <v-icon 
                  v-if="msg.author === author" 
                  size="16" 
                  color="blue-lighten-1"
                  class="ml-1"
                >
                  mdi-check-all
                </v-icon>
              </div>
            </div>
          </div>
        </div>
      </v-col>

      <!-- INPUT DE MENSAGEM -->
      <v-col cols="12" style="background: #f0f0f0; border-top: 1px solid #d1d1d1;">
        <v-form @submit.prevent="send" class="d-flex align-center pa-2">
          <!-- Botão de emoji -->
          <v-btn icon="mdi-emoticon-outline" variant="text" color="grey-darken-1" class="mr-2"></v-btn>
          
          <!-- Campo de texto -->
          <v-text-field
            v-model="text"
            placeholder="Digite uma mensagem"
            variant="outlined"
            density="compact"
            hide-details
            rounded
            bg-color="white"
            class="flex-grow-1"
            @keyup.enter.prevent="send"
          >
            <template v-slot:append-inner>
              <v-btn icon="mdi-paperclip" variant="text" size="small" color="grey-darken-1"></v-btn>
            </template>
          </v-text-field>
          
          <!-- Botão de enviar -->
          <v-btn
            icon
            :color="text.trim() ? '#25d366' : 'grey'"
            class="ml-2"
            @click="send"
            :disabled="!text.trim()"
          >
            <v-icon>{{ text.trim() ? 'mdi-send' : 'mdi-microphone' }}</v-icon>
          </v-btn>
        </v-form>
      </v-col>
    </v-row>

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
            @keyup.enter="showNameDialog = false"
          ></v-text-field>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="#25d366" variant="flat" @click="showNameDialog = false" :disabled="!author.trim()">
            Entrar
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue';
import { io, Socket } from 'socket.io-client';

type Message = { 
  author: string; 
  text: string;
  timestamp?: number;
};

const messages = ref<Message[]>([]);
const author = ref('');
const text = ref('');
const showNameDialog = ref(true);
const messagesContainer = ref<HTMLElement | null>(null);
let socket: Socket | null = null;

onMounted(() => {
  socket = io(import.meta.env.VITE_SOCKET_URL || 'http://localhost:3000', {
    transports: ['websocket'],
  });
  
  socket.on('chat:new-message', (msg: Message) => {
    messages.value.push({
      ...msg,
      timestamp: msg.timestamp || Date.now()
    });
    scrollToBottom();
  });
});

onBeforeUnmount(() => {
  socket?.disconnect();
});

function send() {
  if (!text.value.trim()) return;
  
  const msg: Message = {
    author: author.value || 'Anônimo',
    text: text.value,
    timestamp: Date.now()
  };
  
  socket?.emit('chat:new-message', msg);
  text.value = '';
}

function formatTime(timestamp?: number): string {
  if (!timestamp) return '';
  const date = new Date(timestamp);
  return date.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
}

async function scrollToBottom() {
  await nextTick();
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
  }
}
</script>

<style scoped>
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

.message-bubble {
  max-width: 65%;
  padding: 8px 12px;
  border-radius: 8px;
  position: relative;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.message-bubble.sent {
  background: #dcf8c6;
  border-top-right-radius: 0;
}

.message-bubble.received {
  background: white;
  border-top-left-radius: 0;
}

.author-name {
  color: #075e54;
}

.message-text {
  word-wrap: break-word;
  margin-bottom: 4px;
  font-size: 14px;
  line-height: 1.4;
}

.message-footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 4px;
}

.time {
  font-size: 11px;
  color: rgba(0, 0, 0, 0.45);
}
</style>
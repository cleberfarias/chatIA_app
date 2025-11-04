import { ref, onMounted, onBeforeUnmount } from 'vue';
import { io, Socket } from 'socket.io-client';
import type { Message } from '../types';

export function useChat(socketUrl: string) {
  const messages = ref<Message[]>([]);
  const isConnected = ref(false);
  const isTyping = ref(false);
  let socket: Socket | null = null;

  onMounted(() => {
    socket = io(socketUrl, {
      transports: ['websocket'],
    });

    socket.on('connect', () => {
      isConnected.value = true;
      console.log('✅ Conectado ao servidor');
    });

    socket.on('disconnect', () => {
      isConnected.value = false;
      console.log('❌ Desconectado do servidor');
    });

    socket.on('chat:new-message', (msg: Message) => {
      console.log('📨 Nova mensagem recebida:', msg);
      messages.value.push(msg);
    });

    socket.on('user:typing', (data: { userId: string; isTyping: boolean }) => {
      isTyping.value = data.isTyping;
    });
  });

  onBeforeUnmount(() => {
    socket?.disconnect();
  });

  function sendMessage(message: Omit<Message, 'id' | 'timestamp'>) {
    const msg: Message = {
      ...message,
      id: crypto.randomUUID(),
      timestamp: Date.now(),
    };
    
    console.log('📤 Enviando mensagem:', msg);
    socket?.emit('chat:new-message', msg);
    messages.value.push(msg);
  }

  function sendTypingStatus(typing: boolean) {
    socket?.emit('user:typing', typing);
  }

  return {
    messages,
    isConnected,
    isTyping,
    sendMessage,
    sendTypingStatus,
  };
}
import { defineStore } from 'pinia';
import { io, Socket } from 'socket.io-client';
import type { Message, TypingInfo } from '@/design-system/types/validation';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:3000';

// 🔧 Configurações de retry
const MAX_RETRIES = 3;
const RETRY_DELAYS = [1000, 2000, 4000]; // Backoff: 1s, 2s, 4s

export const useChatStore = defineStore('chat', {
  state: () => ({
    socket: null as Socket | null,
    messages: [] as Message[],
    connected: false,
    currentUser: 'Usuário',
    currentContactId: null as string | null, // 🆕 ID do contato selecionado
    
    // 🆕 UX Features
    isTyping: {} as Record<string, TypingInfo>, // userId -> info
    pendingMessages: new Map<string, { message: Message; retries: number }>(),
    hasMoreMessages: true,
    loadingMore: false,
    
    // 🆕 Scroll tracking
    isScrolledToBottom: true,
    hasUnreadMessages: false,
  }),

  actions: {
    /**
     * 🔌 Conecta ao servidor Socket.IO com autenticação JWT
     */
    async connect(token: string) {
      if (this.socket?.connected) {
        console.log('✅ Socket já conectado');
        return;
      }

      if (!token) {
        console.error('❌ Token JWT não fornecido');
        throw new Error('Token JWT obrigatório para conexão');
      }

      console.log('🔌 Conectando ao Socket.IO com token JWT...');

      this.socket = io(API_URL, {
        auth: { token },
        transports: ['websocket', 'polling'],
        reconnection: true,
        reconnectionAttempts: 5,
        reconnectionDelay: 1000,
      });

      // ✅ Evento: Conectado
      this.socket.on('connect', () => {
        console.log('✅ Socket conectado com sucesso');
        this.connected = true;
        this.retryPendingMessages(); // Tenta reenviar mensagens pendentes
      });

      // ❌ Evento: Desconectado
      this.socket.on('disconnect', (reason: string) => {
        console.log('❌ Socket desconectado:', reason);
        this.connected = false;
      });

      // ❌ Evento: Erro de conexão
      this.socket.on('connect_error', (error: Error) => {
        console.error('❌ Erro ao conectar:', error.message);
        
        // Se erro de autenticação, lança exceção para redirecionar ao login
        if (error.message.includes('invalid') || error.message.includes('unauthorized')) {
          console.warn('⚠️ Token inválido, necessário relogin');
          this.connected = false;
          throw new Error('Autenticação inválida');
        }
      });

      // 📨 Evento: Nova mensagem de outro usuário
      this.socket.on('chat:new-message', async (msg: Message) => {
        console.log('📨 Nova mensagem recebida:', msg);
        console.log('🔍 currentContactId:', this.currentContactId, 'msg.userId:', msg.userId, 'msg.contactId:', msg.contactId);
        
        // 🆕 Verifica se mensagem é do contato que está conversando
        // Mensagem pertence à conversa atual se:
        // - Mensagem VEIO do contato selecionado (msg.userId === currentContactId)
        const isFromCurrentContact = this.currentContactId && msg.userId === this.currentContactId;
        
        console.log('✅ isFromCurrentContact:', isFromCurrentContact);
        
        // Adiciona mensagem ao chat se estiver na conversa correta
        if (isFromCurrentContact || !this.currentContactId) {
          this.messages.push(msg);
          
          // Se usuário está acima, mostra badge "Novas mensagens"
          if (!this.isScrolledToBottom) {
            this.hasUnreadMessages = true;
          }
        }
        
        // 🆕 Atualiza lista de contatos (sempre, independente do contato atual)
        if (msg.userId) {
          const { useContactsStore } = await import('./contacts');
          const contactsStore = useContactsStore();
          
          // Se não está visualizando este contato, incrementa unread
          if (!isFromCurrentContact) {
            console.log('📬 Incrementando unread para contato:', msg.userId);
            contactsStore.incrementUnread(msg.userId);
          }
          
          // Atualiza última mensagem do remetente
          console.log('📝 Atualizando última mensagem do contato:', msg.userId);
          contactsStore.updateContactLastMessage(msg.userId, msg.text, msg.timestamp);
        }
      });

      // ✅ Evento: ACK do servidor (troca tempId por id real)
      this.socket.on('chat:ack', (data: { tempId: string; id: string; status: string; timestamp: number }) => {
        console.log('✅ ACK recebido:', data);
        
        const pending = this.pendingMessages.get(data.tempId);
        if (pending) {
          // Remove da fila de pendentes
          this.pendingMessages.delete(data.tempId);
          
          // Atualiza mensagem na lista
          const msg = this.messages.find((m: Message) => m.tempId === data.tempId);
          if (msg) {
            msg.id = data.id;
            msg.status = data.status as any;
            msg.timestamp = data.timestamp;
            delete msg.tempId;
          }
        }
      });

      // 📬 Evento: Mensagem entregue
      this.socket.on('chat:delivered', (data: { id: string }) => {
        console.log('📬 Delivered:', data.id);
        const msg = this.messages.find((m: Message) => m.id === data.id);
        if (msg && msg.status === 'sent') {
          msg.status = 'delivered';
        }
      });

      // 👁️ Evento: Mensagens lidas
      this.socket.on('chat:read', (data: { ids: string[] }) => {
        console.log('👁️ Read:', data.ids);
        data.ids.forEach((id: string) => {
          const msg = this.messages.find((m: Message) => m.id === id);
          if (msg) msg.status = 'read';
        });
      });

      // ⌨️ Evento: Usuário digitando
      this.socket.on('chat:typing', (data: TypingInfo) => {
        console.log('⌨️ Typing:', data);
        
        if (data.isTyping) {
          this.isTyping[data.userId] = data;
          
          // 🔧 Auto-remove após 3s (timeout)
          setTimeout(() => {
            if (this.isTyping[data.userId]?.isTyping) {
              delete this.isTyping[data.userId];
            }
          }, 3000);
        } else {
          delete this.isTyping[data.userId];
        }
      });

      // ❌ Evento: Erro do servidor
      this.socket.on('error', (error: { message: string; tempId?: string }) => {
        console.error('❌ Erro do servidor:', error);
        
        if (error.tempId) {
          this.retryMessage(error.tempId);
        }
      });

      // 🟢 Evento: Usuário ficou online
      this.socket.on('user:online', async (data: { userId: string }) => {
        console.log('🟢 Usuário online:', data.userId);
        const { useContactsStore } = await import('./contacts');
        const contactsStore = useContactsStore();
        contactsStore.setOnlineStatus(data.userId, true);
      });

      // 🔴 Evento: Usuário ficou offline
      this.socket.on('user:offline', async (data: { userId: string }) => {
        console.log('🔴 Usuário offline:', data.userId);
        const { useContactsStore } = await import('./contacts');
        const contactsStore = useContactsStore();
        contactsStore.setOnlineStatus(data.userId, false);
      });

      // 📜 Carrega histórico inicial
      await this.loadMessages();
    },

    /**
     * 🔌 Desconecta do servidor
     */
    disconnect() {
      this.socket?.disconnect();
      this.socket = null;
      this.connected = false;
    },

    /**
     * 📜 Carrega mensagens do histórico
     */
    async loadMessages(before?: number, contactId?: string) {
      this.loadingMore = true;
      
      try {
        // 🆕 Se tiver contactId, usa rota de contatos
        const endpoint = contactId 
          ? `${API_URL}/contacts/${contactId}/messages`
          : `${API_URL}/messages`;
        
        const url = new URL(endpoint);
        if (before) url.searchParams.set('before', String(before));
        url.searchParams.set('limit', '30');

        const res = await fetch(url.toString());
        const data = await res.json();

        if (before) {
          // Paginação: adiciona no início
          this.messages = [...data.messages, ...this.messages];
        } else {
          // Carregamento inicial
          this.messages = data.messages;
        }

        this.hasMoreMessages = data.hasMore;
        this.currentContactId = contactId || null; // 🆕 Salva contactId atual
      } catch (error) {
        console.error('❌ Erro ao carregar mensagens:', error);
      } finally {
        this.loadingMore = false;
      }
    },

    /**
     * 📤 Envia mensagem (Optimistic UI)
     */
    sendMessage(text: string) {
      if (!this.socket?.connected || !text.trim()) return;

      const tempId = `temp_${Date.now()}_${Math.random()}`;
      const message: Message = {
        tempId,
        author: this.currentUser,
        text: text.trim(),
        type: 'text',
        status: 'pending', // 🔧 Status inicial
        timestamp: Date.now(),
      };

      // 🚀 Optimistic UI: Adiciona ANTES de receber ACK
      this.messages.push(message);
      this.pendingMessages.set(tempId, { message, retries: 0 });

      // 📡 Envia ao servidor (incluindo contactId se houver)
      this.socket.emit('chat:send', {
        author: message.author,
        text: message.text,
        type: message.type,
        tempId,
        contactId: this.currentContactId, // 🆕 Inclui ID do contato
      });

      console.log('📤 Mensagem enviada (optimistic):', tempId, 'para contato:', this.currentContactId);
    },

    /**
     * 🔄 Tenta reenviar mensagem falha
     */
    retryMessage(tempId: string) {
      const pending = this.pendingMessages.get(tempId);
      if (!pending) return;

      // 🚫 Atingiu máximo de tentativas
      if (pending.retries >= MAX_RETRIES) {
        console.error('❌ Máximo de tentativas atingido:', tempId);
        
        // Marca como falha
        const msg = this.messages.find((m: Message) => m.tempId === tempId);
        if (msg) msg.status = 'pending'; // Ou criar status 'failed'
        
        this.pendingMessages.delete(tempId);
        return;
      }

      // 🔧 Backoff exponencial
      const delay = RETRY_DELAYS[pending.retries] || 4000;
      pending.retries++;

      console.log(`🔄 Retry ${pending.retries}/${MAX_RETRIES} em ${delay}ms`);

      setTimeout(() => {
        if (this.socket?.connected) {
          this.socket.emit('chat:send', {
            author: pending.message.author,
            text: pending.message.text,
            type: pending.message.type,
            tempId,
          });
        }
      }, delay);
    },

    /**
     * 🔄 Tenta reenviar TODAS as mensagens pendentes
     */
    retryPendingMessages() {
      this.pendingMessages.forEach((_, tempId) => {
        this.retryMessage(tempId);
      });
    },

    /**
     * ⌨️ Emite evento de digitação
     */
    emitTyping(isTyping: boolean) {
      if (!this.socket?.connected || !this.currentContactId) return;

      this.socket.emit('chat:typing', {
        contactId: this.currentContactId,  // 🆕 Para quem está digitando
        author: this.currentUser,
        isTyping,
      });
    },

    /**
     * 👁️ Marca mensagens como lidas
     */
    markAsRead(messageIds: string[]) {
      if (!this.socket?.connected || messageIds.length === 0) return;

      this.socket.emit('chat:read', { ids: messageIds });
    },

    /**
     * 📜 Atualiza estado do scroll
     */
    setScrolledToBottom(value: boolean) {
      this.isScrolledToBottom = value;
      
      if (value) {
        this.hasUnreadMessages = false;
        
        // 👁️ Marca últimas mensagens como lidas
        const unreadIds = this.messages
          .filter((m: Message) => m.id && m.status !== 'read')
          .map((m: Message) => m.id!)
          .slice(-10); // Últimas 10
        
        if (unreadIds.length > 0) {
          this.markAsRead(unreadIds);
        }
      }
    },
  },

  getters: {
    /**
     * 👥 Usuários que estão digitando
     */
    typingUsers: (state) => {
      return Object.values(state.isTyping).filter(t => t.isTyping);
    },
  },
});
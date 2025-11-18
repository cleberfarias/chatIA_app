import { defineStore } from 'pinia';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:3000';

export interface Contact {
  id: string;
  name: string;
  email: string;
  avatar?: string;
  lastMessage?: string;
  lastMessageTime?: number;
  unreadCount: number;
  online: boolean;
}

export const useContactsStore = defineStore('contacts', {
  state: () => ({
    contacts: [] as Contact[],
    selectedContactId: null as string | null,
    loading: false,
    error: null as string | null,
  }),

  getters: {
    selectedContact: (state) => {
      if (!state.selectedContactId) return null;
      return state.contacts.find(c => c.id === state.selectedContactId) || null;
    },

    sortedContacts: (state) => {
      return [...state.contacts].sort((a, b) => {
        // Online primeiro
        if (a.online !== b.online) return a.online ? -1 : 1;
        // Depois por última mensagem
        return (b.lastMessageTime || 0) - (a.lastMessageTime || 0);
      });
    },

    totalUnread: (state) => {
      return state.contacts.reduce((sum, c) => sum + c.unreadCount, 0);
    },
  },

  actions: {
    async loadContacts() {
      this.loading = true;
      this.error = null;

      try {
        console.log('🔄 Carregando contatos de:', `${API_URL}/contacts/`);
        const res = await fetch(`${API_URL}/contacts/`, {
          redirect: 'follow'
        });
        console.log('📡 Resposta:', res.status, res.ok);
        if (!res.ok) throw new Error('Falha ao carregar contatos');

        this.contacts = await res.json();
        console.log(`✅ ${this.contacts.length} contatos carregados:`, this.contacts);
      } catch (error: any) {
        this.error = error.message;
        console.error('❌ Erro ao carregar contatos:', error);
      } finally {
        this.loading = false;
      }
    },

    selectContact(contactId: string) {
      this.selectedContactId = contactId;
      console.log('📞 Contato selecionado:', contactId);
    },

    unselectContact() {
      this.selectedContactId = null;
    },

    updateContactLastMessage(contactId: string, message: string, timestamp: number) {
      const contact = this.contacts.find(c => c.id === contactId);
      if (contact) {
        contact.lastMessage = message;
        contact.lastMessageTime = timestamp;
      }
    },

    incrementUnread(contactId: string) {
      const contact = this.contacts.find(c => c.id === contactId);
      if (contact) {
        contact.unreadCount++;
      }
    },

    async markContactRead(contactId: string) {
      const contact = this.contacts.find(c => c.id === contactId);
      if (contact) {
        contact.unreadCount = 0;

        try {
          await fetch(`${API_URL}/contacts/${contactId}/mark-read`, {
            method: 'POST',
          });
        } catch (error) {
          console.error('❌ Erro ao marcar como lido:', error);
        }
      }
    },

    setOnlineStatus(contactId: string, online: boolean) {
      const contact = this.contacts.find(c => c.id === contactId);
      if (contact) {
        contact.online = online;
      }
    },
  },
});

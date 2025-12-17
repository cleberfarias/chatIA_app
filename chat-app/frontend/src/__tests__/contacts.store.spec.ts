import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useContactsStore, type Contact } from '@/stores/contacts'
import { useAuthStore } from '@/stores/auth'

global.fetch = vi.fn()

describe('ContactsStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  describe('Estado inicial', () => {
    it('inicializa com lista vazia', () => {
      const store = useContactsStore()
      
      expect(store.contacts).toEqual([])
      expect(store.selectedContactId).toBeNull()
      expect(store.loading).toBe(false)
      expect(store.error).toBeNull()
    })
  })

  describe('Getters', () => {
    it('retorna contato selecionado', () => {
      const store = useContactsStore()
      const mockContacts: Contact[] = [
        { id: '1', name: 'João', email: 'joao@test.com', unreadCount: 0, online: true },
        { id: '2', name: 'Maria', email: 'maria@test.com', unreadCount: 2, online: false }
      ]
      
      store.contacts = mockContacts
      store.selectedContactId = '2'

      expect(store.selectedContact).toEqual(mockContacts[1])
    })

    it('retorna null quando nenhum contato selecionado', () => {
      const store = useContactsStore()
      store.contacts = [
        { id: '1', name: 'João', email: 'joao@test.com', unreadCount: 0, online: true }
      ]

      expect(store.selectedContact).toBeNull()
    })

    it('ordena contatos por status online e última mensagem', () => {
      const store = useContactsStore()
      const mockContacts: Contact[] = [
        { id: '1', name: 'A', email: 'a@test.com', unreadCount: 0, online: false, lastMessageTime: 1000 },
        { id: '2', name: 'B', email: 'b@test.com', unreadCount: 0, online: true, lastMessageTime: 500 },
        { id: '3', name: 'C', email: 'c@test.com', unreadCount: 0, online: true, lastMessageTime: 2000 },
        { id: '4', name: 'D', email: 'd@test.com', unreadCount: 0, online: false, lastMessageTime: 3000 }
      ]
      
      store.contacts = mockContacts

      const sorted = store.sortedContacts
      
      // Online primeiro: C (2000), B (500)
      // Depois offline: D (3000), A (1000)
      expect(sorted[0].id).toBe('3') // C online, último 2000
      expect(sorted[1].id).toBe('2') // B online, último 500
      expect(sorted[2].id).toBe('4') // D offline, último 3000
      expect(sorted[3].id).toBe('1') // A offline, último 1000
    })

    it('calcula total de mensagens não lidas', () => {
      const store = useContactsStore()
      store.contacts = [
        { id: '1', name: 'A', email: 'a@test.com', unreadCount: 3, online: true },
        { id: '2', name: 'B', email: 'b@test.com', unreadCount: 5, online: true },
        { id: '3', name: 'C', email: 'c@test.com', unreadCount: 0, online: false }
      ]

      expect(store.totalUnread).toBe(8)
    })
  })

  describe('loadContacts', () => {
    it('carrega contatos com sucesso', async () => {
      const mockContacts = [
        { id: '1', name: 'João', email: 'joao@test.com', unreadCount: 0, online: true },
        { id: '2', name: 'Maria', email: 'maria@test.com', unreadCount: 2, online: false }
      ]

      const authStore = useAuthStore()
      authStore.token = 'test-token'

      ;(global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockContacts
      })

      const store = useContactsStore()
      await store.loadContacts()

      expect(store.contacts).toEqual(mockContacts)
      expect(store.loading).toBe(false)
      expect(store.error).toBeNull()
    })

    it('define loading durante carregamento', async () => {
      const authStore = useAuthStore()
      authStore.token = 'test-token'

      ;(global.fetch as any).mockImplementationOnce(() => 
        new Promise(resolve => setTimeout(() => resolve({ ok: true, json: async () => [] }), 100))
      )

      const store = useContactsStore()
      const loadPromise = store.loadContacts()

      expect(store.loading).toBe(true)
      
      await loadPromise
      
      expect(store.loading).toBe(false)
    })

    it('trata erro ao carregar contatos', async () => {
      const authStore = useAuthStore()
      authStore.token = 'test-token'

      ;(global.fetch as any).mockRejectedValueOnce(new Error('Network error'))

      const store = useContactsStore()
      await store.loadContacts()

      expect(store.error).toBe('Network error')
      expect(store.loading).toBe(false)
    })

    it('envia token de autenticação no header', async () => {
      const authStore = useAuthStore()
      authStore.token = 'jwt-token-123'

      ;(global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => []
      })

      const store = useContactsStore()
      await store.loadContacts()

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/contacts'),
        expect.objectContaining({
          headers: expect.objectContaining({
            'Authorization': 'Bearer jwt-token-123'
          })
        })
      )
    })
  })

  describe('selectContact', () => {
    it('seleciona contato por ID', () => {
      const store = useContactsStore()
      store.contacts = [
        { id: '1', name: 'João', email: 'joao@test.com', unreadCount: 0, online: true },
        { id: '2', name: 'Maria', email: 'maria@test.com', unreadCount: 3, online: false }
      ]

      store.selectContact('2')

      expect(store.selectedContactId).toBe('2')
      expect(store.selectedContact?.name).toBe('Maria')
    })
  })

  describe('setOnlineStatus', () => {
    it('atualiza status online do contato', () => {
      const store = useContactsStore()
      store.contacts = [
        { id: '1', name: 'João', email: 'joao@test.com', unreadCount: 0, online: false }
      ]

      store.setOnlineStatus('1', true)

      expect(store.contacts[0].online).toBe(true)
    })

    it('não faz nada se contato não existe', () => {
      const store = useContactsStore()
      store.contacts = [
        { id: '1', name: 'João', email: 'joao@test.com', unreadCount: 0, online: false }
      ]

      store.setOnlineStatus('999', true)

      expect(store.contacts[0].online).toBe(false)
    })
  })

  describe('incrementUnread', () => {
    it('incrementa contador de não lidas', () => {
      const store = useContactsStore()
      store.contacts = [
        { id: '1', name: 'João', email: 'joao@test.com', unreadCount: 2, online: true }
      ]

      store.incrementUnread('1')

      expect(store.contacts[0].unreadCount).toBe(3)
    })
  })

  describe('updateContactLastMessage', () => {
    it('atualiza última mensagem do contato', () => {
      const store = useContactsStore()
      store.contacts = [
        { id: '1', name: 'João', email: 'joao@test.com', unreadCount: 0, online: true }
      ]
      const timestamp = Date.now()

      store.updateContactLastMessage('1', 'Olá, como vai?', timestamp)

      expect(store.contacts[0].lastMessage).toBe('Olá, como vai?')
      expect(store.contacts[0].lastMessageTime).toBe(timestamp)
    })
  })
})

import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useChatStore } from '@/stores/chat'
import type { Message, TypingInfo } from '@/design-system/types/validation'

// Mock do Socket.IO
const mockSocket = {
  connected: false,
  on: vi.fn(),
  emit: vi.fn(),
  off: vi.fn(),
  disconnect: vi.fn(),
}

vi.mock('socket.io-client', () => ({
  io: vi.fn(() => mockSocket),
}))

// Mock do axios para contacts store
vi.mock('axios', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
  },
}))

describe('ChatStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    mockSocket.connected = false
  })

  afterEach(() => {
    vi.clearAllTimers()
  })

  describe('Estado inicial', () => {
    it('inicia com valores padrão corretos', () => {
      const chat = useChatStore()

      expect(chat.socket).toBeNull()
      expect(chat.messages).toEqual([])
      expect(chat.connected).toBe(false)
      expect(chat.currentUser).toBe('Usuário')
      expect(chat.currentContactId).toBeNull()
      expect(chat.isTyping).toEqual({})
      expect(chat.hasMoreMessages).toBe(true)
      expect(chat.loadingMore).toBe(false)
      expect(chat.isScrolledToBottom).toBe(true)
      expect(chat.hasUnreadMessages).toBe(false)
    })
  })

  describe('connect', () => {
    it('conecta ao Socket.IO com token JWT', async () => {
      const chat = useChatStore()
      const token = 'test-jwt-token'

      await chat.connect(token)

      // Verifica se io() foi chamado com config correta
      const { io } = await import('socket.io-client')
      expect(io).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          auth: { token },
          transports: ['websocket', 'polling'],
          reconnection: true,
        })
      )
    })

    it('não conecta sem token JWT', async () => {
      const chat = useChatStore()

      await expect(chat.connect('')).rejects.toThrow('Token JWT obrigatório')
    })

    it('não reconecta se socket já está conectado', async () => {
      const chat = useChatStore()
      const token = 'test-jwt-token'

      // Primeira conexão
      await chat.connect(token)
      mockSocket.connected = true

      const { io } = await import('socket.io-client')
      const firstCallCount = (io as any).mock.calls.length

      // Segunda conexão (deve ser ignorada)
      await chat.connect(token)

      // io() não deve ser chamado novamente
      expect((io as any).mock.calls.length).toBe(firstCallCount)
    })

    it('registra listener para evento connect', async () => {
      const chat = useChatStore()
      await chat.connect('test-token')

      const connectListener = mockSocket.on.mock.calls.find(
        (call) => call[0] === 'connect'
      )?.[1]

      expect(connectListener).toBeDefined()

      // Simula evento connect
      connectListener?.()

      expect(chat.connected).toBe(true)
    })

    it('registra listener para evento disconnect', async () => {
      const chat = useChatStore()
      await chat.connect('test-token')

      const disconnectListener = mockSocket.on.mock.calls.find(
        (call) => call[0] === 'disconnect'
      )?.[1]

      expect(disconnectListener).toBeDefined()

      // Simula desconexão
      chat.connected = true
      disconnectListener?.('transport close')

      expect(chat.connected).toBe(false)
    })

    it('lida com erro de autenticação no connect_error', async () => {
      const chat = useChatStore()
      await chat.connect('test-token')

      const errorListener = mockSocket.on.mock.calls.find(
        (call) => call[0] === 'connect_error'
      )?.[1]

      expect(errorListener).toBeDefined()

      // Simula erro de token inválido
      const authError = new Error('invalid token')
      expect(() => errorListener?.(authError)).toThrow('Autenticação inválida')
    })
  })

  describe('sendMessage', () => {
    it('envia mensagem via Socket.IO', async () => {
      const chat = useChatStore()
      await chat.connect('test-token')
      mockSocket.connected = true
      chat.connected = true

      chat.sendMessage('Olá mundo')

      expect(mockSocket.emit).toHaveBeenCalledWith(
        'chat:send',
        expect.objectContaining({
          text: 'Olá mundo',
          author: 'Usuário',
          tempId: expect.any(String),
          type: 'text',
        })
      )
    })

    it('adiciona mensagem à lista local com tempId', async () => {
      const chat = useChatStore()
      await chat.connect('test-token')
      mockSocket.connected = true
      chat.connected = true

      chat.sendMessage('Teste')

      expect(chat.messages).toHaveLength(1)
      expect(chat.messages[0]).toMatchObject({
        text: 'Teste',
        author: 'Usuário',
        status: 'pending',
        tempId: expect.any(String),
        type: 'text',
      })
    })

    it('não envia mensagem se desconectado', async () => {
      const chat = useChatStore()
      chat.connected = false

      chat.sendMessage('Teste')

      expect(mockSocket.emit).not.toHaveBeenCalled()
    })

    it('adiciona mensagem à fila de pendentes mesmo com sucesso', async () => {
      const chat = useChatStore()
      await chat.connect('test-token')
      mockSocket.connected = true
      chat.connected = true

      chat.sendMessage('Teste')

      // Mensagem sempre vai para pendentes até receber ACK
      expect(chat.pendingMessages.size).toBe(1)
      const pending = Array.from(chat.pendingMessages.values())[0]
      expect(pending.message.text).toBe('Teste')
      expect(pending.retries).toBe(0)
    })
  })

  describe('Eventos Socket.IO', () => {
    it('recebe e adiciona nova mensagem com chat:new-message', async () => {
      const chat = useChatStore()
      await chat.connect('test-token')

      const newMessageListener = mockSocket.on.mock.calls.find(
        (call) => call[0] === 'chat:new-message'
      )?.[1]

      const incomingMessage: Message = {
        id: '123',
        text: 'Olá!',
        author: 'Maria',
        timestamp: Date.now(),
        status: 'sent',
        type: 'text'
      }

      await newMessageListener?.(incomingMessage)

      expect(chat.messages).toContainEqual(incomingMessage)
    })

    it('filtra mensagens de agentes no chat:new-message', async () => {
      const chat = useChatStore()
      await chat.connect('test-token')

      const newMessageListener = mockSocket.on.mock.calls.find(
        (call) => call[0] === 'chat:new-message'
      )?.[1]

      const agentMessage: Message = {
        id: '456',
        text: 'Posso ajudar?',
        author: 'Advogado Virtual',
        timestamp: Date.now(),
        status: 'sent',
        type: 'text'
      }

      await newMessageListener?.(agentMessage)

      // Mensagem de agente NÃO deve ser adicionada
      expect(chat.messages).not.toContainEqual(agentMessage)
    })

    it('atualiza mensagem com ACK do servidor', async () => {
      const chat = useChatStore()
      await chat.connect('test-token')
      mockSocket.connected = true
      chat.connected = true

      // Envia mensagem (cria tempId)
      chat.sendMessage('Teste')
      const tempId = chat.messages[0].tempId!

      const ackListener = mockSocket.on.mock.calls.find(
        (call) => call[0] === 'chat:ack'
      )?.[1]

      // Simula ACK do servidor
      ackListener?.({
        tempId,
        id: 'server-id-123',
        status: 'sent',
        timestamp: Date.now(),
      })

      // Mensagem deve ter ID real e não ter mais tempId
      expect(chat.messages[0].id).toBe('server-id-123')
      expect(chat.messages[0].tempId).toBeUndefined()
      expect(chat.messages[0].status).toBe('sent')
    })

    it('atualiza status para delivered com chat:delivered', async () => {
      const chat = useChatStore()
      await chat.connect('test-token')

      // Adiciona mensagem enviada
      chat.messages.push({
        id: 'msg-123',
        text: 'Enviada',
        author: 'João',
        timestamp: Date.now(),
        status: 'sent',
        type: 'text'
      })

      const deliveredListener = mockSocket.on.mock.calls.find(
        (call) => call[0] === 'chat:delivered'
      )?.[1]

      deliveredListener?.({ id: 'msg-123' })

      expect(chat.messages[0].status).toBe('delivered')
    })

    it('atualiza status para read com chat:read', async () => {
      const chat = useChatStore()
      await chat.connect('test-token')

      // Adiciona mensagens
      chat.messages.push(
        {
          id: 'msg-1',
          text: 'Primeira',
          author: 'João',
          timestamp: Date.now(),
          status: 'delivered',
          type: 'text'
        },
        {
          id: 'msg-2',
          text: 'Segunda',
          author: 'João',
          timestamp: Date.now(),
          status: 'delivered',
          type: 'text'
        }
      )

      const readListener = mockSocket.on.mock.calls.find(
        (call) => call[0] === 'chat:read'
      )?.[1]

      readListener?.({ ids: ['msg-1', 'msg-2'] })

      expect(chat.messages[0].status).toBe('read')
      expect(chat.messages[1].status).toBe('read')
    })

    it('adiciona usuário digitando com chat:typing', async () => {
      const chat = useChatStore()
      await chat.connect('test-token')

      const typingListener = mockSocket.on.mock.calls.find(
        (call) => call[0] === 'chat:typing'
      )?.[1]

      const typingData: TypingInfo = {
        userId: 'user-123',
        author: 'Maria',
        chatId: 'chat1',
        isTyping: true
      }

      typingListener?.(typingData)

      expect(chat.isTyping['user-123']).toEqual(typingData)
    })

    it('remove usuário quando para de digitar', async () => {
      const chat = useChatStore()
      await chat.connect('test-token')

      // Adiciona usuário digitando
      chat.isTyping['user-123'] = {
        userId: 'user-123',
        author: 'Maria',
        chatId: 'chat1',
        isTyping: true
      }

      const typingListener = mockSocket.on.mock.calls.find(
        (call) => call[0] === 'chat:typing'
      )?.[1]

      typingListener?.({
        userId: 'user-123',
        author: 'Maria',
        isTyping: false,
        timestamp: Date.now(),
      })

      expect(chat.isTyping['user-123']).toBeUndefined()
    })
  })

  describe('disconnect', () => {
    it('desconecta socket e limpa estado', async () => {
      const chat = useChatStore()
      await chat.connect('test-token')
      mockSocket.connected = true
      chat.connected = true

      chat.disconnect()

      expect(mockSocket.disconnect).toHaveBeenCalled()
      expect(chat.connected).toBe(false)
      expect(chat.socket).toBeNull()
    })
  })

  describe('setScrolledToBottom', () => {
    it('marca hasUnreadMessages como false quando scrollar para baixo', () => {
      const chat = useChatStore()
      chat.hasUnreadMessages = true

      chat.setScrolledToBottom(true)

      expect(chat.isScrolledToBottom).toBe(true)
      expect(chat.hasUnreadMessages).toBe(false)
    })

    it('não altera hasUnreadMessages quando scrollar para cima', () => {
      const chat = useChatStore()
      chat.hasUnreadMessages = false

      chat.setScrolledToBottom(false)

      expect(chat.isScrolledToBottom).toBe(false)
      expect(chat.hasUnreadMessages).toBe(false)
    })
  })
})

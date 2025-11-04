import { defineStore } from 'pinia'
import { ref } from 'vue'
import { io, Socket } from 'socket.io-client'
import type { Message } from '../design-system/types'
import { validateAndNormalizeMessage } from '../design-system/types/validation'

export const useChatStore = defineStore('chat', () => {
    const messages = ref<Message[]>([])
    const isConnected = ref(false)
    const isTyping = ref(false)
    const isLoading = ref(false)
    let socket: Socket | null = null

    function connect(baseUrl: string) {
      if (socket) return
      socket = io(baseUrl, { transports: ['websocket'] })
      
      socket.on('connect', () => { 
        isConnected.value = true 
        console.log('✅ Conectado ao servidor')
      })
      
      socket.on('disconnect', () => { 
        isConnected.value = false 
        console.log('❌ Desconectado do servidor')
      })
      
      socket.on('chat:new-message', (data: unknown) => {
        try {
          const message = validateAndNormalizeMessage(data)
          console.log('📨 Mensagem válida recebida:', message)
          
          // Evita duplicação
          const exists = messages.value.some(m => m.id === message.id)
          if (!exists) {
            messages.value.push(message)
          } else {
            console.log('⚠️  Mensagem duplicada ignorada:', message.id)
          }
        } catch (error) {
          console.error('❌ Erro ao processar mensagem:', error)
        }
      })

      socket.on('user:typing', (data: { userId: string; isTyping: boolean }) => {
        isTyping.value = data.isTyping
      })
    }

    async function loadHistory(baseUrl: string, limit = 50) {
      isLoading.value = true
      try {
        const res = await fetch(`${baseUrl}/messages?limit=${limit}`)
        if (!res.ok) throw new Error('Falha ao buscar histórico')
        
        const data: unknown[] = await res.json()
        console.log('📚 Histórico carregado:', data.length, 'mensagens')

        // Valida todas as mensagens
        const validMessages = data
          .map((msg) => {
            try {
              return validateAndNormalizeMessage(msg)
            } catch (error) {
              console.error('❌ Mensagem inválida no histórico:', error)
              return null
            }
          })
          .filter((msg): msg is Message => msg !== null)

        messages.value = validMessages
      } catch (error) {
        console.error('❌ Erro ao buscar histórico:', error)
        throw error
      } finally {
        isLoading.value = false
      }
    }

    function sendMessage(message: Omit<Message, 'id' | 'timestamp'>) {
      if (!socket) return
      
      const msg: Message = {
        ...message,
        id: crypto.randomUUID(),
        timestamp: Date.now(),
      }
      
      console.log('📤 Enviando mensagem:', msg)
      socket.emit('chat:send', msg)
    }

    function sendTypingStatus(typing: boolean) {
      if (!socket) return
      socket.emit('user:typing', typing)
    }

    function disconnect() {
      if (!socket) return
      socket.disconnect()
      socket = null
      isConnected.value = false
    }

    return {
      messages,
      isConnected,
      isTyping,
      isLoading,
      connect,
      disconnect,
      sendMessage,
      sendTypingStatus,
      loadHistory,
    }
})
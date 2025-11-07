// frontend/src/stores/chat.ts
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { io, Socket } from 'socket.io-client'
import type { Message } from '../design-system/types'
import { validateAndNormalizeMessage } from '../design-system/types/validation'
import { useAuthStore } from './auth'

export const useChatStore = defineStore('chat', () => {
  const messages = ref<Message[]>([])
  const isConnected = ref(false)
  const isTyping = ref(false)
  const isLoading = ref(false)
  let socket: Socket | null = null
  let baseUrl: string | null = null

  function connect(base: string) {
    if (socket) return
    baseUrl = base
    const auth = useAuthStore()
    const token = auth.token
    socket = io(base, {
      transports: ['websocket'],
      auth: { token: token || '' }
    })
    socket.on('connect', () => { isConnected.value = true })
    socket.on('disconnect', () => { isConnected.value = false })
    socket.on('chat:new-message', (msg: Message) => { messages.value.push(msg) })
    socket.on('error', (e: any) => { console.warn('socket error', e) })
  }

  function disconnect() {
    socket?.disconnect()
    socket = null
    isConnected.value = false
  }

  async function loadHistory(base: string, limit = 50) {
    isLoading.value = true
    try {
      const res = await fetch(`${base}/messages?limit=${limit}`)
      const data: Message[] = await res.json()
      messages.value = data
    } finally {
      isLoading.value = false
    }
  }

  function sendMessage(author: string, text: string) {
    if (!socket) return
    const payload = validateAndNormalizeMessage({ author, text })
    socket.emit('chat:send', payload)
  }

  function sendTypingStatus(value: boolean) {
    isTyping.value = !!value
   
  }

  return {
    messages, isConnected, isTyping, isLoading,
    connect, disconnect, loadHistory, sendMessage, sendTypingStatus
  }
})

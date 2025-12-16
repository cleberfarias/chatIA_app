import { ref } from 'vue'
import axios from 'axios'
import { useAuthStore } from '@/stores/auth'

export interface CustomAgentPayload {
  name: string
  emoji: string
  prompt: string
  specialties: string[]
  openaiApiKey: string
  openaiAccount?: string
}

export interface CustomAgentSummary {
  name: string
  emoji: string
  key: string
  specialties: string[]
  createdAt?: string
}

export function useCustomAgents() {
  const loading = ref(false)
  const error = ref<string | null>(null)

  const apiBase = import.meta.env.VITE_API_URL || 'http://localhost:3000'

  const authHeaders = () => ({
    Authorization: `Bearer ${useAuthStore().token || ''}`
  })

  const listAgents = async (): Promise<CustomAgentSummary[]> => {
    loading.value = true
    error.value = null
    try {
      const { data } = await axios.get(`${apiBase}/custom-bots`, {
        headers: authHeaders()
      })
      return data?.bots || []
    } catch (err: any) {
      error.value = err?.response?.data?.detail || 'Erro ao carregar agentes'
      throw err
    } finally {
      loading.value = false
    }
  }

  const createAgent = async (payload: CustomAgentPayload): Promise<CustomAgentSummary> => {
    loading.value = true
    error.value = null
    try {
      const { data } = await axios.post(
        `${apiBase}/custom-bots`,
        {
          name: payload.name,
          emoji: payload.emoji,
          prompt: payload.prompt,
          specialties: payload.specialties,
          openaiApiKey: payload.openaiApiKey,
          openaiAccount: payload.openaiAccount
        },
        { headers: { ...authHeaders(), 'Content-Type': 'application/json' } }
      )
      return data?.bot
    } catch (err: any) {
      error.value = err?.response?.data?.detail || 'Erro ao criar agente'
      throw err
    } finally {
      loading.value = false
    }
  }

  const deleteAgent = async (agentKey: string): Promise<void> => {
    loading.value = true
    error.value = null
    try {
      await axios.delete(`${apiBase}/custom-bots/${agentKey}`, {
        headers: authHeaders()
      })
    } catch (err: any) {
      error.value = err?.response?.data?.detail || 'Erro ao remover agente'
      throw err
    } finally {
      loading.value = false
    }
  }

  return {
    loading,
    error,
    listAgents,
    createAgent,
    deleteAgent
  }
}

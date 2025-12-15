import { ref } from 'vue'
import axios from 'axios'
import { useAuthStore } from '@/stores/auth'

export interface HandoverData {
  customer_id: string
  customer_name?: string
  customer_email?: string
  customer_phone?: string
  reason: 'explicit_request' | 'low_confidence' | 'complaint' | 'complex_query' | 'escalation' | 'technical_issue' | 'outside_hours'
  last_messages: string[]
  entities_extracted?: Record<string, any>
  intent?: string
}

export function useHandover() {
  const loading = ref(false)
  const error = ref<string | null>(null)

  const createHandover = async (data: HandoverData) => {
    loading.value = true
    error.value = null

    try {
      const token = useAuthStore().token
      const response = await axios.post(
        `${import.meta.env.VITE_API_URL}/handovers/`,
        data,
        { headers: { Authorization: `Bearer ${token}` } }
      )

      return response.data
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Erro ao criar handover'
      throw err
    } finally {
      loading.value = false
    }
  }

  const getHandovers = async (filters?: {
    status?: string
    priority?: number
    agent_id?: string
    limit?: number
  }) => {
    loading.value = true
    error.value = null

    try {
      const token = useAuthStore().token
      const response = await axios.get(
        `${import.meta.env.VITE_API_URL}/handovers/`,
        {
          headers: { Authorization: `Bearer ${token}` },
          params: filters
        }
      )

      return response.data
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Erro ao buscar handovers'
      throw err
    } finally {
      loading.value = false
    }
  }

  const acceptHandover = async (handoverId: string, agentId: string, agentName: string) => {
    loading.value = true
    error.value = null

    try {
      const token = useAuthStore().token
      await axios.put(
        `${import.meta.env.VITE_API_URL}/handovers/${handoverId}/accept`,
        { agent_id: agentId, agent_name: agentName },
        { headers: { Authorization: `Bearer ${token}` } }
      )
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Erro ao aceitar handover'
      throw err
    } finally {
      loading.value = false
    }
  }

  const resolveHandover = async (handoverId: string, notes?: string) => {
    loading.value = true
    error.value = null

    try {
      const token = useAuthStore().token
      await axios.put(
        `${import.meta.env.VITE_API_URL}/handovers/${handoverId}/resolve`,
        { resolution_notes: notes },
        { headers: { Authorization: `Bearer ${token}` } }
      )
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Erro ao resolver handover'
      throw err
    } finally {
      loading.value = false
    }
  }

  return {
    loading,
    error,
    createHandover,
    getHandovers,
    acceptHandover,
    resolveHandover
  }
}

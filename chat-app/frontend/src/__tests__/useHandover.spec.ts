import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useHandover, type HandoverData } from '@/composables/useHandover'
import axios from 'axios'
import { useAuthStore } from '@/stores/auth'

vi.mock('axios')

describe('useHandover', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    
    // Mock do authStore com token
    const authStore = useAuthStore()
    authStore.token = 'test-jwt-token'
  })

  describe('Estado inicial', () => {
    it('inicia com valores padrão', () => {
      const { loading, error } = useHandover()

      expect(loading.value).toBe(false)
      expect(error.value).toBeNull()
    })
  })

  describe('createHandover', () => {
    it('cria handover com dados completos', async () => {
      const mockResponse = {
        data: {
          id: 'handover-123',
          customer_id: 'customer-456',
          status: 'pending',
        },
      }

      vi.mocked(axios.post).mockResolvedValue(mockResponse)

      const { createHandover, loading } = useHandover()

      const handoverData: HandoverData = {
        customer_id: 'customer-456',
        customer_name: 'João Silva',
        customer_email: 'joao@test.com',
        customer_phone: '+5511999999999',
        reason: 'explicit_request',
        last_messages: ['Olá', 'Preciso falar com humano'],
        entities_extracted: { intent: 'atendimento_humano' },
        intent: 'human_handover',
      }

      const promise = createHandover(handoverData)

      // Loading deve ser true durante requisição
      expect(loading.value).toBe(true)

      const result = await promise

      // Loading deve ser false após requisição
      expect(loading.value).toBe(false)
      expect(result).toEqual(mockResponse.data)

      // Verifica se chamou axios corretamente
      expect(axios.post).toHaveBeenCalledWith(
        expect.stringContaining('/handovers/'),
        handoverData,
        expect.objectContaining({
          headers: { Authorization: 'Bearer test-jwt-token' },
        })
      )
    })

    it('cria handover com dados mínimos', async () => {
      const mockResponse = {
        data: {
          id: 'handover-789',
          customer_id: 'customer-101',
        },
      }

      vi.mocked(axios.post).mockResolvedValue(mockResponse)

      const { createHandover } = useHandover()

      const minimalData: HandoverData = {
        customer_id: 'customer-101',
        reason: 'low_confidence',
        last_messages: [],
      }

      const result = await createHandover(minimalData)

      expect(result).toEqual(mockResponse.data)
    })

    it('define erro quando requisição falha', async () => {
      const errorResponse = {
        response: {
          data: {
            detail: 'Cliente não encontrado',
          },
        },
      }

      vi.mocked(axios.post).mockRejectedValue(errorResponse)

      const { createHandover, error, loading } = useHandover()

      const handoverData: HandoverData = {
        customer_id: 'invalid',
        reason: 'escalation',
        last_messages: [],
      }

      await expect(createHandover(handoverData)).rejects.toEqual(errorResponse)

      expect(error.value).toBe('Cliente não encontrado')
      expect(loading.value).toBe(false)
    })

    it('define erro genérico quando resposta não tem detail', async () => {
      const errorResponse = {
        response: { data: {} },
      }

      vi.mocked(axios.post).mockRejectedValue(errorResponse)

      const { createHandover, error } = useHandover()

      const handoverData: HandoverData = {
        customer_id: 'test',
        reason: 'complaint',
        last_messages: [],
      }

      await expect(createHandover(handoverData)).rejects.toBeDefined()

      expect(error.value).toBe('Erro ao criar handover')
    })
  })

  describe('getHandovers', () => {
    it('busca todos os handovers sem filtros', async () => {
      const mockResponse = {
        data: [
          { id: 'h1', customer_id: 'c1', status: 'pending' },
          { id: 'h2', customer_id: 'c2', status: 'accepted' },
        ],
      }

      vi.mocked(axios.get).mockResolvedValue(mockResponse)

      const { getHandovers } = useHandover()

      const result = await getHandovers()

      expect(result).toEqual(mockResponse.data)
      expect(axios.get).toHaveBeenCalledWith(
        expect.stringContaining('/handovers/'),
        expect.objectContaining({
          headers: { Authorization: 'Bearer test-jwt-token' },
          params: undefined,
        })
      )
    })

    it('busca handovers com filtros', async () => {
      const mockResponse = {
        data: [{ id: 'h1', status: 'pending', priority: 3 }],
      }

      vi.mocked(axios.get).mockResolvedValue(mockResponse)

      const { getHandovers } = useHandover()

      const filters = {
        status: 'pending',
        priority: 3,
        agent_id: 'agent-123',
        limit: 10,
      }

      const result = await getHandovers(filters)

      expect(result).toEqual(mockResponse.data)
      expect(axios.get).toHaveBeenCalledWith(
        expect.stringContaining('/handovers/'),
        expect.objectContaining({
          params: filters,
        })
      )
    })

    it('trata erro ao buscar handovers', async () => {
      const errorResponse = {
        response: {
          data: { detail: 'Não autorizado' },
        },
      }

      vi.mocked(axios.get).mockRejectedValue(errorResponse)

      const { getHandovers, error } = useHandover()

      await expect(getHandovers()).rejects.toEqual(errorResponse)

      expect(error.value).toBe('Não autorizado')
    })
  })

  describe('acceptHandover', () => {
    it('aceita handover com sucesso', async () => {
      vi.mocked(axios.put).mockResolvedValue({ data: {} })

      const { acceptHandover, loading } = useHandover()

      const promise = acceptHandover('handover-123', 'agent-456', 'Maria Silva')

      expect(loading.value).toBe(true)

      await promise

      expect(loading.value).toBe(false)
      expect(axios.put).toHaveBeenCalledWith(
        expect.stringContaining('/handovers/handover-123/accept'),
        { agent_id: 'agent-456', agent_name: 'Maria Silva' },
        expect.objectContaining({
          headers: { Authorization: 'Bearer test-jwt-token' },
        })
      )
    })

    it('trata erro ao aceitar handover', async () => {
      const errorResponse = {
        response: {
          data: { detail: 'Handover já aceito por outro agente' },
        },
      }

      vi.mocked(axios.put).mockRejectedValue(errorResponse)

      const { acceptHandover, error } = useHandover()

      await expect(
        acceptHandover('handover-123', 'agent-456', 'João')
      ).rejects.toEqual(errorResponse)

      expect(error.value).toBe('Handover já aceito por outro agente')
    })
  })

  describe('resolveHandover', () => {
    it('resolve handover com notas', async () => {
      vi.mocked(axios.put).mockResolvedValue({ data: {} })

      const { resolveHandover } = useHandover()

      await resolveHandover('handover-123', 'Cliente satisfeito com atendimento')

      expect(axios.put).toHaveBeenCalledWith(
        expect.stringContaining('/handovers/handover-123/resolve'),
        { resolution_notes: 'Cliente satisfeito com atendimento' },
        expect.objectContaining({
          headers: { Authorization: 'Bearer test-jwt-token' },
        })
      )
    })

    it('resolve handover sem notas', async () => {
      vi.mocked(axios.put).mockResolvedValue({ data: {} })

      const { resolveHandover } = useHandover()

      await resolveHandover('handover-456')

      expect(axios.put).toHaveBeenCalledWith(
        expect.stringContaining('/handovers/handover-456/resolve'),
        { resolution_notes: undefined },
        expect.anything()
      )
    })

    it('trata erro ao resolver handover', async () => {
      const errorResponse = {
        response: {
          data: { detail: 'Handover não encontrado' },
        },
      }

      vi.mocked(axios.put).mockRejectedValue(errorResponse)

      const { resolveHandover, error } = useHandover()

      await expect(
        resolveHandover('invalid-id')
      ).rejects.toEqual(errorResponse)

      expect(error.value).toBe('Handover não encontrado')
    })
  })

  describe('Integração - fluxo completo', () => {
    it('cria → busca → aceita → resolve handover', async () => {
      // 1. Cria handover
      vi.mocked(axios.post).mockResolvedValue({
        data: { id: 'h-new', customer_id: 'c-123', status: 'pending' },
      })

      const { createHandover, getHandovers, acceptHandover, resolveHandover } =
        useHandover()

      const handoverData: HandoverData = {
        customer_id: 'c-123',
        reason: 'explicit_request',
        last_messages: ['Preciso de ajuda'],
      }

      const created = await createHandover(handoverData)
      expect(created.id).toBe('h-new')

      // 2. Busca handovers pendentes
      vi.mocked(axios.get).mockResolvedValue({
        data: [{ id: 'h-new', status: 'pending' }],
      })

      const handovers = await getHandovers({ status: 'pending' })
      expect(handovers).toHaveLength(1)

      // 3. Aceita handover
      vi.mocked(axios.put).mockResolvedValue({ data: {} })

      await acceptHandover('h-new', 'agent-1', 'Agent Name')

      expect(axios.put).toHaveBeenCalledWith(
        expect.stringContaining('/h-new/accept'),
        expect.anything(),
        expect.anything()
      )

      // 4. Resolve handover
      await resolveHandover('h-new', 'Problema resolvido')

      expect(axios.put).toHaveBeenCalledWith(
        expect.stringContaining('/h-new/resolve'),
        expect.anything(),
        expect.anything()
      )
    })
  })
})

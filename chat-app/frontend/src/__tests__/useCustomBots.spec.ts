import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import {
  useCustomBots,
  type CustomBotPayload,
  type CustomBotSummary,
} from '@/composables/useCustomBots'
import axios from 'axios'
import { useAuthStore } from '@/stores/auth'

vi.mock('axios')

describe('useCustomBots', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()

    // Mock do authStore com token
    const authStore = useAuthStore()
    authStore.token = 'test-jwt-token'
  })

  describe('Estado inicial', () => {
    it('inicia com valores padrão', () => {
      const { loading, error } = useCustomBots()

      expect(loading.value).toBe(false)
      expect(error.value).toBeNull()
    })
  })

  describe('listBots', () => {
    it('lista todos os bots customizados', async () => {
      const mockBots: CustomBotSummary[] = [
        {
          name: 'Advogado Virtual',
          emoji: '⚖️',
          key: 'advogado_virtual',
          specialties: ['direito civil', 'contratos'],
          createdAt: '2024-01-01T00:00:00Z',
        },
        {
          name: 'Psicólogo AI',
          emoji: '🧠',
          key: 'psicologo_ai',
          specialties: ['ansiedade', 'depressão'],
          createdAt: '2024-01-02T00:00:00Z',
        },
      ]

      vi.mocked(axios.get).mockResolvedValue({ data: { bots: mockBots } })

      const { listBots, loading } = useCustomBots()

      const promise = listBots()

      // Loading deve ser true durante requisição
      expect(loading.value).toBe(true)

      const result = await promise

      // Loading deve ser false após requisição
      expect(loading.value).toBe(false)
      expect(result).toEqual(mockBots)

      // Verifica se chamou axios corretamente
      expect(axios.get).toHaveBeenCalledWith(
        expect.stringContaining('/custom-bots'),
        expect.objectContaining({
          headers: { Authorization: 'Bearer test-jwt-token' },
        })
      )
    })

    it('retorna array vazio quando API não retorna bots', async () => {
      vi.mocked(axios.get).mockResolvedValue({ data: {} })

      const { listBots } = useCustomBots()

      const result = await listBots()

      expect(result).toEqual([])
    })

    it('retorna array vazio quando API retorna null', async () => {
      vi.mocked(axios.get).mockResolvedValue({ data: { bots: null } })

      const { listBots } = useCustomBots()

      const result = await listBots()

      expect(result).toEqual([])
    })

    it('define erro quando requisição falha', async () => {
      const errorResponse = {
        response: {
          data: {
            detail: 'Token inválido',
          },
        },
      }

      vi.mocked(axios.get).mockRejectedValue(errorResponse)

      const { listBots, error, loading } = useCustomBots()

      await expect(listBots()).rejects.toEqual(errorResponse)

      expect(error.value).toBe('Token inválido')
      expect(loading.value).toBe(false)
    })

    it('define erro genérico quando resposta não tem detail', async () => {
      vi.mocked(axios.get).mockRejectedValue({ response: { data: {} } })

      const { listBots, error } = useCustomBots()

      await expect(listBots()).rejects.toBeDefined()

      expect(error.value).toBe('Erro ao carregar bots')
    })
  })

  describe('createBot', () => {
    it('cria novo bot com sucesso', async () => {
      const payload: CustomBotPayload = {
        name: 'Vendedor AI',
        emoji: '💼',
        prompt: 'Você é um vendedor experiente...',
        specialties: ['vendas', 'negociação'],
        openaiApiKey: 'sk-test-key-123',
        openaiAccount: 'test-account',
      }

      const createdBot: CustomBotSummary = {
        name: 'Vendedor AI',
        emoji: '💼',
        key: 'vendedor_ai',
        specialties: ['vendas', 'negociação'],
        createdAt: '2024-01-03T00:00:00Z',
      }

      vi.mocked(axios.post).mockResolvedValue({ data: { bot: createdBot } })

      const { createBot, loading } = useCustomBots()

      const promise = createBot(payload)

      expect(loading.value).toBe(true)

      const result = await promise

      expect(loading.value).toBe(false)
      expect(result).toEqual(createdBot)

      // Verifica payload enviado
      expect(axios.post).toHaveBeenCalledWith(
        expect.stringContaining('/custom-bots'),
        expect.objectContaining({
          name: 'Vendedor AI',
          emoji: '💼',
          prompt: 'Você é um vendedor experiente...',
          specialties: ['vendas', 'negociação'],
          openaiApiKey: 'sk-test-key-123',
          openaiAccount: 'test-account',
        }),
        expect.objectContaining({
          headers: expect.objectContaining({
            Authorization: 'Bearer test-jwt-token',
            'Content-Type': 'application/json',
          }),
        })
      )
    })

    it('cria bot sem campo openaiAccount (opcional)', async () => {
      const payload: CustomBotPayload = {
        name: 'Coach AI',
        emoji: '🏋️',
        prompt: 'Você é um coach pessoal...',
        specialties: ['motivação', 'produtividade'],
        openaiApiKey: 'sk-test-key-456',
      }

      const createdBot: CustomBotSummary = {
        name: 'Coach AI',
        emoji: '🏋️',
        key: 'coach_ai',
        specialties: ['motivação', 'produtividade'],
      }

      vi.mocked(axios.post).mockResolvedValue({ data: { bot: createdBot } })

      const { createBot } = useCustomBots()

      const result = await createBot(payload)

      expect(result).toEqual(createdBot)

      // Verifica que openaiAccount foi enviado como undefined
      expect(axios.post).toHaveBeenCalledWith(
        expect.anything(),
        expect.objectContaining({
          openaiAccount: undefined,
        }),
        expect.anything()
      )
    })

    it('trata erro de validação na criação', async () => {
      const errorResponse = {
        response: {
          data: {
            detail: 'Nome do bot já existe',
          },
        },
      }

      vi.mocked(axios.post).mockRejectedValue(errorResponse)

      const { createBot, error } = useCustomBots()

      const payload: CustomBotPayload = {
        name: 'Bot Duplicado',
        emoji: '🤖',
        prompt: 'Teste',
        specialties: [],
        openaiApiKey: 'sk-test',
      }

      await expect(createBot(payload)).rejects.toEqual(errorResponse)

      expect(error.value).toBe('Nome do bot já existe')
    })

    it('trata erro de API key inválida', async () => {
      const errorResponse = {
        response: {
          data: {
            detail: 'OpenAI API Key inválida',
          },
        },
      }

      vi.mocked(axios.post).mockRejectedValue(errorResponse)

      const { createBot, error } = useCustomBots()

      const payload: CustomBotPayload = {
        name: 'Teste Bot',
        emoji: '🧪',
        prompt: 'Teste',
        specialties: [],
        openaiApiKey: 'invalid-key',
      }

      await expect(createBot(payload)).rejects.toEqual(errorResponse)

      expect(error.value).toBe('OpenAI API Key inválida')
    })
  })

  describe('deleteBot', () => {
    it('remove bot por key', async () => {
      vi.mocked(axios.delete).mockResolvedValue({ data: {} })

      const { deleteBot, loading } = useCustomBots()

      const promise = deleteBot('advogado_virtual')

      expect(loading.value).toBe(true)

      await promise

      expect(loading.value).toBe(false)
      expect(axios.delete).toHaveBeenCalledWith(
        expect.stringContaining('/custom-bots/advogado_virtual'),
        expect.objectContaining({
          headers: { Authorization: 'Bearer test-jwt-token' },
        })
      )
    })

    it('trata erro ao remover bot que não existe', async () => {
      const errorResponse = {
        response: {
          data: {
            detail: 'Bot não encontrado',
          },
        },
      }

      vi.mocked(axios.delete).mockRejectedValue(errorResponse)

      const { deleteBot, error } = useCustomBots()

      await expect(deleteBot('bot_inexistente')).rejects.toEqual(errorResponse)

      expect(error.value).toBe('Bot não encontrado')
    })

    it('trata erro de permissão ao remover bot', async () => {
      const errorResponse = {
        response: {
          data: {
            detail: 'Você não tem permissão para remover este bot',
          },
        },
      }

      vi.mocked(axios.delete).mockRejectedValue(errorResponse)

      const { deleteBot, error } = useCustomBots()

      await expect(deleteBot('bot_outro_usuario')).rejects.toEqual(errorResponse)

      expect(error.value).toBe('Você não tem permissão para remover este bot')
    })
  })

  describe('Integração - fluxo completo', () => {
    it('lista → cria → lista novamente → remove', async () => {
      const { listBots, createBot, deleteBot } = useCustomBots()

      // 1. Lista bots (vazio inicialmente)
      vi.mocked(axios.get).mockResolvedValue({ data: { bots: [] } })

      let bots = await listBots()
      expect(bots).toHaveLength(0)

      // 2. Cria novo bot
      const newBot: CustomBotSummary = {
        name: 'Guru AI',
        emoji: '🧘',
        key: 'guru_ai',
        specialties: ['meditação'],
      }

      vi.mocked(axios.post).mockResolvedValue({ data: { bot: newBot } })

      const created = await createBot({
        name: 'Guru AI',
        emoji: '🧘',
        prompt: 'Você é um guru espiritual...',
        specialties: ['meditação'],
        openaiApiKey: 'sk-test',
      })

      expect(created.name).toBe('Guru AI')

      // 3. Lista novamente (agora com 1 bot)
      vi.mocked(axios.get).mockResolvedValue({ data: { bots: [newBot] } })

      bots = await listBots()
      expect(bots).toHaveLength(1)
      expect(bots[0].key).toBe('guru_ai')

      // 4. Remove o bot
      vi.mocked(axios.delete).mockResolvedValue({ data: {} })

      await deleteBot('guru_ai')

      expect(axios.delete).toHaveBeenCalledWith(
        expect.stringContaining('/custom-bots/guru_ai'),
        expect.anything()
      )

      // 5. Lista novamente (vazio)
      vi.mocked(axios.get).mockResolvedValue({ data: { bots: [] } })

      bots = await listBots()
      expect(bots).toHaveLength(0)
    })
  })
})

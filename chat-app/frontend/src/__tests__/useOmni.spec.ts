import { describe, it, expect, beforeEach, vi } from 'vitest'
import { sendOmni, startWppSession, type SendOmniParams } from '@/composables/useOmni'

global.fetch = vi.fn()

describe('useOmni', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('sendOmni', () => {
    it('envia mensagem via WhatsApp com sucesso', async () => {
      const mockResponse = {
        success: true,
        channel: 'whatsapp',
        recipient: '+5511999999999',
        messageId: 'msg-123'
      }

      ;(global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      })

      const params: SendOmniParams = {
        channel: 'whatsapp',
        recipient: '+5511999999999',
        text: 'Olá, tudo bem?'
      }

      const result = await sendOmni('http://localhost:3000', params)

      expect(result).toEqual(mockResponse)
      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:3000/omni/send',
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(params)
        })
      )
    })

    it('envia mensagem para múltiplos canais', async () => {
      const channels: Array<'whatsapp' | 'instagram' | 'facebook'> = ['whatsapp', 'instagram', 'facebook']

      for (const channel of channels) {
        ;(global.fetch as any).mockResolvedValueOnce({
          ok: true,
          json: async () => ({ success: true, channel, recipient: 'test' })
        })

        const result = await sendOmni('http://localhost:3000', {
          channel,
          recipient: 'test-recipient',
          text: 'Test message'
        })

        expect(result.channel).toBe(channel)
        expect(result.success).toBe(true)
      }
    })

    it('envia mensagem WPPConnect com sessão', async () => {
      ;(global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true })
      })

      const params: SendOmniParams = {
        channel: 'wa-dev',
        recipient: '5511999999999',
        text: 'Teste WPPConnect',
        session: 'my-session'
      }

      await sendOmni('http://localhost:3000', params)

      const callBody = JSON.parse((global.fetch as any).mock.calls[0][1].body)
      expect(callBody.session).toBe('my-session')
      expect(callBody.channel).toBe('wa-dev')
    })

    it('lança erro quando requisição falha', async () => {
      ;(global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => ({ detail: 'Erro interno do servidor' })
      })

      const params: SendOmniParams = {
        channel: 'whatsapp',
        recipient: '+5511999999999',
        text: 'Test'
      }

      await expect(
        sendOmni('http://localhost:3000', params)
      ).rejects.toThrow('Erro interno do servidor')
    })

    it('trata erro quando resposta não é JSON', async () => {
      ;(global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => {
          throw new Error('Invalid JSON')
        }
      })

      const params: SendOmniParams = {
        channel: 'whatsapp',
        recipient: 'test',
        text: 'Test'
      }

      await expect(
        sendOmni('http://localhost:3000', params)
      ).rejects.toThrow()
    })

    it('valida diferentes tipos de recipient', async () => {
      const recipients = [
        '+5511999999999',  // Telefone com código
        '5511999999999',   // Telefone sem +
        '@username',       // Username Instagram/Facebook
        'user.id'          // User ID
      ]

      for (const recipient of recipients) {
        ;(global.fetch as any).mockResolvedValueOnce({
          ok: true,
          json: async () => ({ success: true, recipient })
        })

        const result = await sendOmni('http://localhost:3000', {
          channel: 'whatsapp',
          recipient,
          text: 'Test'
        })

        expect(result.recipient).toBe(recipient)
      }
    })
  })

  describe('startWppSession', () => {
    it('inicia sessão WPPConnect com sucesso', async () => {
      const mockResponse = {
        qr: 'data:image/png;base64,iVBORw0KG...',
        status: 'qr'
      }

      ;(global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      })

      const result = await startWppSession('http://localhost:3000', 'default')

      expect(result).toEqual(mockResponse)
      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:3000/omni/wpp/start',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ session: 'default' })
        })
      )
    })

    it('retorna status quando sessão já está conectada', async () => {
      ;(global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ status: 'connected' })
      })

      const result = await startWppSession('http://localhost:3000', 'my-session')

      expect(result.status).toBe('connected')
      expect(result.qr).toBeUndefined()
    })

    it('lança erro quando falha ao iniciar sessão', async () => {
      ;(global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: async () => ({ detail: 'Nome de sessão inválido' })
      })

      await expect(
        startWppSession('http://localhost:3000', '')
      ).rejects.toThrow('Nome de sessão inválido')
    })

    it('aceita diferentes nomes de sessão', async () => {
      const sessions = ['default', 'session-1', 'production', 'test-123']

      for (const session of sessions) {
        ;(global.fetch as any).mockResolvedValueOnce({
          ok: true,
          json: async () => ({ status: 'started', session })
        })

        await startWppSession('http://localhost:3000', session)

        const callBody = JSON.parse((global.fetch as any).mock.calls[global.fetch.mock.calls.length - 1][1].body)
        expect(callBody.session).toBe(session)
      }
    })
  })

  describe('Integração entre funções', () => {
    it('permite workflow completo: start session → send message', async () => {
      // 1. Inicia sessão
      ;(global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ qr: 'qr-code-data', status: 'qr' })
      })

      const sessionResult = await startWppSession('http://localhost:3000', 'test-session')
      expect(sessionResult.status).toBe('qr')

      // 2. Envia mensagem usando a sessão
      ;(global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true, messageId: 'msg-456' })
      })

      const sendResult = await sendOmni('http://localhost:3000', {
        channel: 'wa-dev',
        recipient: '5511999999999',
        text: 'Mensagem de teste',
        session: 'test-session'
      })

      expect(sendResult.success).toBe(true)
      expect(sendResult.messageId).toBe('msg-456')
    })
  })
})

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { requestGrant, confirmUpload, uploadAndSend } from '@/composables/useUpload'

// Mock global fetch
global.fetch = vi.fn()

describe('useUpload', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('requestGrant', () => {
    it('solicita grant de upload com sucesso', async () => {
      const mockGrant = { key: 'test-key-123', putUrl: 'https://s3.example.com/upload' }
      const mockFile = new File(['content'], 'test.jpg', { type: 'image/jpeg' })

      ;(global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockGrant
      })

      const result = await requestGrant('http://localhost:3000', mockFile, 'token-123')

      expect(result).toEqual(mockGrant)
      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:3000/uploads/grant',
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
            'Authorization': 'Bearer token-123'
          })
        })
      )
    })

    it('envia dados corretos do arquivo', async () => {
      const mockFile = new File(['content'], 'document.pdf', { type: 'application/pdf' })
      Object.defineProperty(mockFile, 'size', { value: 1024 })

      ;(global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ key: 'key', putUrl: 'url' })
      })

      await requestGrant('http://localhost:3000', mockFile, 'token')

      const callArgs = (global.fetch as any).mock.calls[0]
      const body = JSON.parse(callArgs[1].body)

      expect(body).toEqual({
        filename: 'document.pdf',
        mimetype: 'application/pdf',
        size: 1024
      })
    })

    it('lança erro quando grant falha', async () => {
      const mockFile = new File(['content'], 'test.jpg', { type: 'image/jpeg' })

      ;(global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 403
      })

      await expect(
        requestGrant('http://localhost:3000', mockFile, 'token')
      ).rejects.toThrow('Falha no grant upload')
    })

    it('funciona sem token (opcional)', async () => {
      const mockFile = new File(['content'], 'test.jpg', { type: 'image/jpeg' })

      ;(global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ key: 'key', putUrl: 'url' })
      })

      await requestGrant('http://localhost:3000', mockFile, null)

      const callArgs = (global.fetch as any).mock.calls[0]
      expect(callArgs[1].headers).not.toHaveProperty('Authorization')
    })
  })

  describe('confirmUpload', () => {
    it('confirma upload com sucesso', async () => {
      const mockMessage = {
        id: 'msg-123',
        author: 'user1',
        text: 'Arquivo enviado',
        type: 'file' as const,
        status: 'sent',
        timestamp: Date.now()
      }

      ;(global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ message: mockMessage })
      })

      const confirmData = {
        key: 'test-key',
        filename: 'doc.pdf',
        mimetype: 'application/pdf',
        author: 'user1',
        contactId: 'contact-123'
      }

      const result = await confirmUpload('http://localhost:3000', confirmData, 'token')

      expect(result).toEqual(mockMessage)
      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:3000/uploads/confirm',
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Authorization': 'Bearer token'
          })
        })
      )
    })

    it('envia dados corretos de confirmação', async () => {
      ;(global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ message: {} })
      })

      const confirmData = {
        key: 'key-456',
        filename: 'image.png',
        mimetype: 'image/png',
        author: 'user2',
        contactId: null
      }

      await confirmUpload('http://localhost:3000', confirmData, 'token')

      const callArgs = (global.fetch as any).mock.calls[0]
      const body = JSON.parse(callArgs[1].body)

      expect(body).toEqual(confirmData)
    })

    it('lança erro quando confirmação falha', async () => {
      ;(global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 500
      })

      const confirmData = {
        key: 'key',
        filename: 'file.txt',
        mimetype: 'text/plain',
        author: 'user'
      }

      await expect(
        confirmUpload('http://localhost:3000', confirmData, 'token')
      ).rejects.toThrow('Falha no confirm upload')
    })
  })

  describe('uploadAndSend (pipeline completo)', () => {
    it('lança erro quando token é null', async () => {
      const mockFile = new File(['content'], 'file.txt')

      await expect(
        uploadAndSend('http://localhost:3000', mockFile, 'user', null)
      ).rejects.toThrow('Token JWT obrigatório para upload')
    })

    it('propaga erro do grant', async () => {
      const mockFile = new File(['content'], 'file.txt')

      ;(global.fetch as any).mockResolvedValueOnce({
        ok: false
      })

      await expect(
        uploadAndSend('http://localhost:3000', mockFile, 'user', 'token')
      ).rejects.toThrow('Falha no grant upload')
    })

    it('valida parâmetros obrigatórios', async () => {
      const mockFile = new File(['content'], 'test.jpg')
      
      // Token é obrigatório
      await expect(
        uploadAndSend('http://localhost:3000', mockFile, 'user', null)
      ).rejects.toThrow()
    })
  })
})

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAuthStore } from '@/stores/auth'

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {}
  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => { store[key] = value },
    removeItem: (key: string) => { delete store[key] },
    clear: () => { store = {} }
  }
})()

Object.defineProperty(global, 'localStorage', { value: localStorageMock })

// Mock fetch
global.fetch = vi.fn()

describe('AuthStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorageMock.clear()
    vi.clearAllMocks()
  })

  describe('Estado inicial', () => {
    it('inicializa com valores null', () => {
      const store = useAuthStore()
      
      expect(store.token).toBeNull()
      expect(store.user).toBeNull()
    })
  })

  describe('Persistência', () => {
    it('carrega dados do localStorage', () => {
      const mockData = {
        token: 'test-token-123',
        user: { id: '1', name: 'João', email: 'joao@test.com' }
      }
      localStorageMock.setItem('app_auth', JSON.stringify(mockData))

      const store = useAuthStore()
      store.load()

      expect(store.token).toBe('test-token-123')
      expect(store.user).toEqual({ id: '1', name: 'João', email: 'joao@test.com' })
    })

    it('ignora dados inválidos do localStorage', () => {
      localStorageMock.setItem('app_auth', 'invalid-json{{{')
      
      const store = useAuthStore()
      store.load()

      expect(store.token).toBeNull()
      expect(store.user).toBeNull()
    })
  })

  describe('Login', () => {
    it('realiza login com sucesso', async () => {
      const mockResponse = {
        access_token: 'jwt-token-abc',
        user: { id: '1', name: 'João Silva', email: 'joao@test.com' }
      }

      ;(global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      })

      const store = useAuthStore()
      await store.login('http://localhost:3000', 'joao@test.com', 'senha123')

      expect(store.token).toBe('jwt-token-abc')
      expect(store.user).toEqual({
        id: '1',
        name: 'João Silva',
        email: 'joao@test.com'
      })
      
      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:3000/auth/login',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ email: 'joao@test.com', password: 'senha123' })
        })
      )
    })

    it('lança erro quando credenciais inválidas', async () => {
      ;(global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 401
      })

      const store = useAuthStore()
      
      await expect(
        store.login('http://localhost:3000', 'wrong@test.com', 'wrong')
      ).rejects.toThrow('Credenciais inválidas')
    })

    it('persiste token após login bem-sucedido', async () => {
      const mockResponse = {
        access_token: 'token-123',
        user: { id: '1', name: 'Test', email: 'test@test.com' }
      }

      ;(global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      })

      const store = useAuthStore()
      await store.login('http://localhost:3000', 'test@test.com', 'pass')

      const saved = JSON.parse(localStorageMock.getItem('app_auth') || '{}')
      expect(saved.token).toBe('token-123')
    })
  })

  describe('Registro', () => {
    it('registra novo usuário com sucesso', async () => {
      // Mock register
      ;(global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({})
      })

      // Mock login subsequente
      ;(global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          access_token: 'new-token',
          user: { id: '2', name: 'Novo User', email: 'novo@test.com' }
        })
      })

      const store = useAuthStore()
      await store.register('http://localhost:3000', 'Novo User', 'novo@test.com', 'senha123')

      expect(store.token).toBe('new-token')
      expect(store.user?.name).toBe('Novo User')
    })

    it('lança erro quando registro falha', async () => {
      ;(global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 400
      })

      const store = useAuthStore()
      
      await expect(
        store.register('http://localhost:3000', 'Test', 'test@test.com', 'pass')
      ).rejects.toThrow('Falha ao registrar')
    })
  })

  describe('Logout', () => {
    it('limpa token e usuário', () => {
      const store = useAuthStore()
      store.token = 'test-token'
      store.user = { id: '1', name: 'Test', email: 'test@test.com' }
      
      store.logout()

      expect(store.token).toBeNull()
      expect(store.user).toBeNull()
      expect(localStorageMock.getItem('app_auth')).toBeNull()
    })
  })

  describe('Validação de token', () => {
    it('detecta token expirado', () => {
      const store = useAuthStore()
      
      // Token expirado (exp no passado)
      const payload = { exp: Math.floor(Date.now() / 1000) - 3600 } // 1 hora atrás
      const token = `header.${btoa(JSON.stringify(payload))}.signature`
      store.token = token

      expect(store.isTokenExpired()).toBe(true)
    })

    it('detecta token válido', () => {
      const store = useAuthStore()
      
      // Token válido (exp no futuro)
      const payload = { exp: Math.floor(Date.now() / 1000) + 3600 } // 1 hora à frente
      const token = `header.${btoa(JSON.stringify(payload))}.signature`
      store.token = token

      expect(store.isTokenExpired()).toBe(false)
    })

    it('considera expirado quando token é null', () => {
      const store = useAuthStore()
      store.token = null

      expect(store.isTokenExpired()).toBe(true)
    })

    it('considera expirado quando token expira em menos de 1 minuto', () => {
      const store = useAuthStore()
      
      // Token expira em 30 segundos
      const payload = { exp: Math.floor(Date.now() / 1000) + 30 }
      const token = `header.${btoa(JSON.stringify(payload))}.signature`
      store.token = token

      expect(store.isTokenExpired()).toBe(true)
    })

    it('trata token malformado como expirado', () => {
      const store = useAuthStore()
      store.token = 'invalid-token-format'

      expect(store.isTokenExpired()).toBe(true)
    })
  })
})

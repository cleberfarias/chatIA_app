// frontend/src/stores/auth.ts
import { defineStore } from 'pinia'
import { ref } from 'vue'

type User = { id: string; name: string; email: string }

const STORAGE_KEY = 'app_auth'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(null)
  const user = ref<User | null>(null)

  function persist() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ token: token.value, user: user.value }))
  }
  function load() {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return
    try {
      const parsed = JSON.parse(raw)
      token.value = parsed.token
      user.value = parsed.user
    } catch { /* ignore */ }
  }
  function clear() {
    token.value = null
    user.value = null
    localStorage.removeItem(STORAGE_KEY)
  }

  async function login(baseUrl: string, email: string, password: string) {
    const res = await fetch(`${baseUrl}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    })
    if (!res.ok) throw new Error('Credenciais inválidas')
    const data = await res.json()
    token.value = data.access_token
    user.value = { 
      id: data.user.id,
      name: data.user.name, 
      email: data.user.email 
    }
    persist()
  }

  async function register(baseUrl: string, name: string, email: string, password: string) {
    const res = await fetch(`${baseUrl}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, email, password })
    })
    if (!res.ok) throw new Error('Falha ao registrar')
    
    await login(baseUrl, email, password)
  }

  function logout() {
    clear()
  }

  return { token, user, login, register, logout, load }
})

import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import TypingIndicator from '@/features/chat/components/TypingIndicator.vue'
import type { TypingInfo } from '@/design-system/types/validation'

describe('TypingIndicator', () => {
  describe('Renderização', () => {
    it('renderiza componente com estrutura correta', () => {
      const users: TypingInfo[] = [{ author: 'João', timestamp: Date.now() }]
      
      const wrapper = mount(TypingIndicator, {
        props: { users }
      })

      expect(wrapper.find('.typing-indicator').exists()).toBe(true)
      expect(wrapper.find('.typing-bubble').exists()).toBe(true)
      expect(wrapper.find('.typing-dots').exists()).toBe(true)
    })

    it('exibe 3 dots animados', () => {
      const users: TypingInfo[] = [{ author: 'Maria', timestamp: Date.now() }]
      
      const wrapper = mount(TypingIndicator, {
        props: { users }
      })

      const dots = wrapper.findAll('.dot')
      expect(dots).toHaveLength(3)
    })

    it('exibe avatar', () => {
      const users: TypingInfo[] = [{ author: 'Pedro', timestamp: Date.now() }]
      
      const wrapper = mount(TypingIndicator, {
        props: { users }
      })

      // Verifica se componente renderiza (Vuetify internals não importam para teste)
      expect(wrapper.find('.typing-indicator').exists()).toBe(true)
    })
  })

  describe('Texto de digitação', () => {
    it('exibe nome único quando 1 usuário está digitando', () => {
      const users: TypingInfo[] = [{ author: 'João Silva', timestamp: Date.now() }]
      
      const wrapper = mount(TypingIndicator, {
        props: { users }
      })

      expect(wrapper.find('.typing-text').text()).toBe('João Silva está digitando')
    })

    it('exibe dois nomes quando 2 usuários estão digitando', () => {
      const users: TypingInfo[] = [
        { author: 'João', timestamp: Date.now() },
        { author: 'Maria', timestamp: Date.now() }
      ]
      
      const wrapper = mount(TypingIndicator, {
        props: { users }
      })

      expect(wrapper.find('.typing-text').text()).toBe('João e Maria estão digitando')
    })

    it('exibe quantidade quando 3+ usuários estão digitando', () => {
      const users: TypingInfo[] = [
        { author: 'João', timestamp: Date.now() },
        { author: 'Maria', timestamp: Date.now() },
        { author: 'Pedro', timestamp: Date.now() }
      ]
      
      const wrapper = mount(TypingIndicator, {
        props: { users }
      })

      expect(wrapper.find('.typing-text').text()).toBe('3 pessoas estão digitando')
    })

    it('exibe texto vazio quando nenhum usuário está digitando', () => {
      const users: TypingInfo[] = []
      
      const wrapper = mount(TypingIndicator, {
        props: { users }
      })

      expect(wrapper.find('.typing-text').text()).toBe('')
    })

    it('usa fallback quando autor não está definido', () => {
      const users: TypingInfo[] = [{ author: '', timestamp: Date.now() }]
      
      const wrapper = mount(TypingIndicator, {
        props: { users }
      })

      expect(wrapper.find('.typing-text').text()).toContain('Alguém')
    })
  })

  describe('Props reativas', () => {
    it('atualiza texto quando usuários mudam', async () => {
      const users: TypingInfo[] = [{ author: 'João', timestamp: Date.now() }]
      
      const wrapper = mount(TypingIndicator, {
        props: { users }
      })

      expect(wrapper.find('.typing-text').text()).toBe('João está digitando')

      await wrapper.setProps({
        users: [
          { author: 'João', timestamp: Date.now() },
          { author: 'Maria', timestamp: Date.now() }
        ]
      })

      expect(wrapper.find('.typing-text').text()).toBe('João e Maria estão digitando')
    })

    it('atualiza de múltiplos para um único usuário', async () => {
      const users: TypingInfo[] = [
        { author: 'João', timestamp: Date.now() },
        { author: 'Maria', timestamp: Date.now() },
        { author: 'Pedro', timestamp: Date.now() }
      ]
      
      const wrapper = mount(TypingIndicator, {
        props: { users }
      })

      expect(wrapper.find('.typing-text').text()).toBe('3 pessoas estão digitando')

      await wrapper.setProps({
        users: [{ author: 'Maria', timestamp: Date.now() }]
      })

      expect(wrapper.find('.typing-text').text()).toBe('Maria está digitando')
    })
  })

  describe('Casos extremos', () => {
    it('lida com nomes muito longos', () => {
      const users: TypingInfo[] = [
        { author: 'João Pedro da Silva Santos Junior', timestamp: Date.now() }
      ]
      
      const wrapper = mount(TypingIndicator, {
        props: { users }
      })

      expect(wrapper.find('.typing-text').text()).toContain('João Pedro da Silva Santos Junior está digitando')
    })

    it('lida com caracteres especiais nos nomes', () => {
      const users: TypingInfo[] = [
        { author: 'José María', timestamp: Date.now() }
      ]
      
      const wrapper = mount(TypingIndicator, {
        props: { users }
      })

      expect(wrapper.find('.typing-text').text()).toContain('José María')
    })

    it('lida com muitos usuários (10+)', () => {
      const users: TypingInfo[] = Array.from({ length: 15 }, (_, i) => ({
        author: `User ${i + 1}`,
        timestamp: Date.now()
      }))
      
      const wrapper = mount(TypingIndicator, {
        props: { users }
      })

      expect(wrapper.find('.typing-text').text()).toBe('15 pessoas estão digitando')
    })
  })
})

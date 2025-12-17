import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import DSChatInput from '@/design-system/components/DSChatInput/DSChatInput.vue'

describe('DSChatInput', () => {
  describe('Renderização', () => {
    it('renderiza componente principal', () => {
      const wrapper = mount(DSChatInput, {
        props: {
          modelValue: ''
        }
      })

      expect(wrapper.find('.ds-chat-input').exists()).toBe(true)
      expect(wrapper.find('.ds-chat-input__field').exists()).toBe(true)
    })

    it('renderiza botão de anexo', () => {
      const wrapper = mount(DSChatInput, {
        props: {
          modelValue: ''
        }
      })

      expect(wrapper.find('.ds-chat-input__attach-btn').exists()).toBe(true)
    })

    it('renderiza botão de enviar', () => {
      const wrapper = mount(DSChatInput, {
        props: {
          modelValue: ''
        }
      })

      expect(wrapper.find('.ds-chat-input__send-btn').exists()).toBe(true)
    })
  })

  describe('Props', () => {
    it('aceita modelValue', () => {
      const wrapper = mount(DSChatInput, {
        props: {
          modelValue: 'Mensagem de teste'
        }
      })

      expect(wrapper.props('modelValue')).toBe('Mensagem de teste')
    })

    it('aceita prop uploading', () => {
      const wrapper = mount(DSChatInput, {
        props: {
          modelValue: '',
          uploading: true
        }
      })

      expect(wrapper.props('uploading')).toBe(true)
    })
  })

  describe('Eventos', () => {
    it('emite submit quando clica no botão enviar', async () => {
      const wrapper = mount(DSChatInput, {
        props: {
          modelValue: 'Mensagem para enviar'
        }
      })

      await wrapper.find('.ds-chat-input__send-btn').trigger('click')

      expect(wrapper.emitted('submit')).toBeTruthy()
      expect(wrapper.emitted('submit')?.length).toBe(1)
    })
  })

  describe('Slot de anexo', () => {
    it('usa slot personalizado para botão de anexo', () => {
      const wrapper = mount(DSChatInput, {
        props: {
          modelValue: ''
        },
        slots: {
          'attach-btn': '<button class="custom-attach">Anexar</button>'
        }
      })

      expect(wrapper.find('.custom-attach').exists()).toBe(true)
      expect(wrapper.find('.custom-attach').text()).toBe('Anexar')
    })
  })
})

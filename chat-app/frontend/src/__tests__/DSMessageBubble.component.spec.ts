import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import DSMessageBubble from '@/design-system/components/DSMessageBubble/DSMessageBubble.vue'

describe('DSMessageBubble', () => {
  const baseProps = {
    timestamp: Date.now(),
    variant: 'received' as const,
    text: 'Olá mundo!'
  }

  describe('Renderização básica', () => {
    it('renderiza mensagem de texto', () => {
      const wrapper = mount(DSMessageBubble, {
        props: baseProps
      })

      expect(wrapper.find('.ds-message-bubble__text').exists()).toBe(true)
      expect(wrapper.html()).toContain('Olá mundo!')
    })

    it('aplica classe correta para mensagem enviada', () => {
      const wrapper = mount(DSMessageBubble, {
        props: {
          ...baseProps,
          variant: 'sent'
        }
      })

      expect(wrapper.classes()).toContain('ds-message-bubble--sent')
    })

    it('aplica classe correta para mensagem recebida', () => {
      const wrapper = mount(DSMessageBubble, {
        props: baseProps
      })

      expect(wrapper.classes()).toContain('ds-message-bubble--received')
    })
  })

  describe('Timestamp', () => {
    it('exibe timestamp formatado', () => {
      const timestamp = new Date('2025-12-17T14:30:00').getTime()
      
      const wrapper = mount(DSMessageBubble, {
        props: {
          ...baseProps,
          timestamp,
          showTimestamp: true
        }
      })

      expect(wrapper.find('.ds-message-bubble__time').exists()).toBe(true)
      expect(wrapper.find('.ds-message-bubble__time').text()).toMatch(/\d{2}:\d{2}/)
    })

    it('oculta timestamp quando showTimestamp é false', () => {
      const wrapper = mount(DSMessageBubble, {
        props: {
          ...baseProps,
          showTimestamp: false
        }
      })

      expect(wrapper.find('.ds-message-bubble__footer').exists()).toBe(false)
    })
  })

  describe('Status da mensagem', () => {
    it('exibe footer com status para mensagem enviada', () => {
      const wrapper = mount(DSMessageBubble, {
        props: {
          ...baseProps,
          variant: 'sent',
          status: 'sent'
        }
      })

      expect(wrapper.find('.ds-message-bubble__footer').exists()).toBe(true)
    })

    it('aceita diferentes valores de status', () => {
      const wrapper = mount(DSMessageBubble, {
        props: {
          ...baseProps,
          variant: 'sent',
          status: 'pending'
        }
      })

      expect(wrapper.props('status')).toBe('pending')
    })
  })

  describe('Autor', () => {
    it('exibe autor quando showAuthor é true', () => {
      const wrapper = mount(DSMessageBubble, {
        props: {
          ...baseProps,
          author: 'João Silva',
          showAuthor: true
        }
      })

      expect(wrapper.find('.ds-message-bubble__author').exists()).toBe(true)
      expect(wrapper.find('.ds-message-bubble__author').text()).toBe('João Silva')
    })

    it('oculta autor quando showAuthor é false', () => {
      const wrapper = mount(DSMessageBubble, {
        props: {
          ...baseProps,
          author: 'João Silva',
          showAuthor: false
        }
      })

      expect(wrapper.find('.ds-message-bubble__author').exists()).toBe(false)
    })
  })

  describe('Anexos - Imagem', () => {
    it('renderiza imagem quando type é image', () => {
      const wrapper = mount(DSMessageBubble, {
        props: {
          ...baseProps,
          type: 'image',
          attachmentUrl: 'https://example.com/image.jpg',
          fileName: 'foto.jpg'
        }
      })

      expect(wrapper.find('.ds-message-bubble__image').exists()).toBe(true)
      expect(wrapper.find('img').exists()).toBe(true)
      expect(wrapper.find('img').attributes('src')).toBe('https://example.com/image.jpg')
      expect(wrapper.find('img').attributes('alt')).toBe('foto.jpg')
    })

    it('link da imagem abre em nova aba', () => {
      const wrapper = mount(DSMessageBubble, {
        props: {
          ...baseProps,
          type: 'image',
          attachmentUrl: 'https://example.com/image.jpg'
        }
      })

      const link = wrapper.find('.ds-message-bubble__image a')
      expect(link.attributes('target')).toBe('_blank')
      expect(link.attributes('rel')).toBe('noopener noreferrer')
    })
  })

  describe('Anexos - Áudio', () => {
    it('renderiza player de áudio quando type é audio', () => {
      const wrapper = mount(DSMessageBubble, {
        props: {
          ...baseProps,
          type: 'audio',
          attachmentUrl: 'https://example.com/audio.mp3'
        }
      })

      expect(wrapper.find('.ds-message-bubble__audio').exists()).toBe(true)
      expect(wrapper.find('audio').exists()).toBe(true)
      expect(wrapper.find('audio').attributes('src')).toBe('https://example.com/audio.mp3')
      expect(wrapper.find('audio').attributes('controls')).toBeDefined()
    })

    it('exibe ícone de microfone para áudio', () => {
      const wrapper = mount(DSMessageBubble, {
        props: {
          ...baseProps,
          type: 'audio',
          attachmentUrl: 'https://example.com/audio.mp3'
        }
      })

      expect(wrapper.find('.ds-message-bubble__audio-icon').exists()).toBe(true)
    })
  })

  describe('Anexos - Arquivo', () => {
    it('renderiza arquivo quando type é file', () => {
      const wrapper = mount(DSMessageBubble, {
        props: {
          ...baseProps,
          type: 'file',
          attachmentUrl: 'https://example.com/doc.pdf',
          fileName: 'documento.pdf'
        }
      })

      expect(wrapper.find('.ds-message-bubble__file').exists()).toBe(true)
      expect(wrapper.find('.ds-message-bubble__file-name').text()).toBe('documento.pdf')
    })

    it('exibe link de download para arquivo', () => {
      const wrapper = mount(DSMessageBubble, {
        props: {
          ...baseProps,
          type: 'file',
          attachmentUrl: 'https://example.com/doc.pdf',
          fileName: 'documento.pdf'
        }
      })

      const downloadLink = wrapper.find('.ds-message-bubble__file-download')
      expect(downloadLink.exists()).toBe(true)
      expect(downloadLink.attributes('href')).toBe('https://example.com/doc.pdf')
      expect(downloadLink.attributes('target')).toBe('_blank')
    })

    it('usa nome padrão quando fileName não é fornecido', () => {
      const wrapper = mount(DSMessageBubble, {
        props: {
          ...baseProps,
          type: 'file',
          attachmentUrl: 'https://example.com/doc.pdf'
        }
      })

      expect(wrapper.find('.ds-message-bubble__file-name').text()).toBe('Arquivo')
    })
  })

  describe('Markdown e Código', () => {
    it('renderiza texto simples', () => {
      const wrapper = mount(DSMessageBubble, {
        props: {
          ...baseProps,
          text: 'Texto simples sem formatação'
        }
      })

      expect(wrapper.html()).toContain('Texto simples sem formatação')
    })

    it('renderiza markdown em negrito', () => {
      const wrapper = mount(DSMessageBubble, {
        props: {
          ...baseProps,
          text: '**texto em negrito**'
        }
      })

      const html = wrapper.find('.ds-message-bubble__text').html()
      expect(html).toContain('<strong>')
    })

    it('renderiza markdown com itálico', () => {
      const wrapper = mount(DSMessageBubble, {
        props: {
          ...baseProps,
          text: '*texto em itálico*'
        }
      })

      const html = wrapper.find('.ds-message-bubble__text').html()
      expect(html).toContain('<em>')
    })
  })
})

<template>
  <div :class="bubbleClasses">
    <div v-if="showAuthor" class="ds-message-bubble__author">
      {{ author }}
    </div>

    <div v-if="type === 'image' && attachmentUrl" class="ds-message-bubble__image">
      <a :href="attachmentUrl" target="_blank" rel="noopener noreferrer">
        <img :src="attachmentUrl" :alt="fileName || 'Imagem'" />
      </a>
    </div>

    <div v-else-if="type === 'audio' && attachmentUrl" class="ds-message-bubble__audio">
      <v-icon icon="mdi-microphone" size="24" class="ds-message-bubble__audio-icon" color="primary" />
      <audio controls :src="attachmentUrl" class="ds-message-bubble__audio-player">
        Seu navegador não suporta o elemento de áudio.
      </audio>
    </div>

    <div v-else-if="type === 'file' && attachmentUrl" class="ds-message-bubble__file">
      <v-icon icon="mdi-file-document" size="32" class="ds-message-bubble__file-icon" />
      <div class="ds-message-bubble__file-info">
        <div class="ds-message-bubble__file-name">{{ fileName || 'Arquivo' }}</div>
        <a :href="attachmentUrl" target="_blank" rel="noopener noreferrer" class="ds-message-bubble__file-download">
          <v-icon icon="mdi-download" size="16" class="mr-1" />
          Download
        </a>
      </div>
    </div>

    <div v-if="type === 'text' || !type" class="ds-message-bubble__text" v-html="renderedText"></div>

    <div v-if="showTimestamp" class="ds-message-bubble__footer">
      <span class="ds-message-bubble__time">{{ formattedTime }}</span>
      <v-icon
        v-if="variant === 'sent' && status"
        :icon="statusIcon"
        :color="statusColor"
        size="16"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { marked } from 'marked';
import hljs from 'highlight.js/lib/core';
import python from 'highlight.js/lib/languages/python';
import javascript from 'highlight.js/lib/languages/javascript';
import typescript from 'highlight.js/lib/languages/typescript';
import bash from 'highlight.js/lib/languages/bash';
import json from 'highlight.js/lib/languages/json';
import 'highlight.js/styles/github-dark.css';

hljs.registerLanguage('python', python);
hljs.registerLanguage('javascript', javascript);
hljs.registerLanguage('typescript', typescript);
hljs.registerLanguage('bash', bash);
hljs.registerLanguage('json', json);

marked.setOptions({
  breaks: true,
  gfm: true,
});

interface Props {
  author?: string;
  timestamp: number;
  variant: 'sent' | 'received';
  status?: 'pending' | 'sent' | 'delivered' | 'read';
  showAuthor?: boolean;
  showTimestamp?: boolean;
  type?: 'text' | 'image' | 'file' | 'audio';
  attachmentUrl?: string;
  fileName?: string;
  text?: string;
}

const props = withDefaults(defineProps<Props>(), {
  showTimestamp: true,
  type: 'text',
});

const bubbleClasses = computed(() => [
  'ds-message-bubble',
  `ds-message-bubble--${props.variant}`,
]);

const formattedTime = computed(() => {
  const date = new Date(props.timestamp);
  return date.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
});

const statusIcon = computed(() => {
  switch (props.status) {
    case 'pending':
      return 'mdi-clock-outline';
    case 'sent':
      return 'mdi-check';
    case 'delivered':
      return 'mdi-check-all';
    case 'read':
      return 'mdi-check-all';
    default:
      return 'mdi-clock-outline';
  }
});

const statusColor = computed(() => {
  switch (props.status) {
    case 'pending':
      return 'grey-lighten-1';
    case 'read':
      return 'blue';
    default:
      return 'grey';
  }
});

const renderedText = computed(() => {
  if (!props.text) return '';

  const html = marked.parse(props.text) as string;
  const parser = new DOMParser();
  const doc = parser.parseFromString(html, 'text/html');
  const codeBlocks = doc.querySelectorAll('pre code');

  codeBlocks.forEach((block) => {
    const code = block.textContent || '';
    const classes = block.className.match(/language-(\w+)/);
    const language = classes ? classes[1] : '';

    if (language && hljs.getLanguage(language)) {
      try {
        const highlighted = hljs.highlight(code, { language }).value;
        block.innerHTML = highlighted;
        block.classList.add('hljs');
      } catch (error) {
        console.error('Erro ao fazer highlight:', error);
      }
    }
  });

  return doc.body.innerHTML;
});
</script>

<style scoped lang="scss" src="./DSMessageBubble.scss"></style>

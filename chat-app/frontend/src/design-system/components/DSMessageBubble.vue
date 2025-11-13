<template>
  <div :class="['ds-message-bubble', variant]">
    <div v-if="showAuthor" class="ds-message-author">
      {{ author }}
    </div>
    
    <!-- 🖼️ IMAGEM -->
    <div v-if="type === 'image' && attachmentUrl" class="ds-message-image">
      <a :href="attachmentUrl" target="_blank" rel="noopener noreferrer">
        <img :src="attachmentUrl" :alt="fileName || 'Imagem'" />
      </a>
    </div>
    
    <!-- 📎 ARQUIVO -->
    <div v-else-if="type === 'file' && attachmentUrl" class="ds-message-file">
      <v-icon icon="mdi-file-document" size="32" class="mr-2" />
      <div class="file-info">
        <div class="file-name">{{ fileName || 'Arquivo' }}</div>
        <a :href="attachmentUrl" target="_blank" rel="noopener noreferrer" class="file-download">
          <v-icon icon="mdi-download" size="16" class="mr-1" />
          Download
        </a>
      </div>
    </div>
    
    <!-- 💬 TEXTO -->
    <div v-if="type === 'text' || !type" class="ds-message-text">
      <slot />
    </div>
    
    <div v-if="showTimestamp" class="ds-message-footer">
      <span class="ds-message-time">{{ formattedTime }}</span>
      <v-icon 
        v-if="variant === 'sent' && status" 
        :icon="statusIcon"
        :color="statusColor"
        size="16"
        class="ml-1"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { colors, spacing, radius, shadows, typography } from '../tokens';

interface Props {
  author?: string;
  timestamp: number;
  variant: 'sent' | 'received';
  status?: 'pending' | 'sent' | 'delivered' | 'read';
  showAuthor?: boolean;
  showTimestamp?: boolean;
  type?: 'text' | 'image' | 'file';
  attachmentUrl?: string;
  fileName?: string;
}

const props = withDefaults(defineProps<Props>(), {
  showTimestamp: true,
  type: 'text',
});

const formattedTime = computed(() => {
  const date = new Date(props.timestamp);
  return date.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
});

const statusIcon = computed(() => {
  switch (props.status) {
    case 'pending': return 'mdi-clock-outline'; // ⏳ Enviando...
    case 'sent': return 'mdi-check'; // ✓ Enviado
    case 'delivered': return 'mdi-check-all'; // ✓✓ Entregue
    case 'read': return 'mdi-check-all'; // ✓✓ Lido (azul)
    default: return 'mdi-clock-outline';
  }
});

const statusColor = computed(() => {
  switch (props.status) {
    case 'pending': return 'grey-lighten-1';
    case 'read': return 'blue';
    default: return 'grey';
  }
});
</script>

<style scoped>
.ds-message-bubble {
  max-width: 85%;
  padding: v-bind('spacing.sm') v-bind('spacing.md');
  border-radius: v-bind('radius.md');
  box-shadow: v-bind('shadows.sm');
  font-family: v-bind('typography.fontFamily.primary');
  font-size: v-bind('typography.fontSize.base');
  line-height: v-bind('typography.lineHeight.normal');
}

/* 📱 Mobile - Bolhas mais largas */
@media (max-width: 599px) {
  .ds-message-bubble {
    max-width: 90%;
    padding: 8px 12px;
  }
}

/* 📱 Tablet */
@media (min-width: 600px) and (max-width: 959px) {
  .ds-message-bubble {
    max-width: 75%;
  }
}

/* 💻 Desktop */
@media (min-width: 960px) {
  .ds-message-bubble {
    max-width: 65%;
  }
}

.ds-message-bubble.sent {
  background: v-bind('colors.sentMessage');
  border-top-right-radius: 0;
}

.ds-message-bubble.received {
  background: v-bind('colors.receivedMessage');
  border-top-left-radius: 0;
}

.ds-message-author {
  color: v-bind('colors.primary');
  font-weight: v-bind('typography.fontWeight.bold');
  font-size: v-bind('typography.fontSize.sm');
  margin-bottom: v-bind('spacing.xs');
}

.ds-message-text {
  word-wrap: break-word;
  margin-bottom: v-bind('spacing.xs');
  color: v-bind('colors.textPrimary');
}

.ds-message-footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: v-bind('spacing.xs');
}

.ds-message-time {
  font-size: v-bind('typography.fontSize.xs');
  color: v-bind('colors.textHint');
}

.ds-message-image {
  margin-bottom: v-bind('spacing.xs');
}

.ds-message-image img {
  max-width: 100%;
  max-height: 300px;
  border-radius: v-bind('radius.sm');
  cursor: pointer;
  transition: opacity 0.2s;
}

/* 📱 Mobile - Imagens menores */
@media (max-width: 599px) {
  .ds-message-image img {
    max-height: 200px;
  }
}

.ds-message-image img:hover {
  opacity: 0.9;
}

.ds-message-file {
  display: flex;
  align-items: center;
  padding: v-bind('spacing.sm');
  background: rgba(0, 0, 0, 0.05);
  border-radius: v-bind('radius.sm');
  margin-bottom: v-bind('spacing.xs');
}

.file-info {
  flex: 1;
  min-width: 0;
}

.file-name {
  font-weight: v-bind('typography.fontWeight.medium');
  margin-bottom: 4px;
  color: v-bind('colors.textPrimary');
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.file-download {
  display: inline-flex;
  align-items: center;
  font-size: v-bind('typography.fontSize.sm');
  color: v-bind('colors.primary');
  text-decoration: none;
}

.file-download:hover {
  text-decoration: underline;
}
</style>
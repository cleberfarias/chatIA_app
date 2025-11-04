<template>
  <div :class="['ds-message-bubble', variant]">
    <div v-if="showAuthor" class="ds-message-author">
      {{ author }}
    </div>
    
    <div class="ds-message-text">
      <slot />
    </div>
    
    <div class="ds-message-footer">
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
  status?: 'sent' | 'delivered' | 'read';
  showAuthor?: boolean;
}

const props = defineProps<Props>();

const formattedTime = computed(() => {
  const date = new Date(props.timestamp);
  return date.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
});

const statusIcon = computed(() => {
  switch (props.status) {
    case 'sent': return 'mdi-check';
    case 'delivered': return 'mdi-check-all';
    case 'read': return 'mdi-check-all';
    default: return 'mdi-clock-outline';
  }
});

const statusColor = computed(() => {
  return props.status === 'read' ? 'blue-lighten-1' : 'grey';
});
</script>

<style scoped>
.ds-message-bubble {
  max-width: 65%;
  padding: v-bind('spacing.sm') v-bind('spacing.md');
  border-radius: v-bind('radius.md');
  box-shadow: v-bind('shadows.sm');
  font-family: v-bind('typography.fontFamily.primary');
  font-size: v-bind('typography.fontSize.base');
  line-height: v-bind('typography.lineHeight.normal');
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
</style>
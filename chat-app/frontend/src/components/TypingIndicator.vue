<template>
  <div class="typing-indicator d-flex align-center pa-3">
    <v-avatar size="32" :color="colors.secondary" class="mr-2">
      <v-icon size="20" color="white">mdi-account</v-icon>
    </v-avatar>
    
    <div class="typing-bubble" :style="{ background: colors.receivedMessage }">
      <span class="typing-text">{{ typingText }}</span>
      <div class="typing-dots">
        <span class="dot"></span>
        <span class="dot"></span>
        <span class="dot"></span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { colors } from '@/design-system/tokens';
import type { TypingInfo } from '@/design-system/types/validation';

interface Props {
  users: TypingInfo[];
}

const props = defineProps<Props>();

const typingText = computed(() => {
  if (props.users.length === 0) return '';
  if (props.users.length === 1) return `${props.users[0]?.author || 'Alguém'} está digitando`;
  if (props.users.length === 2) {
    return `${props.users[0]?.author || 'Alguém'} e ${props.users[1]?.author || 'alguém'} estão digitando`;
  }
  return `${props.users.length} pessoas estão digitando`;
});
</script>

<style scoped>
.typing-indicator {
  animation: fadeIn 0.3s ease-in-out;
}

.typing-bubble {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  border-radius: 18px;
  max-width: 300px;
}

.typing-text {
  font-size: 14px;
  color: rgba(0, 0, 0, 0.6);
  font-style: italic;
}

.typing-dots {
  display: flex;
  gap: 4px;
  align-items: center;
}

.dot {
  width: 6px;
  height: 6px;
  background: rgba(0, 0, 0, 0.4);
  border-radius: 50%;
  animation: bounce 1.4s infinite ease-in-out both;
}

.dot:nth-child(1) {
  animation-delay: -0.32s;
}

.dot:nth-child(2) {
  animation-delay: -0.16s;
}

@keyframes bounce {
  0%, 80%, 100% {
    transform: scale(0);
    opacity: 0.5;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>

<template>
  <div class="messages-content">
    <template v-for="(item, index) in groupedMessages" :key="item.id || index">
      <DSDateSeparator v-if="'date' in item" :date="item.date" />

      <div
        v-else
        :class="['mb-2', item.userId === currentUserId ? 'd-flex justify-end' : 'd-flex justify-start']"
      >
        <DSMessageBubble
          :author="item.author"
          :timestamp="item.timestamp"
          :variant="item.userId === currentUserId ? 'sent' : 'received'"
          :status="item.status"
          :show-author="item.showAuthor"
          :show-timestamp="item.showTimestamp"
          :type="item.type || 'text'"
          :attachment-url="item.url"
          :file-name="item.attachment?.filename || item.text"
          :text="item.type === 'text' ? item.text : ''"
        />
      </div>
    </template>

    <TypingIndicator v-if="typingUsers.length > 0" :users="typingUsers" />
    <div class="messages-spacer" />
  </div>
</template>

<script setup lang="ts">
import DSMessageBubble from '../../../design-system/components/DSMessageBubble';
import { DSDateSeparator } from '../../../design-system/components/DSDateSeparator';
import TypingIndicator from './TypingIndicator.vue';

defineProps<{
  groupedMessages: any[];
  currentUserId: string;
  typingUsers: any[];
}>();
</script>

<style scoped>
.messages-content {
  width: 100%;
  max-width: 1100px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.messages-spacer {
  height: 140px;
  flex-shrink: 0;
}

@media (min-width: 600px) {
  .messages-spacer {
    height: 160px;
  }
}

@media (min-width: 960px) {
  .messages-spacer {
    height: 180px;
  }
}
</style>

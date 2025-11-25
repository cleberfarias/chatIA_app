<template>
  <div class="ds-chat-input">
    <v-form @submit.prevent="handleSubmit" class="ds-chat-input__form">
      <v-btn 
        icon="mdi-emoticon-outline" 
        variant="text" 
        color="grey-darken-1" 
        size="large"
        @click="$emit('emoji')"
      />

      <slot name="attach-btn">
        <v-btn 
          icon 
          variant="text" 
          color="grey-darken-1"
          size="large"
          class="ds-chat-input__attach-btn"
          :disabled="uploading"
        >
          <v-icon class="ds-chat-input__attach-icon">mdi-paperclip</v-icon>
        </v-btn>
      </slot>

      <v-text-field
        :model-value="modelValue"
        @update:model-value="$emit('update:modelValue', $event)"
        placeholder="Digite uma mensagem"
        variant="outlined"
        density="compact"
        hide-details
        rounded
        bg-color="white"
        class="ds-chat-input__field"
        @keyup.enter.exact.prevent="handleEnterKey"
        :disabled="uploading"
      />

      <v-btn
        icon
        :color="hasText ? colors.secondary : 'grey-darken-1'"
        class="ds-chat-input__send-btn"
        @click="handleSubmit"
        :disabled="uploading"
        :loading="uploading"
      >
        <v-icon>{{ hasText ? 'mdi-send' : 'mdi-microphone' }}</v-icon>

        <v-progress-circular
          v-if="uploading && uploadProgress > 0"
          :model-value="uploadProgress"
          :size="40"
          :width="3"
          color="white"
          class="ds-chat-input__progress"
        />
      </v-btn>
    </v-form>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { colors } from '../../tokens';

interface Props {
  modelValue: string;
  uploading?: boolean;
  uploadProgress?: number;
}

const props = withDefaults(defineProps<Props>(), {
  uploading: false,
  uploadProgress: 0
});

const emit = defineEmits<{
  'update:modelValue': [value: string];
  'submit': [text: string];
  'typing': [isTyping: boolean];
  'emoji': [];
  'voice': [];
}>();

const hasText = computed(() => props.modelValue.trim().length > 0);
const typingTimeout = ref<number | null>(null);
const isTyping = ref(false);

watch(() => props.modelValue, (newValue) => {
  if (newValue && !isTyping.value) {
    isTyping.value = true;
    emit('typing', true);
  }

  if (typingTimeout.value) {
    clearTimeout(typingTimeout.value);
  }

  typingTimeout.value = window.setTimeout(() => {
    if (isTyping.value) {
      isTyping.value = false;
      emit('typing', false);
    }
  }, 1000);

  if (!newValue && isTyping.value) {
    isTyping.value = false;
    emit('typing', false);
    if (typingTimeout.value) {
      clearTimeout(typingTimeout.value);
    }
  }
});

function handleEnterKey() {
  if (hasText.value && !props.uploading) {
    sendMessage();
  }
}

function handleSubmit() {
  if (hasText.value && !props.uploading) {
    sendMessage();
  } else if (!hasText.value && !props.uploading) {
    emit('voice');
  }
}

function sendMessage() {
  if (isTyping.value) {
    isTyping.value = false;
    emit('typing', false);
  }
  if (typingTimeout.value) {
    clearTimeout(typingTimeout.value);
  }

  emit('submit', props.modelValue);
  emit('update:modelValue', '');
}
</script>

<style scoped lang="scss" src="./DSChatInput.scss"></style>

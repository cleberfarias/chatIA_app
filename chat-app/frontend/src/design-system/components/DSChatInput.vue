<template>
  <div class="ds-chat-input" :style="{ background: colors.inputBackground, borderTop: `1px solid ${colors.border}` }">
    <v-form @submit.prevent="handleSubmit" class="d-flex align-center pa-2 gap-2">
      <!-- 😊 EMOJI -->
      <v-btn 
        icon="mdi-emoticon-outline" 
        variant="text" 
        color="grey-darken-1" 
        size="large"
        @click="$emit('emoji')"
      />
      
      <!-- 📎 ANEXO (estilo WhatsApp) -->
      <slot name="attach-btn">
        <v-btn 
          icon 
          variant="text" 
          color="grey-darken-1"
          size="large"
          class="attach-btn"
          :disabled="uploading"
        >
          <v-icon class="attach-icon">mdi-paperclip</v-icon>
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
        class="flex-grow-1"
        @keyup.enter.exact.prevent="handleSubmit"
        :disabled="uploading"
      />
      
      <v-btn
        icon
        :color="hasText ? colors.secondary : 'grey-darken-1'"
        class="ml-2 send-btn"
        @click="handleSubmit"
        :disabled="uploading"
        :loading="uploading"
      >
        <v-icon>{{ hasText ? 'mdi-send' : 'mdi-microphone' }}</v-icon>
        
        <!-- Barra de progresso circular -->
        <v-progress-circular
          v-if="uploading && uploadProgress > 0"
          :model-value="uploadProgress"
          :size="40"
          :width="3"
          color="white"
          class="progress-overlay"
        />
      </v-btn>
    </v-form>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { colors } from '../tokens';

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

// 🆕 Debounce para evento de digitação
const typingTimeout = ref<number | null>(null);
const isTyping = ref(false);

watch(() => props.modelValue, (newValue) => {
  // Usuário começou a digitar
  if (newValue && !isTyping.value) {
    isTyping.value = true;
    emit('typing', true);
  }
  
  // Limpa timeout anterior
  if (typingTimeout.value) {
    clearTimeout(typingTimeout.value);
  }
  
  // Define novo timeout de 1s (usuário parou de digitar)
  typingTimeout.value = setTimeout(() => {
    if (isTyping.value) {
      isTyping.value = false;
      emit('typing', false);
    }
  }, 1000);
  
  // Se apagou tudo, emite imediatamente
  if (!newValue && isTyping.value) {
    isTyping.value = false;
    emit('typing', false);
    if (typingTimeout.value) {
      clearTimeout(typingTimeout.value);
    }
  }
});

function handleSubmit() {
  if (hasText.value && !props.uploading) {
    // Para o indicador de digitação
    if (isTyping.value) {
      isTyping.value = false;
      emit('typing', false);
    }
    if (typingTimeout.value) {
      clearTimeout(typingTimeout.value);
    }
    
    emit('submit', props.modelValue);
    // Limpa o campo após enviar
    emit('update:modelValue', '');
  } else if (!hasText.value && !props.uploading) {
    emit('voice');
  }
}
</script>

<style scoped>
.ds-chat-input {
  width: 100%;
}

.send-btn {
  position: relative;
}

.progress-overlay {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  pointer-events: none;
}

/* 📎 Estilo WhatsApp - Clipe rotacionado 135° */
.attach-btn {
  transition: transform 0.2s ease;
}

.attach-icon {
  transform: rotate(135deg);
  transition: transform 0.2s ease;
}

.attach-btn:hover .attach-icon {
  transform: rotate(135deg) scale(1.1);
}

.gap-2 {
  gap: 8px;
}
</style>
<template>
  <div class="ds-chat-input" :style="{ background: colors.inputBackground, borderTop: `1px solid ${colors.border}` }">
    <v-form @submit.prevent="handleSubmit" class="d-flex align-center pa-2">
      <v-btn 
        icon="mdi-emoticon-outline" 
        variant="text" 
        color="grey-darken-1" 
        class="mr-2"
        @click="$emit('emoji')"
      />
      
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
      >
        <template v-slot:append-inner>
          <v-btn 
            icon="mdi-paperclip" 
            variant="text" 
            size="small" 
            color="grey-darken-1"
            @click="$emit('attach')"
          />
        </template>
      </v-text-field>
      
      <v-btn
        icon
        :color="hasText ? colors.secondary : 'grey'"
        class="ml-2"
        @click="handleSubmit"
        :disabled="!hasText"
      >
        <v-icon>{{ hasText ? 'mdi-send' : 'mdi-microphone' }}</v-icon>
      </v-btn>
    </v-form>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { colors } from '../tokens';

interface Props {
  modelValue: string;
}

const props = defineProps<Props>();

const emit = defineEmits<{
  'update:modelValue': [value: string];
  'submit': [text: string];
  'typing': [isTyping: boolean]; // 🆕 Evento de digitação
  'emoji': [];
  'attach': [];
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
  if (hasText.value) {
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
  } else {
    emit('voice');
  }
}
</script>

<style scoped>
.ds-chat-input {
  width: 100%;
}
</style>
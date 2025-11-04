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
import { computed } from 'vue';
import { colors } from '../tokens';

interface Props {
  modelValue: string;
}

const props = defineProps<Props>();

const emit = defineEmits<{
  'update:modelValue': [value: string];
  'submit': [text: string];
  'emoji': [];
  'attach': [];
  'voice': [];
}>();

const hasText = computed(() => props.modelValue.trim().length > 0);

function handleSubmit() {
  if (hasText.value) {
    emit('submit', props.modelValue);
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
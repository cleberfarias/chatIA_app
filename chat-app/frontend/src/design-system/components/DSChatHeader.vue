<template>
  <v-app-bar 
    :color="colors.primary" 
    elevation="1" 
    :style="{ borderBottom: `1px solid ${colors.primaryLight}` }"
  >
    <v-app-bar-title class="text-white d-flex align-center">
      <v-avatar :size="40" :color="colors.secondary" class="mr-3">
        <v-img v-if="avatar" :src="avatar" />
        <span v-else class="text-h6">{{ initials }}</span>
      </v-avatar>
      
      <div>
        <div class="text-subtitle-1 font-weight-bold">{{ name }}</div>
        <div class="text-caption" style="opacity: 0.8;">
          {{ statusText }}
        </div>
      </div>
    </v-app-bar-title>

    <template v-slot:append>
      <v-btn icon="mdi-magnify" color="white" variant="text" @click="$emit('search')" />
      <v-btn icon="mdi-dots-vertical" color="white" variant="text" @click="$emit('menu')" />
    </template>
  </v-app-bar>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { colors } from '../tokens';

interface Props {
  name: string;
  avatar?: string;
  online?: boolean;
  typing?: boolean;
  lastSeen?: number;
}

const props = withDefaults(defineProps<Props>(), {
  online: false,
  typing: false,
});

defineEmits<{
  search: [];
  menu: [];
}>();

const initials = computed(() => {
  return props.name
    .split(' ')
    .map(n => n.charAt(0))
    .slice(0, 2)
    .join('')
    .toUpperCase();
});

const statusText = computed(() => {
  if (props.typing) return 'digitando...';
  if (props.online) return 'online';
  if (props.lastSeen) {
    const date = new Date(props.lastSeen);
    return `visto por último ${date.toLocaleDateString('pt-BR')} às ${date.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}`;
  }
  return 'offline';
});
</script>

<template>
  <v-app-bar 
    :color="colors.primary" 
    elevation="1" 
    :style="{ borderBottom: `1px solid ${colors.primaryLight}` }"
    density="comfortable"
  >
    <div class="d-flex align-center w-100 px-2">
      <v-avatar :size="40" :color="colors.secondary" class="mr-3 flex-shrink-0">
        <v-img v-if="avatar" :src="avatar" />
        <span v-else class="text-h6">{{ initials }}</span>
      </v-avatar>
      
      <div class="header-info flex-grow-1">
        <div class="header-name text-white">{{ name }}</div>
        <div class="header-status text-white">
          {{ statusText }}
        </div>
      </div>

      <div class="d-flex align-center flex-shrink-0">
        <v-btn icon="mdi-magnify" color="white" variant="text" @click="$emit('search')" />
        
        <!-- Menu com opções -->
        <v-menu>
          <template v-slot:activator="{ props }">
            <v-btn icon="mdi-dots-vertical" color="white" variant="text" v-bind="props" />
          </template>
          
          <v-list>
            <v-list-item @click="$emit('wpp-connect')">
              <template v-slot:prepend>
                <v-icon>mdi-qrcode</v-icon>
              </template>
              <v-list-item-title>Conectar WhatsApp</v-list-item-title>
            </v-list-item>
            
            <v-list-item @click="$emit('logout')">
              <template v-slot:prepend>
                <v-icon>mdi-logout</v-icon>
              </template>
              <v-list-item-title>Sair</v-list-item-title>
            </v-list-item>
          </v-list>
        </v-menu>
      </div>
    </div>
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
  wppConnect: [];
  logout: [];
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

<style scoped>
.header-info {
  display: flex;
  flex-direction: column;
  min-width: 0;
  overflow: hidden;
}

.header-name {
  font-size: 1.063rem;
  font-weight: 600;
  line-height: 1.3;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%;
}

.header-status {
  font-size: 0.813rem;
  line-height: 1.2;
  opacity: 0.85;
  white-space: nowrap;
  overflow: visible;
  margin-top: 2px;
}
</style>
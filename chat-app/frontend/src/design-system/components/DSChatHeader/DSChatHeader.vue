<template>
  <v-app-bar
    class="ds-chat-header"
    :color="colors.primary"
    elevation="1"
    density="comfortable"
  >
    <div class="ds-chat-header__content">
      <v-btn
        v-if="showBackButton"
        icon="mdi-arrow-left"
        color="white"
        variant="text"
        class="ds-chat-header__back"
        @click="$emit('back')"
      />

      <v-avatar :size="40" :color="colors.secondary" class="ds-chat-header__avatar">
        <v-img v-if="avatar" :src="avatar" />
        <span v-else class="ds-chat-header__initials">{{ initials }}</span>
      </v-avatar>

      <div class="ds-chat-header__info">
        <div class="ds-chat-header__name">{{ name }}</div>
        <div class="ds-chat-header__status">{{ statusText }}</div>
      </div>

      <div class="ds-chat-header__actions">
        <v-btn icon="mdi-magnify" color="white" variant="text" @click="$emit('search')" />

        <v-menu>
          <template #activator="{ props }">
            <v-btn icon="mdi-dots-vertical" color="white" variant="text" v-bind="props" />
          </template>

          <v-list>
            <v-list-item @click="$emit('wppConnect')">
              <template #prepend>
                <v-icon>mdi-qrcode</v-icon>
              </template>
              <v-list-item-title>Conectar WhatsApp</v-list-item-title>
            </v-list-item>

            <v-list-item @click="$emit('logout')">
              <template #prepend>
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
import { colors } from '../../tokens';

interface Props {
  name: string;
  avatar?: string;
  online?: boolean;
  showBackButton?: boolean;
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
  back: [];
}>();

const initials = computed(() => {
  return props.name
    .split(' ')
    .map((segment) => segment.charAt(0))
    .slice(0, 2)
    .join('')
    .toUpperCase();
});

const statusText = computed(() => {
  if (props.typing) return 'digitando...';
  if (props.online) return 'online';
  if (props.lastSeen) {
    const date = new Date(props.lastSeen);
    const formattedDate = date.toLocaleDateString('pt-BR');
    const formattedTime = date.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
    return `visto por último ${formattedDate} às ${formattedTime}`;
  }
  return 'offline';
});
</script>

<style scoped lang="scss" src="./DSChatHeader.scss"></style>

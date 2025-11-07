<template>
  <div class="date-separator my-4">
    <v-divider />
    <v-chip
      size="small"
      variant="flat"
      color="grey-lighten-3"
      class="date-chip"
    >
      {{ formattedDate }}
    </v-chip>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';

interface Props {
  date: Date;
}

const props = defineProps<Props>();

const formattedDate = computed(() => {
  const now = new Date();
  const msgDate = new Date(props.date);
  
  // Zera horas para comparação de dias
  const nowDay = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const msgDay = new Date(msgDate.getFullYear(), msgDate.getMonth(), msgDate.getDate());
  
  const diffTime = nowDay.getTime() - msgDay.getTime();
  const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));
  
  if (diffDays === 0) return 'Hoje';
  if (diffDays === 1) return 'Ontem';
  if (diffDays < 7) {
    return msgDate.toLocaleDateString('pt-BR', { weekday: 'long' });
  }
  
  return msgDate.toLocaleDateString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric'
  });
});
</script>

<style scoped>
.date-separator {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 24px 0;
}

.date-chip {
  position: absolute;
  background: white;
  font-size: 12px;
  font-weight: 500;
  text-transform: capitalize;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12);
}
</style>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'

interface TimeSlot {
  start: string
  end: string
}

interface Props {
  agentKey: string
  userId: string
  customerEmail?: string
  customerPhone?: string
}

const props = defineProps<Props>()
const emit = defineEmits<{
  (e: 'slot-selected', data: { date: string, time: string, customerEmail: string, customerPhone?: string }): void
  (e: 'close'): void
}>()

const apiBaseUrl = import.meta.env.VITE_API_URL || 'http://localhost:3000'
const loading = ref(false)
const selectedDate = ref<Date>(new Date())
const availableSlots = ref<TimeSlot[]>([])
const selectedSlot = ref<string | null>(null)
const customerEmail = ref(props.customerEmail || '')
const showEmailInput = ref(!props.customerEmail)

// Datas disponíveis (próximos 14 dias úteis)
const availableDates = computed(() => {
  const dates: Date[] = []
  const today = new Date()
  let daysAdded = 0
  let currentDate = new Date(today)

  while (daysAdded < 14) {
    currentDate.setDate(currentDate.getDate() + 1)
    const dayOfWeek = currentDate.getDay()
    
    // Pula finais de semana
    if (dayOfWeek !== 0 && dayOfWeek !== 6) {
      dates.push(new Date(currentDate))
      daysAdded++
    }
  }

  return dates
})

// Formata data para exibição
function formatDate(date: Date): string {
  return date.toLocaleDateString('pt-BR', {
    weekday: 'short',
    day: '2-digit',
    month: 'short'
  })
}

// Formata data para API (YYYY-MM-DD)
function formatDateForAPI(date: Date): string {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

// Verifica se é a data selecionada
function isSelectedDate(date: Date): boolean {
  return formatDateForAPI(date) === formatDateForAPI(selectedDate.value)
}

// Seleciona data e busca horários
async function selectDate(date: Date) {
  selectedDate.value = date
  selectedSlot.value = null
  await loadAvailableSlots()
}

// Busca slots disponíveis para a data selecionada
import { useAuthStore } from '@/stores/auth'

async function loadAvailableSlots() {
  loading.value = true
  try {
    const token = useAuthStore().token
    const dateStr = formatDateForAPI(selectedDate.value)
    
    const url = new URL(`${apiBaseUrl}/calendar/available-slots`)
    url.searchParams.append('date', dateStr)
    url.searchParams.append('duration_minutes', '60')
    
    const response = await fetch(url.toString(), {
      headers: { 
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const data = await response.json()
    availableSlots.value = data.available_slots || []
  } catch (error) {
    console.error('Erro ao buscar slots:', error)
    availableSlots.value = []
  } finally {
    loading.value = false
  }
}

// Seleciona horário
function selectSlot(slot: TimeSlot) {
  selectedSlot.value = `${slot.start}-${slot.end}`
}

// Confirma agendamento
function confirmSchedule() {
  if (!selectedSlot.value || !customerEmail.value) return

  const [startTime] = selectedSlot.value.split('-')
  
  emit('slot-selected', {
    date: formatDateForAPI(selectedDate.value),
    time: startTime,
    customerEmail: customerEmail.value
    , customerPhone: props.customerPhone
  })
}

onMounted(() => {
  // Seleciona amanhã por padrão
  if (availableDates.value.length > 0) {
    selectDate(availableDates.value[0])
  }
})
</script>

<template>
  <v-card class="slot-picker" elevation="0">
    <v-card-title class="d-flex justify-space-between align-center bg-primary">
      <span class="text-white">📅 Selecione Data e Horário</span>
      <v-btn icon="mdi-close" variant="text" color="white" size="small" @click="emit('close')" />
    </v-card-title>

    <v-card-text class="pa-4">
      <!-- Email Input (se necessário) -->
      <v-expand-transition>
        <div v-if="showEmailInput" class="mb-4">
          <v-text-field
            v-model="customerEmail"
            label="Seu email"
            placeholder="seuemail@exemplo.com"
            variant="outlined"
            density="comfortable"
            prepend-inner-icon="mdi-email"
            :rules="[
              (v: string) => !!v || 'Email é obrigatório',
              (v: string) => /.+@.+\..+/.test(v) || 'Email inválido'
            ]"
          />
        </div>
      </v-expand-transition>

      <!-- Seletor de Datas -->
      <div class="mb-4">
        <div class="text-subtitle-2 mb-2">Escolha o dia:</div>
        <div class="date-scroll">
          <v-chip
            v-for="date in availableDates"
            :key="date.toISOString()"
            :color="isSelectedDate(date) ? 'primary' : 'default'"
            :variant="isSelectedDate(date) ? 'flat' : 'outlined'"
            class="ma-1"
            @click="selectDate(date)"
          >
            {{ formatDate(date) }}
          </v-chip>
        </div>
      </div>

      <!-- Horários Disponíveis -->
      <div>
        <div class="text-subtitle-2 mb-2">Horários disponíveis:</div>
        
        <v-progress-circular
          v-if="loading"
          indeterminate
          color="primary"
          class="mx-auto d-block"
        />

        <div v-else-if="availableSlots.length === 0" class="text-center pa-4 text-grey">
          <v-icon size="48">mdi-calendar-remove</v-icon>
          <p>Nenhum horário disponível neste dia</p>
          <p class="text-caption mb-2">Tente outra data ou selecione uma das opções abaixo:</p>
          <div class="fallback-chips">
            <v-chip
              v-for="(d, idx) in availableDates.slice(0, 3)"
              :key="d.toISOString()"
              color="secondary"
              variant="outlined"
              class="ma-1"
              @click="selectDate(d)"
            >
              {{ formatDate(d) }}
            </v-chip>
          </div>
          <p class="text-caption mt-2">Ou envie 2–3 horários que funcionem pra você — eu verifico e agendo.</p>
        </div>

        <div v-else class="time-slots">
          <v-chip
            v-for="slot in availableSlots"
            :key="`${slot.start}-${slot.end}`"
            :color="selectedSlot === `${slot.start}-${slot.end}` ? 'success' : 'default'"
            :variant="selectedSlot === `${slot.start}-${slot.end}` ? 'flat' : 'outlined'"
            class="ma-1 px-4"
            size="large"
            @click="selectSlot(slot)"
          >
            <v-icon start>mdi-clock-outline</v-icon>
            {{ slot.start }} - {{ slot.end }}
          </v-chip>
        </div>
      </div>
    </v-card-text>

    <v-divider />

    <v-card-actions class="pa-4">
      <v-btn variant="text" @click="emit('close')">
        Cancelar
      </v-btn>
      <v-spacer />
      <v-btn
        color="primary"
        variant="flat"
        :disabled="!selectedSlot || !customerEmail"
        @click="confirmSchedule"
      >
        <v-icon start>mdi-check</v-icon>
        Confirmar Agendamento
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<style scoped lang="scss">
.slot-picker {
  max-width: 600px;
  margin: 0 auto;
}

.date-scroll {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  max-height: 200px;
  overflow-y: auto;
  padding: 8px;
  border: 1px solid rgba(0, 0, 0, 0.12);
  border-radius: 8px;
}

.time-slots {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 8px;
  max-height: 300px;
  overflow-y: auto;
}

:deep(.v-chip) {
  cursor: pointer;
  transition: all 0.2s ease;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  }
}
</style>

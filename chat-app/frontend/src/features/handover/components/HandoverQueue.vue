<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import { useAuthStore } from '@/stores/auth'

interface HandoverRequest {
  id: string
  customer_id: string
  customer_name?: string
  customer_email?: string
  customer_phone?: string
  reason: string
  status: string
  priority: number
  last_messages: string[]
  context_summary?: string
  created_at: string
  assigned_agent?: string
  tags: string[]
}

const handovers = ref<HandoverRequest[]>([])
const loading = ref(false)
const selectedHandover = ref<HandoverRequest | null>(null)
const showDetails = ref(false)

// Filtros
const selectedStatus = ref<string>('pending')
const selectedPriority = ref<number | null>(null)

// Computed
const filteredHandovers = computed(() => {
  let filtered = handovers.value

  if (selectedStatus.value !== 'all') {
    filtered = filtered.filter(h => h.status === selectedStatus.value)
  }

  if (selectedPriority.value !== null) {
    filtered = filtered.filter(h => h.priority === selectedPriority.value)
  }

  // Ordena por prioridade (maior primeiro) e data (mais recente primeiro)
  return filtered.sort((a, b) => {
    if (a.priority !== b.priority) {
      return b.priority - a.priority
    }
    return new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  })
})

const statusCounts = computed(() => {
  return {
    pending: handovers.value.filter(h => h.status === 'pending').length,
    accepted: handovers.value.filter(h => h.status === 'accepted').length,
    in_progress: handovers.value.filter(h => h.status === 'in_progress').length,
    resolved: handovers.value.filter(h => h.status === 'resolved').length
  }
})

// Métodos
async function loadHandovers() {
  loading.value = true
  try {
    const token = useAuthStore().token
    const response = await axios.get(`${import.meta.env.VITE_API_URL}/handovers/`, {
      headers: { Authorization: `Bearer ${token}` },
      params: {
        status: selectedStatus.value === 'all' ? undefined : selectedStatus.value,
        priority: selectedPriority.value,
        limit: 50
      }
    })
    handovers.value = response.data
  } catch (error) {
    console.error('Erro ao carregar handovers:', error)
  } finally {
    loading.value = false
  }
}

async function acceptHandover(handover: HandoverRequest) {
  try {
    const token = useAuthStore().token
    const user = useAuthStore().user || { id: undefined, name: undefined, email: undefined }
    
    await axios.put(
      `${import.meta.env.VITE_API_URL}/handovers/${handover.id}/accept`,
      {
        agent_id: user.id,
        agent_name: user.name || user.email
      },
      { headers: { Authorization: `Bearer ${token}` } }
    )
    
    await loadHandovers()
  } catch (error) {
    console.error('Erro ao aceitar handover:', error)
  }
}

async function markInProgress(handover: HandoverRequest) {
  try {
    const token = useAuthStore().token
    await axios.put(
      `${import.meta.env.VITE_API_URL}/handovers/${handover.id}/in-progress`,
      {},
      { headers: { Authorization: `Bearer ${token}` } }
    )
    await loadHandovers()
  } catch (error) {
    console.error('Erro ao marcar em progresso:', error)
  }
}

async function resolveHandover(handover: HandoverRequest) {
  try {
    const token = useAuthStore().token
    await axios.put(
      `${import.meta.env.VITE_API_URL}/handovers/${handover.id}/resolve`,
      { resolution_notes: 'Resolvido pelo agente' },
      { headers: { Authorization: `Bearer ${token}` } }
    )
    await loadHandovers()
  } catch (error) {
    console.error('Erro ao resolver handover:', error)
  }
}

function viewDetails(handover: HandoverRequest) {
  selectedHandover.value = handover
  showDetails.value = true
}

function getPriorityColor(priority: number): string {
  const colors: Record<number, string> = {
    4: 'red-darken-1',
    3: 'orange-darken-1',
    2: 'yellow-darken-2',
    1: 'blue-grey'
  }
  return colors[priority] || 'grey'
}

function getPriorityLabel(priority: number): string {
  const labels: Record<number, string> = {
    4: 'Urgente',
    3: 'Alta',
    2: 'Média',
    1: 'Baixa'
  }
  return labels[priority] || 'Desconhecida'
}

function getReasonLabel(reason: string): string {
  const labels: Record<string, string> = {
    explicit_request: 'Solicitação explícita',
    low_confidence: 'Baixa confiança',
    complaint: 'Reclamação',
    complex_query: 'Consulta complexa',
    escalation: 'Escalação',
    technical_issue: 'Problema técnico',
    outside_hours: 'Fora do horário'
  }
  return labels[reason] || reason
}

function getStatusColor(status: string): string {
  const colors: Record<string, string> = {
    pending: 'orange',
    accepted: 'blue',
    in_progress: 'purple',
    resolved: 'green',
    cancelled: 'grey'
  }
  return colors[status] || 'grey'
}

function formatDate(dateStr: string): string {
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const minutes = Math.floor(diff / 60000)
  
  if (minutes < 1) return 'Agora'
  if (minutes < 60) return `${minutes}m atrás`
  
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}h atrás`
  
  const days = Math.floor(hours / 24)
  return `${days}d atrás`
}

onMounted(() => {
  loadHandovers()
  // Auto-refresh a cada 30 segundos
  setInterval(loadHandovers, 30000)
})
</script>

<template>
  <v-container fluid class="handover-queue">
    <v-row>
      <v-col cols="12">
        <div class="d-flex justify-space-between align-center mb-4">
          <h2 class="text-h4">🤝 Fila de Atendimentos</h2>
          <v-btn
            icon="mdi-refresh"
            variant="text"
            @click="loadHandovers"
            :loading="loading"
          />
        </div>
      </v-col>
    </v-row>

    <!-- Estatísticas -->
    <v-row class="mb-4">
      <v-col cols="12" sm="3">
        <v-card color="orange-lighten-5">
          <v-card-text>
            <div class="text-h5">{{ statusCounts.pending }}</div>
            <div class="text-caption">Pendentes</div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" sm="3">
        <v-card color="blue-lighten-5">
          <v-card-text>
            <div class="text-h5">{{ statusCounts.accepted }}</div>
            <div class="text-caption">Aceitos</div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" sm="3">
        <v-card color="purple-lighten-5">
          <v-card-text>
            <div class="text-h5">{{ statusCounts.in_progress }}</div>
            <div class="text-caption">Em Progresso</div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" sm="3">
        <v-card color="green-lighten-5">
          <v-card-text>
            <div class="text-h5">{{ statusCounts.resolved }}</div>
            <div class="text-caption">Resolvidos</div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Filtros -->
    <v-row class="mb-2">
      <v-col cols="12" sm="6">
        <v-btn-toggle
          v-model="selectedStatus"
          mandatory
          color="primary"
          @update:modelValue="loadHandovers"
        >
          <v-btn value="all">Todos</v-btn>
          <v-btn value="pending">Pendentes</v-btn>
          <v-btn value="accepted">Aceitos</v-btn>
          <v-btn value="in_progress">Em Progresso</v-btn>
        </v-btn-toggle>
      </v-col>
      <v-col cols="12" sm="6" class="text-right">
        <v-chip-group
          v-model="selectedPriority"
          filter
          :mandatory="false"
          @update:modelValue="loadHandovers"
        >
          <v-chip :value="null">Todas</v-chip>
          <v-chip :value="4" :color="getPriorityColor(4)">Urgente</v-chip>
          <v-chip :value="3" :color="getPriorityColor(3)">Alta</v-chip>
          <v-chip :value="2" :color="getPriorityColor(2)">Média</v-chip>
          <v-chip :value="1" :color="getPriorityColor(1)">Baixa</v-chip>
        </v-chip-group>
      </v-col>
    </v-row>

    <!-- Lista de handovers -->
    <v-row>
      <v-col cols="12">
        <v-card v-if="loading" class="pa-6 text-center">
          <v-progress-circular indeterminate color="primary" />
        </v-card>

        <v-card v-else-if="filteredHandovers.length === 0" class="pa-6 text-center">
          <v-icon size="64" color="grey-lighten-1">mdi-inbox</v-icon>
          <p class="text-grey mt-2">Nenhum atendimento encontrado</p>
        </v-card>

        <v-list v-else class="handover-list">
          <v-list-item
            v-for="handover in filteredHandovers"
            :key="handover.id"
            class="handover-item mb-2"
            border
            rounded
          >
            <template #prepend>
              <v-badge
                :color="getPriorityColor(handover.priority)"
                :content="getPriorityLabel(handover.priority)"
                inline
              />
            </template>

            <v-list-item-title class="font-weight-bold">
              {{ handover.customer_name || handover.customer_id }}
            </v-list-item-title>

            <v-list-item-subtitle>
              <v-chip
                size="small"
                :color="getStatusColor(handover.status)"
                class="mr-2"
              >
                {{ handover.status }}
              </v-chip>
              {{ getReasonLabel(handover.reason) }}
              <span class="text-caption ml-2">• {{ formatDate(handover.created_at) }}</span>
            </v-list-item-subtitle>

            <template v-if="handover.context_summary">
              <v-list-item-subtitle class="mt-2 text-caption">
                {{ handover.context_summary.substring(0, 120) }}...
              </v-list-item-subtitle>
            </template>

            <template #append>
              <div class="d-flex flex-column ga-2">
                <v-btn
                  v-if="handover.status === 'pending'"
                  size="small"
                  color="primary"
                  @click="acceptHandover(handover)"
                >
                  Aceitar
                </v-btn>
                <v-btn
                  v-if="handover.status === 'accepted'"
                  size="small"
                  color="purple"
                  @click="markInProgress(handover)"
                >
                  Iniciar
                </v-btn>
                <v-btn
                  v-if="handover.status === 'in_progress'"
                  size="small"
                  color="green"
                  @click="resolveHandover(handover)"
                >
                  Resolver
                </v-btn>
                <v-btn
                  size="small"
                  variant="outlined"
                  @click="viewDetails(handover)"
                >
                  Detalhes
                </v-btn>
              </div>
            </template>
          </v-list-item>
        </v-list>
      </v-col>
    </v-row>

    <!-- Dialog de Detalhes -->
    <v-dialog v-model="showDetails" max-width="800">
      <v-card v-if="selectedHandover">
        <v-card-title class="d-flex justify-space-between align-center">
          <span>Detalhes do Atendimento</span>
          <v-btn icon="mdi-close" variant="text" @click="showDetails = false" />
        </v-card-title>

        <v-divider />

        <v-card-text class="pa-4">
          <v-row>
            <v-col cols="12" sm="6">
              <div class="text-caption text-grey">Cliente</div>
              <div class="text-body-1">{{ selectedHandover.customer_name || 'Não informado' }}</div>
            </v-col>
            <v-col cols="12" sm="6">
              <div class="text-caption text-grey">Email</div>
              <div class="text-body-1">{{ selectedHandover.customer_email || 'Não informado' }}</div>
            </v-col>
            <v-col cols="12" sm="6">
              <div class="text-caption text-grey">Telefone</div>
              <div class="text-body-1">{{ selectedHandover.customer_phone || 'Não informado' }}</div>
            </v-col>
            <v-col cols="12" sm="6">
              <div class="text-caption text-grey">Prioridade</div>
              <v-chip :color="getPriorityColor(selectedHandover.priority)">
                {{ getPriorityLabel(selectedHandover.priority) }}
              </v-chip>
            </v-col>
            <v-col cols="12">
              <div class="text-caption text-grey">Motivo</div>
              <div class="text-body-1">{{ getReasonLabel(selectedHandover.reason) }}</div>
            </v-col>
            <v-col v-if="selectedHandover.context_summary" cols="12">
              <div class="text-caption text-grey">Resumo do Contexto</div>
              <div class="text-body-2">{{ selectedHandover.context_summary }}</div>
            </v-col>
            <v-col v-if="selectedHandover.last_messages.length > 0" cols="12">
              <div class="text-caption text-grey mb-2">Últimas Mensagens</div>
              <v-card variant="outlined" class="pa-3">
                <div
                  v-for="(msg, idx) in selectedHandover.last_messages"
                  :key="idx"
                  class="mb-2"
                >
                  <div class="text-caption">{{ msg }}</div>
                </div>
              </v-card>
            </v-col>
          </v-row>
        </v-card-text>

        <v-divider />

        <v-card-actions>
          <v-spacer />
          <v-btn color="grey" @click="showDetails = false">Fechar</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<style scoped lang="scss">
.handover-queue {
  max-width: 1400px;
  margin: 0 auto;
}

.handover-list {
  background: transparent;
}

.handover-item {
  background: white;
  transition: all 0.2s ease;
  
  &:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    transform: translateY(-2px);
  }
}
</style>

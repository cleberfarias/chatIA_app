<template>
  <div class="agents-view">
    <div class="agents-view__header">
      <div>
        <h1 class="text-h4">Agentes IA</h1>
        <p class="text-grey mt-2">Gerencie seus assistentes virtuais personalizados</p>
      </div>
      <v-btn color="primary" prepend-icon="mdi-robot-excited" @click="showCreatorDialog = true">
        Criar Novo Agente
      </v-btn>
    </div>

    <!-- Loading state -->
    <div v-if="loading" class="text-center py-12">
      <v-progress-circular indeterminate color="primary" size="64" />
      <p class="text-grey mt-4">Carregando agentes...</p>
    </div>

    <!-- Empty state -->
    <v-card v-else-if="agents.length === 0" class="text-center pa-12" elevation="0" variant="outlined">
      <v-icon icon="mdi-robot-confused" size="80" color="grey-lighten-1" class="mb-4" />
      <h2 class="text-h5 mb-2">Nenhum agente criado ainda</h2>
      <p class="text-grey mb-6">Crie seu primeiro agente IA para automatizar atendimentos</p>
      <v-btn color="primary" prepend-icon="mdi-plus" size="large" @click="showCreatorDialog = true">
        Criar Primeiro Agente
      </v-btn>
    </v-card>

    <!-- Agents Grid -->
    <v-row v-else>
      <v-col
        v-for="agent in agents"
        :key="agent.key"
        cols="12"
        sm="6"
        md="4"
      >
        <v-card class="agent-card" elevation="2" hover>
          <v-card-text>
            <!-- Header -->
            <div class="d-flex justify-space-between align-center mb-4">
              <div class="d-flex align-center gap-2">
                <v-avatar :color="getAgentColor(agent.key)" size="48">
                  <span class="text-h6">{{ agent.emoji || '🤖' }}</span>
                </v-avatar>
                <div>
                  <h3 class="text-h6 font-weight-bold">{{ agent.name }}</h3>
                  <v-chip size="x-small" :color="agent.active ? 'success' : 'grey'" variant="flat">
                    {{ agent.active ? 'Ativo' : 'Inativo' }}
                  </v-chip>
                </div>
              </div>
              
              <v-menu>
                <template #activator="{ props }">
                  <v-btn icon="mdi-dots-vertical" size="small" variant="text" v-bind="props" />
                </template>
                <v-list>
                  <v-list-item prepend-icon="mdi-pencil" title="Editar" @click="editAgent(agent)" />
                  <v-list-item prepend-icon="mdi-content-copy" title="Duplicar" @click="duplicateAgent(agent)" />
                  <v-list-item 
                    :prepend-icon="agent.active ? 'mdi-pause' : 'mdi-play'" 
                    :title="agent.active ? 'Desativar' : 'Ativar'"
                    @click="toggleAgent(agent)"
                  />
                  <v-divider />
                  <v-list-item 
                    prepend-icon="mdi-delete" 
                    title="Excluir"
                    color="error"
                    @click="confirmDelete(agent)"
                  />
                </v-list>
              </v-menu>
            </div>

            <!-- Descrição -->
            <p class="text-body-2 text-grey mb-4" style="min-height: 60px;">
              {{ agent.description || 'Sem descrição' }}
            </p>

            <!-- Estatísticas -->
            <v-row dense class="mb-4">
              <v-col cols="6">
                <div class="stat-box">
                  <v-icon icon="mdi-message-text" size="16" class="mr-1" />
                  <span class="text-caption">{{ agent.stats?.totalChats || 0 }} conversas</span>
                </div>
              </v-col>
              <v-col cols="6">
                <div class="stat-box">
                  <v-icon icon="mdi-chart-line" size="16" class="mr-1" />
                  <span class="text-caption">{{ agent.stats?.satisfaction || 95 }}% satisfação</span>
                </div>
              </v-col>
            </v-row>

            <!-- Tags -->
            <div class="d-flex flex-wrap gap-1 mb-3">
              <v-chip v-if="agent.model" size="x-small" variant="outlined">
                {{ agent.model }}
              </v-chip>
              <v-chip v-if="agent.hasCalendar" size="x-small" variant="outlined" prepend-icon="mdi-calendar">
                Agendamento
              </v-chip>
              <v-chip v-if="agent.temperature" size="x-small" variant="outlined">
                Temp: {{ agent.temperature }}
              </v-chip>
            </div>
          </v-card-text>

          <v-divider />

          <v-card-actions>
            <v-btn variant="text" prepend-icon="mdi-message" @click="chatWithAgent(agent)">
              Testar
            </v-btn>
            <v-spacer />
            <v-btn variant="text" icon="mdi-chart-bar" @click="viewStats(agent)" />
            <v-btn variant="text" icon="mdi-cog" @click="editAgent(agent)" />
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>

    <!-- Dialog de criação/edição -->
    <CustomBotCreator
      v-model="showCreatorDialog"
      @agent-created="onAgentCreated"
    />

    <!-- Dialog de confirmação de exclusão -->
    <v-dialog v-model="showDeleteDialog" max-width="400">
      <v-card>
        <v-card-title>Confirmar Exclusão</v-card-title>
        <v-card-text>
          Tem certeza que deseja excluir o agente <strong>{{ agentToDelete?.name }}</strong>?
          Esta ação não pode ser desfeita.
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn text @click="showDeleteDialog = false">Cancelar</v-btn>
          <v-btn color="error" @click="deleteAgent">Excluir</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Snackbar -->
    <v-snackbar v-model="showSnackbar" :color="snackbarColor" timeout="3000">
      {{ snackbarText }}
    </v-snackbar>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import CustomBotCreator from '@/features/agents/components/CustomBotCreator.vue'
import { useCustomBots } from '@/composables/useCustomBots'

interface Agent {
  key: string
  name: string
  emoji?: string
  description?: string
  model?: string
  temperature?: number
  active?: boolean
  hasCalendar?: boolean
  stats?: {
    totalChats: number
    satisfaction: number
  }
}

const router = useRouter()
const route = useRoute()
const { bots, refreshBots, deleteBot } = useCustomBots()

// Estado
const loading = ref(false)
const agents = ref<Agent[]>([])
const showCreatorDialog = ref(false)
const showDeleteDialog = ref(false)
const agentToDelete = ref<Agent | null>(null)
const showSnackbar = ref(false)
const snackbarText = ref('')
const snackbarColor = ref('success')

// Watch para abrir modal de edição quando vem da query string
watch(() => route.query.edit, (agentKey) => {
  if (agentKey && agents.value.length > 0) {
    const agent = agents.value.find(a => a.key === agentKey)
    if (agent) {
      editAgent(agent)
      // Limpa query string
      router.replace({ query: {} })
    }
  }
}, { immediate: true })

// Carrega agentes
const loadAgents = async () => {
  loading.value = true
  try {
    await refreshBots()
    // Mapeia bots para agents com dados mockados de stats
    agents.value = bots.value.map((bot: any) => ({
      key: bot.key,
      name: bot.name,
      emoji: bot.emoji,
      description: bot.systemPrompt?.slice(0, 100) + '...' || 'Agente personalizado',
      model: bot.model || 'gpt-4o-mini',
      temperature: bot.temperature,
      active: true, // TODO: adicionar campo active no backend
      hasCalendar: bot.useCalendar,
      stats: {
        totalChats: Math.floor(Math.random() * 100),
        satisfaction: 90 + Math.floor(Math.random() * 10),
      }
    }))
  } catch (error) {
    console.error('Erro ao carregar agentes:', error)
    snackbarText.value = 'Erro ao carregar agentes'
    snackbarColor.value = 'error'
    showSnackbar.value = true
  } finally {
    loading.value = false
  }
}

// Ações
const editAgent = (_agent: Agent) => {
  // TODO: Implementar edição de agente
  snackbarText.value = 'Edição de agente em desenvolvimento'
  snackbarColor.value = 'info'
  showSnackbar.value = true
}

const duplicateAgent = (_agent: Agent) => {
  // TODO: Implementar duplicação de agente
  snackbarText.value = 'Duplicação de agente em desenvolvimento'
  snackbarColor.value = 'info'
  showSnackbar.value = true
}

const toggleAgent = (agent: Agent) => {
  agent.active = !agent.active
  snackbarText.value = `Agente ${agent.active ? 'ativado' : 'desativado'} com sucesso`
  snackbarColor.value = 'success'
  showSnackbar.value = true
}

const confirmDelete = (agent: Agent) => {
  agentToDelete.value = agent
  showDeleteDialog.value = true
}

const deleteAgent = async () => {
  if (!agentToDelete.value) return
  
  try {
    await deleteBot(agentToDelete.value.key)
    await loadAgents()
    snackbarText.value = 'Agente excluído com sucesso'
    snackbarColor.value = 'success'
  } catch (error) {
    console.error('Erro ao excluir agente:', error)
    snackbarText.value = 'Erro ao excluir agente'
    snackbarColor.value = 'error'
  } finally {
    showSnackbar.value = true
    showDeleteDialog.value = false
    agentToDelete.value = null
  }
}

const chatWithAgent = (agent: Agent) => {
  // Abre chat com o agente
  router.push(`/chat?agent=${agent.key}`)
}

const viewStats = (_agent: Agent) => {
  // TODO: navegar para página de estatísticas do agente
  snackbarText.value = 'Estatísticas do agente em desenvolvimento'
  snackbarColor.value = 'info'
  showSnackbar.value = true
}

const onAgentCreated = async (agent: any) => {
  await loadAgents()
  snackbarText.value = `Agente ${agent.name} criado com sucesso!`
  snackbarColor.value = 'success'
  showSnackbar.value = true
  showCreatorDialog.value = false
}

const getAgentColor = (key: string) => {
  const colors = ['primary', 'success', 'info', 'warning', 'error', 'purple', 'indigo']
  const index = key.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0)
  return colors[index % colors.length]
}

onMounted(async () => {
  await loadAgents()
  
  // Se veio com query param de edição, abre o modal
  const agentKey = route.query.edit
  if (agentKey && agents.value.length > 0) {
    const agent = agents.value.find(a => a.key === agentKey)
    if (agent) {
      editAgent(agent)
      router.replace({ query: {} })
    }
  }
})
</script>

<style scoped lang="scss">
@import '@/design-system/styles/foundations.scss';
@import '@/design-system/styles/crm-mixins.scss';

.agents-view {
  @include crm-page-padding;
  max-width: 1400px;
  margin: 0 auto;
  
  &__header {
    @include crm-page-header;
  }
}

.agent-card {
  @include crm-card;
  height: 100%;
}

.stat-box {
  display: flex;
  align-items: center;
  padding: var(--ds-spacing-sm);
  background-color: var(--ds-color-input-background);
  border-radius: var(--ds-radius-sm);
}
</style>

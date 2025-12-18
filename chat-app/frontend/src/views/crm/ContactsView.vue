<template>
  <div class="contacts-view">
    <div class="contacts-view__header">
      <h1 class="text-h4">Contatos</h1>
      <v-btn color="primary" prepend-icon="mdi-plus">
        Novo Contato
      </v-btn>
    </div>

    <div class="contacts-view__content">
      <!-- Barra de busca e filtros -->
      <v-card class="mb-4" elevation="0" variant="outlined">
        <v-card-text>
          <v-row>
            <v-col cols="12" md="6">
              <v-text-field
                v-model="searchQuery"
                prepend-inner-icon="mdi-magnify"
                label="Buscar contatos"
                variant="outlined"
                density="compact"
                hide-details
                clearable
              />
            </v-col>
            <v-col cols="12" md="3">
              <v-select
                v-model="filterStatus"
                :items="statusOptions"
                label="Status"
                variant="outlined"
                density="compact"
                hide-details
              />
            </v-col>
            <v-col cols="12" md="3">
              <v-select
                v-model="filterSegment"
                :items="segmentOptions"
                label="Segmento"
                variant="outlined"
                density="compact"
                hide-details
              />
            </v-col>
          </v-row>
        </v-card-text>
      </v-card>

      <!-- Lista de contatos -->
      <v-card elevation="0" variant="outlined">
        <v-data-table
          :headers="headers"
          :items="contacts"
          :search="searchQuery"
          :loading="loading"
          class="contacts-table"
        >
          <template #item.name="{ item }">
            <div class="d-flex align-center gap-2">
              <v-avatar :color="item.avatarColor" size="32">
                <span class="text-white">{{ getInitials(item.name) }}</span>
              </v-avatar>
              <div>
                <div class="font-weight-medium">{{ item.name }}</div>
                <div class="text-caption text-grey">{{ item.email }}</div>
              </div>
            </div>
          </template>

          <template #item.status="{ item }">
            <v-chip :color="getStatusColor(item.status)" size="small" variant="flat">
              {{ item.status }}
            </v-chip>
          </template>

          <template #item.actions="{ item: _item }">
            <v-btn icon="mdi-pencil" size="small" variant="text" />
            <v-btn icon="mdi-eye" size="small" variant="text" />
            <v-btn icon="mdi-delete" size="small" variant="text" color="error" />
          </template>
        </v-data-table>
      </v-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

// Estado
const searchQuery = ref('')
const filterStatus = ref('Todos')
const filterSegment = ref('Todos')
const loading = ref(false)

// Opções de filtro
const statusOptions = ['Todos', 'Ativo', 'Inativo', 'Lead', 'Cliente']
const segmentOptions = ['Todos', 'Varejo', 'Atacado', 'Serviços', 'Indústria']

// Headers da tabela
const headers = [
  { title: 'Nome', key: 'name', sortable: true },
  { title: 'Telefone', key: 'phone', sortable: true },
  { title: 'Empresa', key: 'company', sortable: true },
  { title: 'Status', key: 'status', sortable: true },
  { title: 'Última interação', key: 'lastInteraction', sortable: true },
  { title: 'Ações', key: 'actions', sortable: false, align: 'end' as const },
]

// Dados mockados
const contacts = ref([
  {
    id: 1,
    name: 'João Silva',
    email: 'joao@empresa.com',
    phone: '(11) 98765-4321',
    company: 'Empresa XYZ',
    status: 'Cliente',
    lastInteraction: '2 dias atrás',
    avatarColor: 'primary',
  },
  {
    id: 2,
    name: 'Maria Santos',
    email: 'maria@tech.com',
    phone: '(21) 91234-5678',
    company: 'Tech Solutions',
    status: 'Lead',
    lastInteraction: '1 semana atrás',
    avatarColor: 'success',
  },
  {
    id: 3,
    name: 'Pedro Costa',
    email: 'pedro@startup.io',
    phone: '(11) 99999-8888',
    company: 'StartupCo',
    status: 'Ativo',
    lastInteraction: 'Hoje',
    avatarColor: 'warning',
  },
])

// Helpers
const getInitials = (name: string) => {
  return name
    .split(' ')
    .map(n => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2)
}

const getStatusColor = (status: string) => {
  const colors: Record<string, string> = {
    'Cliente': 'success',
    'Lead': 'warning',
    'Ativo': 'info',
    'Inativo': 'grey',
  }
  return colors[status] || 'grey'
}
</script>

<style scoped lang="scss">
@import '@/design-system/styles/foundations.scss';
@import '@/design-system/styles/crm-mixins.scss';

.contacts-view {
  @include crm-page-padding;
  max-width: 1400px;
  margin: 0 auto;
  
  &__header {
    @include crm-page-header;
  }

  &__content {
    width: 100%;
  }
}

.contacts-table {
  :deep(.v-data-table__td) {
    padding: var(--ds-spacing-md) var(--ds-spacing-lg);
  }
}
</style>

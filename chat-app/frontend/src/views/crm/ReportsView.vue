<template>
  <div class="reports-view">
    <div class="reports-view__header">
      <h1 class="text-h4">Relatórios</h1>
      <v-btn color="primary" prepend-icon="mdi-plus">
        Novo Relatório
      </v-btn>
    </div>

    <!-- Filtros -->
    <v-card class="mb-6" elevation="0" variant="outlined">
      <v-card-text>
        <v-row>
          <v-col cols="12" md="3">
            <v-select
              v-model="filterType"
              :items="reportTypes"
              label="Tipo de Relatório"
              variant="outlined"
              density="compact"
              hide-details
            />
          </v-col>
          <v-col cols="12" md="3">
            <v-select
              v-model="filterPeriod"
              :items="['Hoje', 'Esta semana', 'Este mês', 'Últimos 3 meses', 'Este ano']"
              label="Período"
              variant="outlined"
              density="compact"
              hide-details
            />
          </v-col>
          <v-col cols="12" md="3">
            <v-select
              v-model="filterFormat"
              :items="['PDF', 'Excel', 'CSV']"
              label="Formato"
              variant="outlined"
              density="compact"
              hide-details
            />
          </v-col>
          <v-col cols="12" md="3">
            <v-btn block color="primary" height="40">
              Gerar Relatório
            </v-btn>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>

    <!-- Relatórios disponíveis -->
    <v-row>
      <v-col
        v-for="report in availableReports"
        :key="report.id"
        cols="12"
        sm="6"
        md="4"
      >
        <v-card elevation="2" hover class="report-card">
          <v-card-text>
            <div class="d-flex justify-space-between align-center mb-3">
              <v-avatar :color="report.color" size="56">
                <v-icon :icon="report.icon" size="32" color="white" />
              </v-avatar>
              <v-chip :color="report.color" size="small" variant="flat">
                {{ report.category }}
              </v-chip>
            </div>

            <h3 class="text-h6 font-weight-bold mb-2">{{ report.title }}</h3>
            <p class="text-body-2 text-grey mb-4">{{ report.description }}</p>

            <v-divider class="my-3" />

            <div class="d-flex justify-space-between align-center">
              <span class="text-caption text-grey">
                Última atualização: {{ report.lastUpdated }}
              </span>
              <v-btn-group density="compact" variant="outlined">
                <v-btn icon="mdi-eye" size="small" />
                <v-btn icon="mdi-download" size="small" />
              </v-btn-group>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Relatórios recentes -->
    <v-card class="mt-6" elevation="2">
      <v-card-title>Relatórios Recentes</v-card-title>
      <v-data-table
        :headers="headers"
        :items="recentReports"
        :items-per-page="5"
        class="reports-table"
      >
        <template #item.name="{ item }">
          <div class="d-flex align-center gap-2">
            <v-icon :icon="getReportIcon(item.type)" :color="getReportColor(item.type)" />
            <span class="font-weight-medium">{{ item.name }}</span>
          </div>
        </template>

        <template #item.status="{ item }">
          <v-chip :color="getStatusColor(item.status)" size="small" variant="flat">
            {{ item.status }}
          </v-chip>
        </template>

        <template #item.actions>
          <v-btn icon="mdi-download" size="small" variant="text" color="primary" />
          <v-btn icon="mdi-share-variant" size="small" variant="text" />
          <v-btn icon="mdi-delete" size="small" variant="text" color="error" />
        </template>
      </v-data-table>
    </v-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

// Filtros
const filterType = ref('Todos')
const filterPeriod = ref('Este mês')
const filterFormat = ref('PDF')

const reportTypes = [
  'Todos',
  'Atendimento',
  'Vendas',
  'Marketing',
  'Financeiro',
  'Operacional',
]

// Relatórios disponíveis
const availableReports = ref([
  {
    id: 1,
    title: 'Performance de Atendimento',
    description: 'Análise detalhada de métricas de atendimento ao cliente',
    category: 'Atendimento',
    icon: 'mdi-headset',
    color: 'primary',
    lastUpdated: 'Há 2 horas',
  },
  {
    id: 2,
    title: 'Funil de Vendas',
    description: 'Evolução do pipeline de vendas e taxa de conversão',
    category: 'Vendas',
    icon: 'mdi-chart-line',
    color: 'success',
    lastUpdated: 'Hoje',
  },
  {
    id: 3,
    title: 'ROI de Campanhas',
    description: 'Retorno sobre investimento das campanhas de marketing',
    category: 'Marketing',
    icon: 'mdi-chart-arc',
    color: 'warning',
    lastUpdated: 'Ontem',
  },
  {
    id: 4,
    title: 'Receita Mensal',
    description: 'Análise financeira de receitas e despesas do período',
    category: 'Financeiro',
    icon: 'mdi-currency-usd',
    color: 'info',
    lastUpdated: 'Há 3 dias',
  },
  {
    id: 5,
    title: 'Satisfação do Cliente',
    description: 'Índices de NPS e feedback dos clientes',
    category: 'Atendimento',
    icon: 'mdi-heart',
    color: 'error',
    lastUpdated: 'Há 1 semana',
  },
  {
    id: 6,
    title: 'Produtividade da Equipe',
    description: 'Métricas de performance individual e por equipe',
    category: 'Operacional',
    icon: 'mdi-account-group',
    color: 'purple',
    lastUpdated: 'Há 2 dias',
  },
])

// Tabela de relatórios recentes
const headers = [
  { title: 'Nome', key: 'name', sortable: true },
  { title: 'Tipo', key: 'type', sortable: true },
  { title: 'Período', key: 'period', sortable: true },
  { title: 'Gerado em', key: 'createdAt', sortable: true },
  { title: 'Status', key: 'status', sortable: true },
  { title: 'Ações', key: 'actions', sortable: false, align: 'end' as const },
]

const recentReports = ref([
  {
    id: 1,
    name: 'Relatório Mensal - Novembro',
    type: 'Atendimento',
    period: 'Novembro 2025',
    createdAt: '15/12/2025',
    status: 'Concluído',
  },
  {
    id: 2,
    name: 'Análise de Vendas Q4',
    type: 'Vendas',
    period: 'Out-Dez 2025',
    createdAt: '10/12/2025',
    status: 'Concluído',
  },
  {
    id: 3,
    name: 'Performance Semanal',
    type: 'Operacional',
    period: '10-16 Dez',
    createdAt: '17/12/2025',
    status: 'Processando',
  },
])

// Helpers
const getReportIcon = (type: string) => {
  const icons: Record<string, string> = {
    'Atendimento': 'mdi-headset',
    'Vendas': 'mdi-cart',
    'Marketing': 'mdi-bullhorn',
    'Financeiro': 'mdi-currency-usd',
    'Operacional': 'mdi-cog',
  }
  return icons[type] || 'mdi-file-document'
}

const getReportColor = (type: string) => {
  const colors: Record<string, string> = {
    'Atendimento': 'primary',
    'Vendas': 'success',
    'Marketing': 'warning',
    'Financeiro': 'info',
    'Operacional': 'purple',
  }
  return colors[type] || 'grey'
}

const getStatusColor = (status: string) => {
  const colors: Record<string, string> = {
    'Concluído': 'success',
    'Processando': 'warning',
    'Erro': 'error',
  }
  return colors[status] || 'grey'
}
</script>

<style scoped lang="scss">
@import '@/design-system/styles/foundations.scss';
@import '@/design-system/styles/crm-mixins.scss';

.reports-view {
  @include crm-page-padding;
  max-width: 1400px;
  margin: 0 auto;
  
  &__header {
    @include crm-page-header;
  }
}

.report-card {
  @include crm-card;
  height: 100%;
}

.reports-table {
  :deep(.v-data-table__td) {
    padding: var(--ds-spacing-md) var(--ds-spacing-lg);
  }
}
</style>

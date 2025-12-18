<template>
  <div class="ds-navbar">
    <!-- Desktop: Navigation Drawer Retrátil (Rail Mode) -->
    <v-navigation-drawer
      v-if="isDesktop"
      model-value
      permanent
      rail
      expand-on-hover
      class="ds-navbar__drawer"
      width="200"
      rail-width="72"
    >
      <!-- Header -->
      <div v-if="showHeader" class="ds-navbar__header">
        <v-icon icon="mdi-chat" size="32" class="ds-navbar__logo" />
        
      </div>

      <!-- Menu Items -->
      <v-list density="compact" nav class="ds-navbar__list">
        <template v-for="item in items" :key="item.id">
          <!-- Item com subitems (grupo expansível) -->
          <v-list-group v-if="item.children && item.children.length > 0" :value="item.id">
            <template #activator="{ props: activatorProps }">
              <v-list-item
                v-bind="activatorProps"
                :prepend-icon="`mdi-${item.icon}`"
                :title="item.title"
                class="ds-navbar__item"
                rounded="xl"
              >
                <template v-if="item.badge" #append>
                  <v-badge
                    :content="item.badge"
                    :color="item.badgeColor || 'error'"
                    inline
                  />
                </template>
              </v-list-item>
            </template>

            <!-- Subitems (Agentes) -->
            <v-list-item
              v-for="child in item.children"
              :key="child.id"
              :to="child.to"
              :title="child.title"
              class="ds-navbar__subitem"
              rounded="xl"
            >
              <template #prepend>
                <span class="subitem-emoji">{{ child.icon }}</span>
              </template>
            </v-list-item>
          </v-list-group>

          <!-- Item simples (sem subitems) -->
          <v-list-item
            v-else
            :to="item.to"
            :prepend-icon="`mdi-${item.icon}`"
            :title="item.title"
            :value="item.id"
            class="ds-navbar__item"
            rounded="xl"
          >
            <template v-if="item.badge" #append>
              <v-badge
                :content="item.badge"
                :color="item.badgeColor || 'error'"
                inline
              />
            </template>
          </v-list-item>
        </template>
      </v-list>

      <!-- Footer (opcional para configurações, perfil, etc) -->
      <template #append>
        <div class="ds-navbar__footer">
          <v-divider class="mb-2" />
          <v-list-item
            prepend-icon="mdi-cog"
            title="Configurações"
            to="/configuracoes"
            rounded="xl"
          />
          <v-list-item @click="handleLogout">
            <template v-slot:prepend>
              <v-icon>mdi-logout</v-icon>
            </template>
            <v-list-item-title>Sair</v-list-item-title>
          </v-list-item>
        </div>
      </template>
    </v-navigation-drawer>

    <!-- Mobile: Bottom Navigation -->
    <v-bottom-navigation
      v-if="isMobile"
      v-model="selectedItem"
      class="ds-navbar__bottom"
      grow
      bg-color="surface"
    >
      <v-btn
        v-for="item in mainItems"
        :key="item.id"
        :value="item.id"
        :to="item.to"
        class="ds-navbar__bottom-btn"
      >
        <v-badge
          v-if="item.badge"
          :content="item.badge"
          :color="item.badgeColor || 'error'"
          offset-x="-5"
          offset-y="5"
        >
          <v-icon :icon="`mdi-${item.icon}`" />
        </v-badge>
        <v-icon v-else :icon="`mdi-${item.icon}`" />
        <span class="text-caption">{{ item.title }}</span>
      </v-btn>
    </v-bottom-navigation>

    <!-- Toggle Button para Mobile -->
    <v-btn
      v-if="isMobile && !isDesktop"
      icon="mdi-menu"
      class="ds-navbar__toggle"
      position="fixed"
      location="top left"
      @click="drawer = !drawer"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useDisplay } from 'vuetify'
import { useAuthStore } from '@/stores/auth'
import type { DSNavBarProps } from './types'

const props = withDefaults(defineProps<DSNavBarProps>(), {
  showHeader: true,
  headerTitle: 'Chat CRM',
})

const router = useRouter()
const { mobile, mdAndUp } = useDisplay()

// Estado do drawer
const drawer = ref(true)
const selectedItem = ref<string>('')

// Responsividade
const isMobile = computed(() => mobile.value)
const isDesktop = computed(() => mdAndUp.value)

// Items principais para bottom navigation (apenas 4-5 principais)
const mainItems = computed(() => {
  // Em mobile, mostra apenas os 5 primeiros itens mais importantes
  return props.items.slice(0, 5)
})

// Logout handler
const handleLogout = async () => {
  // Limpa estado de autenticação (store + storage)
  try {
    const auth = useAuthStore()
    auth.logout()
  } catch (e) {
    // fallback: remove chaves diretamente
    localStorage.removeItem('token')
    localStorage.removeItem('userId')
  }

  // Redireciona para login sem forçar reload
  // Usamos replace para não deixar histórico de sessão
  try {
    await router.replace('/login')
  } catch {
    // Fallback para navegação global se router falhar
    window.location.href = '/login'
  }
}

// Sincroniza item selecionado com rota atual
const syncSelectedItem = () => {
  if (!router || !router.currentRoute) return
  const currentPath = router.currentRoute.value.path
  const item = props.items.find(i => i.to === currentPath)
  if (item) {
    selectedItem.value = item.id
  }
}

onMounted(() => {
  syncSelectedItem()
  if (router && router.afterEach) {
    router.afterEach(syncSelectedItem)
  }
})
</script>

<style scoped lang="scss">
@import '@/design-system/styles/foundations.scss';

.ds-navbar {
  &__drawer {
    background: #f5f5f5 !important;
    border-right: 1px solid #e0e0e0;
    
    // Quando está em modo rail (retraído), oculta apenas o texto
    &.v-navigation-drawer--rail:not(:hover) {
      :deep(.v-list-item__content) {
        opacity: 0;
        width: 0;
      }
      
      :deep(.v-list-item-title) {
        opacity: 0;
        width: 0;
      }
      
      :deep(.v-list-group__items) {
        display: none;
      }
      
      :deep(.v-badge) {
        opacity: 0;
      }
      
      :deep(.ds-navbar__title) {
        opacity: 0;
        width: 0;
      }
      
      :deep(.v-list-group__header .v-list-item__append) {
        display: none;
      }
    }
  }

  &__header {
    display: flex;
    align-items: center;
    gap: var(--ds-spacing-md);
    padding: var(--ds-spacing-xxl) var(--ds-spacing-lg);
    border-bottom: 1px solid #e0e0e0;
    background: #ffffff;
  }

  &__logo {
    color: var(--ds-color-primary);
  }

  &__title {
    font-size: 20px;
    font-weight: 600;
    color: var(--ds-color-primary);
    margin: 0;
  }

  &__list {
    padding: var(--ds-spacing-md) var(--ds-spacing-sm);
  }

  &__item {
    margin-bottom: var(--ds-spacing-xs);
    border-radius: 12px;
    
    &:hover {
      background-color: rgba(var(--v-theme-primary-rgb), 0.12) !important;
    }

    &.v-list-item--active {
      background-color: rgba(var(--v-theme-primary-rgb), 0.15) !important;
      color: var(--ds-color-primary);
      
      .v-icon {
        color: var(--ds-color-primary);
      }
    }
  }

  &__subitem {
    padding-left: var(--ds-spacing-xxxl) !important;
    margin-bottom: var(--ds-spacing-xs);
    border-radius: 12px;
    
    &:hover {
      background-color: rgba(var(--v-theme-primary-rgb), 0.10) !important;
    }

    &.v-list-item--active {
      background-color: rgba(var(--v-theme-primary-rgb), 0.15) !important;
      color: var(--ds-color-primary);
    }

    .subitem-emoji {
      font-size: 20px;
      margin-right: var(--ds-spacing-sm);
    }
  }

  &__footer {
    padding: var(--ds-spacing-sm);
  }

  &__bottom {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    z-index: 1000;
    border-top: 1px solid rgba(var(--v-theme-on-surface-rgb), 0.12);
    background: rgb(var(--v-theme-surface)) !important;
    box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.1);
  }

  &__bottom-btn {
    .v-icon {
      margin-bottom: var(--ds-spacing-xs);
    }
  }

  &__toggle {
    position: fixed;
    top: var(--ds-spacing-lg);
    left: var(--ds-spacing-lg);
    z-index: 1001;
    background-color: var(--ds-color-primary);
    color: white;

    &:hover {
      background-color: var(--ds-color-primary-light);
    }
  }
}

// Ajusta padding do conteúdo principal em mobile para não ficar atrás da bottom nav
@media (max-width: 960px) {
  .v-main {
    padding-bottom: 56px !important;
  }
}
</style>

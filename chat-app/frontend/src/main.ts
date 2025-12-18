import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'
import { useAuthStore } from './stores/auth'

// Design System
import './design-system/styles/foundations.scss'
import './design-system/styles/utilities.scss'

// Animate.css
import 'animate.css'

// Vuetify
import 'vuetify/styles'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import '@mdi/font/css/materialdesignicons.css'
import './design-system/styles/foundations.scss'
import './design-system/styles/utilities.scss'

// Views
import ChatLayoutView from './views/ChatLayoutView.vue';
import LoginView from './views/LoginView.vue';

// CRM Views
import ContactsView from './views/crm/ContactsView.vue';
import CRMView from './views/crm/CRMView.vue';
import GroupsView from './views/crm/GroupsView.vue';
import AnalyticsView from './views/crm/AnalyticsView.vue';
import ReportsView from './views/crm/ReportsView.vue';
import AgentsView from './views/crm/AgentsView.vue';

const vuetify = createVuetify({
  components,
  directives,
  icons: {
    defaultSet: 'mdi',
  },
  theme: {
    defaultTheme: 'light',
    themes: {
      light: {
        colors: {
          primary: '#1976D2',
          secondary: '#424242',
          accent: '#82B1FF',
          error: '#FF5252',
          info: '#2196F3',
          success: '#4CAF50',
          warning: '#FB8C00',
          background: '#e5ddd5',
          surface: '#ffffff',
        },
      },
    },
  },
})
const pinia = createPinia()
const router = createRouter({
  history: createWebHistory(),
  routes: [
    { 
      path: '/', 
      redirect: '/crm',
      meta: { requiresAuth: true }
    },
    { 
      path: '/chat', 
      component: ChatLayoutView,
      meta: { requiresAuth: true }
    },
    { 
      path: '/login', 
      component: LoginView 
    },
    // Rotas CRM
    {
      path: '/contatos',
      component: ContactsView,
      meta: { requiresAuth: true }
    },
    {
      path: '/bots',
      component: AgentsView,
      meta: { requiresAuth: true }
    },
    {
      path: '/crm',
      component: CRMView,
      meta: { requiresAuth: true }
    },
    {
      path: '/grupos',
      component: GroupsView,
      meta: { requiresAuth: true }
    },
    {
      path: '/analytics',
      component: AnalyticsView,
      meta: { requiresAuth: true }
    },
    {
      path: '/relatorios',
      component: ReportsView,
      meta: { requiresAuth: true }
    }
  ]
})

// Guarda de rota para autenticação
router.beforeEach((to, _from, next) => {
  const authStore = useAuthStore()
  authStore.load() // Garante que o token está carregado
  
  if (to.meta.requiresAuth && !authStore.token) {
    next('/login')
  } else if (to.path === '/login' && authStore.token) {
    next('/')
  } else {
    next()
  }
})

const app = createApp(App)
app.use(pinia)
app.use(router)
app.use(vuetify)

app.mount('#app')

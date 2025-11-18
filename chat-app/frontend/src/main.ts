import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'
import { useAuthStore } from './stores/auth'

// Vuetify
import 'vuetify/styles'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import '@mdi/font/css/materialdesignicons.css'

// Views
import ChatLayoutView from './views/ChatLayoutView.vue';
import LoginView from './views/LoginView.vue';

const vuetify = createVuetify({
  components,
  directives,
  icons: {
    defaultSet: 'mdi',
  },
})
const pinia = createPinia()
const router = createRouter({
  history: createWebHistory(),
  routes: [
    { 
      path: '/', 
      component: ChatLayoutView,
      meta: { requiresAuth: true }
    },
    { 
      path: '/login', 
      component: LoginView 
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

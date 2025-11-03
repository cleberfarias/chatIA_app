import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'

// Vuetify
import 'vuetify/styles'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import '@mdi/font/css/materialdesignicons.css'

// Views
import ChatView from './views/ChatView.vue';

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
  routes: [{ path: '/', component: ChatView }]
})

createApp(App).use(pinia).use(router).use(vuetify).mount('#app')

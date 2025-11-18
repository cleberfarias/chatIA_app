<template>
  <!-- Loading inicial -->
  <div v-if="!isReady" class="loading-container">
    <v-progress-circular indeterminate size="48" color="primary" />
    <p class="mt-4 text-grey">Carregando...</p>
  </div>

  <!-- Layout principal -->
  <div v-else class="chat-layout" :class="{ 'has-contact': !!selectedContact }">
    <!-- Header Global (sempre visível) -->
    <v-app-bar 
      color="primary" 
      elevation="1" 
      density="comfortable"
      class="global-header"
    >
      <div class="d-flex align-center w-100 px-2">
        <!-- Botão voltar (apenas mobile quando contato selecionado) -->
        <v-btn 
          v-if="selectedContact"
          icon="mdi-arrow-left" 
          color="white" 
          variant="text" 
          class="mr-2 mobile-only"
          @click="contactsStore.unselectContact()"
        />
        
        <v-avatar color="secondary" size="40" class="mr-3">
          <span class="text-h6">{{ userInitials }}</span>
        </v-avatar>
        
        <div class="header-info flex-grow-1">
          <div class="header-name text-white">{{ authStore.user?.name || 'Usuário' }}</div>
          <div class="header-status text-white">online</div>
        </div>

        <div class="d-flex align-center flex-shrink-0">
          <v-btn icon="mdi-magnify" color="white" variant="text" />
          
          <v-menu>
            <template v-slot:activator="{ props }">
              <v-btn icon="mdi-dots-vertical" color="white" variant="text" v-bind="props" />
            </template>
            
            <v-list>
              <v-list-item @click="showWppConnect = true">
                <template v-slot:prepend>
                  <v-icon>mdi-whatsapp</v-icon>
                </template>
                <v-list-item-title>Conectar WhatsApp</v-list-item-title>
              </v-list-item>
              
              <v-list-item @click="handleLogout">
                <template v-slot:prepend>
                  <v-icon>mdi-logout</v-icon>
                </template>
                <v-list-item-title>Sair</v-list-item-title>
              </v-list-item>
            </v-list>
          </v-menu>
        </div>
      </div>
    </v-app-bar>

    <!-- Dialog WhatsApp Connect -->
    <WppConnectDialog v-model="showWppConnect" />

    <!-- Content Area -->
    <div class="content-wrapper">
      <!-- SIDEBAR: Lista de Contatos -->
      <div class="sidebar">
        <ContactsList />
      </div>

      <!-- ÁREA PRINCIPAL: Chat -->
      <div class="chat-area">
        <!-- Estado: Nenhum contato selecionado -->
        <div v-if="!selectedContact" class="empty-state">
          <v-icon size="80" color="grey-lighten-1">mdi-message-text-outline</v-icon>
          <h2 class="text-h5 mt-4 text-grey">Selecione uma conversa</h2>
          <p class="text-grey-darken-1">Escolha um contato na lista para começar a conversar</p>
        </div>

        <!-- Chat ativo -->
        <ChatView v-else :contact="selectedContact" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useContactsStore } from '@/stores/contacts';
import { useAuthStore } from '@/stores/auth';
import { useChatStore } from '@/stores/chat';
import { storeToRefs } from 'pinia';
import ContactsList from '@/components/ContactsList.vue';
import ChatView from './ChatView.vue';
import WppConnectDialog from '@/components/WppConnectDialog.vue';

const router = useRouter();
const contactsStore = useContactsStore();
const authStore = useAuthStore();
const chatStore = useChatStore();
const { selectedContact } = storeToRefs(contactsStore);
const isReady = ref(false);
const showWppConnect = ref(false);

const userInitials = computed(() => {
  const name = authStore.user?.name || 'U';
  return name
    .split(' ')
    .map(n => n[0])
    .join('')
    .substring(0, 2)
    .toUpperCase();
});

function handleLogout() {
  chatStore.disconnect();
  authStore.logout();
  router.push('/login');
}

onMounted(async () => {
  console.log('📱 ChatLayoutView mounted');
  
  // Garante que auth está carregado
  if (!authStore.user) {
    authStore.load();
  }
  
  // Pequeno delay para garantir renderização
  await new Promise(resolve => setTimeout(resolve, 100));
  isReady.value = true;
  
  console.log('✅ Layout pronto, usuário:', authStore.user?.name);
});
</script>

<style scoped>
.chat-layout {
  display: flex;
  flex-direction: column;
  height: 100vh;
  width: 100%;
  overflow: hidden;
  position: relative;
}

.global-header {
  flex-shrink: 0;
  position: sticky;
  top: 0;
  z-index: 1000;
}

.header-info {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.header-name {
  font-size: 1.063rem;
  font-weight: 600;
  line-height: 1.3;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.header-status {
  font-size: 0.813rem;
  line-height: 1.2;
  opacity: 0.85;
}

.content-wrapper {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.sidebar {
  width: 360px;
  height: 100%;
  flex-shrink: 0;
  overflow: hidden;
}

.chat-area {
  flex: 1;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f5f5;
  overflow: hidden;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 32px;
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100vh;
  width: 100%;
  background: #f5f5f5;
}

/* Mobile: Layout responsivo mobile-first */
@media (max-width: 768px) {
  .mobile-only {
    display: inline-flex !important;
  }
  
  /* Por padrão: mostra apenas sidebar */
  .sidebar {
    width: 100%;
    display: flex;
  }
  
  .chat-area {
    display: none;
  }
  
  /* Quando há contato selecionado: esconde sidebar, mostra chat */
  .chat-layout.has-contact .sidebar {
    display: none;
  }
  
  .chat-layout.has-contact .chat-area {
    display: flex;
    width: 100%;
  }
}

@media (min-width: 769px) {
  .mobile-only {
    display: none !important;
  }
}

/* Tablets e Desktop: Mantém duas colunas */
@media (min-width: 769px) {
  .sidebar {
    border-right: 1px solid #e0e0e0;
  }
}
</style>

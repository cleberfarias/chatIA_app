<template>
  <div class="contacts-sidebar">
    <!-- Search -->
    <div class="search-wrapper">
      <v-text-field
        v-model="search"
        placeholder="Buscar contato..."
        prepend-inner-icon="mdi-magnify"
        variant="solo"
        density="compact"
        hide-details
        single-line
        flat
        bg-color="grey-lighten-4"
        class="search-input"
      />
    </div>

    <!-- Lista de contatos -->
    <v-list class="contacts-list">
      <v-list-item
        v-for="contact in filteredContacts"
        :key="contact.id"
        :active="selectedContactId === contact.id"
        @click="selectContact(contact.id)"
        class="contact-item"
      >
        <!-- Avatar -->
        <template #prepend>
          <v-badge
            :model-value="contact.online"
            color="success"
            dot
            offset-x="8"
            offset-y="8"
          >
            <v-avatar :color="contact.avatar ? undefined : 'primary'" size="48">
              <v-img v-if="contact.avatar" :src="contact.avatar" />
              <span v-else class="text-h6">{{ getInitials(contact.name) }}</span>
            </v-avatar>
          </v-badge>
        </template>

        <!-- Conteúdo -->
        <v-list-item-title class="font-weight-bold">
          {{ contact.name }}
        </v-list-item-title>
        
        <v-list-item-subtitle class="text-truncate">
          {{ contact.lastMessage || 'Nenhuma mensagem ainda' }}
        </v-list-item-subtitle>

        <!-- Badge de não lidas -->
        <template #append>
          <div class="d-flex flex-column align-end">
            <span v-if="contact.lastMessageTime" class="text-caption text-grey">
              {{ formatTime(contact.lastMessageTime) }}
            </span>
            <v-badge
              v-if="contact.unreadCount > 0"
              :content="contact.unreadCount"
              color="primary"
              inline
              class="mt-1"
            />
          </div>
        </template>
      </v-list-item>

      <!-- Estado vazio -->
      <v-list-item v-if="filteredContacts.length === 0 && !loading">
        <v-list-item-title class="text-center text-grey">
          {{ search ? 'Nenhum contato encontrado' : 'Nenhuma conversa ainda' }}
        </v-list-item-title>
      </v-list-item>

      <!-- Loading -->
      <v-list-item v-if="loading">
        <v-list-item-title class="text-center">
          <v-progress-circular indeterminate size="24" />
        </v-list-item-title>
      </v-list-item>
    </v-list>

    <!-- Dialog para novo chat -->
    <v-dialog v-model="showNewChat" max-width="400">
      <v-card>
        <v-card-title>Nova Conversa</v-card-title>
        <v-card-text>
          <v-list>
            <v-list-item
              v-for="contact in allContacts"
              :key="contact.id"
              @click="startNewChat(contact.id)"
            >
              <template #prepend>
                <v-avatar :color="contact.avatar ? undefined : 'primary'" size="40">
                  <v-img v-if="contact.avatar" :src="contact.avatar" />
                  <span v-else>{{ getInitials(contact.name) }}</span>
                </v-avatar>
              </template>
              <v-list-item-title>{{ contact.name }}</v-list-item-title>
              <v-list-item-subtitle>{{ contact.email }}</v-list-item-subtitle>
            </v-list-item>
          </v-list>
        </v-card-text>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useContactsStore } from '@/stores/contacts';
import { storeToRefs } from 'pinia';

const contactsStore = useContactsStore();
const { contacts, selectedContactId, loading } = storeToRefs(contactsStore);

const search = ref('');
const showNewChat = ref(false);

const filteredContacts = computed(() => {
  if (!search.value) return contactsStore.sortedContacts;
  
  const query = search.value.toLowerCase();
  return contactsStore.sortedContacts.filter(c => 
    c.name.toLowerCase().includes(query) ||
    c.email.toLowerCase().includes(query)
  );
});

const allContacts = computed(() => contacts.value);

function selectContact(contactId: string) {
  console.log('🖱️ Clicou no contato:', contactId);
  contactsStore.selectContact(contactId);
  contactsStore.markContactRead(contactId);
  console.log('✅ selectedContactId agora é:', contactsStore.selectedContactId);
}

function startNewChat(contactId: string) {
  showNewChat.value = false;
  selectContact(contactId);
}

function getInitials(name: string): string {
  return name
    .split(' ')
    .map(n => n[0])
    .join('')
    .substring(0, 2)
    .toUpperCase();
}

function formatTime(timestamp: number): string {
  const date = new Date(timestamp);
  const now = new Date();
  const diff = now.getTime() - date.getTime();
  
  // Hoje - mostra hora
  if (diff < 24 * 60 * 60 * 1000 && date.getDate() === now.getDate()) {
    return date.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
  }
  
  // Essa semana - mostra dia da semana
  if (diff < 7 * 24 * 60 * 60 * 1000) {
    const days = ['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb'];
    return days[date.getDay()] || 'Dom';
  }
  
  // Mais antigo - mostra data
  return date.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' });
}

onMounted(() => {
  contactsStore.loadContacts();
});
</script>

<style scoped>
.contacts-sidebar {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #f5f5f5;
  overflow: hidden;
}

/* Search wrapper */
.search-wrapper {
  padding: 12px 16px 8px 16px;
  background: white;
  flex-shrink: 0;
}

.search-input {
  width: 100%;
}

.search-input :deep(.v-field) {
  border-radius: 20px;
  box-shadow: none;
  font-size: 0.875rem;
}

.search-input :deep(.v-field__input) {
  padding: 6px 12px;
  min-height: 36px;
  line-height: 1.5;
}

.search-input :deep(.v-field__prepend-inner) {
  padding-left: 8px;
  align-items: center;
}

.search-input :deep(.v-field__prepend-inner .v-icon) {
  font-size: 20px;
  opacity: 0.6;
}

.contacts-list {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  background: white;
  -webkit-overflow-scrolling: touch;
}

.contact-item {
  border-bottom: 1px solid #f0f0f0;
  cursor: pointer;
  transition: background 0.2s;
  padding: 12px 16px;
}

.contact-item:hover {
  background: #f5f5f5;
}

.contact-item.v-list-item--active {
  background: #e3f2fd;
}

.text-truncate {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 100%;
}

/* Mobile: ajustes responsivos */
@media (max-width: 768px) {
  .contacts-sidebar {
    height: 100vh;
  }
  
  .sidebar-header {
    padding: 16px;
  }
  
  .sidebar-header h2 {
    font-size: 1.25rem;
  }
  
  .search-wrapper {
    padding: 16px;
  }
  
  .contact-item {
    padding: 16px;
  }
  
  /* Garante que badges não quebrem o layout */
  :deep(.v-list-item__append) {
    min-width: 60px;
    align-items: flex-end;
  }
}

/* Tablets e desktop */
@media (min-width: 769px) {
  .contacts-sidebar {
    border-right: 1px solid #e0e0e0;
  }
}
</style>

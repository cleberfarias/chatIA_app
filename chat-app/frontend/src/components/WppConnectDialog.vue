<template>
  <v-dialog v-model="isOpen" max-width="500" persistent>
    <v-card>
      <v-card-title class="d-flex align-center justify-space-between">
        <span>Conectar WhatsApp Web</span>
        <v-btn icon="mdi-close" variant="text" @click="close" />
      </v-card-title>

      <v-card-text>
        <!-- Loading -->
        <div v-if="loading" class="text-center py-8">
          <v-progress-circular indeterminate color="primary" size="64" />
          <p class="mt-4">Gerando QR Code...</p>
        </div>

        <!-- QR Code -->
        <div v-else-if="qrCode" class="text-center py-4">
          <v-img :src="qrCode" max-width="300" class="mx-auto mb-4" />
          <v-alert type="info" variant="tonal">
            <strong>Escaneie o QR Code</strong>
            <ol class="mt-2 text-left">
              <li>Abra o WhatsApp no celular</li>
              <li>Toque em Menu > Aparelhos conectados</li>
              <li>Toque em Conectar aparelho</li>
              <li>Aponte o celular para esta tela</li>
            </ol>
          </v-alert>
        </div>

        <!-- Erro -->
        <div v-else-if="error" class="text-center py-4">
          <v-icon color="error" size="64">mdi-alert-circle</v-icon>
          <p class="mt-4 text-error">{{ error }}</p>
        </div>
      </v-card-text>

      <v-card-actions>
        <v-spacer />
        <v-btn v-if="error" color="primary" @click="startSession">
          Tentar Novamente
        </v-btn>
        <v-btn variant="text" @click="close">
          Fechar
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import { startWppSession, getWppQrCode } from '../composables/useOmni';

interface Props {
  modelValue: boolean;
  session?: string;
}

const props = withDefaults(defineProps<Props>(), {
  session: 'default',
});

const emit = defineEmits<{
  'update:modelValue': [value: boolean];
}>();

const isOpen = ref(props.modelValue);
const loading = ref(false);
const qrCode = ref('');
const error = ref('');

// Sincroniza com v-model
watch(() => props.modelValue, (val) => {
  isOpen.value = val;
  if (val) {
    startSession();
  }
});

watch(isOpen, (val) => {
  emit('update:modelValue', val);
});

async function startSession() {
  loading.value = true;
  error.value = '';
  qrCode.value = '';

  try {
    const baseUrl = import.meta.env.VITE_SOCKET_URL || 'http://localhost:3000';
    
    // Inicia sessão
    await startWppSession(baseUrl, props.session);
    
    // Aguarda 2 segundos para QR ser gerado
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    // Obtém QR code
    const result = await getWppQrCode(baseUrl, props.session);
    qrCode.value = result.qr;
  } catch (err: any) {
    error.value = err.message || 'Erro ao conectar com WPPConnect';
    console.error('Erro WPPConnect:', err);
  } finally {
    loading.value = false;
  }
}

function close() {
  isOpen.value = false;
}
</script>

<style scoped>
ol {
  padding-left: 20px;
}

ol li {
  margin: 4px 0;
}
</style>

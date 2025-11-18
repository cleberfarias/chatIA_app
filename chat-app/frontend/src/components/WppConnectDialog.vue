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
          <div class="qr-container mx-auto mb-4">
            <img 
              :src="qrCode" 
              alt="QR Code WhatsApp" 
              class="qr-image"
              @error="handleImageError"
              @load="handleImageLoad"
            />
          </div>
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
        <v-btn v-if="error" color="primary" @click="startQrPolling">
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
import { getWppQrCode } from '../composables/useOmni';

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
const description = ref('Carregando... Por favor aguarde.');
const previousQrCode = ref<string | null>(null);
const previousUpdate = ref<number | null>(null);
let pollingInterval: ReturnType<typeof setInterval> | null = null;

// Sincroniza com v-model
watch(() => props.modelValue, (val) => {
  isOpen.value = val;
  if (val) {
    startQrPolling();
  } else {
    stopPolling();
  }
});

watch(isOpen, (val) => {
  emit('update:modelValue', val);
  if (!val) {
    stopPolling();
  }
});

function stopPolling() {
  if (pollingInterval) {
    clearInterval(pollingInterval);
    pollingInterval = null;
  }
}

async function startQrPolling() {
  // Limpa polling anterior
  stopPolling();
  
  // Reset de estado
  loading.value = true;
  error.value = '';
  qrCode.value = '';
  description.value = 'Carregando... Por favor aguarde.';
  previousQrCode.value = null;
  previousUpdate.value = null;
  
  const baseUrl = `${window.location.protocol}//${window.location.hostname}:3000`;
  
  // Primeira chamada verifica containers
  let check_containers = true;
  
  console.log('🔄 Iniciando polling QR Code... (baseado em sistema documentado)');
  
  // Inicia polling a cada 2 segundos (padrão documentado)
  pollingInterval = setInterval(async () => {
    // Verifica se modal ainda está aberto
    if (!isOpen.value) {
      stopPolling();
      return;
    }
    
    try {
      // Busca QR code (primeira vez com check_containers=true)
      const result = await getWppQrCode(baseUrl, props.session, check_containers);
      
      // Após primeira chamada, não precisa mais verificar containers
      check_containers = false;
      
      // Extrai dados da resposta
      const { qr, last_update, description: desc, status } = result;
      
      // Detecta mudanças
      const isNewQr = qr !== previousQrCode.value;
      const lastUpdateNum = last_update ? Number(last_update) : null;
      const isNewUpdate = lastUpdateNum !== previousUpdate.value;
      
      // Atualiza descrição
      description.value = desc || 'Carregando...';
      
      // Processa baseado no status (igual ao sistema documentado)
      if (status?.toUpperCase() === 'LOGGEDIN') {
        // ✅ Conectado com sucesso
        console.log('✅ WhatsApp LOGGEDIN!');
        description.value = 'WhatsApp conectado com sucesso! ✓';
        qrCode.value = '';
        loading.value = false;
        
        // Fecha modal após 8 segundos (padrão documentado)
        setTimeout(() => {
          console.log('Fechando modal...');
          close();
        }, 8000);
        
        stopPolling();
        return;
      }
      else if (['STARTING', 'WAITING_LOGIN', 'NOTLOGGEDIN', 'LOGGEDINWAIT'].includes(status?.toUpperCase() || '')) {
        // ⏳ Processando - mas mantém QR Code se já existe
        console.log(`⏳ Status: ${status}`);
        if (!qrCode.value) {
          loading.value = true;
        }
      }
      else if (qr && (isNewQr || isNewUpdate)) {
        // 📱 QR Code disponível (novo ou renovado)
        console.log('📱 QR Code disponível! Atualizando...');
        
        // Adiciona prefixo data:image se necessário
        if (!qr.startsWith('data:image')) {
          qrCode.value = `data:image/png;base64,${qr}`;
        } else {
          qrCode.value = qr;
        }
        loading.value = false;
        previousQrCode.value = qr;
        previousUpdate.value = lastUpdateNum;
        
        console.log(`✅ QR Code atualizado! Timestamp: ${last_update}`);
      }
      else if (status?.toUpperCase() === 'ERROR') {
        // ❌ Erro
        console.error('❌ Status ERROR recebido');
        error.value = desc || 'Erro ao gerar QR Code';
        loading.value = false;
        stopPolling();
      }
      
    } catch (err: any) {
      console.error('❌ Erro no polling:', err);
      
      // Tratamento de erro conforme documentado
      if (err.response && err.response.status === 400) {
        // Erro conhecido do backend
        description.value = err.response.data.description || 'Erro ao buscar QR Code';
        error.value = description.value;
      } else {
        // Erro desconhecido
        description.value = 'Erro ao buscar QR-Code. Por favor, contate o suporte.';
        error.value = description.value;
      }
      
      loading.value = false;
      stopPolling();
    }
  }, 2000); // Polling a cada 2 segundos (padrão documentado)
}

function handleImageLoad() {
  console.log('✅ Imagem do QR Code carregada');
}

function handleImageError(event: Event) {
  console.error('❌ Erro ao carregar imagem:', event);
  error.value = 'Erro ao carregar QR Code';
}

function close() {
  stopPolling();
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

.qr-container {
  max-width: 300px;
  width: 100%;
  background: white;
  padding: 16px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.qr-image {
  width: 100%;
  height: auto;
  display: block;
}
</style>

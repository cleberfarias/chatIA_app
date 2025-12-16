<template>
  <v-dialog v-model="dialog" max-width="700px" persistent scrollable>
    <v-card>
          <v-card-title class="bg-gradient-custom text-white">
        <div class="d-flex align-center">
          <v-icon class="mr-2">mdi-robot-excited</v-icon>
          <span>Criar Agente Personalizado</span>
        </div>
      </v-card-title>

      <v-card-text class="pt-6 pb-4">
        <v-alert
          v-if="submitError"
          type="error"
          variant="tonal"
          class="mb-4"
          density="compact"
        >
          {{ submitError }}
        </v-alert>

        <v-form ref="formRef" v-model="formValid">
          <!-- Nome do Agente -->
          <v-text-field
            v-model="botName"
            label="Nome do Agente *"
            placeholder="Ex: Assistente de Vendas, Tutor de Matemática..."
            prepend-inner-icon="mdi-robot"
            variant="outlined"
            :rules="[rules.required, rules.minLength]"
            hint="Escolha um nome único para seu bot"
            persistent-hint
            class="mb-4"
          />

          <!-- Emoji do Agente -->
          <v-text-field
            v-model="botEmoji"
            label="Emoji do Agente (opcional)"
            placeholder="🤖"
            prepend-inner-icon="mdi-emoticon-happy"
            variant="outlined"
            :rules="[rules.maxLength]"
            hint="Um emoji que representa seu agente"
            persistent-hint
            class="mb-4"
            maxlength="4"
          />

          <!-- OpenAI API Key -->
          <v-text-field
            v-model="openaiApiKey"
            label="OpenAI API Key *"
            placeholder="sk-proj-..."
            prepend-inner-icon="mdi-key"
            variant="outlined"
            :rules="[rules.required, rules.apiKeyFormat]"
            hint="Sua chave de API da OpenAI"
            persistent-hint
            class="mb-4"
            :type="showApiKey ? 'text' : 'password'"
          >
            <template #append-inner>
              <v-icon
                :icon="showApiKey ? 'mdi-eye-off' : 'mdi-eye'"
                size="small"
                class="cursor-pointer"
                @click="showApiKey = !showApiKey"
              />
            </template>
          </v-text-field>

          <!-- OpenAI Account/Organization -->
          <v-text-field
            v-model="openaiAccount"
            label="OpenAI Organization ID (opcional)"
            placeholder="org-..."
            prepend-inner-icon="mdi-domain"
            variant="outlined"
            hint="ID da organização OpenAI (se aplicável)"
            persistent-hint
            class="mb-4"
          />

          <!-- Tabs: Digitar ou Upload -->
          <v-tabs v-model="inputMode" color="primary" class="mb-4">
            <v-tab value="text">
              <v-icon class="mr-2">mdi-text</v-icon>
              Digitar Prompt
            </v-tab>
            <v-tab value="file">
              <v-icon class="mr-2">mdi-file-document</v-icon>
              Upload de Arquivo
            </v-tab>
          </v-tabs>

          <v-window v-model="inputMode">
            <!-- Tab: Digitar Prompt -->
            <v-window-item value="text">
              <v-textarea
                v-model="botPrompt"
                label="System Prompt *"
                placeholder="Exemplo:
Você é um assistente especializado em vendas B2B.

EXPERTISE:
- Prospecção de leads
- Técnicas de fechamento
- Gestão de objeções

COMPORTAMENTO:
- Seja consultivo e profissional
- Forneça exemplos práticos
- Use metodologias comprovadas"
                prepend-inner-icon="mdi-text-box"
                variant="outlined"
                :rules="[rules.required]"
                rows="12"
                hint="Descreva a personalidade, expertise e comportamento do agente"
                persistent-hint
                auto-grow
                counter
              />
            </v-window-item>

            <!-- Tab: Upload de Arquivo -->
            <v-window-item value="file">
              <v-file-input
                v-model="uploadedFile"
                label="Upload do Prompt"
                placeholder="Selecione um arquivo .txt ou .md"
                prepend-icon="mdi-paperclip"
                variant="outlined"
                accept=".txt,.md"
                :rules="[rules.fileSize]"
                hint="Arquivo com o prompt do bot (máx 100KB)"
                persistent-hint
                show-size
                @change="handleFileUpload"
              />

              <!-- Preview do arquivo -->
              <v-card v-if="fileContent" variant="outlined" class="mt-4">
                <v-card-subtitle class="d-flex align-center">
                  <v-icon size="small" class="mr-2">mdi-eye</v-icon>
                    Preview do Arquivo
                </v-card-subtitle>
                <v-card-text>
                  <pre class="file-preview">{{ fileContent }}</pre>
                </v-card-text>
              </v-card>
            </v-window-item>
          </v-window>

          <!-- Especialidades (opcional) -->
          <v-combobox
            v-model="botSpecialties"
            label="Especialidades (opcional)"
            placeholder="Digite e pressione Enter"
            prepend-inner-icon="mdi-star-circle"
            variant="outlined"
            chips
            multiple
            closable-chips
            hint="Adicione até 5 especialidades"
            persistent-hint
            class="mt-4"
          >
            <template v-slot:chip="{ item, props }">
              <v-chip v-bind="props" color="primary" size="small">
                {{ item.title }}
              </v-chip>
            </template>
          </v-combobox>

          <!-- Preview do Agente -->
          <v-card v-if="botName || botEmoji" variant="tonal" class="mt-6">
            <v-card-subtitle class="d-flex align-center">
              <v-icon size="small" class="mr-2">mdi-robot-happy</v-icon>
              Preview do Agente
            </v-card-subtitle>
            <v-card-text>
              <div class="d-flex align-center">
                <v-avatar color="primary" size="48" class="mr-3">
                  <span class="text-h6">{{ botEmoji || '🤖' }}</span>
                </v-avatar>
                <div>
                  <div class="text-subtitle-1 font-weight-bold">
                    {{ botName || 'Meu Agente' }} {{ botEmoji }}
                  </div>
                  <div v-if="botSpecialties.length" class="text-caption text-grey">
                    {{ botSpecialties.slice(0, 3).join(' • ') }}
                  </div>
                </div>
              </div>
            </v-card-text>
          </v-card>
        </v-form>
      </v-card-text>

      <v-divider />

      <v-card-actions class="pa-4">
        <v-btn
          variant="text"
          @click="closeDialog"
        >
          Cancelar
        </v-btn>
        <v-spacer />
        <v-btn
          color="primary"
          variant="flat"
          :disabled="!canCreate"
          :loading="loading"
          @click="handleCreateBot"
        >
          <v-icon class="mr-2">mdi-plus-circle</v-icon>
          Criar Agente
        </v-btn>
      </v-card-actions>

      <v-snackbar
        v-model="snackbar"
        color="success"
        timeout="2500"
        location="top"
      >
        {{ snackbarText }}
      </v-snackbar>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import { useCustomAgents, type CustomAgentPayload, type CustomAgentSummary } from '../../../composables/useCustomAgents';

// Props
const props = defineProps<{
  modelValue: boolean;
}>();

// Emits
const emit = defineEmits<{
  'update:modelValue': [value: boolean];
  'agent-created': [agent: CustomAgentSummary];
}>();
// Dialog state
const dialog = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
});

// Form
const formRef = ref();
const formValid = ref(false);

// Bot data
const botName = ref('');
const botEmoji = ref('🤖');
const botPrompt = ref('');
const botSpecialties = ref<Array<{ title: string } | string>>([]);
const openaiApiKey = ref('');
const openaiAccount = ref('');
const showApiKey = ref(false);
const inputMode = ref<'text' | 'file'>('text');
const uploadedFile = ref<File[]>([]);
const fileContent = ref('');
<<<<<<< HEAD
const submitError = ref('');
const snackbar = ref(false);
const snackbarText = ref('');

const { createAgent, loading, error } = useCustomAgents();

// Validation rules
const rules = {
  required: (v: string) => !!v || 'Campo obrigatório',
  minLength: (v: string) => (v && v.length >= 3) || 'Mínimo 3 caracteres',
  maxLength: (v: string) => !v || v.length <= 4 || 'Máximo 4 caracteres',
  apiKeyFormat: (v: string) => {
    if (!v) return 'API Key obrigatória';
    if (!v.startsWith('sk-')) return 'API Key deve começar com sk-';
    if (v.length < 20) return 'API Key inválida (muito curta)';
    return true;
  },
  fileSize: (files: File[]) => {
    if (!files || files.length === 0) return true;
    const file = files[0];
    if (!file) return true;
    const maxSize = 100 * 1024; // 100KB
    return file.size <= maxSize || 'Arquivo muito grande (máx 100KB)';
  }
};

// Computed
const canCreate = computed(() => {
  const hasName = !!botName.value && botName.value.length >= 3;
  const hasPrompt = inputMode.value === 'text' 
    ? !!botPrompt.value 
    : !!fileContent.value;
  const hasApiKey = !!openaiApiKey.value && openaiApiKey.value.startsWith('sk-');
  return formValid.value && hasName && hasPrompt && hasApiKey;
});

const finalPrompt = computed(() => {
  return inputMode.value === 'file' ? fileContent.value : botPrompt.value;
});

// Methods
function handleFileUpload() {
  const files = uploadedFile.value;
  if (!files || files.length === 0) {
    fileContent.value = '';
    return;
  }

  const file = files[0];
  if (!file) {
    fileContent.value = '';
    return;
  }
  
  const reader = new FileReader();
  
  reader.onload = (e) => {
    fileContent.value = e.target?.result as string;
  };
  
  reader.onerror = () => {
    console.error('Erro ao ler arquivo');
    fileContent.value = '';
  };
  
  reader.readAsText(file);
}

async function handleCreateBot() {
  if (!formRef.value) return;

  const { valid } = await formRef.value.validate();
  if (!valid) return;

<<<<<<< HEAD
=======
  submitError.value = '';

>>>>>>> origin/main
  try {
    const specialties = botSpecialties.value.map((s) =>
      typeof s === 'string' ? s : s.title
    );
<<<<<<< HEAD
    const payload: CustomAgentPayload = {
=======

    const payload: CustomBotPayload = {
>>>>>>> origin/main
      name: botName.value.trim(),
      emoji: botEmoji.value.trim() || '🤖',
      prompt: finalPrompt.value.trim(),
      specialties: specialties.slice(0, 5),
      openaiApiKey: openaiApiKey.value.trim(),
      openaiAccount: openaiAccount.value.trim() || undefined
    };
<<<<<<< HEAD
    const createdAgent = await createAgent(payload);
    emit('agent-created', createdAgent);
    // Fecha modal e reseta
    closeDialog();
    resetForm();
  } catch (error) {
    console.error('Erro ao criar bot:', error);
  } finally {
    // loading is managed by composable
  }
}

// local persistence removed: creation is persisted via backend composable

=======

    const createdBot = await createBot(payload);
    emit('bot-created', createdBot);

    snackbarText.value = `Agente ${createdBot.name} criado!`;
    snackbar.value = true;
    closeDialog();
    resetForm();
  } catch (err) {
    console.error('Erro ao criar bot:', err);
    submitError.value = error.value || 'Falha ao criar bot';
  }
}

>>>>>>> origin/main
function closeDialog() {
  dialog.value = false;
}

function resetForm() {
  botName.value = '';
  botEmoji.value = '🤖';
  botPrompt.value = '';
  botSpecialties.value = [];
  openaiApiKey.value = '';
  openaiAccount.value = '';
  showApiKey.value = false;
  uploadedFile.value = [];
  fileContent.value = '';
  inputMode.value = 'text';
  submitError.value = '';
  snackbar.value = false;
  formRef.value?.resetValidation();
}

// Watch para resetar quando fechar
watch(dialog, (newVal) => {
  if (!newVal) {
    setTimeout(resetForm, 300); // Aguarda animação
  }
});
</script>

<style scoped>
.bg-gradient-custom {
  background: linear-gradient(135deg, var(--ds-color-primary) 0%, color-mix(in srgb, var(--ds-color-primary) 70%, var(--ds-color-secondary) 30%) 100%);
}

.file-preview {
  max-height: 200px;
  overflow-y: auto;
  padding: var(--ds-spacing-md);
  background-color: color-mix(in srgb, var(--ds-color-border) 30%, var(--ds-color-chat-background) 70%);
  border-radius: var(--ds-radius-sm);
  font-size: var(--ds-font-size-sm);
  line-height: var(--ds-line-height-relaxed);
  white-space: pre-wrap;
  word-break: break-word;
}
</style>

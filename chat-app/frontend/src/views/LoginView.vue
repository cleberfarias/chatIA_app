<template>
  <v-sheet class="fill-height" color="grey-lighten-4">
    <v-container class="fill-height">
      <v-row justify="center" align="center">
        <v-col cols="12" sm="8" md="6" lg="4">
          <!-- CARD PRINCIPAL -->
          <v-card elevation="12" rounded="lg">
            <!-- PROGRESS BAR -->
            <v-progress-linear
              v-if="loading"
              indeterminate
              color="primary"
              height="4"
            />

            <!-- HEADER -->
            <v-card-title class="text-center py-6">
              <div class="w-100">
                <v-avatar size="80" color="primary" class="mb-4">
                  <v-icon size="50" color="white">mdi-chat</v-icon>
                </v-avatar>
                <div class="text-h4 font-weight-bold">Chat-IA</div>
                <div class="text-subtitle-1 text-grey">
                  Conecte-se em tempo real
                </div>
              </div>
            </v-card-title>

            <!-- TABS LOGIN/REGISTRO -->
            <v-tabs v-model="tab" grow color="primary" class="mb-4">
              <v-tab value="login">
                <v-icon start>mdi-login</v-icon>
                Login
              </v-tab>
              <v-tab value="register">
                <v-icon start>mdi-account-plus</v-icon>
                Registrar
              </v-tab>
            </v-tabs>

            <v-divider />

            <!-- CONTEÚDO -->
            <v-card-text class="pa-6">
              <!-- ALERT DE ERRO/SUCESSO -->
              <v-alert
                v-if="alert.show"
                :type="alert.type"
                :text="alert.message"
                closable
                class="mb-4"
                @click:close="alert.show = false"
              />

              <!-- WINDOW TABS -->
              <v-window v-model="tab">
                <!-- TAB LOGIN -->
                <v-window-item value="login">
                  <v-form ref="loginForm" @submit.prevent="handleLogin">
                    <v-text-field
                      v-model="loginData.email"
                      label="Email"
                      type="email"
                      prepend-inner-icon="mdi-email"
                      variant="outlined"
                      :rules="[rules.required, rules.email]"
                      class="mb-3"
                      autofocus
                    />

                    <v-text-field
                      v-model="loginData.password"
                      label="Senha"
                      :type="showPassword ? 'text' : 'password'"
                      prepend-inner-icon="mdi-lock"
                      :append-inner-icon="showPassword ? 'mdi-eye' : 'mdi-eye-off'"
                      variant="outlined"
                      :rules="[rules.required, rules.minLength]"
                      @click:append-inner="showPassword = !showPassword"
                      class="mb-2"
                    />

                    <v-checkbox
                      v-model="rememberMe"
                      label="Lembrar-me"
                      color="primary"
                      density="compact"
                      class="mb-2"
                    />

                    <v-btn
                      type="submit"
                      color="primary"
                      size="large"
                      block
                      :loading="loading"
                      class="mb-3"
                    >
                      <v-icon start>mdi-login</v-icon>
                      Entrar
                    </v-btn>

                    <div class="text-center">
                      <v-btn
                        variant="text"
                        size="small"
                        color="primary"
                        @click="() => {}"
                      >
                        Esqueci minha senha
                      </v-btn>
                    </div>
                  </v-form>
                </v-window-item>

                <!-- TAB REGISTRO -->
                <v-window-item value="register">
                  <v-form ref="registerForm" @submit.prevent="handleRegister">
                    <v-text-field
                      v-model="registerData.name"
                      label="Nome completo"
                      prepend-inner-icon="mdi-account"
                      variant="outlined"
                      :rules="[rules.required]"
                      class="mb-3"
                      autofocus
                    />

                    <v-text-field
                      v-model="registerData.email"
                      label="Email"
                      type="email"
                      prepend-inner-icon="mdi-email"
                      variant="outlined"
                      :rules="[rules.required, rules.email]"
                      class="mb-3"
                    />

                    <v-text-field
                      v-model="registerData.password"
                      label="Senha"
                      :type="showPassword ? 'text' : 'password'"
                      prepend-inner-icon="mdi-lock"
                      :append-inner-icon="showPassword ? 'mdi-eye' : 'mdi-eye-off'"
                      variant="outlined"
                      :rules="[rules.required, rules.minLength]"
                      @click:append-inner="showPassword = !showPassword"
                      class="mb-3"
                      hint="Mínimo 6 caracteres"
                    />

                    <v-text-field
                      v-model="confirmPassword"
                      label="Confirmar senha"
                      :type="showPassword ? 'text' : 'password'"
                      prepend-inner-icon="mdi-lock-check"
                      variant="outlined"
                      :rules="[rules.required, rules.passwordMatch]"
                      class="mb-4"
                    />

                    <v-btn
                      type="submit"
                      color="primary"
                      size="large"
                      block
                      :loading="loading"
                    >
                      <v-icon start>mdi-account-plus</v-icon>
                      Criar conta
                    </v-btn>
                  </v-form>
                </v-window-item>
              </v-window>
            </v-card-text>

            <v-divider />

            <!-- FOOTER -->
            <v-card-actions class="pa-4 justify-center">
              <div class="text-caption text-grey">
                © 2025 Pad Chat-IA - Pad Chat-IA
              </div>
            </v-card-actions>
          </v-card>
        </v-col>
      </v-row>
    </v-container>
  </v-sheet>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '../stores/auth';

const router = useRouter();
const authStore = useAuthStore();

// Estado
const tab = ref('login');
const loading = ref(false);
const showPassword = ref(false);
const rememberMe = ref(false);
const confirmPassword = ref('');

const loginData = reactive({
  email: '',
  password: ''
});

const registerData = reactive({
  name: '',
  email: '',
  password: ''
});

const alert = reactive({
  show: false,
  type: 'error' as 'error' | 'success',
  message: ''
});

// Referências dos formulários
const loginForm = ref<any>(null);
const registerForm = ref<any>(null);

// Regras de validação
const rules = {
  required: (v: string) => !!v || 'Campo obrigatório',
  email: (v: string) => /.+@.+\..+/.test(v) || 'Email inválido',
  minLength: (v: string) => (v && v.length >= 6) || 'Mínimo 6 caracteres',
  passwordMatch: (v: string) => v === registerData.password || 'Senhas não conferem'
};

// URL da API
const baseUrl = import.meta.env.VITE_SOCKET_URL || 'http://localhost:3000';

// Funções
function showAlert(type: 'error' | 'success', message: string) {
  alert.type = type;
  alert.message = message;
  alert.show = true;
}

async function handleLogin() {
  const { valid } = await loginForm.value.validate();
  if (!valid) return;

  loading.value = true;
  try {
    await authStore.login(baseUrl, loginData.email, loginData.password);
    showAlert('success', 'Login realizado com sucesso!');
    setTimeout(() => {
      router.push('/');
    }, 500);
  } catch (error: any) {
    showAlert('error', error.message || 'Erro ao fazer login');
  } finally {
    loading.value = false;
  }
}

async function handleRegister() {
  const { valid } = await registerForm.value.validate();
  if (!valid) return;

  loading.value = true;
  try {
    await authStore.register(
      baseUrl,
      registerData.name,
      registerData.email,
      registerData.password
    );
    showAlert('success', 'Conta criada com sucesso!');
    setTimeout(() => {
      router.push('/');
    }, 500);
  } catch (error: any) {
    showAlert('error', error.message || 'Erro ao criar conta');
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
.fill-height {
  height: 100vh;
}

.w-100 {
  width: 100%;
}
</style>

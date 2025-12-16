import { ref } from 'vue';
import axios from 'axios';
import { useAuthStore } from '@/stores/auth';

export interface CustomBotPayload {
  name: string;
  emoji: string;
  prompt: string;
  specialties: string[];
  openaiApiKey: string;
  openaiAccount?: string;
}

export interface CustomBotSummary {
  name: string;
  emoji: string;
  key: string;
  specialties: string[];
  createdAt?: string;
}

export function useCustomBots() {
  const loading = ref(false);
  const error = ref<string | null>(null);

  const apiBase = import.meta.env.VITE_API_URL || 'http://localhost:3000';

  const authHeaders = () => {
    const authStore = useAuthStore();
    return {
      Authorization: `Bearer ${authStore.token || ''}`
    };
  };

  const listBots = async (): Promise<CustomBotSummary[]> => {
    loading.value = true;
    error.value = null;
    try {
      const { data } = await axios.get(`${apiBase}/custom-bots`, {
        headers: authHeaders()
      });
      return data?.bots || [];
    } catch (err: any) {
      error.value = err?.response?.data?.detail || 'Erro ao carregar bots';
      throw err;
    } finally {
      loading.value = false;
    }
  };

  const createBot = async (payload: CustomBotPayload): Promise<CustomBotSummary> => {
    loading.value = true;
    error.value = null;
    try {
      const { data } = await axios.post(
        `${apiBase}/custom-bots`,
        {
          name: payload.name,
          emoji: payload.emoji,
          prompt: payload.prompt,
          specialties: payload.specialties,
          openaiApiKey: payload.openaiApiKey,
          openaiAccount: payload.openaiAccount
        },
        { headers: { ...authHeaders(), 'Content-Type': 'application/json' } }
      );
      return data?.bot;
    } catch (err: any) {
      error.value = err?.response?.data?.detail || 'Erro ao criar bot';
      throw err;
    } finally {
      loading.value = false;
    }
  };

  const deleteBot = async (botKey: string): Promise<void> => {
    loading.value = true;
    error.value = null;
    try {
      await axios.delete(`${apiBase}/custom-bots/${botKey}`, {
        headers: authHeaders()
      });
    } catch (err: any) {
      error.value = err?.response?.data?.detail || 'Erro ao remover bot';
      throw err;
    } finally {
      loading.value = false;
    }
  };

  return {
    loading,
    error,
    listBots,
    createBot,
    deleteBot
  };
}

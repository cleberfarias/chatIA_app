<template>
  <transition name="slide-up">
    <div v-if="modelValue" class="voice-recorder-whatsapp">
      <!-- Barra de gravação (durante gravação) -->
      <div v-if="isRecording && !audioBlob" class="recording-bar">
        <!-- Botão deletar/cancelar -->
        <v-btn
          icon
          size="40"
          variant="text"
          @click="handleCancel"
        >
          <v-icon color="white">mdi-delete</v-icon>
        </v-btn>

        <!-- Visualização de ondas + Timer -->
        <div class="recording-content">
          <div class="recording-wave">
            <div class="wave-bar" v-for="i in 30" :key="i" :style="{ animationDelay: `${i * 0.05}s` }"></div>
          </div>
          <span class="recording-time">{{ formattedTime }}</span>
        </div>

        <!-- Texto "Deslize para cancelar" -->
        <div class="slide-to-cancel">
          <v-icon size="16" color="rgba(255,255,255,0.6)">mdi-chevron-left</v-icon>
          <span>Deslize para cancelar</span>
        </div>

        <!-- Botão enviar -->
        <v-btn
          icon
          size="48"
          color="success"
          elevation="0"
          @click="stopRecording"
        >
          <v-icon color="white">mdi-send</v-icon>
        </v-btn>
      </div>

      <!-- Barra de preview (após gravar) -->
      <div v-if="!isRecording && audioBlob" class="preview-bar">
        <!-- Botão deletar -->
        <v-btn
          icon
          size="40"
          variant="text"
          @click="deleteRecording"
        >
          <v-icon color="white">mdi-close</v-icon>
        </v-btn>

        <!-- Visualização do áudio gravado -->
        <div class="audio-preview">
          <v-btn
            icon
            size="32"
            color="white"
            variant="text"
            @click="playAudio"
          >
            <v-icon color="success">{{ isPlaying ? 'mdi-pause' : 'mdi-play' }}</v-icon>
          </v-btn>
          
          <div class="audio-waveform">
            <div class="waveform-bar" v-for="i in 40" :key="i"></div>
          </div>
          
          <span class="audio-time">{{ formattedTime }}</span>
        </div>

        <!-- Botão enviar -->
        <v-btn
          icon
          size="48"
          color="success"
          elevation="0"
          @click="sendAudio"
          :loading="sending"
        >
          <v-icon color="white">mdi-send</v-icon>
        </v-btn>
      </div>

      <!-- Mensagem de erro -->
      <v-snackbar
        v-model="showError"
        color="error"
        :timeout="3000"
        location="top"
      >
        {{ error }}
      </v-snackbar>
    </div>
  </transition>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue';

interface Props {
  modelValue: boolean;
}

const props = defineProps<Props>();

const emit = defineEmits<{
  'update:modelValue': [value: boolean];
  'audio-recorded': [blob: Blob];
}>();

const isRecording = ref(false);
const isPlaying = ref(false);
const sending = ref(false);
const audioBlob = ref<Blob | null>(null);
const mediaRecorder = ref<MediaRecorder | null>(null);
const audioChunks = ref<Blob[]>([]);
const recordingTime = ref(0);
const error = ref('');
const showError = ref(false);
const audioContext = ref<AudioContext | null>(null);
const analyser = ref<AnalyserNode | null>(null);
const animationId = ref<number | null>(null);
const timerInterval = ref<number | null>(null);
const audioElement = ref<HTMLAudioElement | null>(null);

const formattedTime = computed(() => {
  const minutes = Math.floor(recordingTime.value / 60);
  const seconds = recordingTime.value % 60;
  return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
});

watch(() => props.modelValue, async (newValue) => {
  if (newValue) {
    // Inicia gravação automaticamente ao abrir
    await startRecording();
  } else {
    cleanup();
  }
});

async function startRecording() {
  try {
    error.value = '';
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    
    // Configura MediaRecorder
    mediaRecorder.value = new MediaRecorder(stream);
    audioChunks.value = [];
    
    mediaRecorder.value.ondataavailable = (event) => {
      if (event.data.size > 0) {
        audioChunks.value.push(event.data);
      }
    };
    
    mediaRecorder.value.onstop = () => {
      const blob = new Blob(audioChunks.value, { type: 'audio/webm' });
      audioBlob.value = blob;
      stream.getTracks().forEach(track => track.stop());
      
      if (animationId.value) {
        cancelAnimationFrame(animationId.value);
      }
    };
    
    // Inicia gravação
    mediaRecorder.value.start();
    isRecording.value = true;
    recordingTime.value = 0;
    
    // Timer
    timerInterval.value = setInterval(() => {
      recordingTime.value++;
      
      // Limita gravação a 5 minutos
      if (recordingTime.value >= 300) {
        stopRecording();
      }
    }, 1000);
    
    // Visualização de onda
    setupAudioVisualization(stream);
    
  } catch (err) {
    error.value = 'Erro ao acessar microfone. Permita o acesso nas configurações.';
    showError.value = true;
    console.error('Erro ao gravar áudio:', err);
    emit('update:modelValue', false);
  }
}

function stopRecording() {
  if (mediaRecorder.value && isRecording.value) {
    mediaRecorder.value.stop();
    isRecording.value = false;
    
    if (timerInterval.value) {
      clearInterval(timerInterval.value);
      timerInterval.value = null;
    }
    
    if (animationId.value) {
      cancelAnimationFrame(animationId.value);
    }
  }
}

function setupAudioVisualization(stream: MediaStream) {
  // Simplificado - não usamos mais canvas visual
  audioContext.value = new AudioContext();
  analyser.value = audioContext.value.createAnalyser();
  const source = audioContext.value.createMediaStreamSource(stream);
  source.connect(analyser.value);
}

function playAudio() {
  if (!audioBlob.value) return;
  
  if (isPlaying.value) {
    audioElement.value?.pause();
    isPlaying.value = false;
    return;
  }
  
  const url = URL.createObjectURL(audioBlob.value);
  audioElement.value = new Audio(url);
  
  audioElement.value.onended = () => {
    isPlaying.value = false;
  };
  
  audioElement.value.play();
  isPlaying.value = true;
}

function deleteRecording() {
  audioBlob.value = null;
  recordingTime.value = 0;
  isPlaying.value = false;
  
  if (audioElement.value) {
    audioElement.value.pause();
    audioElement.value = null;
  }
}

async function sendAudio() {
  if (!audioBlob.value) return;
  
  sending.value = true;
  emit('audio-recorded', audioBlob.value);
  
  // Fecha o dialog após 500ms
  setTimeout(() => {
    sending.value = false;
    emit('update:modelValue', false);
    cleanup();
  }, 500);
}

function handleCancel() {
  if (isRecording.value) {
    stopRecording();
  }
  emit('update:modelValue', false);
  cleanup();
}

function cleanup() {
  if (mediaRecorder.value) {
    mediaRecorder.value.stream?.getTracks().forEach(track => track.stop());
  }
  
  if (timerInterval.value) {
    clearInterval(timerInterval.value);
  }
  
  if (animationId.value) {
    cancelAnimationFrame(animationId.value);
  }
  
  if (audioElement.value) {
    audioElement.value.pause();
  }
  
  if (audioContext.value) {
    audioContext.value.close();
  }
  
  isRecording.value = false;
  isPlaying.value = false;
  audioBlob.value = null;
  recordingTime.value = 0;
  error.value = '';
}
</script>

<style scoped>
/* Animação de entrada */
.slide-up-enter-active,
.slide-up-leave-active {
  transition: transform 0.3s ease;
}

.slide-up-enter-from {
  transform: translateY(100%);
}

.slide-up-leave-to {
  transform: translateY(100%);
}

/* Container principal */
.voice-recorder-whatsapp {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 9999;
}

/* Barra de gravação */
.recording-bar {
  background: color-mix(in srgb, var(--ds-color-text-primary) 90%, black);
  padding: var(--ds-spacing-md) var(--ds-spacing-lg);
  display: flex;
  align-items: center;
  gap: var(--ds-spacing-md);
  box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.3);
}

.recording-content {
  flex: 1;
  display: flex;
  align-items: center;
  gap: var(--ds-spacing-md);
}

/* Ondas de gravação */
.recording-wave {
  display: flex;
  align-items: center;
  gap: 2px;
  height: 32px;
  flex: 1;
}

.wave-bar {
  width: 3px;
  height: 8px;
  background: rgba(255, 255, 255, 0.6);
  border-radius: 2px;
  animation: wave-pulse 1.2s ease-in-out infinite;
}

@keyframes wave-pulse {
  0%, 100% {
    height: 8px;
    opacity: 0.6;
  }
  50% {
    height: 24px;
    opacity: 1;
  }
}

/* Timer de gravação */
.recording-time {
  color: rgba(255, 255, 255, 0.9);
  font-size: 16px;
  font-weight: 500;
  font-family: 'Roboto', sans-serif;
  min-width: 60px;
}

/* Texto "Deslize para cancelar" */
.slide-to-cancel {
  position: absolute;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%);
  display: flex;
  align-items: center;
  gap: 4px;
  color: rgba(255, 255, 255, 0.6);
  font-size: 14px;
  pointer-events: none;
}

/* Barra de preview */
.preview-bar {
  background: color-mix(in srgb, var(--ds-color-text-primary) 90%, black);
  padding: var(--ds-spacing-md) var(--ds-spacing-lg);
  display: flex;
  align-items: center;
  gap: var(--ds-spacing-md);
  box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.3);
}

.audio-preview {
  flex: 1;
  display: flex;
  align-items: center;
  gap: var(--ds-spacing-md);
  background: rgba(255, 255, 255, 0.1);
  border-radius: var(--ds-radius-xl);
  padding: var(--ds-spacing-sm) var(--ds-spacing-lg);
}

/* Waveform do áudio gravado */
.audio-waveform {
  display: flex;
  align-items: center;
  gap: 2px;
  height: 32px;
  flex: 1;
}

.waveform-bar {
  width: 2px;
  background: var(--ds-color-success);
  border-radius: 1px;
}

.waveform-bar:nth-child(1) { height: 12px; }
.waveform-bar:nth-child(2) { height: 18px; }
.waveform-bar:nth-child(3) { height: 24px; }
.waveform-bar:nth-child(4) { height: 16px; }
.waveform-bar:nth-child(5) { height: 20px; }
.waveform-bar:nth-child(6) { height: 28px; }
.waveform-bar:nth-child(7) { height: 22px; }
.waveform-bar:nth-child(8) { height: 14px; }
.waveform-bar:nth-child(9) { height: 26px; }
.waveform-bar:nth-child(10) { height: 18px; }
.waveform-bar:nth-child(11) { height: 20px; }
.waveform-bar:nth-child(12) { height: 24px; }
.waveform-bar:nth-child(13) { height: 16px; }
.waveform-bar:nth-child(14) { height: 22px; }
.waveform-bar:nth-child(15) { height: 28px; }
.waveform-bar:nth-child(16) { height: 14px; }
.waveform-bar:nth-child(17) { height: 18px; }
.waveform-bar:nth-child(18) { height: 24px; }
.waveform-bar:nth-child(19) { height: 20px; }
.waveform-bar:nth-child(20) { height: 16px; }
.waveform-bar:nth-child(21) { height: 22px; }
.waveform-bar:nth-child(22) { height: 26px; }
.waveform-bar:nth-child(23) { height: 18px; }
.waveform-bar:nth-child(24) { height: 14px; }
.waveform-bar:nth-child(25) { height: 20px; }
.waveform-bar:nth-child(26) { height: 24px; }
.waveform-bar:nth-child(27) { height: 16px; }
.waveform-bar:nth-child(28) { height: 28px; }
.waveform-bar:nth-child(29) { height: 22px; }
.waveform-bar:nth-child(30) { height: 18px; }
.waveform-bar:nth-child(31) { height: 12px; }
.waveform-bar:nth-child(32) { height: 16px; }
.waveform-bar:nth-child(33) { height: 20px; }
.waveform-bar:nth-child(34) { height: 24px; }
.waveform-bar:nth-child(35) { height: 18px; }
.waveform-bar:nth-child(36) { height: 14px; }
.waveform-bar:nth-child(37) { height: 22px; }
.waveform-bar:nth-child(38) { height: 26px; }
.waveform-bar:nth-child(39) { height: 20px; }
.waveform-bar:nth-child(40) { height: 16px; }

.audio-time {
  color: rgba(255, 255, 255, 0.9);
  font-size: var(--ds-font-size-base);
  font-weight: var(--ds-font-weight-medium);
  min-width: 50px;
  text-align: right;
}

/* Responsivo */
@media (max-width: 599px) {
  .recording-bar,
  .preview-bar {
    padding: var(--ds-spacing-sm) var(--ds-spacing-md);
  }

  .recording-time,
  .audio-time {
    font-size: var(--ds-font-size-base);
  }

  .slide-to-cancel {
    font-size: 12px;
  }
}
</style>

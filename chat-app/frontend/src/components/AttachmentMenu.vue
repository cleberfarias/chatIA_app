<template>
  <v-menu
    :model-value="modelValue"
    @update:model-value="$emit('update:modelValue', $event)"
    location="top"
    :close-on-content-click="false"
    offset="16"
  >
    <template v-slot:activator="{ props }">
      <slot name="activator" :props="props" />
    </template>

    <div class="attachment-menu">
      <!-- 📄 DOCUMENTO -->
      <div class="attachment-option document" @click="handleDocumentClick">
        <v-btn
          icon
          size="56"
          color="#7F66FF"
          elevation="4"
        >
          <v-icon size="28">mdi-file-document</v-icon>
        </v-btn>
        <span class="option-label">Documento</span>
      </div>

      <!-- 📷 CÂMERA -->
      <div class="attachment-option camera" @click="handleCameraClick">
        <v-btn
          icon
          size="56"
          color="#FF4081"
          elevation="4"
        >
          <v-icon size="28">mdi-camera</v-icon>
        </v-btn>
        <span class="option-label">Câmera</span>
      </div>

      <!-- 🖼️ GALERIA -->
      <div class="attachment-option gallery" @click="handleGalleryClick">
        <v-btn
          icon
          size="56"
          color="#00BFA5"
          elevation="4"
        >
          <v-icon size="28">mdi-image</v-icon>
        </v-btn>
        <span class="option-label">Galeria</span>
      </div>

      <!-- 🎵 ÁUDIO -->
      <div class="attachment-option audio" @click="handleAudioClick">
        <v-btn
          icon
          size="56"
          color="#FF6F00"
          elevation="4"
        >
          <v-icon size="28">mdi-headphones</v-icon>
        </v-btn>
        <span class="option-label">Áudio</span>
      </div>

      <!-- 📍 LOCALIZAÇÃO -->
      <div class="attachment-option location" @click="handleLocationClick">
        <v-btn
          icon
          size="56"
          color="#4CAF50"
          elevation="4"
        >
          <v-icon size="28">mdi-map-marker</v-icon>
        </v-btn>
        <span class="option-label">Localização</span>
      </div>

      <!-- 👤 CONTATO -->
      <div class="attachment-option contact" @click="handleContactClick">
        <v-btn
          icon
          size="56"
          color="#2196F3"
          elevation="4"
        >
          <v-icon size="28">mdi-account</v-icon>
        </v-btn>
        <span class="option-label">Contato</span>
      </div>
    </div>

    <!-- Input oculto para upload de arquivos -->
    <input
      ref="fileInput"
      type="file"
      style="display: none"
      @change="handleFileChange"
      :accept="acceptedFileTypes"
      multiple
    />

    <input
      ref="imageInput"
      type="file"
      style="display: none"
      @change="handleImageChange"
      accept="image/*"
      multiple
    />

    <input
      ref="cameraInput"
      type="file"
      style="display: none"
      @change="handleCameraChange"
      accept="image/*"
      capture="environment"
    />
  </v-menu>
</template>

<script setup lang="ts">
import { ref } from 'vue';

interface Props {
  modelValue: boolean;
}

defineProps<Props>();

const emit = defineEmits<{
  'update:modelValue': [value: boolean];
  'file-selected': [files: FileList];
}>();

const fileInput = ref<HTMLInputElement>();
const imageInput = ref<HTMLInputElement>();
const cameraInput = ref<HTMLInputElement>();
const acceptedFileTypes = ref('*/*');

function handleDocumentClick() {
  acceptedFileTypes.value = '.pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.txt,.zip,.rar';
  fileInput.value?.click();
}

function handleGalleryClick() {
  imageInput.value?.click();
}

function handleCameraClick() {
  cameraInput.value?.click();
}

function handleAudioClick() {
  acceptedFileTypes.value = 'audio/*';
  fileInput.value?.click();
}

function handleLocationClick() {
  // TODO: Implementar compartilhamento de localização
  console.log('🗺️ Localização em desenvolvimento');
  emit('update:modelValue', false);
}

function handleContactClick() {
  // TODO: Implementar compartilhamento de contato
  console.log('👤 Contato em desenvolvimento');
  emit('update:modelValue', false);
}

function handleFileChange(event: Event) {
  const target = event.target as HTMLInputElement;
  if (target.files && target.files.length > 0) {
    emit('file-selected', target.files);
    emit('update:modelValue', false);
    target.value = ''; // Reset input
  }
}

function handleImageChange(event: Event) {
  const target = event.target as HTMLInputElement;
  if (target.files && target.files.length > 0) {
    emit('file-selected', target.files);
    emit('update:modelValue', false);
    target.value = ''; // Reset input
  }
}

function handleCameraChange(event: Event) {
  const target = event.target as HTMLInputElement;
  if (target.files && target.files.length > 0) {
    emit('file-selected', target.files);
    emit('update:modelValue', false);
    target.value = ''; // Reset input
  }
}
</script>

<style scoped>
.attachment-menu {
  background: white;
  border-radius: 16px;
  padding: 16px;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  min-width: 280px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}

/* 📱 Mobile - Grid 2 colunas, botões menores */
@media (max-width: 599px) {
  .attachment-menu {
    grid-template-columns: repeat(2, 1fr);
    gap: 16px;
    min-width: 240px;
    padding: 12px;
  }
}

/* 📱 Tablet - Grid 3 colunas */
@media (min-width: 600px) and (max-width: 959px) {
  .attachment-menu {
    grid-template-columns: repeat(3, 1fr);
    min-width: 300px;
  }
}

.attachment-option {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  transition: transform 0.2s ease;
}

/* 🖱️ Desktop - Hover */
@media (hover: hover) and (pointer: fine) {
  .attachment-option:hover {
    transform: scale(1.05);
  }
}

/* 📱 Mobile - Touch */
@media (hover: none) and (pointer: coarse) {
  .attachment-option:active {
    transform: scale(0.95);
  }
}

.option-label {
  font-size: 12px;
  color: rgba(0, 0, 0, 0.6);
  font-weight: 500;
  text-align: center;
  white-space: nowrap;
}

/* 📱 Mobile - Texto menor */
@media (max-width: 599px) {
  .option-label {
    font-size: 11px;
  }
}

/* Animação de entrada dos botões */
.attachment-option {
  animation: fadeInUp 0.3s ease forwards;
  opacity: 0;
}

.attachment-option.document { animation-delay: 0.05s; }
.attachment-option.camera { animation-delay: 0.1s; }
.attachment-option.gallery { animation-delay: 0.15s; }
.attachment-option.audio { animation-delay: 0.2s; }
.attachment-option.location { animation-delay: 0.25s; }
.attachment-option.contact { animation-delay: 0.3s; }

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>

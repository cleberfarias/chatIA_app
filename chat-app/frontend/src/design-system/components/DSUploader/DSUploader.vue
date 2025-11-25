<template>
  <div class="uploader">
    <!-- Zona de drop -->
    <div
      class="dropzone"
      :class="{ 'is-dragover': isDragOver }"
      @dragover.prevent="onDragOver"
      @dragleave.prevent="onDragLeave"
      @drop.prevent="onDrop"
    >
      <div class="dz-content">
        <v-icon size="36">mdi-cloud-upload</v-icon>
        <div class="mt-2">
          <strong>Arraste arquivos</strong> ou
          <v-btn size="small" variant="tonal" class="ml-1" @click="openPicker">escolha</v-btn>
        </div>
        <div class="hint">Imagens (png, jpg, webp) e PDFs/ZIP/TXT. Máx {{ maxMb }} MB.</div>
      </div>
      <input ref="fileInput" type="file" :accept="accept" :multiple="multiple" class="hidden-input" @change="onPick" />
    </div>

    <!-- Prévias & progresso -->
    <div v-if="items.length" class="preview-list">
      <div v-for="it in items" :key="it.id" class="preview-item">
        <div class="left">
          <template v-if="it.previewUrl && it.kind === 'image'">
            <img :src="it.previewUrl" alt="" class="thumb" />
          </template>
          <template v-else>
            <v-icon>mdi-file</v-icon>
          </template>
        </div>

        <div class="center">
          <div class="name">{{ it.file.name }}</div>
          <div class="meta">{{ humanSize(it.file.size) }} • {{ it.file.type || 'arquivo' }}</div>
          <v-progress-linear
            v-if="it.status==='uploading' || it.progress < 100"
            :model-value="it.progress"
            height="6"
            class="mt-1"
          />
          <div v-if="it.error" class="error">{{ it.error }}</div>
          <div v-if="it.status==='done'" class="ok">Enviado ✔</div>
        </div>

        <div class="right">
          <v-btn v-if="it.status==='idle' || it.error" size="small" variant="text" @click="startUpload(it)">Enviar</v-btn>
          <v-btn v-if="it.status==='done'" size="small" variant="text" @click="removeItem(it.id)">Remover</v-btn>
          <v-btn v-if="it.status==='uploading'" size="small" variant="text" disabled>Enviando…</v-btn>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onBeforeUnmount } from 'vue'
import { uploadAndSend } from '@/composables/useUpload'

type LocalItem = {
  id: string
  file: File
  previewUrl?: string
  kind: 'image' | 'file'
  progress: number
  status: 'idle' | 'uploading' | 'done'
  error?: string
}

const props = defineProps<{
  baseUrl: string
  author: string
  token: string | null
  contactId?: string | null
  multiple?: boolean
  maxMb?: number
  accept?: string
}>()

const emit = defineEmits<{
  (e: 'uploaded', message: any): void
}>()

const multiple = props.multiple ?? true
const maxMb = props.maxMb ?? 15
const accept = props.accept ?? 'image/png,image/jpeg,image/webp,application/pdf,application/zip,text/plain'

const isDragOver = ref(false)
const fileInput = ref<HTMLInputElement | null>(null)
const items = reactive<LocalItem[]>([])

function openPicker() {
  fileInput.value?.click()
}

function onDragOver() {
  isDragOver.value = true
}
function onDragLeave() {
  isDragOver.value = false
}

function addFiles(files: FileList | File[]) {
  const arr = Array.from(files)
  for (const f of arr) {
    const sizeMb = Math.ceil(f.size / (1024 * 1024))
    if (sizeMb > maxMb) {
      items.push({ id: crypto.randomUUID(), file: f, progress: 0, status: 'idle', kind: 'file', error: `Arquivo > ${maxMb}MB` })
      continue
    }
    const isImg = (f.type || '').startsWith('image/')
    const obj: LocalItem = {
      id: crypto.randomUUID(),
      file: f,
      previewUrl: isImg ? URL.createObjectURL(f) : undefined,
      kind: isImg ? 'image' : 'file',
      progress: 0,
      status: 'idle',
    }
    items.push(obj)
  }
}

function onDrop(e: DragEvent) {
  isDragOver.value = false
  if (!e.dataTransfer?.files?.length) return
  addFiles(e.dataTransfer.files)
}

function onPick(e: Event) {
  const input = e.target as HTMLInputElement
  if (!input.files?.length) return
  addFiles(input.files)
  input.value = ''
}

async function startUpload(it: LocalItem) {
  it.error = undefined
  it.status = 'uploading'
  try {
    if (!props.token) {
      throw new Error('Token JWT ausente para upload')
    }
    
    const message = await uploadAndSend(
      props.baseUrl,
      it.file,
      props.author,
      props.token,
      props.contactId,
      (pct) => {
        it.progress = pct
      }
    )
    it.progress = 100
    it.status = 'done'
    emit('uploaded', message) // opcional: o socket já fará broadcast; mas o pai pode reagir
  } catch (err: any) {
    it.error = err?.message || 'Falha no upload'
    it.status = 'idle'
  }
}

function removeItem(id: string) {
  const idx = items.findIndex(i => i.id === id)
  if (idx < 0) return
  
  const obj = items[idx]!
  if (obj.previewUrl) URL.revokeObjectURL(obj.previewUrl)
  items.splice(idx, 1)
}

onBeforeUnmount(() => {
  items.forEach(i => i.previewUrl && URL.revokeObjectURL(i.previewUrl))
})

function humanSize(n: number) {
  const mb = n / (1024 * 1024)
  if (mb >= 1) return `${mb.toFixed(1)} MB`
  const kb = n / 1024
  return `${kb.toFixed(0)} KB`
}
</script>

<style scoped>
.uploader { 
  display: flex; 
  flex-direction: column; 
  gap: var(--ds-spacing-md); 
}

.dropzone {
  border: 2px dashed var(--ds-color-border);
  border-radius: var(--ds-radius-lg);
  padding: var(--ds-spacing-lg);
  text-align: center;
  transition: background 0.2s, border-color 0.2s;
}

.dropzone.is-dragover { 
  background: color-mix(in srgb, var(--ds-color-primary) 6%, transparent);
  border-color: var(--ds-color-primary);
}

.dz-content .hint { 
  color: var(--ds-color-text-secondary);
  font-size: var(--ds-font-size-sm);
  margin-top: var(--ds-spacing-xs);
}

.hidden-input { display: none; }

.preview-list { 
  display: flex; 
  flex-direction: column; 
  gap: var(--ds-spacing-sm);
}

.preview-item { 
  display: grid; 
  grid-template-columns: 56px 1fr auto; 
  gap: var(--ds-spacing-md);
  align-items: center; 
  padding: var(--ds-spacing-sm);
  border: 1px solid var(--ds-color-border);
  border-radius: var(--ds-radius-md);
}

.thumb { 
  width: 56px; 
  height: 56px; 
  object-fit: cover; 
  border-radius: var(--ds-radius-md);
  border: 1px solid var(--ds-color-border);
}

.name { 
  font-weight: var(--ds-font-weight-semibold);
}

.meta { 
  font-size: var(--ds-font-size-sm);
  color: var(--ds-color-text-secondary);
}

.error { 
  color: var(--ds-color-error);
  font-size: var(--ds-font-size-sm);
  margin-top: var(--ds-spacing-xs);
}

.ok { 
  color: var(--ds-color-success);
  font-size: var(--ds-font-size-sm);
  margin-top: var(--ds-spacing-xs);
}
</style>

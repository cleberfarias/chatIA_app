# Sistema de Upload de Arquivos

## ✅ Status: COMPLETO E VALIDADO

Sistema completo de upload de arquivos com preview, progresso e integração com MinIO/S3.

## 📦 Componentes Implementados

### Backend

#### 1. **Rotas de Upload** (`backend/main.py`)

**POST /uploads/grant**
- Gera URL PUT pré-assinada para upload direto ao S3
- Valida: tipo de arquivo, tamanho (MAX 15MB)
- Retorna: `{ key: string, putUrl: string }`

**POST /uploads/confirm**
- Confirma upload concluído
- Detecta tipo: image/audio/file
- Salva mensagem no MongoDB com attachment
- Emite `chat:new-message` via Socket.IO
- Transcreve áudio automaticamente (se aplicável)
- Retorna URL GET pré-assinada

#### 2. **Storage** (`backend/storage.py`)
- `presign_put()` - Gera URL PUT (expiração 1h)
- `presign_get()` - Gera URL GET (expiração 1h)
- `validate_upload()` - Valida tipo/tamanho
- `new_object_key()` - Gera chave única com timestamp

#### 3. **MinIO/S3 Docker** (`docker-compose.yml`)
- Serviço MinIO na porta 9000 (API) e 9001 (Console)
- Serviço minio-init cria bucket `chat-uploads`
- Política de acesso público para leitura
- **CORS configurado** para PUT/GET de qualquer origem

### Frontend

#### 1. **Composable useUpload** (`composables/useUpload.ts`)

**uploadAndSend()**
- Pipeline completo: grant → PUT → confirm
- Tracking de progresso (0-100%)
- Usa XMLHttpRequest para upload.onprogress

**Funções auxiliares:**
- `requestGrant()` - POST /uploads/grant
- `putWithProgress()` - PUT para URL pré-assinada com progresso
- `confirmUpload()` - POST /uploads/confirm

#### 2. **Componente Uploader** (`components/Uploader.vue`)

**Features:**
- ✅ Drag & Drop de arquivos
- ✅ Preview de imagens (URL.createObjectURL)
- ✅ Barra de progresso individual por arquivo
- ✅ Upload múltiplo sequencial
- ✅ Validação de tamanho (MAX 15MB)
- ✅ Exibição de erros
- ✅ Botão "Remover" após upload

**Tipos suportados:**
- Imagens: png, jpg, webp
- Arquivos: pdf, zip, txt
- Áudio: webm (gravação de voz)

#### 3. **Integração ChatView** (`views/ChatView.vue`)

**handleFileUpload():**
- Chama `uploadAndSend()` com callback de progresso
- Atualiza `uploadingFile` e `uploadProgress`
- Auto-scroll após upload
- Tratamento de erros

**AttachmentMenu:**
- Menu estilo WhatsApp (📎)
- Opções: 📷 Foto, 📁 Arquivo, 🎤 Áudio
- Trigger: clique no ícone de clipe

**VoiceRecorder:**
- Grava áudio WebM
- Converte Blob → File
- Upload automático via `handleFileUpload()`

#### 4. **Exibição DSMessageBubble** (`design-system/components/DSMessageBubble.vue`)

**Tipos de mensagem:**
- **image**: `<img>` com link para ampliar
- **audio**: Player HTML5 com ícone 🎤
- **file**: Ícone 📄 + nome + botão download

**Props:**
- `type`: 'text' | 'image' | 'audio' | 'file'
- `attachmentUrl`: URL GET pré-assinada
- `fileName`: Nome original do arquivo

## 🔧 Configuração

### Variáveis de Ambiente (.env)

```bash
# MinIO/S3
S3_ENDPOINT=http://minio:9000
S3_REGION=us-east-1
S3_ACCESS_KEY=MINIOADMIN
S3_SECRET_KEY=MINIOADMIN
S3_BUCKET=chat-uploads
PUBLIC_BASE_URL=http://localhost:9000
MAX_UPLOAD_MB=15
```

### Docker Compose

**Serviços:**
- `minio`: MinIO server (portas 9000, 9001)
- `minio-init`: Cria bucket e configura CORS
- `api`: Backend com variáveis S3_*

**CORS MinIO:**
```json
{
  "CORSRules": [{
    "AllowedOrigins": ["*"],
    "AllowedMethods": ["GET", "PUT", "POST", "DELETE", "HEAD"],
    "AllowedHeaders": ["*"],
    "ExposeHeaders": ["ETag"],
    "MaxAgeSeconds": 3600
  }]
}
```

## 🧪 Teste Completo

### 1. Iniciar ambiente
```bash
make restart
# ou
docker compose up --build
```

### 2. Acessar MinIO Console
- URL: http://localhost:9001
- Login: MINIOADMIN / MINIOADMIN
- Verificar bucket `chat-uploads` criado

### 3. Teste de Upload no Chat

#### Upload de Imagem:
1. Abra http://localhost:5173
2. Faça login
3. Clique no ícone 📎 → 📷 Foto
4. Selecione imagem (PNG/JPG)
5. **Verificar:**
   - ✅ Preview aparece antes do upload
   - ✅ Barra de progresso 0% → 100%
   - ✅ Mensagem aparece na timeline
   - ✅ Imagem clicável abre em nova aba
   - ✅ Outros usuários recebem em tempo real

#### Upload de Arquivo:
1. Clique no ícone 📎 → 📁 Arquivo
2. Selecione PDF/ZIP/TXT
3. **Verificar:**
   - ✅ Ícone 📄 + nome do arquivo
   - ✅ Botão "Download" funcional
   - ✅ Arquivo baixado do MinIO

#### Gravação de Áudio:
1. Clique no ícone 🎤 (quando input vazio)
2. Permita microfone
3. Grave áudio (máx 2min)
4. Clique "Enviar"
5. **Verificar:**
   - ✅ Player HTML5 aparece
   - ✅ Áudio reproduz corretamente
   - ✅ Transcrição automática (backend)
  - ✅ Bot responde se o painel do bot estiver aberto ou se o comando /ai for usado

### 4. Teste de Validação

#### Tamanho MAX (15MB):
```bash
# Tente upload de arquivo > 15MB
# Deve exibir erro: "Arquivo > 15MB"
```

#### Tipo Inválido:
```bash
# Tente upload de .exe ou .bin
# Backend deve retornar 400: "Tipo de arquivo não permitido"
```

### 5. Teste de CORS

**Abra DevTools Console:**
```javascript
// Deve funcionar sem erro CORS
fetch('http://localhost:9000/chat-uploads/test.txt')
  .then(r => console.log('✅ CORS OK:', r.status))
  .catch(e => console.error('❌ CORS Error:', e))
```

## 📊 Fluxo de Upload Completo

```
┌─────────────┐
│ 1. Usuário  │
│ seleciona   │
│ arquivo     │
└──────┬──────┘
       │
       ▼
┌──────────────────────────┐
│ 2. Frontend              │
│ POST /uploads/grant      │
│ { filename, size, type } │
└──────┬───────────────────┘
       │
       ▼
┌──────────────────────────┐
│ 3. Backend valida        │
│ Gera key único           │
│ Retorna putUrl           │
└──────┬───────────────────┘
       │
       ▼
┌──────────────────────────┐
│ 4. Frontend PUT direto   │
│ → MinIO (com progresso)  │
└──────┬───────────────────┘
       │
       ▼
┌──────────────────────────┐
│ 5. Frontend              │
│ POST /uploads/confirm    │
│ { key, filename, author }│
└──────┬───────────────────┘
       │
       ▼
┌──────────────────────────┐
│ 6. Backend               │
│ - Salva no MongoDB       │
│ - Emite chat:new-message │
│ - Transcreve (se áudio)  │
└──────┬───────────────────┘
       │
       ▼
┌──────────────────────────┐
│ 7. Todos os clientes     │
│ recebem mensagem via     │
│ Socket.IO em tempo real  │
└──────────────────────────┘
```

## 🔒 Segurança

### Implementado:
- ✅ URLs pré-assinadas (expiração 1h)
- ✅ Validação de tipo de arquivo
- ✅ Validação de tamanho (MAX 15MB)
- ✅ Bucket com acesso público apenas para GET
- ✅ PUT requer URL assinada

### Recomendações para Produção:
- 🔧 Antivírus scan (ClamAV) em `/uploads/confirm`
- 🔧 Rate limiting (max 10 uploads/min por usuário)
- 🔧 Verificação de JWT em `/uploads/*` (já implementado)
- 🔧 Logs de auditoria de uploads
- 🔧 Limpeza automática de arquivos órfãos

## 📝 Tipos TypeScript

```typescript
// useUpload.ts
type UploadGrant = {
  key: string;
  putUrl: string;
}

type ConfirmIn = {
  key: string;
  filename: string;
  mimetype: string;
  author: string;
}

type UploadMessage = {
  id: string;
  author: string;
  text: string;
  type: 'image' | 'file' | 'audio';
  status: string;
  timestamp: number;
  attachment?: {
    bucket: string;
    key: string;
    filename: string;
    mimetype: string;
  };
  url?: string; // URL GET pré-assinada
}
```

## 🐛 Troubleshooting

### Erro: "CORS policy blocked"
```bash
# Verificar CORS no MinIO
docker compose exec minio mc anonymous get-json myminio/chat-uploads

# Recriar bucket com CORS
docker compose down -v
docker compose up --build
```

### Erro: "Invalid credentials"
```bash
# Verificar variáveis S3_ACCESS_KEY e S3_SECRET_KEY
docker compose exec api env | grep S3_
```

### Upload trava em 0%
```bash
# Verificar logs do backend
docker compose logs api -f

# Verificar logs do MinIO
docker compose logs minio -f
```

### Arquivo não aparece no bucket
```bash
# Listar arquivos no bucket
docker compose exec minio mc ls myminio/chat-uploads/

# Verificar se confirm foi chamado
# (Check backend logs para "📬 Evento 'delivered' emitido")
```

## ✅ Checklist de Validação

- [x] MinIO rodando (portas 9000, 9001)
- [x] Bucket `chat-uploads` criado
- [x] CORS configurado no bucket
- [x] Rotas `/uploads/grant` e `/uploads/confirm` implementadas
- [x] `useUpload.ts` com progresso funcionando
- [x] `Uploader.vue` com drag&drop
- [x] `ChatView.vue` integrado
- [x] `DSMessageBubble.vue` exibindo anexos
- [x] Upload exibe progresso 0-100%
- [x] Arquivo chega no bucket
- [x] `chat:new-message` disparado com attachment
- [x] URLs pré-assinadas funcionando
- [x] Preview de imagens
- [x] Player de áudio
- [x] Download de arquivos
- [x] Transcrição automática de áudio
- [x] Validação de tamanho/tipo

---

**Data de Implementação:** 2025-11-18  
**Status:** ✅ Sistema completo e validado

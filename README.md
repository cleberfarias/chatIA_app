# 💬 Chat App — Aplicação de Chat em Tempo Real (Vue 3 + FastAPI)

[![Vue 3](https://img.shields.io/badge/Vue-3.5-4FC08D?logo=vue.js)](https://vuejs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python)](https://www.python.org/)
[![Socket.IO](https://img.shields.io/badge/Socket.IO-4.8-010101?logo=socket.io)](https://socket.io/)
[![MongoDB](https://img.shields.io/badge/MongoDB-ReplicaSet-47A248?logo=mongodb)](https://www.mongodb.com/)
[![MinIO](https://img.shields.io/badge/Storage-MinIO%20(S3)-FD5E5E?logo=minio)](https://min.io/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker)](https://www.docker.com/)
[![Vuetify](https://img.shields.io/badge/Vuetify-3.10-1867C0?logo=vuetify)](https://vuetifyjs.com/)

> App de chat moderno, **Vue 3 + Pinia + Vuetify** no front e **FastAPI + python-socketio + Mongo** no back. Uploads via **MinIO (S3)** e **integração omnichannel** (WhatsApp/Instagram/Facebook).

---

## ✨ Recursos

- ✅ **Tempo real** com Socket.IO (WS)
- ✅ **Histórico persistido** em MongoDB (índice por `createdAt` + paginação)
- ✅ **Uploads** com URL pré‑assinada (MinIO/S3)
- ✅ **Autenticação JWT** + Socket protegido
- ✅ **UI** com Vuetify (dark/light), Pinia e Vue Router
- ✅ **Bots & Automações** (APScheduler: cron + keyword)
- ✅ **Omnichannel**: WhatsApp Cloud, Instagram Messaging, Facebook Messenger e WPPConnect (dev/homolog)
- ✅ **Docker Compose** para subir tudo localmente

---

## 🏗️ Arquitetura (visão)

**Core (Client ⇄ Server ⇄ Data)**  
![Arquitetura Core](arquitetura-core.png)

**Omnichannel (canais Meta + WPPConnect)**  
![Arquitetura Omnichannel](arquitetura-omni-clean.png)

> Se os diagramas não renderizarem aqui, baixe:
> - PNG Core: `arquitetura-core.png`
> - PNG Omnichannel: `arquitetura-omni-clean.png`

---

## 📋 Pré‑requisitos

- [Docker](https://www.docker.com/) e Docker Compose
- OU ambiente local com:
  - **Python 3.11+**
  - **Node 20+**
  - **MongoDB 6+** (com Replica Set ativo se for usar change streams)

---

## 🚀 Início Rápido

### 1) Com Docker (recomendado)

```bash
# 1. Clone
git clone https://github.com/cleberfarias/projeto_estudo.git
cd projeto_estudo/chat-app

# 2. Suba os serviços
docker compose up -d --build

# 3. (Apenas na 1ª vez) Inicie o Replica Set do Mongo
docker compose exec mongo mongosh --eval 'rs.initiate({_id:"rs0",members:[{_id:0,host:"mongo:27017"}]})'
```

Acesse:
- **Frontend**: http://localhost:5173  
- **Backend**:  http://localhost:3000 (docs em `/docs`)

### 2) Sem Docker (dev)

**Backend (FastAPI):**
```bash
cd backend
python -m venv .venv && source .venv/bin/activate  # (Windows: .venv\Scripts\activate)
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 3000
```

**Frontend (Vue 3 + Vite):**
```bash
cd frontend
npm install
npm run dev -- --host --port 5173
```

---

## 🧩 Estrutura do Projeto

```
chat-app/
├── backend/                      # FastAPI + python-socketio + Mongo (Motor)
│   ├── main.py                   # App principal, rotas e eventos WS
│   ├── database.py               # Conexão Mongo + coleções
│   ├── models.py                 # Pydantic models
│   ├── storage.py                # MinIO/S3 presign helpers
│   ├── bots/                     # Comandos e automações (APScheduler)
│   ├── routers/
│   │   └── omni.py               # /omni/send + sessões WPP
│   ├── meta.py                   # Graph API (WA Cloud, IG, FB)
│   ├── wpp.py                    # WPPConnect client (dev/homolog)
│   └── requirements.txt
├── frontend/                     # Vue 3 + Pinia + Vuetify
│   ├── src/
│   │   ├── stores/               # authStore, chatStore
│   │   ├── views/ChatView.vue    # tela principal do chat
│   │   ├── components/Uploader.vue
│   │   └── design-system/
│   └── vite.config.ts
├── docker-compose.yml            # Mongo, MinIO, API, Front e WPPConnect
└── README.md
```

---

## 🔌 API (principais)

### REST
- `POST /auth/register | /auth/login` — JWT (opcionalmente habilitado)
- `GET  /messages?limit=30&before=<ts>` — histórico paginado
- `POST /uploads/grant` — retorna `putUrl` (S3 presign)
- `POST /uploads/confirm` — cria mensagem com `attachment`
- `POST /omni/send` — **envio unificado**: `{ channel, recipient, text, session? }`
- `POST /automations` — cria automação (cron/keyword)

### WebSockets (Socket.IO)
- **Cliente → Servidor**
  - `chat:send` `{tempId?, author, text, type?}`
  - `chat:typing` `{isTyping: boolean}`
  - `chat:read` `{ids: string[]}`
- **Servidor → Cliente**
  - `chat:new-message` `{...message}`
  - `chat:ack` `{tempId, id, timestamp, status:'sent'}`
  - `chat:delivered` `{id}` / `chat:read` `{ids:[]}`

### Webhooks
- `GET/POST /webhooks/meta` — Meta (WhatsApp Cloud, Instagram, Messenger) com **HMAC X‑Hub‑Signature‑256**
- `POST /webhooks/wppconnect` — WPPConnect com **HMAC x-webhook-signature**

---

## ⚙️ Variáveis de Ambiente

Crie/edite `.env` (ou defina no `docker-compose.yml`).

**Frontend**
```env
VITE_SOCKET_URL=http://localhost:3000
```

**Backend (principais)**
```env
# Mongo
DATABASE_URL=mongodb://mongo:27017/chatdb?replicaSet=rs0

# Auth
JWT_SECRET=troque
JWT_TTL_MIN=60

# S3 / MinIO
S3_ENDPOINT=http://minio:9000
S3_REGION=us-east-1
S3_ACCESS_KEY=MINIOADMIN
S3_SECRET_KEY=MINIOADMIN
S3_BUCKET=chat-uploads
PUBLIC_BASE_URL=http://localhost:9000
MAX_UPLOAD_MB=15

# Meta (Graph)
META_APP_ID=...
META_APP_SECRET=...
META_VERIFY_TOKEN=...
META_PAGE_ID=...
META_PAGE_ACCESS_TOKEN=...
IG_BIZ_ACCOUNT_ID=...
IG_ACCESS_TOKEN=...
WA_PHONE_NUMBER_ID=...
WA_CLOUD_ACCESS_TOKEN=...

# WPPConnect
WPP_BASE_URL=http://wppconnect:21465
WPP_WEBHOOK_SECRET=super_secret_webhook
```

**CORS do bucket MinIO (na UI do MinIO):**
```json
[
  {
    "AllowedOrigin": ["http://localhost:5173"],
    "AllowedMethod": ["PUT", "GET"],
    "AllowedHeader": ["*"],
    "ExposeHeader": ["ETag"],
    "MaxAgeSeconds": 3000
  }
]
```

---

## 📡 Fluxos principais

### Upload (imagem/arquivo)
1. `POST /uploads/grant` → `{ key, putUrl }`  
2. `PUT putUrl` (binário direto ao S3)  
3. `POST /uploads/confirm` → cria mensagem + emite `chat:new-message`

### Envio otimista
1. Front cria `tempId` e envia `chat:send` (`status:'pending'`)  
2. Back persiste e devolve `chat:ack` (troca `tempId` por `id`)  
3. Status podem evoluir com `chat:delivered` e `chat:read`

### Omnichannel
- Envio: `POST /omni/send { channel, recipient, text }`  
- Recebimento: Webhooks → salva Mongo → `socket.emit('chat:new-message')`

---

## 🧪 Scripts & Dev

**Backend**
```bash
uvicorn main:app --reload --port 3000
pytest -q  # (se configurado)
```

**Frontend**
```bash
npm run dev
npm run build && npm run preview
```

---

## 🐛 Troubleshooting

- **Replica Set do Mongo não iniciado**  
  ```bash
  docker compose exec mongo mongosh --eval 'rs.initiate({_id:"rs0",members:[{_id:0,host:"mongo:27017"}]})'
  ```

- **CORS no upload (403/blocked)**  
  Verifique CORS do bucket no MinIO e `AllowedOrigin` apontando para `http://localhost:5173`.

- **Socket.IO atrás de proxy**  
  No Nginx, habilite `upgrade`/`connection` e aumente `proxy_read_timeout`.

- **Tokens Meta inválidos**  
  Use tokens **long‑lived**, vincule Página/IG Business e valide `verify_token` do webhook.

---

## 🛣️ Roadmap

- [x] Tempo real (Socket.IO) + histórico (Mongo)
- [x] Uploads (MinIO presigned)
- [x] Autenticação (JWT) + Socket protegido
- [x] Bots & Automações (cron/keyword)
- [x] Integrações Meta (WA Cloud, IG, FB) + WPPConnect (dev)
- [ ] UI de sessões (QR/status) para WPPConnect
- [ ] Lista de conversas (contatos/threads) + busca/filtros
- [ ] Notificações (desktop/push)
- [ ] Observabilidade (logs estruturados, métricas)
- [ ] Testes E2E e CI/CD

---

## 📝 Licença

Projeto de estudo — Licença ISC.

## 👨‍💻 Autor

**Cleber Farias** — GitHub: [@cleberfarias](https://github.com/cleberfarias)

> Se este projeto te ajudou, ⭐ dê uma estrela!

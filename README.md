# 💬 Chat App - Aplicação de Chat em Tempo Real

[![Vue 3](https://img.shields.io/badge/Vue-3.5-4FC08D?logo=vue.js)](https://vuejs.org/)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.9-3178C6?logo=typescript)](https://www.typescriptlang.org/)
[![Socket.IO](https://img.shields.io/badge/Socket.IO-5.11-010101?logo=socket.io)](https://socket.io/)
[![MongoDB](https://img.shields.io/badge/MongoDB-7.0-47A248?logo=mongodb)](https://www.mongodb.com/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker)](https://www.docker.com/)
[![Vuetify](https://img.shields.io/badge/Vuetify-3.10-1867C0?logo=vuetify)](https://vuetifyjs.com/)
[![License](https://img.shields.io/badge/License-AGPL--3.0-blue.svg)](chat-app/LICENSE)

> Aplicação de chat moderna, com frontend Vue 3 + Vuetify e backend FastAPI/Socket.IO, persistência MongoDB e uploads para MinIO/S3. Inclui agentes de IA especializados e bots personalizados.

## ✨ Recursos

- **Comunicação em tempo real** via Socket.IO (websocket + fallback)
- **Autenticação JWT** com registro e login de usuários
- **Upload de arquivos** com URLs pré-assinadas para MinIO/S3
- **Interface estilo WhatsApp** com menu de anexos e indicador de digitação
- **Persistência** de mensagens em MongoDB (replica set)
- **Sistema de agentes IA** com 5 especialistas e bots customizados (OpenAI)
- **Docker ready** para desenvolvimento com hot-reload

## 🗺️ Arquitetura

A visão visual da arquitetura (frontend, FastAPI/Socket.IO, MongoDB, MinIO e integrações externas) está documentada em [`chat-app/docs/ARCHITECTURE.md`](chat-app/docs/ARCHITECTURE.md), com diagramas Mermaid e fluxo de comunicação principal. Resumo do stack:

- **Frontend:** Vue 3 + TypeScript, Vite, Vuetify, Socket.IO client, Zod para validação.
- **Backend:** Python 3.11, FastAPI, python-socketio, Motor (MongoDB), Pydantic, PyJWT e boto3 para MinIO/S3.
- **Infra:** MongoDB replica set, MinIO/S3 para objetos, Docker Compose para orquestração.

## 📋 Pré-requisitos

- [Docker](https://www.docker.com/) e Docker Compose (recomendado)
- **OU**
- [Python](https://www.python.org/) 3.11+ (backend)
- [Node.js](https://nodejs.org/) 20+ (frontend)
- [MongoDB](https://www.mongodb.com/) 7.0+ com replica set
- npm ou yarn

## 🚀 Início Rápido

### Com Docker (recomendado)

```bash
# 1. Clone o repositório
git clone https://github.com/cleberfarias/projeto_estudo.git
cd projeto_estudo/chat-app

# 2. Suba os containers
docker-compose up

# 3. Acesse
# Frontend: http://localhost:5173
# Backend:  http://localhost:3000
# MongoDB:  localhost:27017
# MinIO S3: http://localhost:9000 (console: 9001)
```

### Sem Docker

**MongoDB (replica set):**
```bash
mongod --replSet rs0
mongosh --eval "rs.initiate()"
```

**Backend (FastAPI + Socket.IO):**
```bash
cd chat-app/backend
pip install -r requirements.txt
uvicorn main:socket_app --reload --port 3000
```

**Frontend (Vue 3 + Vite):**
```bash
cd chat-app/frontend
npm install
npm run dev
```

## 🏗️ Estrutura do Projeto

```
chat-app/
├── backend/              # FastAPI + Socket.IO + MongoDB (Motor)
│   ├── main.py          # App FastAPI + servidor Socket.IO
│   ├── routers/         # Rotas REST (auth, mensagens, uploads, bots)
│   ├── socket_handlers.py # Eventos Socket.IO
│   ├── storage.py       # Integração MinIO/S3 (presigned URLs)
│   └── bots/            # Agentes IA e automações
├── frontend/            # Vue 3 + Vuetify
│   ├── src/
│   │   ├── views/       # Chat principal e telas de autenticação
│   │   ├── components/  # Uploads, criador de bot, indicadores
│   │   └── stores/      # Pinia (auth/chat)
├── docs/                # Documentação (inclui arquitetura)
├── docker-compose.yml   # Orquestração (frontend, backend, mongo, minio)
├── LICENSE              # AGPL-3.0
└── README.md            # Este arquivo
```

## 🔧 Configuração

Defina as variáveis de ambiente em `chat-app/.env`:

```env
# Backend
DATABASE_URL=mongodb://mongo:27017/chatdb?replicaSet=rs0
JWT_SECRET=seu-secret-super-seguro-aqui
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=43200

# Frontend
VITE_SOCKET_URL=http://localhost:3000

# MinIO / S3
S3_ENDPOINT=http://minio:9000
S3_REGION=us-east-1
S3_ACCESS_KEY=MINIOADMIN
S3_SECRET_KEY=MINIOADMIN
S3_BUCKET=chat-uploads
PUBLIC_BASE_URL=http://localhost:9000
```

## 📦 Scripts úteis

### Backend (Python)
```bash
uvicorn main:socket_app --reload --port 3000
python -m pytest  # se houver testes configurados
```

### Frontend (Vue/TypeScript)
```bash
npm run dev
npm run build
npm run preview
npm run lint
```

### Docker
```bash
docker-compose up              # Inicia todos os serviços
docker-compose down -v         # Para e remove volumes
docker-compose logs -f backend # Logs do backend em tempo real
```

## 📚 Documentação

- Visão técnica completa: [`chat-app/README.md`](chat-app/README.md)
- Arquitetura visual e fluxos: [`chat-app/docs/ARCHITECTURE.md`](chat-app/docs/ARCHITECTURE.md)
- Documentação detalhada por módulo: [`chat-app/DOCUMENTACAO.md`](chat-app/DOCUMENTACAO.md)

## 📝 Licença

Este projeto é distribuído sob **AGPL-3.0** com termos adicionais descritos em [`chat-app/LICENSE`](chat-app/LICENSE). Para uso comercial, consulte o autor.

## 👨‍💻 Autor

**Cleber Farias** — cleberfarias@gmail.com | [@cleberfarias](https://github.com/cleberfarias)

⭐️ Se este projeto foi útil para seus estudos, considere dar uma estrela!

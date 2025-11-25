# 💬 Chat App - Aplicação de Chat em Tempo Real

[![Vue 3](https://img.shields.io/badge/Vue-3.5-4FC08D?logo=vue.js)](https://vuejs.org/)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.9-3178C6?logo=typescript)](https://www.typescriptlang.org/)
[![Socket.IO](https://img.shields.io/badge/Socket.IO-5.11-010101?logo=socket.io)](https://socket.io/)
[![MongoDB](https://img.shields.io/badge/MongoDB-7.0-47A248?logo=mongodb)](https://www.mongodb.com/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker)](https://www.docker.com/)
[![Vuetify](https://img.shields.io/badge/Vuetify-3.10-1867C0?logo=vuetify)](https://vuetifyjs.com/)
[![License](https://img.shields.io/badge/License-AGPL--3.0-blue.svg)](LICENSE)

> Uma aplicação de chat em tempo real moderna, construída com Vue 3, FastAPI (Python), Socket.IO e MongoDB, totalmente containerizada com Docker.

## 📜 Licença e Proteção

**Copyright © 2025 Cleber Farias. Todos os direitos reservados.**

Este projeto é licenciado sob **AGPL-3.0** com termos adicionais de proteção:

- ✅ **Open-source** para uso pessoal e educacional
- ✅ **Copyleft forte**: Modificações devem ser compartilhadas sob AGPL-3.0
- ✅ **Network use**: SaaS/hospedagem requer disponibilização do código-fonte
- ⚠️ **Trademark**: Nome "Chat App" e marcas são protegidos (veja [TRADEMARK.md](TRADEMARK.md))
- 💼 **Licença comercial** disponível para uso empresarial em larga escala

**Leia mais:**
- [LICENSE](LICENSE) - Licença AGPL-3.0 completa
- [CONTRIBUTORS.md](CONTRIBUTORS.md) - Acordo de contribuição (CLA)
- [PATENTS.md](PATENTS.md) - Propriedade intelectual e patentes
- [TRADEMARK.md](TRADEMARK.md) - Diretrizes de uso de marca

## ✨ Recursos

- ✅ **Comunicação em Tempo Real** via WebSockets (Socket.IO)
- ✅ **Autenticação JWT** com registro e login de usuários
- ✅ **Upload de Arquivos** com MinIO/S3 e URLs pré-assinadas
- ✅ **Compartilhamento de Imagens** com preview e download
- ✅ **Design Responsivo** mobile-first (xs/sm/md/lg/xl breakpoints)
- ✅ **Interface Estilo WhatsApp** com menu de anexos e clip icon rotacionado
- ✅ **Persistência de Mensagens** com MongoDB (replica set)
- ✅ **Interface Moderna** com Material Design (Vuetify)
- ✅ **Type-Safe** com TypeScript (frontend) e Python type hints (backend)
- ✅ **Validação de Dados** com Pydantic no backend e Zod no frontend
- ✅ **Backend Assíncrono** com FastAPI e Motor (MongoDB async driver)
- ✅ **Armazenamento S3** com MinIO para arquivos e imagens
- ✅ **Docker Ready** com hot-reload para desenvolvimento
- ✅ **Gerenciamento de Estado** com Pinia
- ✅ **Roteamento** com Vue Router
- ✅ **Sistema de Agentes IA** com 5 especialistas pré-configurados
- ✅ **Bots Personalizados** com credenciais OpenAI individuais
- ✅ **IA Conversacional** integrada ao chat (@guru, @advogado, @vendedor, @medico, @psicologo)

## 🗺️ Arquitetura Visual

O diagrama abaixo mostra como frontend, backend e serviços de apoio se conectam. Veja a versão detalhada em [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

```mermaid
flowchart TB
    subgraph Client[Cliente - Vue 3 + Vuetify]
        UI[UI + Pinia + Router\nSocket.IO client]
    end

    subgraph Backend[Backend - FastAPI + Socket.IO]
        API[REST: auth, contatos, mensagens, uploads, bots, webhooks]
        WS[Eventos Socket.IO\nchat:new-message / typing / read]
        SCHED[Agendador de automações\n(bots e rotinas)]
    end

    subgraph Data[Infra]
        DB[(MongoDB\nreplica set)]
        S3[(MinIO / S3\nURLs pré-assinadas)]
        LLM[(OpenAI/LLMs\npara agentes IA)]
        WA[(WhatsApp integração\nwebhook/selenium)]
    end

    UI -- "HTTP (login, uploads, histórico)" --> API
    UI <-->|"Socket.IO"| WS
    UI -. "Upload PUT direto" .-> S3

    API --> DB
    WS --> DB
    API --> S3
    WS -. "presigned URL" .-> UI

    API --> LLM
    SCHED --> LLM
    API --> WA
    WS --> WA
```

## 📋 Pré-requisitos

- [Docker](https://www.docker.com/) e Docker Compose (recomendado)
- **OU**
- [Python](https://www.python.org/) 3.11+ (backend)
- [Node.js](https://nodejs.org/) 20+ (frontend)
- [MongoDB](https://www.mongodb.com/) 7.0+ com replica set
- npm ou yarn

## 🚀 Início Rápido

### Com Docker (Recomendado)

```bash
# 1. Clone o repositório
git clone https://github.com/cleberfarias/projeto_estudo.git
cd projeto_estudo/chat-app

# 2. Inicie os containers
docker-compose up

# 3. Acesse a aplicação
# Frontend:      http://localhost:5173
# Backend API:   http://localhost:3000
# MongoDB:       localhost:27017
# MinIO S3:      http://localhost:9000
# MinIO Console: http://localhost:9001 (MINIOADMIN/MINIOADMIN)
```

### Sem Docker

**MongoDB (com replica set):**
```bash
# Inicie MongoDB com replica set
mongod --replSet rs0

# Em outro terminal, inicialize o replica set
mongosh --eval "rs.initiate()"
```

**Backend:**
```bash
cd backend
pip install -r requirements.txt
uvicorn main:socket_app --reload --port 3000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## 🏗️ Estrutura do Projeto

```
chat-app/
├── backend/              # Servidor Python + FastAPI + Socket.IO
│   ├── main.py          # Servidor principal com Socket.IO + rotas upload + agentes
│   ├── models.py        # Modelos Pydantic (validação + AttachmentInfo)
│   ├── database.py      # Conexão MongoDB com Motor
│   ├── auth.py          # Autenticação JWT
│   ├── users.py         # Rotas de registro e login
│   ├── storage.py       # Integração MinIO/S3 + presigned URLs
│   ├── requirements.txt # Dependências Python (boto3, python-multipart, httpx)
│   ├── Dockerfile
│   ├── bots/
│   │   ├── agents.py    # Sistema de agentes IA especializados (5 agentes + custom)
│   │   ├── ai_bot.py    # Bot Guru com OpenAI
│   │   ├── core.py      # Sistema de comandos
│   │   └── automations.py # Automações agendadas
│   └── prisma/
│       └── schema.prisma # Schema do banco (legado)
├── frontend/            # Cliente Vue 3 + Vuetify
│   ├── src/
│   │   ├── main.ts     # Entry point
│   │   ├── App.vue     # Componente raiz
│   │   ├── components/
│   │   │   ├── TypingIndicator.vue    # Indicador "digitando..."
│   │   │   ├── DateSeparator.vue      # Separador de datas
│   │   │   ├── AttachmentMenu.vue     # Menu anexos WhatsApp
│   │   │   ├── CustomBotCreator.vue   # Modal criação bots IA
│   │   │   └── Uploader.vue           # Upload drag-and-drop
│   │   ├── composables/
│   │   │   └── useUpload.ts           # Lógica de upload com progresso
│   │   ├── views/
│   │   │   ├── ChatView.vue           # Chat principal + upload
│   │   │   └── LoginView.vue          # Login/Registro
│   │   ├── stores/
│   │   │   ├── chat.ts                # Store do chat (Pinia)
│   │   │   └── auth.ts                # Store de autenticação
│   │   └── design-system/
│   │       ├── components/
│   │       │   ├── DSChatHeader.vue   # Header responsivo
│   │       │   ├── DSChatInput.vue    # Input + clip WhatsApp
│   │       │   └── DSMessageBubble.vue # Bolha com imagens/arquivos
│   │       ├── composables/
│   │       │   ├── useChat.ts         # Lógica do chat
│   │       │   └── useScrollToBottom.ts # Auto-scroll
│   │       ├── tokens/                # Design tokens + breakpoints
│   │       └── types/                 # TypeScript types + AttachmentSchema
│   ├── Dockerfile
│   ├── package.json
│   ├── tsconfig.app.json # Config TypeScript com path alias
│   └── vite.config.ts    # Config Vite com resolve alias
├── mongo-init/
│   └── init-replica.sh  # Script para inicializar replica set
├── minio-init/
│   ├── init-bucket.sh   # Script para criar bucket S3
│   └── cors.json        # Configuração CORS (opcional)
├── docker-compose.yml   # Orquestração dos serviços (mongo, api, web, minio)
├── MINIO_CORS_SETUP.md # Documentação MinIO e presigned URLs
├── .env                 # Variáveis de ambiente
├── README.md           # Este arquivo
└── DOCUMENTACAO.md     # Documentação técnica detalhada
```

## 🤖 Agentes IA Especializados

O sistema inclui **5 agentes IA** pré-configurados com personalidades e expertises específicas:

### Agentes Disponíveis

| Agente | Menção | Emoji | Especialidades |
|--------|--------|-------|----------------|
| **Guru** | `@guru` | 🧠 | Programação, Arquitetura, Debugging, Code Review |
| **Dr. Advocatus** | `@advogado` | ⚖️ | Direito Civil/Trabalhista/Consumidor, Contratos |
| **Sales Pro** | `@vendedor` | 💼 | Prospecção B2B, Técnicas de Fechamento, Objeções |
| **Dr. Health** | `@medico` | 🩺 | Educação em Saúde, Primeiros Socorros, Prevenção |
| **MindCare** | `@psicologo` | 🧘 | Gestão de Ansiedade, Mindfulness, Autocuidado |

### Como Usar

```bash
# Iniciar conversa com agente
@advogado preciso de ajuda com rescisão de contrato

# Ver comandos disponíveis
@vendedor /ajuda

# Limpar histórico do agente
@guru /limpar

# Ver contexto da conversa
@medico /contexto

# Listar todos os agentes
/agentes
```

### Criando Bots Personalizados

1. Clique no botão roxo **+** (canto inferior direito)
2. Preencha o formulário:
   - **Nome**: Nome único do bot
   - **Emoji**: Ícone representativo (opcional)
   - **OpenAI API Key**: Sua chave da OpenAI (sk-proj-...)
   - **Organization ID**: ID da organização (opcional)
   - **Prompt**: Personalidade e comportamento do bot
   - **Especialidades**: Até 5 áreas de expertise
3. Clique em **Criar Bot**
4. Use com `@nomedoeubot sua pergunta`

**Recursos:**
- ✅ Credenciais OpenAI individuais por bot
- ✅ Upload de arquivo .txt/.md para prompts longos
- ✅ Histórico de conversa independente (10 mensagens)
- ✅ Comandos universais (/ajuda, /limpar, /contexto)
- ✅ Preview ao vivo do bot

## 📡 API

### REST Endpoints

| Método | Endpoint | Descrição | Auth |
|--------|----------|-----------|------|
| `GET` | `/` | Health check | Não |
| `POST` | `/register` | Criar nova conta | Não |
| `POST` | `/login` | Autenticar usuário | Não |
| `GET` | `/messages` | Histórico de mensagens (paginação: `?before=timestamp&limit=30`) | Sim |
| `POST` | `/uploads/grant` | Gera URL pré-assinada para upload S3 | Não |
| `POST` | `/uploads/confirm` | Confirma upload e cria mensagem com anexo | Não |
| `POST` | `/custom-bots` | Criar bot personalizado com credenciais OpenAI | Sim |
| `GET` | `/custom-bots` | Listar bots personalizados do usuário | Sim |
| `DELETE` | `/custom-bots/{bot_key}` | Deletar bot personalizado | Sim |

### Socket.IO Events

#### Cliente → Servidor

| Evento | Payload | Descrição |
|--------|---------|-----------|
| `chat:send` | `{author, text, tempId?, status?, type?, attachment?}` | Envia nova mensagem (texto ou anexo) |
| `chat:typing` | `{userId, author, chatId, isTyping}` | Indica que usuário está digitando |
| `chat:read` | `{messageIds: string[]}` | Marca mensagens como lidas |

#### Servidor → Cliente

| Evento | Payload | Descrição |
|--------|---------|-----------|
| `chat:new-message` | `{id, author, text, timestamp, status, type, attachment?, url?}` | Broadcasting de nova mensagem (texto ou arquivo) |
| `chat:ack` | `{tempId, id, timestamp, status}` | Confirma recebimento (troca tempId por id real) |
| `chat:typing` | `{userId, author, chatId, isTyping}` | Broadcasting de status de digitação |
| `chat:delivered` | `{messageId}` | Mensagem entregue ao destinatário |
| `chat:read` | `{messageIds: string[]}` | Mensagens foram lidas |
| `error` | `{message: string}` | Notificação de erro |

## 🔧 Configuração

### Variáveis de Ambiente

Edite `.env` na raiz do projeto:

```env
# Backend
DATABASE_URL=mongodb://mongo:27017/chatdb?replicaSet=rs0
JWT_SECRET=seu-secret-super-seguro-aqui
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=43200

# Frontend
VITE_SOCKET_URL=http://localhost:3000

# OpenAI (para agentes IA)
OPENAI_API_KEY=sk-proj-...
OPENAI_MODEL=gpt-3.5-turbo

# MinIO / S3
S3_ENDPOINT=http://minio:9000
S3_REGION=us-east-1
S3_ACCESS_KEY=MINIOADMIN
S3_SECRET_KEY=MINIOADMIN
S3_BUCKET=chat-uploads
PUBLIC_BASE_URL=http://localhost:9000
MAX_UPLOAD_MB=15

## 🛡️ Segurança e gerenciamento de segredos

Siga estas práticas para manter suas credenciais seguras:

- Nunca commite o arquivo `.env` ou arquivos com chaves privadas; use `.env.example` com placeholders.
- Se encontrar uma chave real no repo (ou na sua máquina), **rotacione-a imediatamente** no provedor (OpenAI, MinIO, Meta, etc.).
- Para remover segredos do histórico git, use ferramentas como `git filter-repo` ou `BFG Repo-Cleaner` e então force-push: `git filter-repo --path .env --invert-paths`.
- Configure `pre-commit` com um scanner de segredos (ex: `detect-secrets` ou `git-secrets`) para evitar futuros commits acidentais.
- Adicione `*.pem`, `*.key`, `*.crt`, `.env*` ao `.gitignore` (já definido neste repositório).

Como executar um scan local rápido para detectar segredos:

```bash
# Instale pre-commit e detect-secrets
pip install detect-secrets pre-commit

# Rode o scanner (padrão inspeciona o diretório atual)
detect-secrets scan > .secrets.baseline

# Revise e adicione o baseline com pre-commit
pre-commit install
pre-commit run --all-files
```

Se você confirmar que arquivos sensíveis foram commited no passado, **rotacione imediatamente** as credenciais afetadas e, em seguida, remova-as do histórico com as ferramentas citadas acima.
```

### Portas

- **Frontend:** 5173
- **Backend API:** 3000
- **MongoDB:** 27017
- **MinIO S3:** 9000
- **MinIO Console:** 9001

Para alterar, edite `docker-compose.yml`:

```yaml
ports:
  - "NOVA_PORTA:PORTA_CONTAINER"
```

## 📦 Scripts Disponíveis

### Backend (Python)

```bash
uvicorn main:socket_app --reload --port 3000  # Servidor com hot-reload
python -m pytest                              # Executar testes (se houver)
```

### Frontend (Vue/TypeScript)

```bash
npm run dev      # Dev server Vite com hot-reload
npm run build    # Build para produção
npm run preview  # Preview da build
npm run lint     # Verificar código
```

### Docker

```bash
docker-compose up              # Inicia todos os serviços
docker-compose up -d           # Inicia em background
docker-compose down            # Para os serviços
docker-compose down -v         # Para e remove volumes
docker-compose logs -f backend # Logs do backend em tempo real
docker-compose restart backend # Reinicia apenas o backend
```

## 🎨 Tecnologias Utilizadas

### Frontend
- **Vue 3** - Framework progressivo (Composition API)
- **TypeScript** - Type safety
- **Vuetify 3** - Material Design UI (componentes responsivos)
- **Pinia** - State management oficial
- **Vue Router** - Roteamento SPA
- **Socket.IO Client** - WebSocket client
- **Zod** - Validação de schemas (com AttachmentSchema)
- **Vite** - Build tool ultra-rápido
- **XMLHttpRequest** - Upload com progresso (0-100%)

### Backend
- **Python 3.11** - Linguagem de programação
- **FastAPI** - Framework web assíncrono moderno
- **python-socketio** - WebSocket server
- **Motor** - Driver MongoDB assíncrono
- **Pydantic** - Validação de dados com type hints
- **PyJWT** - Geração e validação de tokens JWT
- **Uvicorn** - Servidor ASGI de alto desempenho
- **Passlib + bcrypt** - Hashing seguro de senhas
- **boto3** - SDK AWS para MinIO/S3
- **python-multipart** - Suporte a uploads multipart

### Database & Storage
- **MongoDB 7.0** - Banco NoSQL orientado a documentos
- **Replica Set** - Alta disponibilidade e oplog para change streams
- **MinIO** - Object storage S3-compatible
- **Presigned URLs** - Upload/download direto sem passar pelo backend

### DevOps
- **Docker** - Containerização
- **Docker Compose** - Orquestração multi-container

## 🐛 Troubleshooting

### MongoDB não inicia / Erro de replica set

```bash
# Remova volumes e reinicie
docker-compose down -v
docker-compose up mongo -d

# Aguarde 10 segundos e verifique logs
docker-compose logs mongo

# Se necessário, reinicialize replica set
docker exec -it chat-app-mongo-1 mongosh --eval "rs.initiate()"
```

### Mensagens não são recebidas

1. Verifique se está autenticado (token JWT válido)
2. Confirme eventos Socket.IO: cliente envia `chat:send`, servidor emite `chat:new-message`
3. Verifique logs do backend: `docker-compose logs -f backend`

### Erro de autenticação JWT

```bash
# Verifique se JWT_SECRET está definido
docker-compose exec backend env | grep JWT

# Limpe token no localStorage do navegador
# Abra DevTools > Application > Local Storage > Clear
```

### CORS Error

CORS já está configurado para aceitar qualquer origem (`*`). Para produção, altere em `backend/main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://seu-dominio.com"],  # Altere aqui
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Containers não iniciam

```bash
# Remova containers e volumes antigos
docker-compose down -v

# Reconstrua as imagens
docker-compose build --no-cache

# Inicie novamente
docker-compose up
```

### Hot-reload não funciona

Verifique se os volumes estão configurados corretamente no `docker-compose.yml`:

```yaml
volumes:
  - ./backend:/app          # Código do backend
  - ./frontend:/app         # Código do frontend
  - /app/node_modules       # Preserva node_modules do container
```

### Python packages não encontrados

```bash
# Rebuilde a imagem do backend
docker-compose build backend

# Ou instale manualmente no container
docker-compose exec backend pip install -r requirements.txt
```

## 📚 Documentação

Para documentação técnica detalhada linha por linha, consulte [`DOCUMENTACAO.md`](DOCUMENTACAO.md).

## 🚀 Deploy

### Opções de Hospedagem

- **Frontend:** [Vercel](https://vercel.com/), [Netlify](https://www.netlify.com/), [GitHub Pages](https://pages.github.com/)
- **Backend:** [Railway](https://railway.app/), [Render](https://render.com/), [Fly.io](https://fly.io/)
- **Full Stack:** [Heroku](https://www.heroku.com/), [DigitalOcean](https://www.digitalocean.com/)

### Preparação para Produção

1. **Configure variáveis de ambiente:**
   ```env
   # Backend
   DATABASE_URL=mongodb+srv://user:pass@cluster.mongodb.net/chatdb?retryWrites=true
   JWT_SECRET=GERE_UM_SECRET_FORTE_AQUI_64_CARACTERES_MINIMO
   JWT_ALGORITHM=HS256
   JWT_EXPIRATION_MINUTES=43200
   
   # Frontend
   VITE_SOCKET_URL=https://api.seu-dominio.com
   ```

2. **Ative HTTPS** (obrigatório para WebSockets seguros - wss://)

3. **Configure CORS** para aceitar apenas domínios autorizados em `backend/main.py`:
   ```python
   app.add_middleware(
       CORSMiddleware,
       allow_origins=[
           "https://seu-dominio.com",
           "https://www.seu-dominio.com"
       ],
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

4. **MongoDB Atlas** (recomendado para produção):
   - Crie cluster gratuito em [mongodb.com/atlas](https://www.mongodb.com/atlas)
   - Configure replica set automaticamente
   - Use connection string do Atlas no `DATABASE_URL`

5. **Build do frontend:**
   ```bash
   cd frontend
   npm run build
   # Deploy pasta dist/ para Vercel/Netlify/S3
   ```

6. **Backend em produção:**
   ```bash
   pip install -r requirements.txt
   uvicorn main:socket_app --host 0.0.0.0 --port 3000
   ```

## 🛣️ Roadmap

### ✅ Implementado
- [x] Persistência de mensagens no MongoDB
- [x] Autenticação JWT (registro + login)
- [x] Histórico de mensagens com paginação
- [x] Indicador de digitação ("Digitando...")
- [x] Confirmações de status (⏳ Enviando, ✓ Enviada, ✓✓ Lida)
- [x] Auto-scroll inteligente
- [x] Agrupamento de mensagens por data e autor
- [x] Separadores de data contextuais
- [x] Optimistic UI com retry/backoff
- [x] Backend migrado para Python/FastAPI
- [x] Upload de arquivos e imagens (MinIO/S3)
- [x] Presigned URLs para uploads seguros
- [x] Menu de anexos estilo WhatsApp (6 opções)
- [x] Progresso de upload (0-100%)
- [x] Preview de imagens clicáveis
- [x] Download de arquivos com ícone
- [x] Design responsivo mobile-first
- [x] Breakpoints xs/sm/md/lg/xl
- [x] Clip icon rotacionado 135° (WhatsApp style)
- [x] **Sistema de Agentes IA Especializados**
  - [x] 5 agentes pré-configurados (@guru, @advogado, @vendedor, @medico, @psicologo)
  - [x] Histórico de conversa por usuário (10 mensagens)
  - [x] Comandos específicos por agente (/ajuda, /limpar, /contexto)
  - [x] Integração com OpenAI GPT-3.5-turbo
- [x] **Criação de Bots Personalizados**
  - [x] Modal completo com formulário validado
  - [x] Upload de arquivo .txt/.md para prompts
  - [x] Credenciais OpenAI individuais por bot
  - [x] Suporte para Organization ID
  - [x] API REST para CRUD de bots
  - [x] Persistência em localStorage + backend

### 🚧 Em Desenvolvimento
- [ ] Salas de chat múltiplas (rooms)
- [ ] Status online/offline de usuários
- [ ] Compartilhamento de localização (GPS)
- [ ] Compartilhamento de contatos
- [ ] Upload de áudio/voz
- [ ] Reações a mensagens (emoji)
- [ ] Busca de mensagens
- [ ] Notificações push
- [ ] Modo escuro/claro
- [ ] Testes unitários e E2E
- [ ] CI/CD Pipeline
- [ ] Rate limiting e throttling
- [ ] Antivírus para arquivos enviados
- [ ] Mensagens criptografadas (E2E encryption)
- [ ] Persistência de bots personalizados em MongoDB
- [ ] Marketplace de bots (compartilhar com comunidade)
- [ ] Templates de prompts pré-configurados
- [ ] Edição de bots existentes
- [ ] Analytics de uso dos agentes IA

## 🤝 Contribuindo

Contribuições são bem-vindas! Siga os passos:

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/MinhaFeature`)
3. Commit suas mudanças (`git commit -m 'Adiciona MinhaFeature'`)
4. Push para a branch (`git push origin feature/MinhaFeature`)
5. Abra um Pull Request

## 📝 Licença

Este projeto é um projeto de estudo e está disponível sob a licença ISC.

## 👨‍💻 Autor

**Cleber Farias** - Creator & Copyright Holder

- GitHub: [@cleberfarias](https://github.com/cleberfarias)
- Email: cleberfarias@gmail.com
- Licenciamento comercial: Entre em contato para uso empresarial

## 🤝 Contribuindo

Contribuições são bem-vindas! Por favor, leia:

1. [CONTRIBUTORS.md](CONTRIBUTORS.md) - CLA e processo de contribuição
2. [COMMIT_INSTRUCTIONS.md](COMMIT_INSTRUCTIONS.md) - Padrões de commit
3. [CONTRIBUTING.md](CONTRIBUTING.md) - Guia completo de contribuição

**Ao submeter um Pull Request, você aceita o CLA e a licença AGPL-3.0.**

## 🛡️ Segurança

Para relatar vulnerabilidades de segurança:
- **NÃO** abra issues públicos
- Envie email para: cleberfarias@gmail.com
- Assunto: "Security Vulnerability - Chat App"
- Responderemos em até 48 horas

## 📄 Documentação Legal

- [LICENSE](LICENSE) - Licença AGPL-3.0 completa
- [CONTRIBUTORS.md](CONTRIBUTORS.md) - Acordo de contribuição
- [PATENTS.md](PATENTS.md) - Propriedade intelectual
- [TRADEMARK.md](TRADEMARK.md) - Uso de marcas
- [SECURITY_CLEANUP.md](SECURITY_CLEANUP.md) - Histórico de segurança

## 🙏 Agradecimentos

- [Vue.js](https://vuejs.org/) - Framework incrível
- [Socket.IO](https://socket.io/) - WebSockets simplificados
- [Vuetify](https://vuetifyjs.com/) - Componentes lindos
- [TypeScript](https://www.typescriptlang.org/) - Type safety
- [Docker](https://www.docker.com/) - Containerização
- [OpenAI](https://openai.com/) - GPT API
- Comunidade open source 💚

## ⚠️ Disclaimer

Este software é fornecido "como está", sem garantias de qualquer tipo. Veja [LICENSE](LICENSE) para detalhes completos.

O uso deste software para integração com OpenAI está sujeito aos [Termos de Uso da OpenAI](https://openai.com/policies/terms-of-use/).

---

## 📖 Histórico de Aulas

- **TECH-01:** Validação Zod para mensagens Socket.IO
- **TECH-02:** Persistência MongoDB + carregamento de histórico
- **TECH-02 (refactor):** Migração backend Node.js → Python/FastAPI
- **TECH-03:** Sistema completo de autenticação JWT
- **TECH-04:** UX avançada (auto-scroll, typing, status, grouping, pagination, optimistic UI)
- **TECH-05:** Upload de arquivos/imagens + MinIO/S3 + Design responsivo mobile-first
- **TECH-06:** Sistema de Agentes IA Especializados + Bots Personalizados com OpenAI
- **TECH-07:** Proteção máxima - AGPL-3.0 + CLA + Patents + Trademark

---

⭐️ Se este projeto foi útil para seus estudos, considere dar uma estrela!

**Status:** 🚀 Funcional - Em evolução constante  
**Licença:** AGPL-3.0 (com termos adicionais)  
**Criado em:** Novembro de 2025  
**Última atualização:** 18 de novembro de 2025 (TECH-07)  
**Copyright:** © 2025 Cleber Farias. Todos os direitos reservados.

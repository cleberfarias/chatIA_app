# 💬 Chat App - Aplicação de Chat em Tempo Real

[![Vue 3](https://img.shields.io/badge/Vue-3.5-4FC08D?logo=vue.js)](https://vuejs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.9-3178C6?logo=typescript)](https://www.typescriptlang.org/)
[![Socket.IO](https://img.shields.io/badge/Socket.IO-4.8-010101?logo=socket.io)](https://socket.io/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker)](https://www.docker.com/)
[![Vuetify](https://img.shields.io/badge/Vuetify-3.10-1867C0?logo=vuetify)](https://vuetifyjs.com/)

> Uma aplicação de chat em tempo real moderna, construída com Vue 3, Node.js e Socket.IO, totalmente containerizada com Docker.

## ✨ Recursos

- ✅ **Comunicação em Tempo Real** via WebSockets (Socket.IO)
- ✅ **Interface Moderna** com Material Design (Vuetify)
- ✅ **Type-Safe** com TypeScript em frontend e backend
- ✅ **Validação de Dados** com Zod no backend
- ✅ **Docker Ready** com hot-reload para desenvolvimento
- ✅ **Gerenciamento de Estado** com Pinia
- ✅ **Roteamento** com Vue Router

## 📋 Pré-requisitos

- [Docker](https://www.docker.com/) e Docker Compose (recomendado)
- **OU**
- [Node.js](https://nodejs.org/) 20+
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
# Frontend: http://localhost:5173
# Backend:  http://localhost:3000
```

### Sem Docker

**Backend:**
```bash
cd backend
npm install
npm run dev
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
├── backend/              # Servidor Node.js + Express + Socket.IO
│   ├── src/
│   │   └── index.ts     # Servidor principal
│   ├── Dockerfile
│   ├── package.json
│   └── tsconfig.json
├── frontend/            # Cliente Vue 3 + Vuetify
│   ├── src/
│   │   ├── main.ts     # Entry point
│   │   ├── App.vue     # Componente raiz
│   │   ├── views/
│   │   │   └── ChatView.vue
│   │   └── design-system/
│   │       ├── components/
│   │       ├── composables/
│   │       ├── tokens/
│   │       └── types/
│   ├── Dockerfile
│   ├── package.json
│   └── vite.config.ts
├── docker-compose.yml   # Orquestração dos serviços
├── .env                 # Variáveis de ambiente
├── README.md           # Este arquivo
└── DOCUMENTACAO.md     # Documentação técnica detalhada
```

## 📡 API Socket.IO

### Eventos do Cliente → Servidor

| Evento | Payload | Descrição |
|--------|---------|-----------|
| `chat:new-message` | `{author: string, text: string}` | Envia nova mensagem |

### Eventos do Servidor → Cliente

| Evento | Payload | Descrição |
|--------|---------|-----------|
| `chat:new-message` | `{author: string, text: string}` | Broadcasting de mensagem para todos |

## 🔧 Configuração

### Variáveis de Ambiente

Edite `.env` na raiz do projeto:

```env
VITE_SOCKET_URL=http://localhost:3000
```

### Portas

- **Backend:** 3000
- **Frontend:** 5173

Para alterar, edite `docker-compose.yml`:

```yaml
ports:
  - "NOVA_PORTA:PORTA_CONTAINER"
```

## 📦 Scripts Disponíveis

### Backend

```bash
npm run dev      # Servidor com hot-reload
npm run build    # Compilar TypeScript
npm start        # Executar versão compilada
```

### Frontend

```bash
npm run dev      # Dev server Vite com hot-reload
npm run build    # Build para produção
npm run preview  # Preview da build
```

## 🎨 Tecnologias Utilizadas

### Frontend
- **Vue 3** - Framework progressivo
- **TypeScript** - Type safety
- **Vuetify** - Material Design UI
- **Pinia** - State management
- **Vue Router** - Roteamento
- **Socket.IO Client** - WebSocket client
- **Vite** - Build tool

### Backend
- **Node.js** - Runtime JavaScript
- **Express** - Framework web
- **Socket.IO** - WebSocket server
- **TypeScript** - Type safety
- **Zod** - Schema validation
- **CORS** - Cross-origin support

### DevOps
- **Docker** - Containerização
- **Docker Compose** - Orquestração

## 🐛 Troubleshooting

### Mensagens não são recebidas

Verifique se os eventos Socket.IO estão sincronizados entre backend e frontend. O evento deve ser `'chat:new-message'` em ambos.

### CORS Error

Certifique-se que o CORS está habilitado no backend (`backend/src/index.ts`):

```typescript
app.use(cors())
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
  - ./backend:/app
  - /app/node_modules
```

## 📚 Documentação

Para documentação técnica detalhada linha por linha, consulte [`DOCUMENTACAO.md`](DOCUMENTACAO.md).

## 🚀 Deploy

### Opções de Hospedagem

- **Frontend:** [Vercel](https://vercel.com/), [Netlify](https://www.netlify.com/), [GitHub Pages](https://pages.github.com/)
- **Backend:** [Railway](https://railway.app/), [Render](https://render.com/), [Fly.io](https://fly.io/)
- **Full Stack:** [Heroku](https://www.heroku.com/), [DigitalOcean](https://www.digitalocean.com/)

### Preparação para Produção

1. Configure `VITE_SOCKET_URL` com URL do backend em produção
2. Ative HTTPS (obrigatório para WebSockets seguros)
3. Configure CORS para aceitar apenas domínios autorizados:

```typescript
const io = new Server(server, {
  cors: {
    origin: 'https://seu-dominio.com',
    methods: ['GET', 'POST']
  }
})
```

## 🛣️ Roadmap

- [ ] Persistência de mensagens (MongoDB/PostgreSQL)
- [ ] Salas de chat múltiplas
- [ ] Autenticação de usuários (JWT)
- [ ] Upload de imagens/arquivos
- [ ] Indicador de digitação
- [ ] Status online/offline
- [ ] Histórico de mensagens
- [ ] Notificações push
- [ ] Testes unitários e E2E
- [ ] CI/CD Pipeline

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

**Cleber Farias**

- GitHub: [@cleberfarias](https://github.com/cleberfarias)

## 🙏 Agradecimentos

- [Vue.js](https://vuejs.org/) - Framework incrível
- [Socket.IO](https://socket.io/) - WebSockets simplificados
- [Vuetify](https://vuetifyjs.com/) - Componentes lindos
- [TypeScript](https://www.typescriptlang.org/) - Type safety
- [Docker](https://www.docker.com/) - Containerização
- Comunidade open source 💚

---

⭐️ Se este projeto foi útil para seus estudos, considere dar uma estrela!

**Status:** 🚧 Em desenvolvimento  
**Criado em:** Novembro de 2025  
**Última atualização:** Novembro de 2025

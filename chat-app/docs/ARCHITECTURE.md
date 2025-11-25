# 🗺️ Arquitetura Visual

Este diagrama resume como os principais componentes do chat se conectam, destacando os fluxos HTTP, WebSocket e de upload direto para o storage.

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

## Fluxos principais
- **Autenticação e API REST**: o frontend chama rotas do FastAPI para registrar/logar usuários, listar contatos e buscar histórico de mensagens. Os tokens JWT autenticam tanto HTTP quanto o handshake Socket.IO.
- **Tempo real**: o cliente mantém um canal Socket.IO para enviar eventos (`chat:new-message`, digitação, leitura) e receber mensagens em broadcast. Handlers em `socket_handlers.py` gravam no MongoDB e distribuem os eventos.
- **Uploads e anexos**: o backend emite uma URL pré-assinada MinIO/S3; o navegador faz `PUT` direto para o bucket e depois confirma o anexo via API.
- **Agentes e IA**: chamadas REST e eventos acionam bots especializados e o "Guru", que usam provedores LLM configurados em `bots/`. O agendador em `bots/automations.py` dispara rotinas e notificações periódicas.
- **Integrações externas**: webhooks e o módulo `whatsapp-selenium/` permitem interoperar com WhatsApp; notificações ou comandos podem ser gerenciados via rotas `routers/webhooks.py` e handlers omni.

## Componentes de implementação
- **Frontend** (`frontend/src`): interface em Vue 3 + Vuetify, com Pinia para estado e Socket.IO client para tempo real.
- **Backend** (`backend`): FastAPI expõe rotas REST e monta o servidor Socket.IO através de `socket_manager.py` e `socket_handlers.py`. O ciclo de vida ativa o agendador (`main.py`).
- **Infra** (`docker-compose.yml`): orquestra MongoDB (replica set), MinIO para storage de arquivos, API FastAPI e frontend Vite.

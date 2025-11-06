# Backend Python - Chat API

Backend do chat em tempo real desenvolvido com **FastAPI**, **Socket.IO** e **MongoDB**.

## Stack

- **FastAPI** 0.115.5 - Framework web assíncrono
- **python-socketio** 5.11.4 - WebSockets em tempo real
- **Motor** 3.6.0 - Driver MongoDB assíncrono
- **Pydantic** 2.10.2 - Validação de dados
- **Uvicorn** 0.32.1 - Servidor ASGI

## Estrutura

```
backend-python/
├── main.py           # FastAPI app + Socket.IO handlers
├── models.py         # Modelos Pydantic (validação)
├── database.py       # Conexão MongoDB com Motor
├── requirements.txt  # Dependências Python
├── Dockerfile        # Build da imagem
└── .dockerignore     # Arquivos ignorados no build
```

## Endpoints REST

- `GET /` - Health check
- `GET /messages?limit=50` - Retorna histórico de mensagens

## Eventos Socket.IO

### Cliente → Servidor
- `chat:send` - Envia mensagem para persistir

### Servidor → Clientes
- `chat:new-message` - Broadcast de nova mensagem
- `error` - Notificação de erro

## Desenvolvimento Local

```bash
# Instalar dependências
pip install -r requirements.txt

# Rodar servidor
uvicorn main:socket_app --reload --port 3000
```

## Docker

```bash
# Build
docker build -t chat-api-python .

# Run
docker run -p 3000:3000 \
  -e DATABASE_URL=mongodb://mongo:27017/chatdb?replicaSet=rs0 \
  chat-api-python
```

## Variáveis de Ambiente

- `DATABASE_URL` - String de conexão MongoDB (padrão: `mongodb://mongo:27017/chatdb?replicaSet=rs0`)

## Diferenças do Backend Node.js

| Aspecto | Node.js (anterior) | Python (atual) |
|---------|-------------------|----------------|
| Framework | Express + Socket.IO | FastAPI + python-socketio |
| ORM | Prisma | Motor (driver nativo) |
| Validação | Zod | Pydantic |
| Runtime | tsx/ts-node | uvicorn |
| Tipagem | TypeScript | Python type hints |
| Async | Promises | async/await nativo |

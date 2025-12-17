# 🚀 Recomendações de Otimização - Chat-IA

## 📦 Otimização de Containers

### Backend (reduzir de 358MB para ~250MB)

```dockerfile
# backend/Dockerfile
FROM python:3.11-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

FROM python:3.11-slim
WORKDIR /app
# Copia apenas os pacotes Python compilados
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH
# Instala apenas curl (essencial para healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean
COPY . .
EXPOSE 3000
CMD ["uvicorn", "main:socket_app", "--host", "0.0.0.0", "--port", "3000"]
```

**Redução estimada:** 358MB → ~250MB (30% menor)

---

### Frontend (reduzir de 382MB para ~180MB)

```dockerfile
# frontend/Dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
# Build de produção
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

**Para desenvolvimento**, manter atual mas otimizar:
```dockerfile
FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
EXPOSE 5173
# Remover npm install do CMD (já executado acima)
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]
```

**Redução estimada:** 382MB → ~180MB (53% menor)

---

### WhatsApp Selenium (reduzir de 1.05GB)

```dockerfile
# whatsapp-selenium/Dockerfile
FROM python:3.11-slim
WORKDIR /app

# Instala Firefox ESR (mais leve que Chrome) + geckodriver
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    firefox-esr \
    wget \
    && wget -q https://github.com/mozilla/geckodriver/releases/download/v0.33.0/geckodriver-v0.33.0-linux64.tar.gz \
    && tar -xzf geckodriver-v0.33.0-linux64.tar.gz -C /usr/local/bin \
    && rm geckodriver-v0.33.0-linux64.tar.gz \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
EXPOSE 21466
CMD ["python", "capture_qr.py"]
```

**Redução estimada:** 1.05GB → ~650MB (38% menor)

---

## ⚡ Performance e Escalabilidade

### 1. Redis para Socket.IO Clustering

```yaml
# docker-compose.yml
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

volumes:
  redis_data:
```

```python
# backend/socket_manager.py
import socketio
import os

# Adicionar Redis adapter para múltiplas instâncias
sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins="*",
    client_manager=socketio.AsyncRedisManager(
        os.getenv("REDIS_URL", "redis://redis:6379")
    )
)
```

**Benefícios:**
- Suporta múltiplas instâncias da API
- Load balancing automático de conexões WebSocket
- Sessões persistentes entre restarts

---

### 2. Caching de Mensagens com Redis

```python
# backend/routers/messages.py
import redis.asyncio as redis
import json

redis_client = redis.from_url(os.getenv("REDIS_URL", "redis://redis:6379"))

@router.get("/messages")
async def get_messages(
    before: Optional[int] = None,
    limit: int = Query(default=30, le=100),
    contact_id: Optional[str] = None,
    current_user_id: str = Depends(get_current_user_id)
):
    # Cache key baseado nos parâmetros
    cache_key = f"messages:{current_user_id}:{contact_id}:{before}:{limit}"
    
    # Tenta buscar do cache
    cached = await redis_client.get(cache_key)
    if cached:
        return json.loads(cached)
    
    # Busca do MongoDB se não está no cache
    query = {"userId": current_user_id}
    if contact_id:
        query["contactId"] = contact_id
    # ... resto da lógica
    
    # Salva no cache por 60 segundos
    await redis_client.setex(cache_key, 60, json.dumps(result))
    return result
```

**Benefício:** Reduz 70-90% das queries no MongoDB para histórico recente

---

### 3. Connection Pooling do MongoDB

```python
# backend/database.py
from motor.motor_asyncio import AsyncIOMotorClient

DATABASE_URL = getenv("DATABASE_URL", "mongodb://mongo:27017/chatdb?replicaSet=rs0")

# Configurar pool de conexões
client = AsyncIOMotorClient(
    DATABASE_URL,
    maxPoolSize=50,  # Máximo de conexões simultâneas
    minPoolSize=10,  # Mínimo de conexões mantidas
    maxIdleTimeMS=30000,  # Fecha conexões ociosas após 30s
    serverSelectionTimeoutMS=5000,  # Timeout de seleção de servidor
)
```

---

### 4. Índices Otimizados no MongoDB

```python
# backend/database.py
async def create_indexes():
    # Índice composto para mensagens (query comum)
    await messages_collection.create_index(
        [("userId", 1), ("contactId", 1), ("createdAt", -1)],
        name="user_contact_date"
    )
    
    # Índice para busca full-text
    await messages_collection.create_index(
        [("text", "text")],
        name="text_search"
    )
    
    # Índice TTL para mensagens antigas (opcional - auto-delete)
    await messages_collection.create_index(
        [("createdAt", 1)],
        name="message_ttl",
        expireAfterSeconds=2592000  # 30 dias
    )
```

---

## 🔒 Segurança

### 1. Rate Limiting (CRÍTICO - falta implementar)

```python
# backend/middleware/rate_limit.py
from collections import defaultdict
from datetime import datetime, timedelta
from fastapi import HTTPException, Request
from functools import wraps

class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window = timedelta(seconds=window_seconds)
        self.requests = defaultdict(list)
    
    def check(self, key: str) -> bool:
        now = datetime.now()
        cutoff = now - self.window
        
        # Remove requisições antigas
        self.requests[key] = [
            req for req in self.requests[key]
            if req > cutoff
        ]
        
        # Verifica limite
        if len(self.requests[key]) >= self.max_requests:
            return False
        
        self.requests[key].append(now)
        return True

# Limitadores específicos
login_limiter = RateLimiter(max_requests=5, window_seconds=300)  # 5 por 5min
upload_limiter = RateLimiter(max_requests=10, window_seconds=60)  # 10 por 1min
message_limiter = RateLimiter(max_requests=100, window_seconds=60)  # 100 por 1min

# Uso nas rotas
@router.post("/login")
async def login(data: LoginIn, request: Request):
    ip = request.client.host
    if not login_limiter.check(ip):
        raise HTTPException(429, "Muitas tentativas. Aguarde 5 minutos.")
    # ... resto do código
```

---

### 2. Validação de Input (melhorar)

```python
# backend/models.py
from pydantic import BaseModel, Field, validator
import re

class MessageCreate(BaseModel):
    author: str = Field(..., min_length=1, max_length=100)
    text: str = Field(..., min_length=1, max_length=5000)
    
    @validator('text')
    def sanitize_text(cls, v):
        # Remove HTML/JS injection
        v = re.sub(r'<script.*?>.*?</script>', '', v, flags=re.DOTALL)
        v = re.sub(r'<.*?>', '', v)
        return v.strip()
    
    @validator('author')
    def sanitize_author(cls, v):
        # Apenas letras, números e espaços
        if not re.match(r'^[a-zA-Z0-9\s]+$', v):
            raise ValueError('Nome de autor inválido')
        return v.strip()
```

---

### 3. Segurança do JWT

```python
# backend/auth.py
import secrets

# ❌ NUNCA use default em produção
JWT_SECRET = os.getenv("JWT_SECRET", "your_jwt_secret_change_in_production")

# ✅ Validar que não está usando default
if JWT_SECRET == "your_jwt_secret_change_in_production":
    if os.getenv("ENVIRONMENT") == "production":
        raise ValueError("JWT_SECRET não configurado em produção!")
    print("⚠️  AVISO: Usando JWT_SECRET padrão (INSEGURO)")

# Gerar secret seguro:
# python -c "import secrets; print(secrets.token_urlsafe(64))"
```

**Adicionar ao .env:**
```bash
JWT_SECRET=<gerar com: python -c "import secrets; print(secrets.token_urlsafe(64))">
```

---

### 4. HTTPS e Secure Headers

```python
# backend/main.py
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

if os.getenv("ENVIRONMENT") == "production":
    # Força HTTPS
    app.add_middleware(HTTPSRedirectMiddleware)
    
    # Valida host
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=os.getenv("ALLOWED_HOSTS", "").split(",")
    )

# Security Headers
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000"
    return response
```

---

## 📊 Monitoramento e Observabilidade

### 1. Logs Estruturados

```python
# backend/logging_config.py
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
        }
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_data)

# Configurar logger
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logger = logging.getLogger("chat-api")
logger.addHandler(handler)
logger.setLevel(logging.INFO)
```

---

### 2. Métricas com Prometheus

```python
# backend/requirements.txt
prometheus-fastapi-instrumentator==7.0.0

# backend/main.py
from prometheus_fastapi_instrumentator import Instrumentator

# Adicionar métricas automáticas
Instrumentator().instrument(app).expose(app, endpoint="/metrics")
```

```yaml
# docker-compose.yml
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3001:3000"
    volumes:
      - grafana_data:/var/lib/grafana

volumes:
  prometheus_data:
  grafana_data:
```

---

## 🧪 Testes

### Estrutura de Testes Recomendada

```bash
backend/tests/
├── unit/
│   ├── test_auth.py          # Testa hash/JWT isoladamente
│   ├── test_validation.py    # Testa Pydantic models
│   └── test_bots.py          # Testa lógica de bots
├── integration/
│   ├── test_messages_api.py  # Testa rotas com DB fake
│   ├── test_socket_io.py     # Testa eventos Socket.IO
│   └── test_uploads.py       # Testa fluxo de upload
└── e2e/
    └── test_chat_flow.py     # Testa fluxo completo
```

**Configurar cobertura:**
```bash
# backend/requirements-dev.txt
pytest==8.0.0
pytest-asyncio==0.23.0
pytest-cov==4.1.0
httpx==0.27.0

# Executar testes com cobertura
pytest --cov=. --cov-report=html --cov-report=term
```

**Meta de cobertura:** 80%+

---

## 📝 CI/CD Pipeline

```yaml
# .github/workflows/test-and-deploy.yml
name: Test & Deploy

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: |
          cd backend
          pip install -r requirements-dev.txt
          pytest --cov=. --cov-report=xml
      - uses: codecov/codecov-action@v3

  test-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '20'
      - run: |
          cd frontend
          npm ci
          npm run build

  deploy:
    needs: [test-backend, test-frontend]
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: |
          docker build -t chat-api backend/
          docker build -t chat-web frontend/
          # Deploy para seu servidor
```

---

## 📈 Resumo das Melhorias

| Categoria | Impacto | Esforço | Prioridade |
|-----------|---------|---------|------------|
| Redis clustering | 🔥 Alto | ⚡ Baixo | 🎯 ALTA |
| Rate limiting | 🔥 Alto | ⚡ Baixo | 🎯 ALTA |
| Otimizar Dockerfiles | 🔥 Alto | ⚡ Médio | 🎯 ALTA |
| JWT secret validation | 🔥 Alto | ⚡ Baixo | 🎯 ALTA |
| MongoDB indexes | 🔥 Alto | ⚡ Baixo | 🎯 ALTA |
| Caching com Redis | 🟡 Médio | ⚡ Médio | 🎯 MÉDIA |
| Security headers | 🔥 Alto | ⚡ Baixo | 🎯 MÉDIA |
| Monitoramento | 🟡 Médio | ⚡ Alto | 🎯 MÉDIA |
| Testes automatizados | 🟡 Médio | ⚡ Alto | 🎯 BAIXA |
| CI/CD pipeline | 🟡 Médio | ⚡ Alto | 🎯 BAIXA |

---

## 🚀 Próximos Passos (Ordem Recomendada)

1. ✅ **Implementar rate limiting** (2-3h)
2. ✅ **Validar JWT_SECRET** (30min)
3. ✅ **Otimizar Dockerfiles** (2-3h)
4. ✅ **Adicionar Redis** (1-2h)
5. ✅ **Configurar índices MongoDB** (1h)
6. ✅ **Security headers** (1h)
7. ✅ **Logs estruturados** (2h)
8. ✅ **Caching com Redis** (3-4h)
9. ✅ **Monitoramento** (4-6h)
10. ✅ **Testes unitários** (8-16h)

**Estimativa total:** 25-40 horas de desenvolvimento

---

**Última atualização:** 2025-01-17
**Autor:** GitHub Copilot

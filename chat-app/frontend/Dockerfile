# ============================================================
# Development Dockerfile - Otimizado mas com hot-reload
# ============================================================
FROM node:20-alpine

WORKDIR /app

# Instala dependências (cache otimizado)
COPY package*.json ./
RUN npm ci --prefer-offline --no-audit

# Instala curl para healthcheck
RUN apk add --no-cache curl

# Copia código fonte
COPY . .

# Cria usuário não-root
RUN addgroup -g 1000 appuser && \
    adduser -D -u 1000 -G appuser appuser && \
    chown -R appuser:appuser /app

USER appuser

EXPOSE 5173

# Inicia dev server (já instalado, sem npm install duplicado)
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]

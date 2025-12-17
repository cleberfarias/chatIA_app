# Multi-stage build para otimização de tamanho
FROM python:3.11-slim AS builder

WORKDIR /app

# Instala dependências em ambiente isolado
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# ============================================================
# Stage final - imagem mínima
# ============================================================
FROM python:3.11-slim

WORKDIR /app

# Copia apenas os pacotes Python compilados do builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Instala apenas curl (essencial para healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copia código da aplicação
COPY . .

# Cria usuário não-root para maior segurança
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 3000

# Roda com uvicorn (sem --reload em produção)
CMD ["uvicorn", "main:socket_app", "--host", "0.0.0.0", "--port", "3000"]

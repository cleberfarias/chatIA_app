# Usa Python slim como base
FROM python:3.11-slim

# Instala Firefox, geckodriver e dependências (incluindo Xvfb para headless)
RUN apt-get update && apt-get install -y \
    firefox-esr \
    wget \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

# Baixa e instala geckodriver
RUN wget -q https://github.com/mozilla/geckodriver/releases/download/v0.34.0/geckodriver-v0.34.0-linux64.tar.gz \
    && tar -xzf geckodriver-v0.34.0-linux64.tar.gz -C /usr/local/bin \
    && rm geckodriver-v0.34.0-linux64.tar.gz \
    && chmod +x /usr/local/bin/geckodriver

# Cria diretório de trabalho
WORKDIR /app

# Copia requirements
COPY requirements.txt .

# Instala dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copia script de captura
COPY capture_qr.py .

# Cria diretório para sessões
RUN mkdir -p /app/sessions && chmod 777 /app/sessions

# Define variáveis de ambiente
ENV PYTHONUNBUFFERED=1

# Expõe porta para API
EXPOSE 21466

# Comando de inicialização
CMD ["python3", "capture_qr.py"]

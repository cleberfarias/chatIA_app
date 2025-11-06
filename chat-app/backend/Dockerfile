FROM python:3.11-slim

WORKDIR /app

# Copia requirements e instala dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia código da aplicação
COPY . .

EXPOSE 3000

# Roda com uvicorn
CMD ["uvicorn", "main:socket_app", "--host", "0.0.0.0", "--port", "3000", "--reload"]

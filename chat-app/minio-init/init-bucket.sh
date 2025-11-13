#!/bin/bash

# Aguarda MinIO estar pronto
echo "Aguardando MinIO inicializar..."
until mc alias set myminio http://minio:9000 MINIOADMIN MINIOADMIN; do
  echo "MinIO não está pronto ainda. Tentando novamente em 5s..."
  sleep 5
done

echo "✅ MinIO pronto!"

# Cria o bucket se não existir
if mc ls myminio/chat-uploads 2>/dev/null; then
  echo "ℹ️  Bucket 'chat-uploads' já existe"
else
  echo "📦 Criando bucket 'chat-uploads'..."
  mc mb myminio/chat-uploads
  echo "✅ Bucket criado!"
fi

# Define política de acesso público para leitura
echo "🔓 Configurando política de acesso..."
mc anonymous set download myminio/chat-uploads

# Configura CORS
echo "🌐 Configurando CORS..."
mc anonymous set-json /config/cors.json myminio/chat-uploads

echo "✅ Inicialização completa!"

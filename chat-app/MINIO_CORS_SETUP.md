# Configuração de CORS no MinIO

## ⚠️ Observação Importante sobre CORS

O MinIO com **URLs Pré-Assinadas** **NÃO PRECISA** de configuração CORS tradicional!

## Por que não precisa de CORS?

### URLs Pré-Assinadas (Presigned URLs)

Quando usamos URLs pré-assinadas geradas pelo backend (`presign_put()` e `presign_get()`), o navegador faz requisições **diretamente ao MinIO** com:

1. **URL completa** com token de autenticação embutido
2. **Sem headers customizados** (apenas Content-Type)
3. **Request simples** do ponto de vista CORS

Isso significa que:
- ✅ Requisições PUT para upload funcionam sem CORS
- ✅ Requisições GET para download funcionam sem CORS
- ✅ Bucket pode ficar **privado** (mais seguro)
- ✅ Acesso controlado pelo tempo de expiração da URL

## Configuração Atual

### Backend (storage.py)

```python
# Tipos permitidos
ALLOWED = {
    "image/png",
    "image/jpeg",
    "image/webp",
    "application/pdf",
    "text/plain",
    "application/zip",
    "application/octet-stream"
}

# Limite de tamanho
MAX_UPLOAD_MB = 15

# Gera URL PUT com expiração de 5 minutos
def presign_put(key: str, mimetype: str, expires=300):
    return s3.generate_presigned_url(
        "put_object",
        Params={"Bucket": S3_BUCKET, "Key": key, "ContentType": mimetype},
        ExpiresIn=expires,
    )

# Gera URL GET com expiração de 1 hora
def presign_get(key: str, expires=3600):
    return s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": S3_BUCKET, "Key": key},
        ExpiresIn=expires,
    )
```

### Variáveis de Ambiente

```bash
S3_ENDPOINT=http://minio:9000      # Endpoint interno (backend → MinIO)
PUBLIC_BASE_URL=http://localhost:9000  # URL pública (não usado com presigned)
S3_ACCESS_KEY=MINIOADMIN
S3_SECRET_KEY=MINIOADMIN
S3_BUCKET=chat-uploads
MAX_UPLOAD_MB=15
```

## Segurança

### ✅ Boas Práticas Implementadas

1. **Bucket Privado** - Apenas acesso via URLs assinadas
2. **Validação de Tipo** - Backend valida extensões permitidas
3. **Limite de Tamanho** - Frontend e backend validam MAX_UPLOAD_MB
4. **Expiração de URLs** - PUT expira em 5min, GET em 1h
5. **Chaves Únicas** - UUID + timestamp para evitar conflitos

### ⚠️ Considerações

- URLs assinadas podem ser compartilhadas durante o período de validade
- Não há antivírus (apenas stub no código)
- Bucket público para download (`mc anonymous set download`) permite acesso via URL direta (sem assinatura)

## Configuração Manual de CORS (Se Necessário)

Se por algum motivo precisar de CORS tradicional (acesso direto sem presigned URLs):

### Via MinIO Client (mc)

```bash
# Criar arquivo cors-config.json
cat > cors-config.json << 'EOF'
{
  "CORSRules": [
    {
      "AllowedOrigins": ["http://localhost:5173"],
      "AllowedMethods": ["GET", "PUT", "POST", "DELETE"],
      "AllowedHeaders": ["*"],
      "ExposeHeaders": ["ETag", "Content-Length"],
      "MaxAgeSeconds": 3000
    }
  ]
}
EOF

# Aplicar CORS
docker compose exec minio mc cors import myminio/chat-uploads < cors-config.json
```

### Via Console MinIO

1. Acesse http://localhost:9001
2. Login: `MINIOADMIN` / `MINIOADMIN`
3. Vá em **Buckets** → `chat-uploads` → **Summary**
4. Em **Access Rules**, configure CORS manualmente

## Troubleshooting

### Erro: "CORS policy: No 'Access-Control-Allow-Origin' header"

**Causa:** Tentando fazer upload/download sem usar URLs presigned

**Solução:** 
- Use `uploadAndSend()` do frontend (já usa presigned URLs)
- Backend deve gerar URLs via `presign_put()` e `presign_get()`

### Erro: "PUT failed: 403 Forbidden"

**Possíveis causas:**
1. URL expirada (> 5 minutos)
2. Content-Type incorreto
3. Credenciais do MinIO incorretas

**Solução:**
- Regere a URL com `/uploads/grant`
- Verifique `S3_ACCESS_KEY` e `S3_SECRET_KEY`

## Teste de Upload

```bash
# Via API
curl -X POST http://localhost:3000/uploads/grant \
  -H "Content-Type: application/json" \
  -d '{
    "filename": "test.png",
    "mimetype": "image/png",
    "size": 1024000
  }'

# Resposta esperada:
# {
#   "key": "messages/2025/11/13/abc123.png",
#   "putUrl": "http://minio:9000/chat-uploads/..."
# }
```

## Referências

- [MinIO Presigned URLs](https://min.io/docs/minio/linux/developers/python/API.html#presigned_put_object)
- [AWS S3 CORS](https://docs.aws.amazon.com/AmazonS3/latest/userguide/cors.html)
- [Boto3 Presigned URLs](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/s3-presigned-urls.html)

# 📱 Configuração WhatsApp Cloud API

## Passo 1: Criar App no Meta for Developers

1. Acesse: https://developers.facebook.com/apps/
2. Clique em **"Criar App"**
3. Selecione **"Business"** como tipo
4. Preencha:
   - Nome do app: `Chat-IA WhatsApp`
   - Email de contato: seu email
   - Business Account: Selecione ou crie uma

## Passo 2: Adicionar WhatsApp ao App

1. No painel do app, procure **"WhatsApp"**
2. Clique em **"Configurar"**
3. Na seção **"API Setup"**, você verá:
   - **Phone Number ID** (copie este ID)
   - **Access Token** (token temporário para testes)

## Passo 3: Configurar no .env

Adicione no arquivo `.env`:

```bash
# WhatsApp Cloud API
WA_PHONE_NUMBER_ID=123456789012345  # Phone Number ID do passo 2
WA_CLOUD_ACCESS_TOKEN=EAAxxxxxxxxxxxxx  # Token do passo 2
```

## Passo 4: Configurar Webhook (para receber mensagens)

1. No painel do WhatsApp, vá em **"Configuration"**
2. Clique em **"Edit"** no Webhook
3. Configure:
   - **Callback URL**: `https://seu-dominio.com/webhooks/meta`
     - Use ngrok para teste: `ngrok http 3000`
   - **Verify Token**: `chaapp_webhook_2024_secret` (já configurado no .env)
4. Clique em **"Verify and Save"**
5. Em **"Webhook fields"**, marque:
   - ✅ `messages`
   - ✅ `message_status`

## Passo 5: Testar Envio

```bash
# No Postman ou curl
POST http://localhost:3000/omni/send
Content-Type: application/json

{
  "channel": "whatsapp",
  "recipient": "5511999999999",
   "text": "Olá do Pad Chat-IA!"
}
```

## ⚠️ Limitações do Modo Teste

- **Número de teste**: Meta fornece um número temporário
- **Destinatários limitados**: Apenas 5 números verificados
- **Mensagens limitadas**: 1000 conversas/mês no modo dev

## 🚀 Para Produção

1. Adicione números de telefone verificados em **"Phone numbers"**
2. Complete o **Business Verification**
3. Envie o app para **Review** (aprovação da Meta)
4. Após aprovação, terá acesso ilimitado

## 📚 Documentação Oficial

- [WhatsApp Cloud API Docs](https://developers.facebook.com/docs/whatsapp/cloud-api)
- [Get Started Guide](https://developers.facebook.com/docs/whatsapp/cloud-api/get-started)

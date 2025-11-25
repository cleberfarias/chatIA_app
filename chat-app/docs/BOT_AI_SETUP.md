# 🤖 Bot de IA com ChatGPT

## 📋 Configuração

### 1. Obter API Key da OpenAI

1. Acesse [platform.openai.com](https://platform.openai.com/api-keys)
2. Crie uma conta ou faça login
3. Vá em "API Keys"
4. Clique em "Create new secret key"
5. Copie a chave (começa com `sk-proj-...`)

### 2. Configurar variáveis de ambiente

Adicione no arquivo `.env` na raiz do projeto:

```env
OPENAI_API_KEY=sk-proj-sua-chave-aqui
OPENAI_MODEL=gpt-3.5-turbo
```

**Modelos disponíveis:**
- `gpt-3.5-turbo` - Mais rápido e barato (recomendado)
- `gpt-4` - Mais inteligente, mas mais caro
- `gpt-4-turbo` - Melhor custo-benefício do GPT-4

### 3. Rebuild do container

```bash
docker compose up --build -d api
```

---

## 💬 Como usar

### Opção 1: Comando `/ai`

```
/ai Qual a capital do Brasil?
/ai Explique o que é Python em 2 linhas
/ai Me conte uma piada
```

### Opção 2: Mencionar o bot

```
@bot O que é Docker?
bot, como funciona o Socket.IO?
hey bot qual a diferença entre let e const?
```

---

## 🎯 Exemplos de uso

**Perguntas gerais:**
```
@bot O que você pode fazer?
/ai Explique REST API
```

**Ajuda com código:**
```
@bot Como fazer um loop em Python?
/ai Qual a diferença entre async e sync?
```

**Dicas e sugestões:**
```
@bot Me dê 3 dicas de produtividade
/ai Sugira um nome para meu projeto
```

---

## ⚙️ Personalização

### Alterar o comportamento do bot

Edite o `SYSTEM_PROMPT` em `backend/bots/ai_bot.py`:

```python
SYSTEM_PROMPT = """Você é um assistente especializado em programação.
Responda sempre com exemplos de código quando relevante.
Use emojis para deixar as respostas mais amigáveis."""
```

### Ajustar parâmetros

No arquivo `backend/bots/ai_bot.py`, função `ask_chatgpt`:

```python
{
    "model": OPENAI_MODEL,
    "messages": messages,
    "temperature": 0.7,    # Criatividade (0.0 a 1.0)
    "max_tokens": 500      # Tamanho máximo da resposta
}
```

**Temperature:**
- `0.0` - Mais determinístico e focado
- `0.5` - Equilibrado
- `1.0` - Mais criativo e variado

**Max Tokens:**
- `150` - Respostas curtas
- `500` - Respostas médias (padrão)
- `1000` - Respostas longas

---

## 💰 Custos

### Preços da OpenAI (Nov 2024):

**GPT-3.5-turbo:**
- Input: $0.50 / 1M tokens
- Output: $1.50 / 1M tokens
- ~1000 mensagens = $0.50

**GPT-4:**
- Input: $30 / 1M tokens
- Output: $60 / 1M tokens
- ~1000 mensagens = $30

### Estimar custos:

- 1 token ≈ 4 caracteres
- Mensagem média ≈ 200 tokens (50 palavras)
- Resposta média ≈ 400 tokens (100 palavras)

**Exemplo com GPT-3.5:**
- 100 perguntas/dia
- 600 tokens/interação (pergunta + resposta)
- Custo mensal: ~$2.70

---

## 🔒 Segurança

### Boas práticas:

1. **Nunca commite** a API key no Git
2. Use `.env` e adicione ao `.gitignore`
3. Configure **limites de uso** no dashboard da OpenAI
4. Monitore os custos regularmente
5. Considere adicionar rate limiting por usuário

### Rate Limiting (exemplo):

```python
# Em bots/ai_bot.py
from collections import defaultdict
from datetime import datetime, timedelta

user_requests = defaultdict(list)
MAX_REQUESTS_PER_HOUR = 10

def check_rate_limit(user_id: str) -> bool:
    now = datetime.now()
    hour_ago = now - timedelta(hours=1)
    
    # Remove requisições antigas
    user_requests[user_id] = [
        req for req in user_requests[user_id] 
        if req > hour_ago
    ]
    
    # Verifica limite
    if len(user_requests[user_id]) >= MAX_REQUESTS_PER_HOUR:
        return False
    
    user_requests[user_id].append(now)
    return True
```

---

## 🐛 Troubleshooting

### Erro: "Bot de IA não configurado"
- Verifique se `OPENAI_API_KEY` está no `.env`
- Reinicie o container: `docker compose restart api`

### Erro: "Timeout ao conectar com ChatGPT"
- Verifique sua conexão com a internet
- Aumente o timeout em `ai_bot.py`: `timeout=60.0`

### Erro: "Rate limit exceeded"
- Você atingiu o limite da OpenAI
- Aguarde alguns minutos
- Considere upgrade do plano

### Erro: "Insufficient quota"
- Saldo insuficiente na conta OpenAI
- Adicione créditos em: https://platform.openai.com/account/billing

---

## 📊 Monitoramento

### Ver logs do bot:

```bash
docker compose logs -f api | grep "🤖"
```

### Dashboard da OpenAI:

Acesse [platform.openai.com/usage](https://platform.openai.com/usage) para ver:
- Requisições por dia
- Tokens consumidos
- Custos acumulados
- Erros e latência

---

## 🚀 Próximos passos

### Melhorias possíveis:

1. **Histórico de conversa** - Manter contexto entre mensagens
2. **Embeddings** - Busca semântica em documentação
3. **Function calling** - Bot pode executar ações (criar tarefas, buscar dados, etc)
4. **Moderação** - Filtrar conteúdo inapropriado
5. **Streaming** - Respostas em tempo real palavra por palavra
6. **Multi-idioma** - Detectar idioma e responder adequadamente

### Alternativas gratuitas/locais:

- **Ollama** - Roda modelos localmente (Llama 2, Mistral, etc)
- **HuggingFace** - API gratuita com limite
- **LocalAI** - Self-hosted compatível com OpenAI API

---

## 📚 Recursos

- [Documentação OpenAI](https://platform.openai.com/docs)
- [Pricing OpenAI](https://openai.com/pricing)
- [Best Practices](https://platform.openai.com/docs/guides/production-best-practices)
- [Rate Limits](https://platform.openai.com/docs/guides/rate-limits)

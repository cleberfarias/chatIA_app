# 🤖 NLU com GPT - Configuração e Uso

## 📋 Visão Geral

O sistema NLU (Natural Language Understanding) agora suporta **dois modos de detecção de intenção**:

### 1. 🔍 Pattern Matching (Padrão)
- **Vantagens**: Rápido, sem custo, offline, previsível
- **Limitações**: Baseado em keywords fixas, não entende sinônimos
- **Uso**: Ideal para produção com orçamento limitado

### 2. 🤖 GPT (Opcional)
- **Vantagens**: Mais preciso, entende contexto, sinônimos e nuances
- **Limitações**: Requer API OpenAI, tem custo por requisição, latência
- **Uso**: Ideal quando precisão é crítica

---

## ⚙️ Configuração

### 1. Variáveis de Ambiente

Adicione ao seu arquivo `.env`:

```bash
# NLU com GPT (opcional)
USE_GPT_NLU=true                    # true = usa GPT, false = usa patterns
OPENAI_NLU_MODEL=gpt-4o-mini        # Modelo mais barato (recomendado)
# Alternativas: gpt-4o, gpt-4-turbo, gpt-3.5-turbo

# Já existente (necessário para GPT)
OPENAI_API_KEY=sk-proj-xxxxx...
```

### 2. Modelos Recomendados

| Modelo | Custo (por 1M tokens) | Velocidade | Precisão | Recomendação |
|--------|----------------------|------------|----------|--------------|
| `gpt-4o-mini` | $0.15 (input) / $0.60 (output) | ⚡⚡⚡ Rápido | 🎯🎯🎯 Ótima | ✅ **Melhor custo-benefício** |
| `gpt-4o` | $2.50 (input) / $10.00 (output) | ⚡⚡ Médio | 🎯🎯🎯🎯 Excelente | Para casos críticos |
| `gpt-3.5-turbo` | $0.50 (input) / $1.50 (output) | ⚡⚡⚡⚡ Muito rápido | 🎯🎯 Boa | Alternativa mais barata |

💡 **Recomendação**: Use `gpt-4o-mini` para NLU - ele é rápido, barato e muito preciso para detecção de intenção.

---

## 🚀 Como Usar

### Modo Automático (Configuração)

O sistema usa automaticamente o modo configurado em `USE_GPT_NLU`:

```python
# No socket_handlers.py, routers/nlu.py, agents.py
intent = await detect_intent(text, "customer")  # Usa configuração
```

### Modo Manual (Forçar)

Você pode forçar um método específico:

```python
# Forçar GPT (mesmo se USE_GPT_NLU=false)
intent = await detect_intent(text, "customer", use_gpt=True)

# Forçar patterns (mesmo se USE_GPT_NLU=true)
intent = await detect_intent(text, "customer", use_gpt=False)
```

### Verificar Método Usado

O Intent retornado informa qual método foi usado:

```python
intent = await detect_intent("quero agendar reunião", "customer")
print(f"Método: {intent.method}")  # "gpt" ou "pattern"
print(f"Confiança: {intent.confidence}")
```

---

## 🧪 Testes

### Teste via CLI

```bash
# No container
docker compose exec api python3 bots/nlu.py

# Com GPT habilitado
USE_GPT_NLU=true docker compose exec api python3 bots/nlu.py
```

### Teste via API

```bash
# Pattern matching
curl -X POST http://localhost:3000/nlu/analyze \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "text": "quero agendar uma reunião amanhã",
    "speaker": "customer"
  }'

# Response
{
  "intent": "scheduling",
  "confidence": 0.85,
  "method": "gpt",  // ou "pattern"
  "entities": {...}
}
```

---

## 📊 Comparação de Resultados

### Exemplo 1: Mensagem Direta

**Texto**: "quero agendar reunião"

| Método | Intent | Confidence | Observação |
|--------|--------|------------|------------|
| Pattern | `scheduling` | 1.0 | Match exato de keyword |
| GPT | `scheduling` | 0.95 | Entende contexto |

✅ **Ambos funcionam bem**

### Exemplo 2: Mensagem Ambígua

**Texto**: "preciso conversar sobre aquele problema"

| Método | Intent | Confidence | Observação |
|--------|--------|------------|------------|
| Pattern | `general` | 0.0 | Nenhuma keyword encontrada |
| GPT | `complaint` | 0.65 | Entende "problema" como reclamação |

✅ **GPT é superior**

### Exemplo 3: Sinônimos

**Texto**: "gostaria de marcar um horário"

| Método | Intent | Confidence | Observação |
|--------|--------|------------|------------|
| Pattern | `general` | 0.0 | "marcar" não está nas keywords |
| GPT | `scheduling` | 0.90 | Entende sinônimo de "agendar" |

✅ **GPT é superior**

---

## 💰 Estimativa de Custos

### Cálculo por Requisição

Para NLU com GPT, cada análise usa aproximadamente:
- **Input**: ~200 tokens (prompt + intenções)
- **Output**: ~50 tokens (JSON de resposta)

**Custo com gpt-4o-mini**:
- Input: 200 tokens × $0.15 / 1M = $0.00003
- Output: 50 tokens × $0.60 / 1M = $0.00003
- **Total por análise: ~$0.00006 (R$ 0.0003)**

### Projeção Mensal

| Mensagens/dia | Mensagens/mês | Custo/mês (USD) | Custo/mês (BRL) |
|---------------|---------------|-----------------|-----------------|
| 100 | 3.000 | $0.18 | R$ 0.90 |
| 1.000 | 30.000 | $1.80 | R$ 9.00 |
| 10.000 | 300.000 | $18.00 | R$ 90.00 |
| 100.000 | 3.000.000 | $180.00 | R$ 900.00 |

💡 **Para a maioria dos casos, o custo é desprezível!**

---

## 🎯 Quando Usar Cada Modo

### Use Pattern Matching quando:
- ✅ Orçamento é limitado
- ✅ Latência precisa ser mínima (<10ms)
- ✅ As keywords cobrem bem os casos de uso
- ✅ Sistema precisa ser 100% offline
- ✅ Resultados precisam ser determinísticos

### Use GPT quando:
- ✅ Precisão é crítica para o negócio
- ✅ Usuários usam linguagem variada/informal
- ✅ Precisa entender sinônimos e contexto
- ✅ Quer detectar nuances e sentimentos
- ✅ Pode aceitar latência de 200-500ms

### Estratégia Híbrida (Recomendado):
1. Comece com **Pattern Matching** (sem custo)
2. Monitor logs para ver confidence baixa
3. Habilite **GPT** para casos com confidence < 0.5
4. Avalie ROI e mantenha o que funciona melhor

---

## 🔧 Troubleshooting

### GPT não está sendo usado

```bash
# Verifique as variáveis
docker compose exec api python3 -c "
import os
from dotenv import load_dotenv
load_dotenv()
print('USE_GPT_NLU:', os.getenv('USE_GPT_NLU'))
print('OPENAI_API_KEY:', os.getenv('OPENAI_API_KEY')[:20] + '...' if os.getenv('OPENAI_API_KEY') else 'Not set')
"
```

### Erros de API

Verifique os logs:
```bash
docker compose logs api -f | grep "GPT NLU"
```

Erros comuns:
- `❌ GPT NLU error: 401` - API key inválida
- `❌ GPT NLU error: 429` - Rate limit excedido
- `❌ GPT NLU JSON parse error` - Resposta malformada (retry automático)

### Fallback Automático

O sistema **sempre** faz fallback para pattern matching se GPT falhar:

```
⚠️  GPT NLU falhou, usando pattern matching como fallback
🔍 NLU via patterns: scheduling (confidence: 0.85)
```

---

## 📈 Melhorias Futuras

- [ ] Cache de intenções para mensagens similares
- [ ] Fine-tuning de modelo específico para seu domínio
- [ ] Análise de sentimento integrada
- [ ] Multi-idioma automático
- [ ] Métricas de precisão por método
- [ ] Dashboard de comparação GPT vs Patterns

---

## 📚 Documentação Relacionada

- [HYBRID_AI_SYSTEM.md](./HYBRID_AI_SYSTEM.md) - Sistema híbrido completo
- [BOT_AI_SETUP.md](./BOT_AI_SETUP.md) - Configuração do ChatGPT
- [IMPLEMENTACAO_HIBRIDA.md](../IMPLEMENTACAO_HIBRIDA.md) - Guia de implementação

---

**🎉 Agora seu NLU está turbinado com GPT!**

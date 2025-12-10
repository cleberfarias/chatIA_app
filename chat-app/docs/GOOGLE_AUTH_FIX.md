# 🔐 Solução: Erro de Autorização Google Calendar

## 🚨 Problema
```
Fazer Login com o Google
Acesso bloqueado: erro de autorização
cleber.fdelgado@gmail.com
```

## ✅ Solução: Adicionar Usuário de Teste

### Passo 1: Acessar Google Cloud Console
1. Vá para: https://console.cloud.google.com/
2. Selecione o projeto: **chat-app-479320**

### Passo 2: Configurar Tela de Consentimento OAuth
1. No menu lateral, vá em: **APIs e Serviços** → **Tela de consentimento OAuth**
2. Se estiver como "Em produção", clique em **"Publicar aplicativo"** ou mantenha em **"Teste"**

### Passo 3: Adicionar Usuários de Teste
1. Na mesma página da **Tela de consentimento OAuth**
2. Role até a seção **"Usuários de teste"**
3. Clique em **"+ ADD USERS"**
4. Adicione o email: **cleber.fdelgado@gmail.com**
5. Clique em **"Salvar"**

### Passo 4: Tentar Novamente a Autenticação
Após adicionar o usuário de teste, execute:

```bash
cd /home/cleber_delgado/workspace/projeto_estudo/chat-app

# Gerar nova URL de autorização
docker compose exec api python3 -c "
from google_auth_oauthlib.flow import InstalledAppFlow
import json

SCOPES = ['https://www.googleapis.com/auth/calendar']

with open('credentials.json', 'r') as f:
    creds_data = json.load(f)

flow = InstalledAppFlow.from_client_config(creds_data, SCOPES)

auth_url, _ = flow.authorization_url(
    access_type='offline',
    include_granted_scopes='true',
    prompt='consent'
)

print('\n📱 Abra esta URL no navegador:\n')
print(auth_url)
print('\n')
"
```

### Passo 5: Autorizar e Obter Código
1. Abra a URL gerada no navegador
2. Faça login com **cleber.fdelgado@gmail.com**
3. Você verá um aviso: **"Google hasn't verified this app"**
4. Clique em **"Advanced"** (ou "Avançado")
5. Clique em **"Go to chat-app (unsafe)"** (ou "Ir para chat-app (não seguro)")
6. Autorize o acesso ao Calendar
7. Copie o código da URL de retorno (após `code=`)

### Passo 6: Completar Autenticação
Cole o código obtido quando solicitado.

---

## 🔄 Alternativa: Publicar Aplicativo (Para Produção)

Se preferir publicar o aplicativo para uso geral:

### 1. Preencher Formulário de Verificação
1. Acesse: **Tela de consentimento OAuth**
2. Clique em **"Publicar aplicativo"**
3. Preencha todas as informações obrigatórias:
   - Nome do aplicativo
   - Logo
   - Política de privacidade
   - Termos de serviço
   - Domínio autorizado

### 2. Processo de Verificação
- O Google pode levar **de 3 a 5 dias úteis** para analisar
- Você receberá email quando aprovado
- Durante este período, use a opção de **usuários de teste**

---

## 📝 Informações do Projeto

- **Project ID:** `chat-app-479320`
- **Client ID:** `696334455492-hsrctldlv0m0ksonoagd40ddt8nh8cd6.apps.googleusercontent.com`
- **Scopes necessários:** `https://www.googleapis.com/auth/calendar`

---

## 🐛 Troubleshooting

### Erro: "redirect_uri_mismatch"
1. Vá em **APIs e Serviços** → **Credenciais**
2. Clique na sua credencial OAuth 2.0
3. Em **URIs de redirecionamento autorizados**, adicione:
   - `http://localhost`
   - `http://localhost:3000`
   - `http://localhost:8080`

### Erro: "invalid_scope"
Certifique-se de que a API do Google Calendar está habilitada:
1. **APIs e Serviços** → **Biblioteca**
2. Pesquise por: **Google Calendar API**
3. Clique em **"Ativar"**

### Erro persiste após adicionar usuário de teste
1. Limpe o cache do navegador
2. Use uma janela anônima/privada
3. Aguarde 5-10 minutos para propagação das configurações
4. Tente com outro navegador

---

## ✅ Próximos Passos Após Autorização

Quando a autenticação funcionar, você terá:

1. ✅ Arquivo `backend/token.json` criado
2. ✅ Acesso ao Google Calendar
3. ✅ Sistema de agendamento visual funcionando
4. ✅ Eventos criados automaticamente com Google Meet

**Teste o fluxo completo:**
```
Painel SDR → Digite seu email → "quero agendar" → Calendário aparece → Selecione slot → Confirmação
```

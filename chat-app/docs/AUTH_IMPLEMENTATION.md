# Implementação de Autenticação JWT

## ✅ Status: COMPLETO

Este documento descreve a implementação completa do sistema de autenticação JWT integrado com Socket.IO.

## 📋 Funcionalidades Implementadas

### Backend

#### 1. **Autenticação JWT** (`backend/auth.py`)
- ✅ Geração de tokens JWT com expiry de 60 minutos
- ✅ Hash de senhas com PBKDF2-SHA256
- ✅ Validação de tokens
- ✅ Algoritmo HS256

**Funções:**
- `hash_password(password)` - Faz hash da senha
- `verify_password(plain, hashed)` - Valida senha
- `create_access_token(sub)` - Cria token JWT
- `decode_token(token)` - Valida e decodifica token

#### 2. **Rotas de Autenticação** (`backend/users.py`)
- ✅ `POST /auth/register` - Registro de usuário
- ✅ `POST /auth/login` - Login e geração de token

**Response:**
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "user": {
    "id": "507f1f77bcf86cd799439011",
    "email": "user@example.com",
    "name": "Nome do Usuário"
  }
}
```

#### 3. **Validação Socket.IO** (`backend/main.py`)
- ✅ Validação de token no handshake da conexão
- ✅ Rejeita conexões sem token válido
- ✅ Verifica se usuário existe no banco
- ✅ Armazena dados do usuário no ambiente do socket
- ✅ Registra sessões ativas (sid → user_id)

**Fluxo de conexão:**
1. Cliente envia `{ auth: { token } }`
2. Servidor valida token com `decode_token()`
3. Verifica se usuário existe no banco
4. Armazena `user_id`, `user_name`, `user_email` no `environ`
5. Registra sessão em `active_sessions`
6. Retorna `True` (aceita) ou `False` (rejeita)

### Frontend

#### 1. **Store de Autenticação** (`frontend/src/stores/auth.ts`)
- ✅ Gerenciamento de estado (token + user)
- ✅ Persistência em localStorage
- ✅ Métodos `login()`, `register()`, `logout()`
- ✅ Restauração automática via `load()`

**State:**
```typescript
{
  token: string | null,
  user: { name: string, email: string } | null
}
```

**Storage:** `localStorage.app_auth`

#### 2. **Store de Chat** (`frontend/src/stores/chat.ts`)
- ✅ Conexão Socket.IO com token JWT
- ✅ Tratamento de erros de autenticação
- ✅ Reconexão automática (5 tentativas)
- ✅ Emissão de erro quando token inválido

**Método de conexão:**
```typescript
async connect(token: string) {
  if (!token) throw new Error('Token JWT obrigatório')
  
  this.socket = io(API_URL, {
    auth: { token },
    transports: ['websocket', 'polling'],
    reconnection: true,
    reconnectionAttempts: 5
  })
  
  // Tratamento de connect_error para tokens inválidos
}
```

#### 3. **Tela de Login** (`frontend/src/views/LoginView.vue`)
- ✅ UI completa com tabs (Login/Registro)
- ✅ Validação de email e senha
- ✅ Estados de loading
- ✅ Exibição de erros
- ✅ Redirecionamento após login

#### 4. **Chat View** (`frontend/src/views/ChatView.vue`)
- ✅ Carregamento de auth no `onMounted()`
- ✅ Verificação de token antes de conectar
- ✅ Conexão Socket.IO com token JWT
- ✅ Logout completo (desconecta socket + limpa auth)
- ✅ Redirecionamento para login se não autenticado

#### 5. **Router Guards** (`frontend/src/main.ts`)
- ✅ Guard `beforeEach` verificando `authStore.token`
- ✅ Redirecionamento para `/login` se não autenticado
- ✅ Redirecionamento para `/` se já autenticado na página de login
- ✅ Restauração automática do localStorage

## 🔧 Configuração

### Variáveis de Ambiente

**Backend** (`.env` ou `docker-compose.yml`):
```bash
JWT_SECRET=your_jwt_secret_change_in_production
# Gere um seguro com: openssl rand -base64 32
```

**Frontend** (`.env` ou `docker-compose.yml`):
```bash
VITE_API_URL=http://localhost:3000
VITE_SOCKET_URL=http://localhost:3000
```

### Docker Compose

O `docker-compose.yml` já está configurado com:
- ✅ `JWT_SECRET` no serviço `api`
- ✅ `VITE_API_URL` e `VITE_SOCKET_URL` no serviço `web`

## 🧪 Teste do Fluxo Completo

### 1. Primeiro Acesso (Sem Autenticação)
```
Usuário acessa "/" 
  → Router detecta sem token 
  → Redireciona para "/login"
```

### 2. Registro de Novo Usuário
```
Usuário preenche formulário de registro
  → Frontend POST /auth/register
  → Backend valida e cria usuário
  → Backend retorna token + user
  → authStore.register() salva no localStorage
  → Router redireciona para "/"
```

### 3. Login
```
Usuário preenche formulário de login
  → Frontend POST /auth/login
  → Backend valida credenciais
  → Backend retorna token + user
  → authStore.login() salva no localStorage
  → Router redireciona para "/"
```

### 4. Conexão Socket.IO
```
ChatView.onMounted() executa:
  → authStore.load() (restaura do localStorage)
  → Verifica se tem token
  → chatStore.connect(authStore.token)
  → Socket.IO envia { auth: { token } }
  → Backend valida token
  → Backend aceita conexão ✅
```

### 5. Persistência (Refresh)
```
Usuário dá refresh na página
  → Router beforeEach executa
  → authStore.load() restaura do localStorage
  → Token válido → permite navegação
  → ChatView carrega e conecta socket
```

### 6. Logout
```
Usuário clica em "Sair"
  → ChatView.handleLogout() executa:
    1. chatStore.disconnect() (fecha socket)
    2. authStore.logout() (limpa localStorage)
    3. router.push('/login')
```

### 7. Token Inválido
```
Backend detecta token inválido/expirado
  → Retorna False no connect event
  → Socket.IO emite 'connect_error'
  → Frontend captura erro
  → chatStore.connect() lança exceção
  → ChatView catch redireciona para /login
```

## 🔒 Segurança

### Implementado
- ✅ Tokens JWT com expiry (60 minutos)
- ✅ Hash de senhas com PBKDF2-SHA256
- ✅ Validação de token no handshake do Socket.IO
- ✅ Verificação de usuário no banco antes de aceitar conexão
- ✅ Secret configurável via variável de ambiente

### Recomendações para Produção
- 🔧 Gerar `JWT_SECRET` seguro: `openssl rand -base64 32`
- 🔧 Configurar HTTPS (TLS) no servidor
- 🔧 Usar `sameSite: 'strict'` se usar cookies
- 🔧 Implementar refresh tokens para sessões longas
- 🔧 Rate limiting nas rotas de login/register
- 🔧 Logs de auditoria de autenticação

## 📁 Arquivos Modificados

### Backend
- ✅ `backend/auth.py` - Funções JWT
- ✅ `backend/users.py` - Rotas /auth/register e /auth/login
- ✅ `backend/main.py` - Validação Socket.IO connect event

### Frontend
- ✅ `frontend/src/stores/auth.ts` - Store de autenticação
- ✅ `frontend/src/stores/chat.ts` - Socket.IO com token
- ✅ `frontend/src/views/LoginView.vue` - UI de login/registro
- ✅ `frontend/src/views/ChatView.vue` - Integração auth + chat
- ✅ `frontend/src/main.ts` - Router guards

### Configuração
- ✅ `.env.example` - Documentação de variáveis
- ✅ `docker-compose.yml` - Configuração de ambiente

## ✅ Critérios de Pronto

- ✅ **Não conecta no socket sem JWT válido**
  - Backend valida token no handshake
  - Frontend trata erro e redireciona para login

- ✅ **UI mantém login após refresh**
  - authStore persiste no localStorage
  - Router guard restaura estado
  - ChatView reconecta socket com token

## 🎯 Próximos Passos (Opcional)

1. **Refresh Tokens**: Implementar renovação automática de tokens
2. **2FA**: Adicionar autenticação de dois fatores
3. **OAuth**: Integrar com Google/GitHub/Facebook
4. **Rate Limiting**: Limitar tentativas de login
5. **Auditoria**: Logs de autenticação e acessos
6. **Testes**: Testes unitários e E2E do fluxo de auth

---

**Data de Implementação:** 2025-01-27  
**Status:** ✅ Pronto para uso

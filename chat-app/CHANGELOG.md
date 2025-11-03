# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Semantic Versioning](https://semver.org/lang/pt-BR/).

## [Não lançado]

### Adicionado
- Sistema de chat em tempo real com Socket.IO
- Interface de usuário com Vue 3 e Vuetify
- Design System com componentes reutilizáveis
- Containerização com Docker e Docker Compose
- Validação de dados com Zod no backend
- Type safety completo com TypeScript
- Hot-reload em desenvolvimento
- Documentação técnica detalhada

### Backend
- Servidor Express com Socket.IO
- Validação de mensagens com esquema Zod
- Suporte a CORS para comunicação cross-origin
- Health check endpoint
- Broadcasting de mensagens em tempo real

### Frontend
- Componentes Vue 3 com Composition API
- Gerenciamento de estado com Pinia
- Roteamento com Vue Router
- Material Design com Vuetify 3
- Ícones Material Design (@mdi/font)
- Cliente Socket.IO para WebSockets
- Interface responsiva

### DevOps
- Dockerfile para backend
- Dockerfile para frontend
- Docker Compose para orquestração
- Volumes configurados para hot-reload
- Variáveis de ambiente

### Documentação
- README.md completo
- DOCUMENTACAO.md técnica linha por linha
- CONTRIBUTING.md com guia de contribuição
- LICENSE (ISC)
- .gitignore configurado
- .dockerignore para otimizar builds

## [0.1.0] - 2025-11-03

### Inicial
- Setup inicial do projeto
- Estrutura básica backend/frontend
- Configuração de desenvolvimento

---

**Legenda:**
- `Adicionado` para novas funcionalidades
- `Alterado` para mudanças em funcionalidades existentes
- `Descontinuado` para funcionalidades que serão removidas
- `Removido` para funcionalidades removidas
- `Corrigido` para correções de bugs
- `Segurança` para vulnerabilidades corrigidas

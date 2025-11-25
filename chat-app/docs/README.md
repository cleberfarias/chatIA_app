# 📚 Documentação Técnica

Esta pasta contém documentações específicas sobre recursos e configurações avançadas do projeto.

## 📄 Arquivos Disponíveis

### Autenticação e Segurança
- **[AUTH_IMPLEMENTATION.md](AUTH_IMPLEMENTATION.md)** - Implementação de autenticação JWT, bcrypt, refresh tokens

### Inteligência Artificial
- **[BOT_AI_SETUP.md](BOT_AI_SETUP.md)** - Configuração de agentes IA (Guru, TechMaster, etc.), OpenAI API, prompts customizados

### Storage e Upload
- **[UPLOAD_SYSTEM.md](UPLOAD_SYSTEM.md)** - Sistema de upload com MinIO/S3, presigned URLs, validação de arquivos
- **[MINIO_CORS_SETUP.md](MINIO_CORS_SETUP.md)** - Configuração de CORS no MinIO para upload direto do browser

### Arquitetura
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Diagrama visual da topologia (frontend, FastAPI/Socket.IO, MongoDB, MinIO, IA e integrações)

### Integrações
- **[WHATSAPP_SETUP.md](WHATSAPP_SETUP.md)** - Integração com WhatsApp Web via wppconnect, QR Code, webhooks

## 🔗 Links Úteis

- [Documentação Principal](../DOCUMENTACAO.md)
- [README do Projeto](../README.md)
- [Design System](../frontend/src/design-system/README.md)
- [Padrões de Código](../.github/copilot-instructions.md)

## 📝 Como Contribuir

Ao adicionar novas features, crie documentação correspondente nesta pasta seguindo o padrão:

```markdown
# Título da Feature

## Objetivo
Breve descrição do que faz

## Arquitetura
Diagramas e explicação técnica

## Implementação
Código e exemplos

## Configuração
Variáveis de ambiente e setup

## Testes
Como testar a funcionalidade

## Troubleshooting
Problemas comuns e soluções
```

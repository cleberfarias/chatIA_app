# 💬 Chat-IA — Aplicação de Chat em Tempo Real (Vue 3 + FastAPI)

[![Vue 3](https://img.shields.io/badge/Vue-3.5-4FC08D?logo=vue.js)](https://vuejs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python)](https://www.python.org/)
[![Socket.IO](https://img.shields.io/badge/Socket.IO-4.8-010101?logo=socket.io)](https://socket.io/)
[![MongoDB](https://img.shields.io/badge/MongoDB-ReplicaSet-47A248?logo=mongodb)](https://www.mongodb.com/)
[![MinIO](https://img.shields.io/badge/Storage-MinIO%20(S3)-FD5E5E?logo=minio)](https://min.io/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker)](https://www.docker.com/)
[![Vuetify](https://img.shields.io/badge/Vuetify-3.10-1867C0?logo=vuetify)](https://vuetifyjs.com/)

> App de chat moderno, **Vue 3 + Pinia + Vuetify** no front e **FastAPI + python-socketio + Mongo** no back. Uploads via **MinIO (S3)** e **integração omnichannel** (WhatsApp/Instagram/Facebook)[...]

---

## O que resolve

Este repositório é um projeto de estudo e uma base técnica que resolve problemas práticos comuns ao construir uma aplicação de chat em tempo real. Em linguagem direta, ele entrega:

- Comunicação em tempo real confiável e escalável (Socket.IO) para troca instantânea de mensagens entre cliente e servidor.
- Histórico de conversas persistido no MongoDB com paginação, garantindo que mensagens antigas sejam consultáveis e que a interface carregue de forma eficiente.
- Uploads de arquivos e imagens usando URLs pré‑assinadas (MinIO/S3), reduzindo carga no backend e permitindo uploads diretos do navegador para storage.
- Segurança de acesso com autenticação JWT e proteção de conexões Socket, evitando acessos não autorizados.
- Integração omnichannel (WhatsApp Cloud, Instagram, Facebook, WPPConnect), facilitando o envio/recebimento unificado de mensagens de múltiplos canais.
- Automação e bots (APScheduler + comandos) para respostas automáticas, tarefas agendadas e workflows simples.
- Sistema de agentes IA integrado (OpenAI) para criar assistentes especializados dentro do chat (suporte, vendas, jurídico, saúde, etc.).
- Ambiente de desenvolvimento pronto para rodar localmente com Docker Compose, reduzindo tempo de setup.
- Padrão modular e extensível que serve como base para estudos, prototipagem rápida e projetos de produção com ajustes.

Benefícios para desenvolvedores e equipes:

- Economiza tempo ao fornecer uma base pronta com patterns testados (realtime, presigned uploads, auth, omnichannel). 
- Facilita experimentação com agentes IA e bots em um ambiente integrado.
- Ajuda a aprender boas práticas (async FastAPI, Motor, Socket.IO patterns, presigned URLs, Docker). 
- Fornece exemplos claros para evolução (adicionar rooms, notificações push, E2E tests, observabilidade).

---
## 🧭 IA como Core (Assistente Principal)

Este projeto prioriza a Inteligência Artificial como peça central da experiência de atendimento — o Assistente IA é a interface principal para suporte, vendas e operações. A aplicação vem com agentes pré-configurados (Guru, Advogado, Vendedor, Médico, Psicólogo), porém você pode criar ágeis bots personalizados com comportamento, prompts e credenciais independentes.

Principais recursos do Assistente IA:
- Respostas context-aware: os agentes mantêm contexto parcial da conversa para respostas mais coerentes.
- Automação de agendamentos, sugestões e ações: operações automatizadas via agentes (ex.: SDR auto-agendamento).
- Multicanal: os agentes podem atuar em canais Omnichannel (WhatsApp/Instagram/FB) via webhook/integrations.
- Extensível: crie bots com prompts customizados e credenciais OpenAI por bot.

Como ativar e configurar (exemplo):
```bash
# No Docker Compose / .env
OPENAI_API_KEY="sua-chave-openai"
DEFAULT_AGENT_KEY="guru"               # agente padrão exibido no painel
ASSISTANT_CORE_ENABLED="true"   

## ✨ Recursos

- ✅ **Tempo real** com Socket.IO (WS)
- ✅ **Histórico persistido** em MongoDB (índice por `createdAt` + paginação)
- ✅ **Uploads** com URL pré‑assinada (MinIO/S3)
- ✅ **Autenticação JWT** + Socket protegido
- ✅ **UI** com Vuetify (dark/light), Pinia e Vue Router
- ✅ **Bots & Automações** (APScheduler: cron + keyword)
- ✅ **Omnichannel**: WhatsApp Cloud, Instagram Messaging, Facebook Messenger e WPPConnect (dev/homolog)
- ✅ **Docker Compose** para subir tudo localmente

---

## 🏗️ Arquitetura (visão)

<img width="1189" height="275" alt="arquitetura-core" src="https://github.com/user-attachments/assets/328f1b1d-579e-43d3-ad77-d1f5e4ea10e6" />

**Core (Client ⇄ Server ⇄ Data)**  
![Arquitetura Core](arquitetura-core.png)

**Omnichannel (canais Meta + WPPConnect)**  
![Arquitetura Omnichannel](arquitetura-omni-clean.png)

> Se os diagramas não renderizarem aqui, baixe:
> - PNG Core: `arquitetura-core.png`
> - PNG Omnichannel: `arquitetura-omni-clean.png`

---

## 📋 Pré‑requisitos

- [Docker](https://www.docker.com/) e Docker Compose
- OU ambiente local com:
  - **Python 3.11+**
  - **Node 20+**
  - **MongoDB 6+** (com Replica Set ativo se for usar change streams)

---

## 🚀 Início Rápido

### 1) Com Docker (recomendado)

```bash
# 1. Clone
git clone https://github.com/cleberfarias/chatIA_app
cd pad-chat-ia/chat-app

# 2. Suba os serviços
docker compose up -d --build

# 3. (Apenas na 1ª vez) Inicie o Replica Set do Mongo
docker compose exec mongo mongosh --eval 'rs.initiate({_id:"rs0",members:[{_id:0,host:"mongo:27017"}]})'

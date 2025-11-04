.PHONY: help up down build restart logs clean install dev stop ps

# Cores para output
GREEN  := \033[0;32m
YELLOW := \033[0;33m
RESET  := \033[0m

help: ## Mostra este menu de ajuda
	@echo "$(GREEN)Chat App - Comandos Disponíveis$(RESET)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-15s$(RESET) %s\n", $$1, $$2}'
	@echo ""

up: ## Inicia os containers (docker-compose up)
	@echo "$(GREEN)Iniciando containers...$(RESET)"
	docker-compose up

up-d: ## Inicia os containers em background (detached mode)
	@echo "$(GREEN)Iniciando containers em background...$(RESET)"
	docker-compose up -d

build: ## Reconstrói as imagens do zero
	@echo "$(GREEN)Reconstruindo imagens...$(RESET)"
	docker-compose build --no-cache

rebuild: ## Para, reconstrói e inicia os containers
	@echo "$(GREEN)Reconstruindo e reiniciando...$(RESET)"
	docker-compose down
	docker-compose build --no-cache
	docker-compose up

down: ## Para e remove os containers
	@echo "$(GREEN)Parando containers...$(RESET)"
	docker-compose down

stop: ## Para os containers sem removê-los
	@echo "$(GREEN)Parando containers...$(RESET)"
	docker-compose stop

restart: ## Reinicia os containers
	@echo "$(GREEN)Reiniciando containers...$(RESET)"
	docker-compose restart

logs: ## Mostra os logs dos containers
	docker-compose logs -f

logs-api: ## Mostra logs apenas do backend
	docker-compose logs -f api

logs-web: ## Mostra logs apenas do frontend
	docker-compose logs -f web

ps: ## Lista os containers em execução
	docker-compose ps

clean: ## Remove containers, volumes e imagens
	@echo "$(YELLOW)Limpando containers, volumes e imagens...$(RESET)"
	docker-compose down -v --rmi all

clean-volumes: ## Remove apenas os volumes
	@echo "$(YELLOW)Removendo volumes...$(RESET)"
	docker-compose down -v

install-backend: ## Instala dependências do backend
	@echo "$(GREEN)Instalando dependências do backend...$(RESET)"
	cd backend && npm install

install-frontend: ## Instala dependências do frontend
	@echo "$(GREEN)Instalando dependências do frontend...$(RESET)"
	cd frontend && npm install

install: install-backend install-frontend ## Instala todas as dependências

dev-backend: ## Roda backend localmente (sem Docker)
	@echo "$(GREEN)Iniciando backend em modo dev...$(RESET)"
	cd backend && npm run dev

dev-frontend: ## Roda frontend localmente (sem Docker)
	@echo "$(GREEN)Iniciando frontend em modo dev...$(RESET)"
	cd frontend && npm run dev

shell-api: ## Abre shell no container do backend
	docker-compose exec api sh

shell-web: ## Abre shell no container do frontend
	docker-compose exec web sh

health: ## Verifica se os serviços estão rodando
	@echo "$(GREEN)Verificando saúde dos serviços...$(RESET)"
	@curl -s http://localhost:3000/health && echo "$(GREEN)✓ Backend OK$(RESET)" || echo "$(YELLOW)✗ Backend offline$(RESET)"
	@curl -s http://localhost:5173 > /dev/null && echo "$(GREEN)✓ Frontend OK$(RESET)" || echo "$(YELLOW)✗ Frontend offline$(RESET)"

setup: ## Setup inicial do projeto
	@echo "$(GREEN)Configurando projeto...$(RESET)"
	@if [ ! -f .env ]; then cp .env.example .env && echo "$(GREEN)✓ .env criado$(RESET)"; fi
	@echo "$(GREEN)Setup completo! Execute 'make up' para iniciar$(RESET)"

git-status: ## Mostra status do Git
	@git status

git-add-docs: ## Adiciona arquivos de documentação ao Git
	@echo "$(GREEN)Adicionando documentação ao Git...$(RESET)"
	git add README.md CONTRIBUTING.md CHANGELOG.md LICENSE .gitignore .env.example Makefile

git-commit-docs: git-add-docs ## Commita arquivos de documentação
	@echo "$(GREEN)Commitando documentação...$(RESET)"
	git commit -m "docs: adiciona documentação completa do projeto"

.DEFAULT_GOAL := help

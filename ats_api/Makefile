# =============================================================================
# MAKEFILE - Comandos para gerenciar o ambiente Docker
# =============================================================================
# Uso: make <comando>
# =============================================================================

.PHONY: help build up down restart logs shell bundle-install bundle-update reset-gems clean

# Cores para output
GREEN  := $(shell tput -Txterm setaf 2)
YELLOW := $(shell tput -Txterm setaf 3)
RESET  := $(shell tput -Txterm sgr0)

help: ## Mostra esta ajuda
	@echo ''
	@echo 'Uso:'
	@echo '  ${YELLOW}make${RESET} ${GREEN}<comando>${RESET}'
	@echo ''
	@echo 'Comandos:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  ${YELLOW}%-20s${RESET} %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# =============================================================================
# COMANDOS PRINCIPAIS
# =============================================================================

build: ## Rebuild das imagens (use após mudar Dockerfile)
	docker compose build --no-cache

up: ## Inicia todos os serviços
	docker compose up -d

down: ## Para todos os serviços
	docker compose down

restart: ## Reinicia todos os serviços
	docker compose restart

logs: ## Mostra logs de todos os serviços
	docker compose logs -f

logs-web: ## Mostra logs apenas do web
	docker compose logs -f web

logs-sidekiq: ## Mostra logs apenas do sidekiq
	docker compose logs -f sidekiq

# =============================================================================
# GERENCIAMENTO DE GEMS (A MÁGICA ESTÁ AQUI!)
# =============================================================================

bundle-install: ## Instala gems em todos os containers (use após adicionar gems)
	@echo "${YELLOW}📦 Instalando gems...${RESET}"
	docker compose run --rm web bundle install
	@echo "${GREEN}✅ Gems instaladas! Reiniciando serviços...${RESET}"
	docker compose restart web sidekiq sneakers

bundle-update: ## Atualiza gems específicas. Uso: make bundle-update gem=nome_da_gem
	@echo "${YELLOW}📦 Atualizando gem: $(gem)${RESET}"
	docker compose run --rm web bundle update $(gem)
	@echo "${GREEN}✅ Gem atualizada! Reiniciando serviços...${RESET}"
	docker compose restart web sidekiq sneakers

reset-gems: ## NUCLEAR: Limpa TODO o cache de gems e reinstala (use se tudo der errado)
	@echo "${YELLOW}💣 Removendo volume de gems...${RESET}"
	docker compose down
	docker volume rm ats_bundle_cache || true
	@echo "${YELLOW}📦 Recriando e instalando gems...${RESET}"
	docker compose build
	docker compose up -d
	@echo "${GREEN}✅ Ambiente recriado do zero!${RESET}"

# =============================================================================
# COMANDOS ÚTEIS
# =============================================================================

shell: ## Abre um shell no container web
	docker compose exec web bash

console: ## Abre o rails console
	docker compose exec web rails console

db-migrate: ## Roda migrações
	docker compose exec web rails db:migrate

db-reset: ## Reset do banco (CUIDADO!)
	docker compose exec web rails db:reset

routes: ## Lista todas as rotas
	docker compose exec web rails routes

# =============================================================================
# TESTES DE REFINAMENTO
# =============================================================================

test-refinement-status: ## 🔍 Verifica status dos componentes de refinamento
	@docker compose exec web bundle exec rails runner scripts/test_refinement_status.rb

test-refinement-all: ## 🎯 Roda TODOS os testes de refinamento (specs + validação)
	@echo "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
	@echo "${GREEN}🧪 SUITE COMPLETA DE TESTES - REFINAMENTO${RESET}"
	@echo "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
	@echo ""
	@echo "${YELLOW}[1/5] Specs automatizados...${RESET}"
	@docker compose exec web bundle exec rspec spec/services/candidates/similar_candidates/ --format progress
	@echo ""
	@echo "${YELLOW}[2/5] Testando modelos Gemini...${RESET}"
	@docker compose exec web bundle exec rails runner scripts/test_gemini_models.rb
	@echo ""
	@echo "${YELLOW}[3/5] Verificando normalização...${RESET}"
	@docker compose exec web bundle exec rails runner scripts/check_gemini_embedding_normalization.rb
	@echo ""
	@echo "${YELLOW}[4/5] Teste rápido de intent...${RESET}"
	@docker compose exec web bundle exec rails runner scripts/quick_intent_test.rb
	@echo ""
	@echo "${YELLOW}[5/5] Teste completo de refinamento...${RESET}"
	@docker compose exec web bundle exec rails runner scripts/test_sourcing_564_intent.rb
	@echo ""
	@echo "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
	@echo "${GREEN}✅ Suite completa executada!${RESET}"
	@echo "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"

test-models: ## Testa quais modelos Gemini funcionam
	@echo "${YELLOW}🧪 Testando modelos Gemini...${RESET}"
	@docker compose exec web bundle exec rails runner scripts/test_gemini_models.rb

test-intent-quick: ## Teste rápido de extração de intent
	@echo "${YELLOW}🧪 Teste rápido de intent...${RESET}"
	@docker compose exec web bundle exec rails runner scripts/quick_intent_test.rb

test-intent-full: ## Teste completo de refinamento com intent
	@echo "${YELLOW}🧪 Teste completo de refinamento...${RESET}"
	@docker compose exec web bundle exec rails runner scripts/test_sourcing_564_intent.rb

test-visual-evidence: ## 🎯 Evidência visual de que o refinamento funciona
	@echo "${YELLOW}🎯 Gerando evidência visual do refinamento...${RESET}"
	@docker compose exec web bundle exec rails runner scripts/refinement_visual_evidence.rb

test-normalization: ## Verifica normalização dos embeddings do Gemini
	@echo "${YELLOW}🧪 Verificando normalização...${RESET}"
	@docker compose exec web bundle exec rails runner scripts/check_gemini_embedding_normalization.rb

test-refinement-specs: ## Roda apenas specs RSpec de refinamento
	@echo "${YELLOW}🧪 Rodando specs...${RESET}"
	@docker compose exec web bundle exec rspec spec/services/candidates/similar_candidates/ --format documentation

# =============================================================================
# MICROSOFT TEAMS
# =============================================================================

teams-reset: ## 🔄 Reset Teams subscriptions (use quando ngrok restartar)
	@docker compose exec web bundle exec rails teams:reset_fast

teams-nuke: ## 💣 NUKE: Delete ALL MS subscriptions (orphans included) and recreate
	@docker compose exec web bundle exec rails teams:nuke

teams-diagnose: ## 🔍 Diagnóstico completo das subscriptions do Teams
	@docker compose exec web bundle exec rails teams:diagnose

teams-status: ## 📊 Ver status de todas as subscriptions
	@docker compose exec web bundle exec rails teams:status

teams-renew: ## ⏰ Renovar subscriptions que estão expirando
	@docker compose exec web bundle exec rails teams:renew

teams-reset-full: ## 💣 Reset completo (deleta da Microsoft, mais lento)
	@docker compose exec web bundle exec rails teams:reset

teams-auto-reset: ## 🤖 Reset automático (silencioso, ideal para cron)
	@docker compose exec -T web bundle exec rails teams:auto_reset

teams-retry: ## 🔁 Retry all failed subscriptions
	@docker compose exec web bundle exec rails teams:retry_failed

teams-outreach: ## 🚀 Enviar mensagem proativa da LIA para todos @wedotalent.cc
	@docker compose exec web bundle exec rails "teams:outreach[wedotalent.cc]"

teams-outreach-dry: ## 🔍 Dry-run do outreach (mostra quem receberia)
	@docker compose exec web bundle exec rails "teams:outreach_dry_run[wedotalent.cc]"

teams-show-cron: ## 📋 Mostrar exemplos de crontab
	@cat crontab.example

# =============================================================================
# LIMPEZA
# =============================================================================

clean: ## Remove containers parados, imagens não usadas, etc.
	docker system prune -f

clean-all: ## NUCLEAR: Remove TUDO (containers, volumes, imagens)
	docker compose down -v --rmi all
	docker system prune -af


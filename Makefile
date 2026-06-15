# ============================================================================
# Stock Predictor - build & deployment automation
#
# Two independent services (agent + ui), each containerized, orchestrated with
# docker compose. Targets honor a clean -> build -> package -> containerize ->
# run pipeline.
#
# Usage:  make help
# ============================================================================

COMPOSE        ?= docker compose
AGENT_IMAGE    ?= stockpredictor-agent:latest
UI_IMAGE       ?= stockpredictor-ui:latest
DIST_DIR       ?= build

.DEFAULT_GOAL := help
.PHONY: help env install-hooks clean build package containerize up down restart logs ps health \
        build-agent build-ui rebuild

help: ## Show this help
	@echo "Stock Predictor - available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

env: ## Create .env from .env.example if it does not exist
	@test -f .env || (cp .env.example .env && echo "Created .env (edit it to add your API keys).")

install-hooks: ## Install git hooks (keeps API keys out of commits)
	@bash scripts/install-hooks.sh

clean: ## Remove build artifacts, caches, and stop/remove containers
	-$(COMPOSE) down --remove-orphans
	rm -rf $(DIST_DIR)
	rm -rf ui/dist ui/node_modules ui/.vite
	find . -type d -name "__pycache__" -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "Clean complete."

build-agent: ## Build the agent Docker image
	$(COMPOSE) build agent

build-ui: ## Build the ui Docker image
	$(COMPOSE) build ui

build: env build-agent build-ui ## Build both service images
	@echo "Build complete."

containerize: build ## Alias for build (produce container images)

package: build ## Save built images as tarballs in $(DIST_DIR)
	mkdir -p $(DIST_DIR)
	docker save $(AGENT_IMAGE) -o $(DIST_DIR)/stockpredictor-agent.tar
	docker save $(UI_IMAGE)    -o $(DIST_DIR)/stockpredictor-ui.tar
	@echo "Packaged images into $(DIST_DIR)/"

up: env ## Build (if needed) and start both services in the background
	$(COMPOSE) up -d --build
	@echo "UI:    http://localhost:$${UI_PORT:-3000}"
	@echo "Agent: http://localhost:$${AGENT_PORT:-8000}/health"

down: ## Stop and remove the running services
	$(COMPOSE) down

restart: down up ## Restart the stack

rebuild: ## Force a no-cache rebuild and restart
	$(COMPOSE) build --no-cache
	$(COMPOSE) up -d

logs: ## Follow logs from both services
	$(COMPOSE) logs -f

ps: ## Show running services
	$(COMPOSE) ps

health: ## Curl the agent health endpoint
	curl -fsS http://localhost:$${AGENT_PORT:-8000}/health && echo

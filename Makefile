# ==============================================================================
# Global / Setup
# ==============================================================================
.PHONY: install
install: ## Install all dependencies (backend, frontend, prek)
	@echo "Installing root Python tools..."
	@uv sync
	@echo "Installing backend dependencies..."
	@uv sync --directory backend
	@echo "Installing frontend dependencies..."
	@bun install
	@if git rev-parse --git-dir > /dev/null 2>&1; then \
		echo "Installing pre-commit hooks..."; \
		uv run prek install -f; \
	else \
		echo "Not a git repository - skipping pre-commit hooks"; \
	fi
	@echo "Setup complete! Run 'make help' to see available commands."

.PHONY: check
check: ## Run all code quality checks (prek + backend + frontend)
	@echo "Running prek hooks..."
	@uv run prek run --all-files
	@echo "Running backend checks..."
	@$(MAKE) backend-check
	@echo "Running frontend lint..."
	@$(MAKE) frontend-lint

.PHONY: test
test: backend-test frontend-test ## Run all tests (backend + frontend)

.PHONY: build
build: clean-build ## Build backend wheel file
	@echo "Creating wheel file..."
	@uvx --from build pyproject-build --installer uv backend/

.PHONY: clean-build
clean-build: ## Clean build artifacts
	@echo "Removing build artifacts..."
	@rm -rf backend/dist

# ==============================================================================
# Docker
# ==============================================================================
.PHONY: docker-up
docker-up: docker-build ## Start all Docker services (rebuilds first)
	@docker compose up -d

.PHONY: docker-down
docker-down: ## Stop all Docker services
	@docker compose down

.PHONY: docker-logs
docker-logs: ## View Docker service logs
	@docker compose logs -f

.PHONY: docker-build
docker-build: ## Build backend and frontend Docker images
	@docker compose build backend prestart frontend

# ==============================================================================
# Backend (using uv)
# ==============================================================================
.PHONY: backend-install
backend-install: ## Install backend dependencies
	@uv sync --directory backend

.PHONY: backend-test
backend-test: ## Run fast backend tests (excludes slow tests)
	@echo "Running fast backend tests..."
	@uv run --directory backend python -m pytest tests -m "not slow" -v --cov=app --cov-report=xml

.PHONY: backend-test-full
backend-test-full: ## Run all backend tests including slow ones
	@echo "Running all backend tests..."
	@uv run --directory backend python -m pytest tests -v --cov=app --cov-report=xml

.PHONY: backend-check
backend-check: ## Run backend code quality checks (ty + ruff)
	@echo "Running backend type checks (ty)..."
	@uv run --directory backend ty check
	@echo "Running backend linting (ruff)..."
	@uv run --directory backend ruff check app
	@uv run --directory backend ruff format --check app

.PHONY: backend-dev
backend-dev: ## Start backend development server
	@echo "Starting backend development server..."
	@uv run --directory backend fastapi dev app/main.py

.PHONY: backend-stop
backend-stop: ## Stop backend development server gracefully
	@echo "Stopping backend development server..."
	@pkill -f "fastapi dev app/main.py" || echo "No backend server running"

.PHONY: backend-kill
backend-kill: ## Force kill backend development server
	@echo "Force killing backend development server..."
	@pkill -9 -f "fastapi dev app/main.py" || echo "No backend server running"

# ==============================================================================
# Database Migrations (Alembic via uv)
# ==============================================================================
.PHONY: migrate
migrate: ## Run database migrations
	@echo "Running database migrations..."
	@uv run --directory backend alembic upgrade head

.PHONY: migrate-create
migrate-create: ## Create a new migration (usage: make migrate-create msg="message")
	@echo "Creating new migration..."
	@uv run --directory backend alembic revision --autogenerate -m "$(msg)"

.PHONY: migrate-down
migrate-down: ## Rollback last migration
	@echo "Rolling back last migration..."
	@uv run --directory backend alembic downgrade -1

# ==============================================================================
# Dictionary Pipeline
# ==============================================================================
.PHONY: download-sources
download-sources: ## Download SCOWL word list for dictionary building
	@echo "Downloading dictionary sources..."
	@python backend/scripts/download_sources.py

.PHONY: build-dictionary
build-dictionary: download-sources ## Build game dictionary from sources
	@echo "Building dictionary..."
	@python backend/scripts/build_dictionary.py

# ==============================================================================
# Frontend (using Bun)
# ==============================================================================
.PHONY: frontend-install
frontend-install: ## Install frontend dependencies
	@bun install

.PHONY: frontend-dev
frontend-dev: ## Start frontend development server
	@echo "Starting frontend development server..."
	@bun run --filter frontend dev

.PHONY: frontend-stop
frontend-stop: ## Stop frontend development server gracefully
	@echo "Stopping frontend development server..."
	@pkill -f "vite.*--mode" || pkill -f "bun run.*dev" || echo "No frontend server running"

.PHONY: frontend-kill
frontend-kill: ## Force kill frontend development server
	@echo "Force killing frontend development server..."
	@pkill -9 -f "vite.*--mode" || pkill -9 -f "bun run.*dev" || echo "No frontend server running"

.PHONY: frontend-build
frontend-build: ## Build frontend for production
	@echo "Building frontend..."
	@bun run --filter frontend build

.PHONY: frontend-lint
frontend-lint: ## Lint frontend code
	@echo "Linting frontend code..."
	@bunx biome check --write --no-errors-on-unmatched frontend/

.PHONY: frontend-test
frontend-test: ## Run frontend tests with Playwright
	@echo "Running frontend tests..."
	@bun run --filter frontend test

.PHONY: frontend-test-ui
frontend-test-ui: ## Run frontend tests with Playwright UI
	@echo "Running frontend tests with UI..."
	@bun run --filter frontend test:ui

.PHONY: generate-client
generate-client: ## Generate TypeScript API client from OpenAPI schema
	@echo "Generating TypeScript API client..."
	@chmod +x scripts/generate-client.sh
	@./scripts/generate-client.sh

# ==============================================================================
# Development Workflow
# ==============================================================================
.PHONY: dev
dev: ## Start full development environment (requires Docker)
	@echo "Starting development environment..."
	@docker compose up -d db mailcatcher
	@echo "Waiting for database..."
	@sleep 3
	@$(MAKE) migrate
	@echo "Development environment ready!"
	@echo "  - Database: localhost:5432"
	@echo "  - Mailcatcher: http://localhost:1080"
	@echo ""
	@echo "Start servers with:"
	@echo "  Backend:  make backend-dev"
	@echo "  Frontend: make frontend-dev"
	@echo ""
	@echo "Stop servers with:"
	@echo "  Servers:  make stop"
	@echo "  Backend:  make backend-stop"
	@echo "  Frontend: make frontend-stop"

.PHONY: stop
stop: backend-stop frontend-stop ## Stop all development servers gracefully
	@echo "All servers stopped."

.PHONY: kill
kill: backend-kill frontend-kill ## Force kill all development servers
	@echo "All servers force killed."

.PHONY: help
help:
	@python -c "import re; \
	[[print(f'\033[36m{m[0]:<20}\033[0m {m[1]}') for m in re.findall(r'^([a-zA-Z_-]+):.*?## (.*)$$', open(makefile).read(), re.M)] for makefile in ('$(MAKEFILE_LIST)').strip().split()]"

.DEFAULT_GOAL := help

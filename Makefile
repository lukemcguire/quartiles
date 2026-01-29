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
test: backend-test ## Run all tests (currently alias for backend-test)

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
docker-up: ## Start all Docker services
	@docker compose up -d

.PHONY: docker-down
docker-down: ## Stop all Docker services
	@docker compose down

.PHONY: docker-logs
docker-logs: ## View Docker service logs
	@docker compose logs -f

.PHONY: docker-build
docker-build: ## Build Docker images
	@docker compose build

# ==============================================================================
# Backend (using uv)
# ==============================================================================
.PHONY: backend-install
backend-install: ## Install backend dependencies
	@uv sync --directory backend

.PHONY: backend-test
backend-test: ## Run backend tests with pytest
	@echo "Running backend tests..."
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
# Frontend (using Bun)
# ==============================================================================
.PHONY: frontend-install
frontend-install: ## Install frontend dependencies
	@bun install

.PHONY: frontend-dev
frontend-dev: ## Start frontend development server
	@echo "Starting frontend development server..."
	@bun run --filter frontend dev

.PHONY: frontend-build
frontend-build: ## Build frontend for production
	@echo "Building frontend..."
	@bun run --filter frontend build

.PHONY: frontend-lint
frontend-lint: ## Lint frontend code
	@echo "Linting frontend code..."
	@bunx biome check --write --no-errors-on-unmatched frontend/

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

.PHONY: help
help:
	@python -c "import re; \
	[[print(f'\033[36m{m[0]:<20}\033[0m {m[1]}') for m in re.findall(r'^([a-zA-Z_-]+):.*?## (.*)$$', open(makefile).read(), re.M)] for makefile in ('$(MAKEFILE_LIST)').strip().split()]"

.DEFAULT_GOAL := help

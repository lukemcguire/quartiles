.PHONY: install
install: ## Install dependencies and pre-commit hooks
	@echo "Installing root dev dependencies..."
	@uv sync
	@echo "Installing backend dependencies..."
	@cd backend && uv sync
	@if git rev-parse --git-dir > /dev/null 2>&1; then \
		echo "Installing pre-commit hooks..."; \
		uv run pre-commit install; \
	else \
		echo "Not a git repository - skipping pre-commit hooks"; \
	fi
	@echo "Setup complete! Run 'make help' to see available commands."

.PHONY: check
check: ## Run all code quality checks (backend + frontend)
	@echo "Running pre-commit hooks..."
	@uv run pre-commit run -a
	@echo "Running backend checks..."
	@$(MAKE) backend-check
	@echo "Running frontend lint..."
	@$(MAKE) frontend-lint

.PHONY: test
test: backend-test ## Run all tests (alias for backend-test)

.PHONY: build
build: clean-build ## Build backend wheel file
	@echo "Creating wheel file..."
	@cd backend && uvx --from build pyproject-build --installer uv

.PHONY: clean-build
clean-build: ## Clean build artifacts
	@echo "Removing build artifacts..."
	@rm -rf backend/dist

# Docker commands
.PHONY: docker-up
docker-up: ## Start all Docker services
	@echo "Starting Docker services..."
	@docker compose up -d

.PHONY: docker-down
docker-down: ## Stop all Docker services
	@echo "Stopping Docker services..."
	@docker compose down

.PHONY: docker-logs
docker-logs: ## View Docker service logs
	@docker compose logs -f

.PHONY: docker-build
docker-build: ## Build Docker images
	@echo "Building Docker images..."
	@docker compose build

# Backend commands
.PHONY: backend-install
backend-install: ## Install backend dependencies
	@echo "Installing backend dependencies..."
	@cd backend && uv sync

.PHONY: backend-test
backend-test: ## Run backend tests with pytest
	@echo "Running backend tests..."
	@cd backend && uv run python -m pytest app/tests -v --cov=app --cov-report=xml

.PHONY: backend-check
backend-check: ## Run backend code quality checks (ty + ruff)
	@echo "Running backend type checks with ty..."
	@cd backend && uv run ty check
	@echo "Running backend linting with ruff..."
	@cd backend && uv run ruff check app
	@cd backend && uv run ruff format --check app

.PHONY: backend-dev
backend-dev: ## Start backend development server
	@echo "Starting backend development server..."
	@cd backend && uv run fastapi dev app/main.py

# Database migrations
.PHONY: migrate
migrate: ## Run database migrations
	@echo "Running database migrations..."
	@cd backend && uv run alembic upgrade head

.PHONY: migrate-create
migrate-create: ## Create a new migration (usage: make migrate-create msg="migration message")
	@echo "Creating new migration..."
	@cd backend && uv run alembic revision --autogenerate -m "$(msg)"

.PHONY: migrate-down
migrate-down: ## Rollback last migration
	@echo "Rolling back last migration..."
	@cd backend && uv run alembic downgrade -1

# Frontend commands
.PHONY: frontend-install
frontend-install: ## Install frontend dependencies
	@echo "Installing frontend dependencies..."
	@cd frontend && npm install

.PHONY: frontend-dev
frontend-dev: ## Start frontend development server
	@echo "Starting frontend development server..."
	@cd frontend && npm run dev

.PHONY: frontend-build
frontend-build: ## Build frontend for production
	@echo "Building frontend..."
	@cd frontend && npm run build

.PHONY: frontend-lint
frontend-lint: ## Lint frontend code
	@echo "Linting frontend code..."
	@cd frontend && npm run lint

.PHONY: generate-client
generate-client: ## Generate TypeScript API client from OpenAPI schema
	@echo "Generating TypeScript API client..."
	@./scripts/generate-client.sh

# Development workflow
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

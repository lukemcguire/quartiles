# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Quartiles is a full-stack web application built with FastAPI (backend) and React (frontend). The project is based on the FastAPI Full Stack Template and uses a monorepo structure with separate backend and frontend directories.

**Stack:**
- Backend: FastAPI + SQLModel (ORM) + PostgreSQL + Alembic (migrations)
- Frontend: React + TypeScript + TanStack Router + TanStack Query + Tailwind CSS + shadcn/ui
- Package Management: uv (Python), bun/npm (JavaScript)
- Database: PostgreSQL
- Containerization: Docker Compose

## Development Commands

### Initial Setup

```bash
make install              # Install all dependencies (root, backend, frontend) and pre-commit hooks
```

### Backend Development

```bash
cd backend && uv sync     # Install backend dependencies
make backend-dev          # Start backend dev server (uses fastapi dev)
make backend-test         # Run tests with pytest (includes coverage)
make backend-check        # Run type checking (ty) and linting (ruff)
```

**Run a single test:**
```bash
cd backend && uv run python -m pytest tests/path/to/test_file.py::test_function_name -v
```

### Frontend Development

```bash
cd frontend && npm install  # Install frontend dependencies
make frontend-dev           # Start frontend dev server (Vite at localhost:5173)
make frontend-build         # Build for production
make frontend-lint          # Run ESLint
```

### Database Migrations

```bash
make migrate                           # Apply all migrations
make migrate-create msg="description"  # Create new migration
make migrate-down                      # Rollback last migration
```

Migrations are managed with Alembic. Always create migrations in the backend container or with `cd backend && uv run alembic ...`

### Docker Development

```bash
make docker-up      # Start all services (db, backend, frontend, mailcatcher)
make docker-down    # Stop all services
make docker-build   # Rebuild Docker images
make dev            # Start dev environment (db + mailcatcher only, no backend/frontend)
```

The `make dev` command starts only supporting services (PostgreSQL, Mailcatcher). Run backend and frontend servers separately with `make backend-dev` and `make frontend-dev`.

### Code Quality

```bash
make check          # Run all checks (pre-commit, backend checks, frontend lint)
```

### API Client Generation

```bash
make generate-client  # Generate TypeScript API client from OpenAPI schema
```

Run this after modifying backend API routes. The generated client is in `frontend/src/client/`.

## Architecture

### Backend Structure

- `backend/app/main.py` - FastAPI application entry point, CORS configuration
- `backend/app/api/main.py` - API router aggregation
- `backend/app/api/routes/` - API endpoints organized by domain (users, items, login, utils, private)
- `backend/app/game/` - **Pure Python game logic (NO FastAPI/SQLModel/Pydantic imports)**
  - `types.py` - Dataclasses for game domain models
  - `dictionary.py` - Word lookups, trie structures
  - `generator.py` - Puzzle generation algorithms
  - `solver.py` - Validation and scoring logic
- `backend/app/models.py` - SQLModel models for database tables and Pydantic schemas
- `backend/app/crud.py` - Database operations (Create, Read, Update, Delete)
- `backend/app/core/` - Core configuration, security, database connection
  - `config.py` - Settings loaded from `.env` via pydantic-settings
  - `security.py` - JWT authentication and password hashing
  - `db.py` - Database session management
- `backend/app/api/deps.py` - FastAPI dependencies (authentication, database session)
- `backend/app/alembic/` - Database migration scripts
- `backend/tests/` - Pytest test suite

**API routing:** All routes are prefixed with `/api/v1` (configured in `settings.API_V1_STR`). The `private.router` is only included when `ENVIRONMENT=local`.

**Authentication:** JWT tokens stored in localStorage on frontend. Backend uses `get_current_user` and `get_current_active_superuser` dependencies from `app.api.deps`.

**Game Logic Architecture:** The `backend/app/game/` module contains pure Python code for Quartiles puzzle generation, validation, and scoring. This module intentionally avoids any FastAPI, SQLModel, or Pydantic dependencies to maintain clean separation of concerns. The API routes in `backend/app/api/routes/` act as the adapter layer, converting between the game domain types (dataclasses) and HTTP/database representations (Pydantic/SQLModel schemas). This architecture allows the game logic to be easily tested in isolation and potentially extracted into a standalone package if needed.

### Frontend Structure

- `frontend/src/main.tsx` - Application entry point, sets up TanStack Router/Query, theme provider
- `frontend/src/routes/` - File-based routing with TanStack Router
  - `__root.tsx` - Root layout
  - `_layout.tsx` - Authenticated layout with sidebar
  - `login.tsx`, `signup.tsx`, etc. - Public routes
  - `_layout/index.tsx`, `_layout/items.tsx`, etc. - Protected routes
- `frontend/src/client/` - **Auto-generated** TypeScript API client (DO NOT EDIT MANUALLY)
- `frontend/src/components/` - React components organized by feature
  - Uses shadcn/ui components (Tailwind-based)
- `frontend/src/hooks/` - Custom React hooks

**Routing:** Uses TanStack Router with file-based routing. Routes under `_layout/` require authentication.

**State management:** TanStack Query for server state. API client configured with `OpenAPI.BASE` and `OpenAPI.TOKEN` in main.tsx.

**Styling:** Tailwind CSS + shadcn/ui components. Dark mode supported via theme-provider.

### Data Models

Models in `backend/app/models.py` follow a pattern:
- `*Base` classes define shared properties
- `*Create` classes for API input on creation
- `*Update` classes for API input on updates (all fields optional)
- `*` classes (no suffix) are SQLModel table models with `table=True`
- `*Public` classes define public API response schemas

Example: `UserBase`, `UserCreate`, `UserUpdate`, `User`, `UserPublic`

### Authentication Flow

1. User logs in via `/api/v1/login/access-token` (username/password form)
2. Backend returns JWT access token
3. Frontend stores token in localStorage
4. Frontend sets `OpenAPI.TOKEN` async function to retrieve token
5. Protected routes require `CurrentUser` dependency on backend
6. 401/403 responses trigger logout and redirect to login (handled in main.tsx)

### Database

- PostgreSQL accessed via SQLModel (built on SQLAlchemy)
- Database sessions created per request via `SessionDep` dependency
- UUIDs used as primary keys (auto-generated with `uuid.uuid4`)
- Timestamps use UTC via `get_datetime_utc()` helper
- Connection string built in `core/config.py` from `.env` variables

### Game Logic Boundary Pattern

When implementing game features, maintain a clean separation between the game logic and web framework:

**Game module (`backend/app/game/`):**
- Use standard Python dataclasses, not Pydantic models
- No imports from `fastapi`, `sqlmodel`, or `pydantic`
- Can use any pure Python data structures and algorithms
- Should be testable without any database or HTTP setup

**API routes (`backend/app/api/routes/`):**
- Act as the adapter/translation layer
- Convert Pydantic request models to game dataclasses
- Call game module functions with plain Python types
- Convert game dataclass responses back to Pydantic response models
- Handle all database operations via CRUD layer

**Example pattern:**
```python
# backend/app/game/types.py
from dataclasses import dataclass

@dataclass
class Puzzle:
    tiles: list[str]
    solutions: set[frozenset[str]]

# backend/app/api/routes/game.py
from app.game import generate_puzzle
from app.models import PuzzleResponse

@router.get("/puzzle")
def get_daily_puzzle() -> PuzzleResponse:
    puzzle = generate_puzzle(difficulty=3)  # Returns game dataclass
    return PuzzleResponse.from_domain(puzzle)  # Convert to Pydantic
```

This pattern keeps the game logic portable and independently testable while maintaining FastAPI's validation and documentation benefits at the API boundary.

## Configuration

Configuration is stored in the root `.env` file and loaded by:
- Backend: `backend/app/core/config.py` via pydantic-settings
- Frontend: Environment variables prefixed with `VITE_` (e.g., `VITE_API_URL`)

**Important `.env` variables:**
- `SECRET_KEY` - JWT signing key (NEVER commit real secrets)
- `POSTGRES_*` - Database connection settings
- `FIRST_SUPERUSER` / `FIRST_SUPERUSER_PASSWORD` - Initial admin user
- `FRONTEND_HOST` - Used by backend for email links
- `BACKEND_CORS_ORIGINS` - CORS allowed origins
- `ENVIRONMENT` - `local`, `staging`, or `production`

## Testing

Backend tests use pytest with fixtures defined in `backend/tests/conftest.py`. Tests create a test database and clean up after each run.

Frontend E2E tests use Playwright. Run with `bunx playwright test` or `bunx playwright test --ui`.

## Email Development

Mailcatcher runs on `http://localhost:1080` when using Docker. SMTP settings in `.env` configure email delivery. Email templates are in `backend/app/email-templates/` (MJML source in `src/`, compiled HTML in `build/`).

## Code Quality Tools

- **Backend:**
  - `ty` - Type checking
  - `ruff` - Linting and formatting (configured with extensive rule set in pyproject.toml)
  - `pytest` - Testing with coverage
  - `prek` - Pre-commit hook manager

- **Frontend:**
  - ESLint - Linting
  - TypeScript - Type checking

## Important Notes

- Always run `make generate-client` after modifying backend API schemas
- Database schema changes require creating and applying Alembic migrations
- Frontend client in `src/client/` is auto-generated - never edit manually
- Use `make check` before committing to catch issues early
- Private routes (for debugging) are only available in local environment
- Backend uses Google-style docstrings (configured in pyproject.toml)

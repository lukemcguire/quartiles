# Backend Architecture

## Directory Structure

```
backend/app/
├── main.py              # FastAPI entry point, CORS configuration
├── api/
│   ├── main.py          # API router aggregation
│   ├── deps.py          # FastAPI dependencies (auth, db session)
│   └── routes/          # API endpoints by domain
│       ├── users.py
│       ├── items.py
│       ├── login.py
│       ├── utils.py
│       └── private.py   # Only included when ENVIRONMENT=local
├── game/                # Pure Python game logic (see below)
├── core/
│   ├── config.py        # Settings from .env via pydantic-settings
│   ├── security.py      # JWT auth, password hashing
│   └── db.py            # Database session management
├── models.py            # SQLModel tables + Pydantic schemas
├── crud.py              # Database operations (CRUD)
└── alembic/             # Database migration scripts
```

## API Routing

- All routes prefixed with `/api/v1` (configured in `settings.API_V1_STR`)
- Private router only included when `ENVIRONMENT=local`
- Protected routes require `get_current_user` or `get_current_active_superuser` dependencies from `app.api.deps`

## Game Logic Architecture

The `backend/app/game/` module contains **pure Python code** for Quartiles puzzle generation, validation, and scoring.

### Critical Boundary Rules

**Game module (`backend/app/game/`):**
- Use standard Python `dataclasses`, not Pydantic models
- No imports from `fastapi`, `sqlmodel`, or `pydantic`
- Can use any pure Python data structures and algorithms
- Should be testable without any database or HTTP setup

**API routes (`backend/app/api/routes/`):**
- Act as the adapter/translation layer
- Convert Pydantic request models → game dataclasses
- Call game module functions with plain Python types
- Convert game dataclass responses → Pydantic response models
- Handle all database operations via CRUD layer

### Example Pattern

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

This pattern keeps game logic portable, independently testable, and potentially extractable to a standalone package.

## Backend Commands

```bash
cd backend && uv sync           # Install dependencies
make backend-dev                # Start dev server (fastapi dev)
make backend-test               # Run pytest with coverage
make backend-check              # Run type checking (ty) and linting (ruff)

# Run single test
cd backend && uv run python -m pytest tests/path/to/test_file.py::test_function_name -v
```

## Migrations

Managed with Alembic. Always create migrations in the backend container or with `cd backend && uv run alembic ...`

```bash
make migrate                           # Apply all migrations
make migrate-create msg="description"  # Create new migration
make migrate-down                      # Rollback last migration
```

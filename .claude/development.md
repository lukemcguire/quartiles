# Development Workflow

## Docker Development

```bash
make docker-up      # Start all services (db, backend, frontend, mailcatcher)
make docker-down    # Stop all services
make docker-build   # Rebuild Docker images
make dev            # Start dev environment (db + mailcatcher only)
```

The `make dev` command starts only supporting services. Run backend and frontend servers separately with `make backend-dev` and `make frontend-dev`.

## Configuration

Configuration is stored in the root `.env` file and loaded by:
- **Backend:** `backend/app/core/config.py` via pydantic-settings
- **Frontend:** Environment variables prefixed with `VITE_` (e.g., `VITE_API_URL`)

### Important .env Variables

| Variable | Purpose |
|----------|---------|
| `SECRET_KEY` | JWT signing key (NEVER commit real secrets) |
| `POSTGRES_*` | Database connection settings |
| `FIRST_SUPERUSER` / `FIRST_SUPERUSER_PASSWORD` | Initial admin user |
| `FRONTEND_HOST` | Used by backend for email links |
| `BACKEND_CORS_ORIGINS` | CORS allowed origins |
| `ENVIRONMENT` | `local`, `staging`, or `production` |

## Testing

**Backend:** Pytest with fixtures in `backend/tests/conftest.py`. Tests create a test database and clean up after each run.

```bash
make backend-test               # Run all tests
cd backend && uv run python -m pytest tests/path/to/test.py::test_func -v  # Single test
```

**Frontend:** Playwright E2E tests.

```bash
bunx playwright test        # Run tests
bunx playwright test --ui   # Run with UI
```

## Code Quality Tools

### Backend
- `ty` - Type checking
- `ruff` - Linting and formatting (extensive rule set in pyproject.toml)
- `pytest` - Testing with coverage
- `prek` - Pre-commit hook manager

### Frontend
- ESLint - Linting
- TypeScript - Type checking

```bash
make check    # Run all checks (pre-commit, backend, frontend)
```

## Email Development

Mailcatcher runs on `http://localhost:1080` when using Docker. SMTP settings in `.env` configure email delivery. Email templates are in `backend/app/email-templates/` (MJML source in `src/`, compiled HTML in `build/`).

## Important Notes

- Always run `make generate-client` after modifying backend API schemas
- Frontend client in `src/client/` is auto-generated - never edit manually
- Private routes (for debugging) are only available in local environment
- Backend uses Google-style docstrings (configured in pyproject.toml)
- Use `make check` before committing to catch issues early

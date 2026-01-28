# CLAUDE.md

Quartiles is a full-stack FastAPI + React application with a pure Python game logic module.

**Stack:** FastAPI, SQLModel, PostgreSQL, React, TypeScript, TanStack Router/Query, Tailwind, shadcn/ui

## Quick Reference

**Package Managers:** `uv` (Python), `bun/npm` (JavaScript)

```bash
make install          # Initial setup
make backend-dev      # Backend dev server
make frontend-dev     # Frontend dev server (localhost:5173)
make dev              # Start DB + Mailcatcher only
make check            # Run all checks
make generate-client  # Generate TS API client from OpenAPI
```

## Critical Pattern: Game Logic Boundary

The `backend/app/game/` module uses **pure Python dataclasses only** - no FastAPI/SQLModel/Pydantic imports. API routes act as adapters, converting between Pydantic and game domain types.

## Detailed Guides

- [Backend Architecture](.claude/backend.md)
- [Frontend Architecture](.claude/frontend.md)
- [Data Models & Auth](.claude/data-models.md)
- [Development Workflow](.claude/development.md)

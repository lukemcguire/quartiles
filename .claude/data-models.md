# Data Models & Authentication

## Data Model Pattern

Models in `backend/app/models.py` follow a consistent naming pattern:

| Suffix | Purpose |
|--------|---------|
| `*Base` | Shared properties |
| `*Create` | API input on creation |
| `*Update` | API input on updates (all fields optional) |
| `*` (no suffix) | SQLModel table models with `table=True` |
| `*Public` | Public API response schemas |

**Example:** `UserBase`, `UserCreate`, `UserUpdate`, `User`, `UserPublic`

## Database

- **PostgreSQL** accessed via SQLModel (built on SQLAlchemy)
- Database sessions created per request via `SessionDep` dependency
- **UUIDs** used as primary keys (auto-generated with `uuid.uuid4`)
- **Timestamps** use UTC via `get_datetime_utc()` helper
- Connection string built in `core/config.py` from `.env` variables

## Authentication Flow

1. User logs in via `/api/v1/login/access-token` (username/password form)
2. Backend returns JWT access token
3. Frontend stores token in localStorage
4. Frontend sets `OpenAPI.TOKEN` async function to retrieve token
5. Protected routes require `CurrentUser` dependency on backend
6. 401/403 responses trigger logout and redirect to login (handled in main.tsx)

## Database Migrations

**Critical:** Database schema changes require creating and applying Alembic migrations.

```bash
make migrate-create msg="description"  # Create migration
make migrate                           # Apply migration
```

Always create migrations in the backend container or with `cd backend && uv run alembic ...`

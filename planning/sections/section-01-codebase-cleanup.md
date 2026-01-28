# Section 01: Codebase Cleanup (Pre-commit Compliance)

## Background

The Quartiles codebase was generated from a template and contains placeholder/scaffolding code that doesn't pass pre-commit hooks. Before implementing new features, we need to establish a clean baseline where every commit passes quality checks.

Pre-commit hooks enforce:
- **Backend:** ruff (Python linting + formatting)
- **Frontend:** biome (TypeScript/JavaScript linting)
- **General:** trailing whitespace, end-of-file fixes

## Dependencies

- **Requires:** None (this is the first section)
- **Blocks:** All other sections (02-09)

## Requirements

When this section is complete:
1. `pre-commit run --all-files` passes with no errors
2. Scaffolding code that won't be used has been deleted
3. Core infrastructure files have proper docstrings
4. The codebase is ready for new feature development

## Implementation Details

### Backend Cleanup

**Files to fix (add docstrings):**

1. `backend/app/api/deps.py`
   - Add module docstring
   - Add docstrings to `get_db()`, `get_current_user()`, `get_current_active_superuser()`

2. `backend/app/api/main.py`
   - Add module docstring

3. `backend/app/core/config.py`
   - Add module docstring

4. `backend/app/core/security.py`
   - Add module docstring
   - Add docstrings to public functions

5. `backend/app/core/db.py`
   - Add module docstring

6. `backend/app/models.py`
   - Add module docstring (we'll extend this file later)

7. `backend/app/crud.py`
   - Add module docstring

**Files to delete (scaffolding):**

1. `backend/app/api/routes/items.py` - Template CRUD not needed
2. Remove Item-related schemas from `backend/app/models.py` (Item, ItemCreate, ItemUpdate, ItemPublic, ItemsPublic)
3. Remove Item-related CRUD from `backend/app/crud.py`
4. Remove items router registration from `backend/app/api/main.py`
5. Delete item-related tests if any

**Auto-fix command:**
```bash
cd backend && uv run ruff check --fix .
cd backend && uv run ruff format .
```

### Frontend Cleanup

**Files to delete (scaffolding we're replacing):**

1. `frontend/src/components/Items/` - Entire directory (template CRUD)
2. `frontend/src/components/Admin/` - Entire directory (placeholder)
3. `frontend/src/components/Pending/PendingItems.tsx` - Related to Items

**Files to keep (will be modified later):**
- `frontend/src/components/ui/` - Keep for now, will be replaced by daisyUI in Section 02
- Core routing files
- Auth hooks

**Note:** Frontend biome checks currently pass, so no linting fixes needed.

### Commit Strategy

After cleanup:
1. Stage all changes
2. Run `pre-commit run --all-files`
3. Fix any remaining issues
4. Commit with message: "chore: clean up scaffolding and fix linting"

## Acceptance Criteria

- [ ] `pre-commit run --all-files` passes completely
- [ ] `backend/app/api/routes/items.py` deleted
- [ ] Item-related code removed from models.py and crud.py
- [ ] Items router removed from api/main.py
- [ ] `frontend/src/components/Items/` directory deleted
- [ ] `frontend/src/components/Admin/` directory deleted
- [ ] All backend Python files have module docstrings
- [ ] All public functions in deps.py have docstrings
- [ ] `uv run ruff check backend/` shows no errors
- [ ] `npx biome check frontend/src/` shows no errors

## Files Summary

### Delete
- `backend/app/api/routes/items.py`
- `frontend/src/components/Items/` (directory)
- `frontend/src/components/Admin/` (directory)
- `frontend/src/components/Pending/PendingItems.tsx`

### Modify
- `backend/app/api/deps.py` - Add docstrings
- `backend/app/api/main.py` - Add docstring, remove items router
- `backend/app/core/config.py` - Add docstring
- `backend/app/core/security.py` - Add docstrings
- `backend/app/core/db.py` - Add docstring
- `backend/app/models.py` - Add docstring, remove Item schemas
- `backend/app/crud.py` - Add docstring, remove Item CRUD

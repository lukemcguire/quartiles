# Quartiles Implementation PRD (Ralphy CLI)

This file is designed for use with the Ralphy CLI, which processes section files from the referenced paths.

## Project Summary

**Project:** Quartiles - A daily word puzzle game inspired by Apple News+ Quartiles
**Repository:** quartiles
**Primary Stack:** FastAPI + React + PostgreSQL + daisyUI

## Game Overview

Quartiles presents players with a 4x5 grid of 20 letter tiles (2-4 letters each). Players combine tiles to form valid English words:
- 1-tile word = 2 points
- 2-tile word = 4 points
- 3-tile word = 7 points
- 4-tile word (Quartile) = 10 points

The puzzle is "solved" at 100 points. Players compete on a daily leaderboard by fastest solve time.

## Critical Constraints

| Constraint | Description |
|------------|-------------|
| **Pre-commit compliance** | Every commit must pass `pre-commit run --all-files` |
| **Game logic isolation** | `backend/app/game/` has NO FastAPI/SQLModel/Pydantic imports |
| **Server-authoritative** | Scoring, timing, validation all server-side |
| **First-play-wins** | One competitive attempt per player per puzzle |
| **Security** | Client never receives valid_words list |

## Section Manifest

```yaml
sections:
  - id: "01"
    path: planning/sections/section-01-codebase-cleanup.md
    title: Codebase Cleanup (Pre-commit Compliance)
    requires: []
    blocks: ["02", "03", "04", "05", "06", "07", "08", "09"]

  - id: "02"
    path: planning/sections/section-02-design-foundation.md
    title: Design Foundation (Figma + Theme)
    requires: ["01"]
    blocks: ["07"]

  - id: "03"
    path: planning/sections/section-03-dictionary-pipeline.md
    title: Dictionary Building Pipeline
    requires: ["01"]
    blocks: ["04"]

  - id: "04"
    path: planning/sections/section-04-game-logic.md
    title: Pure Python Game Logic
    requires: ["03"]
    blocks: ["05"]

  - id: "05"
    path: planning/sections/section-05-database-models.md
    title: Database Models & Migrations
    requires: ["01", "04"]
    blocks: ["06"]

  - id: "06"
    path: planning/sections/section-06-game-api.md
    title: Game API Endpoints
    requires: ["04", "05"]
    blocks: ["07", "08"]

  - id: "07"
    path: planning/sections/section-07-frontend-game-ui.md
    title: Frontend Game UI Components
    requires: ["02", "06"]
    blocks: ["08", "09"]

  - id: "08"
    path: planning/sections/section-08-daily-system.md
    title: Daily Puzzle System Integration
    requires: ["06", "07"]
    blocks: ["09"]

  - id: "09"
    path: planning/sections/section-09-testing-polish.md
    title: Testing & Polish
    requires: ["07", "08"]
    blocks: []
```

## Dependency Graph

```
                    ┌─────────────────┐
                    │  01: Cleanup    │
                    └────────┬────────┘
                             │
          ┌──────────────────┼──────────────────┐
          │                  │                  │
          ▼                  ▼                  │
┌─────────────────┐  ┌─────────────────┐        │
│  02: Design     │  │  03: Dictionary │        │
└────────┬────────┘  └────────┬────────┘        │
         │                    │                 │
         │                    ▼                 │
         │           ┌─────────────────┐        │
         │           │  04: Game Logic │        │
         │           └────────┬────────┘        │
         │                    │                 │
         │          ┌─────────┴─────────┐       │
         │          │                   │       │
         │          ▼                   ▼       │
         │  ┌─────────────────┐        ┌───────┴───────┐
         │  │  05: DB Models  │◄───────│  (from 01)    │
         │  └────────┬────────┘        └───────────────┘
         │           │
         │           ▼
         │  ┌─────────────────┐
         │  │  06: Game API   │
         │  └────────┬────────┘
         │           │
         └─────┬─────┘
               │
               ▼
      ┌─────────────────┐
      │  07: Frontend   │
      └────────┬────────┘
               │
               ▼
      ┌─────────────────┐
      │  08: Daily Sys  │
      └────────┬────────┘
               │
               ▼
      ┌─────────────────┐
      │  09: Testing    │
      └─────────────────┘
```

## Recommended Execution Order

1. **Section 01** - Codebase Cleanup (blocking, must be first)
2. **Sections 02 + 03** - Design Foundation + Dictionary (can run in parallel)
3. **Section 04** - Game Logic (needs dictionary)
4. **Section 05** - Database Models (needs game logic types)
5. **Section 06** - Game API (needs database + game logic)
6. **Section 07** - Frontend (needs design + API)
7. **Section 08** - Daily System (needs frontend + API)
8. **Section 09** - Testing & Polish (final)

## Section Files Reference

### Section 01: Codebase Cleanup
**File:** `planning/sections/section-01-codebase-cleanup.md`

Purpose: Fix pre-commit violations in scaffolding code, delete unused placeholder files, establish clean baseline.

Key deliverables:
- All backend Python files have docstrings
- Item-related scaffolding deleted
- `pre-commit run --all-files` passes

---

### Section 02: Design Foundation
**File:** `planning/sections/section-02-design-foundation.md`

Purpose: Establish visual direction with daisyUI theme and animation specifications.

Key deliverables:
- daisyUI installed and configured
- Custom `quartiles` and `quartiles-dark` themes
- Animation keyframes (float, wobble, shake)
- Grain texture CSS

---

### Section 03: Dictionary Pipeline
**File:** `planning/sections/section-03-dictionary-pipeline.md`

Purpose: Build curated word dictionary with definitions for game validation.

Key deliverables:
- `backend/scripts/download_sources.py`
- `backend/scripts/build_dictionary.py`
- `backend/data/dictionary.bin` (15K-35K words)
- `backend/app/game/dictionary.py` with Dictionary class

---

### Section 04: Game Logic
**File:** `planning/sections/section-04-game-logic.md`

Purpose: Pure Python game mechanics with no framework dependencies.

Key deliverables:
- `backend/app/game/types.py` - Domain dataclasses
- `backend/app/game/generator.py` - Puzzle generation (CSP)
- `backend/app/game/solver.py` - Word finding, scoring
- Unit tests with >90% coverage

---

### Section 05: Database Models
**File:** `planning/sections/section-05-database-models.md`

Purpose: Add game tables to SQLModel schema.

Key deliverables:
- Player, Puzzle, GameSession, LeaderboardEntry, QuartileCooldown tables
- API response schemas
- Alembic migration

---

### Section 06: Game API
**File:** `planning/sections/section-06-game-api.md`

Purpose: REST endpoints for game functionality with server-authoritative validation.

Key deliverables:
- `POST /game/start` - Start session (no valid_words exposed)
- `POST /game/sessions/{id}/word` - Server-side validation
- `POST /game/sessions/{id}/submit` - Server-calculated time
- `POST /game/sessions/{id}/hint` - Definition with time penalty
- `GET /leaderboard/today` - Rankings

---

### Section 07: Frontend Game UI
**File:** `planning/sections/section-07-frontend-game-ui.md`

Purpose: React components for game interface with daisyUI.

Key deliverables:
- Remove shadcn/ui, use daisyUI
- GameBoard, TileGrid, TileButton components
- useGame hook with localStorage persistence
- Keyboard navigation (arrows + vim hjkl)
- Found words grouped by tile count

---

### Section 08: Daily System
**File:** `planning/sections/section-08-daily-system.md`

Purpose: Daily puzzle mechanics and player identity.

Key deliverables:
- First-play-wins enforcement
- Automatic puzzle generation (7 days ahead)
- Timezone handling (client-determined date)
- Device fingerprint + player persistence
- AlreadyPlayed component with countdown

---

### Section 09: Testing & Polish
**File:** `planning/sections/section-09-testing-polish.md`

Purpose: Quality assurance and final polish.

Key deliverables:
- Backend unit tests (>90% coverage)
- E2E tests with Playwright
- Performance targets met
- Accessibility basics (keyboard, focus, WCAG AA)

---

## Commit Strategy

After completing each section:

1. Stage changes: `git add <files>`
2. Verify quality: `pre-commit run --all-files`
3. Commit with format: `feat(section-XX): <description>`
4. Continue to next section

## Quick Commands

```bash
# Backend development
make backend-dev       # Start backend server
make check             # Run all checks

# Frontend development
make frontend-dev      # Start frontend (localhost:5173)
make generate-client   # Generate TS API client

# Database
make dev               # Start DB + Mailcatcher
cd backend && uv run alembic upgrade head  # Run migrations

# Testing
cd backend && uv run pytest app/game/tests/ -v
cd frontend && npx playwright test
```

## Environment Notes

- **Python Package Manager:** uv
- **JavaScript Package Manager:** bun/npm
- **Backend Framework:** FastAPI with SQLModel
- **Frontend Framework:** React with TanStack Router/Query
- **Component Library:** daisyUI (replacing shadcn/ui)
- **Database:** PostgreSQL

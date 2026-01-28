# Quartiles Implementation Sections

This index provides an overview of all implementation sections for the Quartiles project. Each section is self-contained and can be implemented independently (respecting dependencies).

## SECTION_MANIFEST

```yaml
sections:
  - id: "01"
    name: "codebase-cleanup"
    title: "Codebase Cleanup (Pre-commit Compliance)"
    requires: []
    blocks: ["02", "03", "04", "05", "06", "07", "08", "09"]

  - id: "02"
    name: "design-foundation"
    title: "Design Foundation (Figma + Theme)"
    requires: ["01"]
    blocks: ["05", "06", "07"]

  - id: "03"
    name: "dictionary-pipeline"
    title: "Dictionary Building Pipeline"
    requires: ["01"]
    blocks: ["04"]

  - id: "04"
    name: "game-logic"
    title: "Pure Python Game Logic"
    requires: ["03"]
    blocks: ["05"]

  - id: "05"
    name: "database-models"
    title: "Database Models & Migrations"
    requires: ["01", "04"]
    blocks: ["06"]

  - id: "06"
    name: "game-api"
    title: "Game API Endpoints"
    requires: ["04", "05"]
    blocks: ["07", "08"]

  - id: "07"
    name: "frontend-game-ui"
    title: "Frontend Game UI Components"
    requires: ["02", "06"]
    blocks: ["08", "09"]

  - id: "08"
    name: "daily-system"
    title: "Daily Puzzle System Integration"
    requires: ["06", "07"]
    blocks: ["09"]

  - id: "09"
    name: "testing-polish"
    title: "Testing & Polish"
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

## Section Overview

### Section 01: Codebase Cleanup
**Purpose:** Ensure pre-commit hooks pass before starting new development
- Fix backend ruff linting violations in core files
- Delete scaffolding code (Items CRUD, placeholder components)
- Establish commit-by-commit quality standard

### Section 02: Design Foundation
**Purpose:** Establish visual direction before UI implementation
- Research "Grain & Gradient / Lo-Fi Organic" aesthetic
- Create Figma mockups for all game screens
- Configure daisyUI theme with custom colors

### Section 03: Dictionary Building Pipeline
**Purpose:** Create the word list and definitions for the game
- Download and filter SCOWL word list
- Integrate COCA frequency data
- Export WordNet definitions
- Build serialized trie structure

### Section 04: Pure Python Game Logic
**Purpose:** Implement core game mechanics without framework dependencies
- Domain types (Tile, Puzzle, GameSession)
- Trie-based Dictionary class
- Puzzle generator with CSP algorithm
- Solver for finding valid words
- Comprehensive unit tests

### Section 05: Database Models & Migrations
**Purpose:** Add game-specific database tables
- Player, Puzzle, GameSession, LeaderboardEntry tables
- QuartileCooldown for word cooldown tracking
- Alembic migration creation

### Section 06: Game API Endpoints
**Purpose:** REST API for game functionality
- `/game/start` - Start new session
- `/game/sessions/{id}/word` - Validate word (per-word feedback)
- `/game/sessions/{id}/submit` - Finalize game
- `/game/sessions/{id}/hint` - Request hint
- `/puzzle/today` - Get daily puzzle
- `/leaderboard/today` - Get rankings

### Section 07: Frontend Game UI Components
**Purpose:** React components for the game interface
- Replace shadcn/ui with daisyUI
- TileGrid and TileButton components
- WordFormation zone
- ScoreDisplay and Timer
- FoundWordsList sidebar
- Keyboard navigation (arrows + vim)
- localStorage persistence

### Section 08: Daily Puzzle System Integration
**Purpose:** Wire up daily puzzle mechanics
- First-play-wins enforcement
- Automatic puzzle generation (cron/scheduler)
- Timezone-aware date handling
- Player identity management

### Section 09: Testing & Polish
**Purpose:** Quality assurance and refinement
- Backend unit test completion
- E2E test suite with Playwright
- Performance optimization
- Accessibility audit

## Implementation Order

**Recommended sequence:**
1. Section 01 (cleanup) - Start here
2. Sections 02 + 03 (design + dictionary) - Can run in parallel
3. Section 04 (game logic) - Needs dictionary
4. Section 05 (database) - Needs game logic types
5. Section 06 (API) - Needs database + game logic
6. Section 07 (frontend) - Needs design + API
7. Section 08 (daily system) - Needs frontend + API
8. Section 09 (testing) - Final polish

**Parallel opportunities:**
- Sections 02 and 03 can be done simultaneously
- Backend (03-06) can progress while frontend design (02) is being finalized

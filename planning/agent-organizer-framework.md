# Agent-Organizer Framework for Quartiles Implementation

## Overview

This document provides the framework for implementing Sections 02-09 of the Quartiles project using the agent-organizer pattern with specialized agents.

**Section 01 Status:** ✅ COMPLETE (commit `a37e531`)

---

## Core Workflow Pattern

```
Main Session (Coordinator)
    │
    ├─ 1. Read section spec from planning/sections/section-XX-*.md
    │
    ├─ 2. Decompose into implementation chunks (3-5 chunks typical)
    │
    ├─ 3. For each chunk:
    │     ├─ coder agent → Implementation
    │     ├─ verification-agent → Pass/Fail report
    │     └─ (if tests involved) test-automator or qa-expert
    │
    ├─ 4. Run `make check` after all chunks pass
    │
    └─ 5. Commit with conventional message via /git-commit
```

---

## Agent Roles & When to Use

| Agent | Role | Invoke When |
|-------|------|-------------|
| **coder** | Write production code | Implementation chunks |
| **verification-agent** | Verify acceptance criteria | After each coder chunk |
| **test-automator** | Design/implement test infrastructure | Setting up test frameworks, writing test suites |
| **qa-expert** | Test strategy, coverage analysis | Planning test approach, identifying gaps |
| **code-reviewer** | Quality/security review | After significant implementations |
| **ui-designer** | UI/UX decisions | Frontend component design |
| **architect-reviewer** | Architecture decisions | Database schema, API design |
| **research-analyst** | Research topics | External integrations, best practices |
| **documentation-engineer** | Create/update docs | API docs, README updates, usage guides |

---

## Section Implementation Plans

### Section 02: Design Foundation
**Requires:** 01 ✅ | **Blocks:** 05, 06, 07

```
agent-organizer
    │
    ├─ research-analyst: Research "Grain & Gradient / Lo-Fi Organic" aesthetic
    │
    ├─ ui-designer: Design color palette, theme tokens, component patterns
    │
    ├─ coder (chunk 1): Configure daisyUI theme in tailwind.config
    │     └─ verification-agent
    │
    ├─ coder (chunk 2): Replace shadcn Button/Card/Input with daisyUI
    │     └─ verification-agent
    │
    ├─ coder (chunk 3): Update remaining UI components
    │     └─ verification-agent
    │
    └─ qa-expert: Verify accessibility and visual consistency
```

---

### Section 03: Dictionary Pipeline
**Requires:** 01 ✅ | **Blocks:** 04

```
agent-organizer
    │
    ├─ coder (chunk 1): Download and filter SCOWL word list
    │     └─ verification-agent
    │
    ├─ coder (chunk 2): Integrate COCA frequency data
    │     └─ verification-agent
    │
    ├─ coder (chunk 3): Export WordNet definitions
    │     └─ verification-agent
    │
    ├─ coder (chunk 4): Build serialized trie structure
    │     └─ verification-agent
    │
    └─ test-automator: Create pipeline validation tests
          └─ verification-agent
```

---

### Section 04: Pure Python Game Logic
**Requires:** 03 | **Blocks:** 05

```
agent-organizer
    │
    ├─ coder (chunk 1): Domain types (Tile, Puzzle, GameSession) in backend/app/game/
    │     └─ verification-agent
    │
    ├─ coder (chunk 2): Trie-based Dictionary class
    │     └─ verification-agent
    │
    ├─ coder (chunk 3): Puzzle generator with CSP algorithm
    │     └─ verification-agent
    │
    ├─ coder (chunk 4): Word solver for finding valid words
    │     └─ verification-agent
    │
    ├─ qa-expert: Define test strategy for game logic (edge cases, invariants)
    │
    ├─ test-automator: Implement comprehensive unit test suite
    │     └─ verification-agent
    │
    ├─ code-reviewer: Verify pure Python boundary (no FastAPI/SQLModel imports)
    │
    └─ documentation-engineer: Document game module API (types, functions, usage)
```

**Critical:** The `backend/app/game/` module must use **pure Python dataclasses only** - no FastAPI/SQLModel/Pydantic imports.

---

### Section 05: Database Models & Migrations
**Requires:** 01 ✅, 04 | **Blocks:** 06

```
agent-organizer
    │
    ├─ architect-reviewer: Review schema design against game domain types
    │
    ├─ coder (chunk 1): Player, Puzzle models in backend/app/models.py
    │     └─ verification-agent
    │
    ├─ coder (chunk 2): GameSession, LeaderboardEntry models
    │     └─ verification-agent
    │
    ├─ coder (chunk 3): QuartileCooldown for word cooldown tracking
    │     └─ verification-agent
    │
    ├─ coder (chunk 4): Alembic migrations
    │     └─ verification-agent
    │
    └─ test-automator: Create model unit tests
          └─ verification-agent
```

---

### Section 06: Game API Endpoints
**Requires:** 04, 05 | **Blocks:** 07, 08

```
agent-organizer
    │
    ├─ architect-reviewer: Review API design and adapter pattern
    │
    ├─ coder (chunk 1): /game/start - Start new session
    │     └─ verification-agent
    │
    ├─ coder (chunk 2): /game/sessions/{id}/word - Validate word
    │     └─ verification-agent
    │
    ├─ coder (chunk 3): /game/sessions/{id}/submit - Finalize game
    │     └─ verification-agent
    │
    ├─ coder (chunk 4): /game/sessions/{id}/hint - Request hint
    │     └─ verification-agent
    │
    ├─ coder (chunk 5): /puzzle/today, /leaderboard/today
    │     └─ verification-agent
    │
    ├─ qa-expert: Define API test strategy (happy path, edge cases, auth)
    │
    ├─ test-automator: Implement API integration tests
    │     └─ verification-agent
    │
    ├─ code-reviewer: Review adapter layer between Pydantic and game types
    │
    └─ documentation-engineer: API usage examples and endpoint documentation
```

---

### Section 07: Frontend Game UI
**Requires:** 02, 06 | **Blocks:** 08, 09

```
agent-organizer
    │
    ├─ ui-designer: Review component hierarchy and interaction patterns
    │
    ├─ coder (chunk 1): TileGrid and TileButton components
    │     └─ verification-agent
    │
    ├─ coder (chunk 2): WordFormation zone
    │     └─ verification-agent
    │
    ├─ coder (chunk 3): ScoreDisplay and Timer components
    │     └─ verification-agent
    │
    ├─ coder (chunk 4): FoundWordsList sidebar
    │     └─ verification-agent
    │
    ├─ coder (chunk 5): Keyboard navigation (arrows + vim bindings)
    │     └─ verification-agent
    │
    ├─ coder (chunk 6): localStorage persistence
    │     └─ verification-agent
    │
    ├─ qa-expert: Accessibility audit checklist
    │
    └─ test-automator: Component tests with React Testing Library
          └─ verification-agent
```

---

### Section 08: Daily Puzzle System
**Requires:** 06, 07 | **Blocks:** 09

```
agent-organizer
    │
    ├─ architect-reviewer: Review first-play-wins enforcement design
    │
    ├─ coder (chunk 1): First-play-wins enforcement logic
    │     └─ verification-agent
    │
    ├─ coder (chunk 2): Automatic puzzle generation (cron/scheduler)
    │     └─ verification-agent
    │
    ├─ coder (chunk 3): Timezone-aware date handling
    │     └─ verification-agent
    │
    ├─ coder (chunk 4): Player identity management
    │     └─ verification-agent
    │
    └─ test-automator: Integration tests for daily system
          └─ verification-agent
```

---

### Section 09: Testing & Polish
**Requires:** 07, 08 | **Blocks:** None

```
agent-organizer
    │
    ├─ qa-expert: Full test coverage analysis and gap identification
    │
    ├─ test-automator (chunk 1): Complete backend unit test coverage
    │     └─ verification-agent
    │
    ├─ test-automator (chunk 2): E2E test suite with Playwright
    │     └─ verification-agent
    │
    ├─ code-reviewer: Performance review
    │
    ├─ qa-expert: Accessibility audit execution
    │
    ├─ ui-designer: Final visual polish review
    │
    └─ documentation-engineer: Final README, setup guide, and user documentation
```

---

## Parallel Execution Strategy

Sections 02 and 03 can run **in parallel** (no dependencies on each other):

```
Session A                    Session B
───────────────────          ───────────────────
Section 02: Design           Section 03: Dictionary
    │                            │
    ▼                            ▼
(waits for 06)               Section 04: Game Logic
                                 │
                                 ▼
                             Section 05: Database
                                 │
                                 ▼
                             Section 06: API
                                 │
                    ─────────────┴─────────────
                                 │
                                 ▼
                         Section 07: Frontend (needs both 02 + 06)
                                 │
                                 ▼
                         Section 08: Daily System
                                 │
                                 ▼
                         Section 09: Testing
```

---

## Invocation Template

To start any section, use this prompt:

```
Implement Section XX using the agent-organizer pattern:

1. Read planning/sections/section-XX-*.md for full requirements
2. Follow the workflow from ~/.claude/plans/floofy-floating-forest.md
3. Decompose into chunks as specified
4. For each chunk: coder → verification-agent
5. Involve qa-expert for test strategy, test-automator for test implementation
6. Run `make check` before committing
7. Commit with conventional commit message via /git-commit
```

---

## Key Files Reference

| Purpose | Path |
|---------|------|
| Section specs | `planning/sections/section-XX-*.md` |
| Dependency graph | `planning/sections/index.md` |
| Game logic (pure Python) | `backend/app/game/` |
| API routes | `backend/app/api/routes/` |
| Models | `backend/app/models.py` |
| Frontend components | `frontend/src/components/` |
| Verification agent | `~/.claude/agents/verification-agent.md` |

---

## Verification Checklist (Every Section)

Before committing each section:
- [ ] `make check` passes (prek + ty + ruff + biome)
- [ ] All acceptance criteria from section spec verified
- [ ] qa-expert reviewed test coverage (where applicable)
- [ ] test-automator created tests (where applicable)
- [ ] No regressions in existing functionality

# Quartiles Implementation Prompt (ralph-loop)

This file is designed for use with the ralph-loop plugin, which executes sections autonomously with all content embedded inline.

## Project Overview

**Project:** Quartiles - A daily word puzzle game inspired by Apple News+ Quartiles
**Stack:** FastAPI + SQLModel + PostgreSQL (backend), React + TypeScript + TanStack + daisyUI (frontend)
**Game Logic:** Pure Python module with no framework dependencies

## Critical Constraints

1. **Pre-commit compliance**: Every commit must pass `pre-commit run --all-files`
2. **Game logic isolation**: `backend/app/game/` must have NO imports from FastAPI, SQLModel, or Pydantic
3. **Server-authoritative**: All scoring, timing, and validation happens server-side; client never receives valid_words list
4. **First-play-wins**: Each player gets exactly one competitive attempt per daily puzzle

## Implementation Sections

Execute sections in order, respecting dependencies. Each section has acceptance criteria that must be verified before proceeding.

---

## Section 01: Codebase Cleanup (Pre-commit Compliance)

### Background

The Quartiles codebase was generated from a template and contains placeholder/scaffolding code that doesn't pass pre-commit hooks. Before implementing new features, we need to establish a clean baseline where every commit passes quality checks.

Pre-commit hooks enforce:
- **Backend:** ruff (Python linting + formatting)
- **Frontend:** biome (TypeScript/JavaScript linting)
- **General:** trailing whitespace, end-of-file fixes

### Dependencies

- **Requires:** None (this is the first section)
- **Blocks:** All other sections (02-09)

### Implementation Tasks

**Backend Cleanup:**

1. Add docstrings to these files:
   - `backend/app/api/deps.py` - Module + function docstrings
   - `backend/app/api/main.py` - Module docstring
   - `backend/app/core/config.py` - Module docstring
   - `backend/app/core/security.py` - Module + function docstrings
   - `backend/app/core/db.py` - Module docstring
   - `backend/app/models.py` - Module docstring
   - `backend/app/crud.py` - Module docstring

2. Delete scaffolding files:
   - `backend/app/api/routes/items.py`
   - Remove Item-related schemas from `backend/app/models.py`
   - Remove Item-related CRUD from `backend/app/crud.py`
   - Remove items router from `backend/app/api/main.py`

3. Run auto-fix:
   ```bash
   cd backend && uv run ruff check --fix . && uv run ruff format .
   ```

**Frontend Cleanup:**

Delete scaffolding directories:
- `frontend/src/components/Items/`
- `frontend/src/components/Admin/`
- `frontend/src/components/Pending/PendingItems.tsx`

### Acceptance Criteria

- [ ] `pre-commit run --all-files` passes completely
- [ ] `backend/app/api/routes/items.py` deleted
- [ ] Item-related code removed from models.py and crud.py
- [ ] Items router removed from api/main.py
- [ ] `frontend/src/components/Items/` directory deleted
- [ ] `frontend/src/components/Admin/` directory deleted
- [ ] All backend Python files have module docstrings
- [ ] `uv run ruff check backend/` shows no errors
- [ ] `npx biome check frontend/src/` shows no errors

---

## Section 02: Design Foundation (Figma + Theme)

### Background

Quartiles uses a "Grain & Gradient / Lo-Fi Organic" aesthetic. Before implementing UI components, establish the design foundation with daisyUI theme configuration and animation specifications.

### Dependencies

- **Requires:** Section 01
- **Blocks:** Section 07

### Implementation Tasks

1. **Install daisyUI:**
   ```bash
   cd frontend && npm install daisyui@^4
   ```

2. **Configure tailwind.config.js** with custom `quartiles` and `quartiles-dark` themes:
   - Muted, earthy color palette
   - Custom animations (float, wobble, shake)
   - Organic border radius

3. **Create style files:**
   - `frontend/src/styles/theme.css` - Grain texture, tile styling
   - `frontend/src/styles/animations.css` - Keyframe animations

4. **Document design tokens** in `planning/design/`:
   - Color palette with hex codes
   - Typography selections
   - Animation timing specifications

### Acceptance Criteria

- [ ] daisyUI added to package.json
- [ ] `quartiles` theme defined in tailwind.config.js
- [ ] `quartiles-dark` theme defined
- [ ] Custom animations (float, wobble, shake) working
- [ ] Grain texture CSS created
- [ ] Theme renders correctly in browser

---

## Section 03: Dictionary Building Pipeline

### Background

Quartiles requires a high-quality word dictionary for word validation and hint definitions. The dictionary is built from SCOWL (size 60) filtered by COCA frequency, enriched with WordNet definitions, and serialized as a binary trie.

### Dependencies

- **Requires:** Section 01
- **Blocks:** Section 04

### Implementation Tasks

1. **Create directory structure:**
   ```
   backend/
   ├── data/
   │   ├── raw/              # gitignored
   │   └── dictionary.bin    # committed
   └── scripts/
       ├── download_sources.py
       └── build_dictionary.py
   ```

2. **Implement download_sources.py:**
   - Download SCOWL 2of12inf word list

3. **Implement build_dictionary.py:**
   - Filter words to 3+ letters
   - Optionally filter by COCA frequency (top 30K)
   - Remove blocklisted words
   - Enrich with WordNet definitions
   - Serialize as pickle trie

4. **Implement Dictionary class** in `backend/app/game/dictionary.py`:
   - `contains(word)` - O(k) lookup
   - `contains_prefix(prefix)` - For search pruning
   - `get_definition(word)` - For hints
   - `load(path)` - Class method to load binary

### Acceptance Criteria

- [ ] `backend/scripts/download_sources.py` downloads SCOWL
- [ ] `backend/scripts/build_dictionary.py` executes full pipeline
- [ ] `backend/data/dictionary.bin` generated (15K-35K words)
- [ ] Dictionary class loads in <100ms
- [ ] `contains()`, `contains_prefix()`, `get_definition()` work correctly
- [ ] Unit tests pass for Dictionary class

---

## Section 04: Pure Python Game Logic

### Background

The game logic is isolated in `backend/app/game/` with **NO** dependencies on FastAPI, SQLModel, or Pydantic. This ensures testability and reusability.

### Dependencies

- **Requires:** Section 03
- **Blocks:** Section 05

### Implementation Tasks

1. **Create domain types** in `backend/app/game/types.py`:
   - `Tile(id, letters)` - Frozen dataclass, 2-4 letters
   - `Word(text, tile_ids, points)` - Frozen dataclass
   - `Puzzle(tiles, quartile_words, valid_words, total_points)` - 20 tiles, 5 quartiles
   - `GameState(puzzle, found_words, current_score, hints_used)` - Mutable

2. **Create puzzle generator** in `backend/app/game/generator.py`:
   - `generate_puzzle(dictionary, excluded_quartiles)` -> Puzzle
   - Uses CSP with backtracking
   - Each quartile decomposes into exactly 4 tiles
   - No duplicate tiles across words
   - Total points >= 130

3. **Create solver** in `backend/app/game/solver.py`:
   - `find_all_valid_words(tiles, dictionary)` -> set[str]
   - Uses permutations with prefix pruning
   - `score_word(tile_count)` -> int: {1:2, 2:4, 3:7, 4:10}
   - `calculate_hint_penalty(hint_number)` -> int (ms)

4. **Create comprehensive tests** in `backend/app/game/tests/`

### Acceptance Criteria

- [ ] NO imports from FastAPI, SQLModel, or Pydantic in game module
- [ ] Tile validates 2-4 letters
- [ ] Puzzle validates 20 tiles, 5 quartiles
- [ ] `generate_puzzle()` succeeds within 1000 attempts
- [ ] `find_all_valid_words()` completes in <100ms
- [ ] Test coverage >90% for game module
- [ ] `pytest backend/app/game/tests/` passes

---

## Section 05: Database Models & Migrations

### Background

Add game-specific tables to the existing SQLModel setup.

### Dependencies

- **Requires:** Sections 01, 04
- **Blocks:** Section 06

### Implementation Tasks

1. **Add tables to `backend/app/models.py`:**
   - `Player(id, display_name, device_fingerprint, user_id, created_at)`
   - `Puzzle(id, date, tiles_json, quartile_words_json, valid_words_json, total_available_points, created_at)`
   - `GameSession(id, puzzle_id, player_id, start_time, completed_at, solve_time_ms, final_score, hints_used, hint_penalty_ms, words_found_json)`
   - `LeaderboardEntry(id, puzzle_id, player_id, solve_time_ms, created_at)`
   - `QuartileCooldown(word, last_used_date)`

2. **Add Pydantic schemas** for API responses:
   - `TileSchema`, `PuzzleResponse`, `GameStartResponse`
   - `WordValidationResponse`, `GameSubmitResponse`
   - `HintResponse`, `LeaderboardEntrySchema`

3. **Create Alembic migration:**
   ```bash
   cd backend && uv run alembic revision --autogenerate -m "add game tables"
   ```

4. **Run migration:**
   ```bash
   uv run alembic upgrade head
   ```

### Acceptance Criteria

- [ ] All tables defined with correct relationships
- [ ] Alembic migration generated successfully
- [ ] Migration runs without errors
- [ ] Tables visible in database
- [ ] `pre-commit run --all-files` passes

---

## Section 06: Game API Endpoints

### Background

REST API for game functionality. Server is authoritative for all scoring and timing.

### Dependencies

- **Requires:** Sections 04, 05
- **Blocks:** Sections 07, 08

### Implementation Tasks

1. **Create name generator** in `backend/app/services/name_generator.py`:
   - `generate_player_name()` -> AdjectiveNoun format
   - 100+ adjectives, 100+ nouns

2. **Create game routes** in `backend/app/api/routes/game.py`:
   - `POST /game/start` - Start session, return tiles (NOT valid_words)
   - `POST /game/sessions/{id}/word` - Validate word server-side
   - `POST /game/sessions/{id}/submit` - Finalize, calculate server time
   - `POST /game/sessions/{id}/hint` - Return definition, add penalty

3. **Create puzzle routes** in `backend/app/api/routes/puzzle.py`:
   - `GET /puzzle/today` - Get today's puzzle (lazy generation)
   - `GET /puzzle/{date}` - Get puzzle by date

4. **Create leaderboard routes** in `backend/app/api/routes/leaderboard.py`:
   - `GET /leaderboard/today` - Get rankings sorted by solve_time_ms
   - `GET /leaderboard/{date}` - Historical rankings

5. **Create puzzle scheduler** in `backend/app/services/puzzle_scheduler.py`:
   - `ensure_puzzle_exists_for_date(date, db)`
   - Respects 30-day quartile cooldown

6. **Register routes** in `backend/app/api/main.py`

### Acceptance Criteria

- [ ] `/game/start` does NOT return valid word list
- [ ] `/game/sessions/{id}/word` validates server-side
- [ ] `/game/sessions/{id}/submit` calculates time server-side
- [ ] Hint penalties: 30s, 60s, 120s, 240s, 480s
- [ ] Maximum 5 hints enforced
- [ ] First-play-wins enforced
- [ ] All endpoints have proper error handling
- [ ] `pre-commit run --all-files` passes

---

## Section 07: Frontend Game UI Components

### Background

React components for the game interface using daisyUI.

### Dependencies

- **Requires:** Sections 02, 06
- **Blocks:** Sections 08, 09

### Implementation Tasks

1. **Remove shadcn/ui:**
   ```bash
   cd frontend
   npm uninstall @radix-ui/react-* cmdk lucide-react class-variance-authority clsx tailwind-merge
   rm -rf src/components/ui/
   ```

2. **Create game hook** in `frontend/src/hooks/useGame.ts`:
   - Reducer-based state management
   - localStorage persistence
   - Timer (display only - server authoritative)
   - API integration

3. **Create keyboard hook** in `frontend/src/hooks/useKeyboardNavigation.ts`:
   - Arrow keys + vim-style (hjkl)
   - Enter/Space to select
   - Escape to clear

4. **Create components:**
   - `GameBoard.tsx` - Main container
   - `TileGrid.tsx` - 4x5 grid
   - `TileButton.tsx` - Individual tile with states
   - `WordFormation.tsx` - Selected tiles display
   - `ScoreDisplay.tsx` - Score + timer
   - `FoundWordsList.tsx` - Grouped by tile count

5. **Create animations.css** with float, wobble, shake keyframes

6. **Create game route** at `/game`

### Acceptance Criteria

- [ ] shadcn/ui removed
- [ ] TileGrid displays 4x5 grid
- [ ] Toggle selection on click
- [ ] Keyboard navigation (arrows + hjkl)
- [ ] Word validation via API
- [ ] Shake animation for invalid words
- [ ] Timer increments while playing
- [ ] Found words grouped by tile count
- [ ] localStorage persistence
- [ ] Responsive design

---

## Section 08: Daily Puzzle System Integration

### Background

Wire up daily puzzle mechanics: first-play-wins, automatic generation, timezone handling.

### Dependencies

- **Requires:** Sections 06, 07
- **Blocks:** Section 09

### Implementation Tasks

1. **Implement first-play-wins** in `backend/app/services/first_play.py`:
   - Check for completed session
   - Return previous result if already played

2. **Implement puzzle scheduler**:
   - APScheduler for midnight generation
   - Pre-generate 7 days ahead
   - Startup hook ensures today's puzzle exists

3. **Create timezone utilities** in `frontend/src/utils/timezone.ts`:
   - `getLocalPuzzleDate()` - Client's local date
   - `getTimeUntilNextPuzzle()` - Countdown timer

4. **Create fingerprint utility** in `frontend/src/utils/fingerprint.ts`:
   - Device fingerprint for player identity

5. **Create player hook** in `frontend/src/hooks/usePlayer.ts`:
   - Persist player_id and display_name

6. **Create AlreadyPlayed component** with countdown timer

### Acceptance Criteria

- [ ] Player can complete puzzle only once per day
- [ ] Second visit shows previous result
- [ ] Puzzles pre-generated 7 days ahead
- [ ] 30-day quartile cooldown respected
- [ ] Countdown timer to next puzzle
- [ ] Player identity persists across sessions

---

## Section 09: Testing & Polish

### Background

Final quality assurance: comprehensive testing, performance optimization, accessibility.

### Dependencies

- **Requires:** Sections 07, 08
- **Blocks:** None (final section)

### Implementation Tasks

1. **Backend unit tests** in `backend/app/game/tests/`:
   - test_types.py - Domain type validation
   - test_dictionary.py - Trie operations
   - test_generator.py - Puzzle generation
   - test_solver.py - Word finding, scoring

2. **E2E tests** in `frontend/e2e/game.spec.ts`:
   - Tile selection toggles
   - Keyboard navigation
   - Timer functionality
   - State persistence

3. **Performance verification:**
   - Dictionary load <50ms
   - Page load <2s
   - Word validation <100ms

4. **Accessibility:**
   - All tiles keyboard accessible
   - Focus states visible
   - aria-live for score updates
   - Color contrast WCAG AA

### Acceptance Criteria

- [ ] `pytest backend/app/game/tests/` passes
- [ ] Game logic coverage >90%
- [ ] `npx playwright test` passes
- [ ] E2E covers: selection, keyboard, timer, persistence
- [ ] `pre-commit run --all-files` passes
- [ ] No TypeScript errors
- [ ] No console errors in browser

---

## Execution Notes

1. **Commit after each section** with message format: `feat(section-XX): <description>`
2. **Verify acceptance criteria** before proceeding to next section
3. **Run `pre-commit run --all-files`** before every commit
4. **Sections 02 and 03 can be done in parallel** after Section 01
5. **Generate TypeScript client** after API changes: `make generate-client`

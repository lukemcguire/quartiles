# Quartiles Implementation Plan

## Overview

This document provides a complete implementation plan for building Quartiles, a web-based word puzzle game. The plan is designed to be self-contained - an engineer or LLM with no prior context should understand what we're building, why, and how.

### What We're Building

**Quartiles** is a daily word puzzle game where players:
1. See a 4x5 grid of 20 letter tiles (each tile has 2-4 letters)
2. Combine tiles to form valid English words
3. Score points based on tiles used (1-tile=2pts, 2-tile=4pts, 3-tile=7pts, 4-tile=10pts)
4. Race to reach 100 points (the "solve threshold")
5. Compete on a daily leaderboard ranked by solve time

**Key Features:**
- Exactly 5 "quartile words" (4-tile combinations) per puzzle
- Hints that reveal quartile word definitions (with time penalties)
- Two-phase gameplay: timed competition then relaxed completion
- Anonymous play with generated silly names (ChubbyPenguin, RotundUnicorn)
- "Grain & Gradient / Lo-Fi Organic" visual aesthetic

### Tech Stack

- **Backend:** FastAPI + SQLModel + PostgreSQL
- **Frontend:** React + TypeScript + TanStack Router/Query + Tailwind CSS + daisyUI
- **Game Logic:** Pure Python module (isolated from web framework)

### Project Structure

```
quartiles/
├── backend/app/
│   ├── game/              # Pure Python game logic
│   │   ├── types.py       # Domain dataclasses
│   │   ├── dictionary.py  # Trie-based word validation
│   │   ├── generator.py   # Puzzle generation algorithm
│   │   └── solver.py      # Word finding, scoring
│   ├── api/routes/
│   │   └── game.py        # Game API endpoints
│   ├── models.py          # Database models (add game tables)
│   └── services/
│       └── puzzle.py      # Puzzle scheduling service
├── frontend/src/
│   ├── routes/
│   │   └── _layout/
│   │       └── game.tsx   # Main game page
│   └── components/
│       └── Game/          # Game UI components
└── planning/              # This documentation
```

---

## Phase -1: Codebase Cleanup (Pre-commit Compliance)

### Background

The codebase has pre-commit hooks that enforce:
- **Backend:** ruff (linting + formatting)
- **Frontend:** biome (linting)
- **General:** trailing whitespace, end-of-file fixes

Current state:
- Frontend biome checks **pass** (no errors)
- Backend ruff checks have ~50+ violations (missing docstrings, type annotations)
- Most violations are in placeholder/scaffolding code

### Strategy: Incremental Cleanup

Rather than a big-bang cleanup of scaffolding code we'll mostly delete, we'll:

1. **Fix backend linting on files we keep** (core infrastructure)
2. **Delete scaffolding we're replacing** (Items CRUD, placeholder routes)
3. **Ensure each new commit passes pre-commit hooks**

### -1.1 Backend Cleanup Tasks

**Files to fix (keep and clean up):**
- `backend/app/api/deps.py` - Add docstrings to auth dependencies
- `backend/app/api/main.py` - Add module docstring
- `backend/app/core/` - Add docstrings to security, config, db modules
- `backend/app/models.py` - Add docstrings (we're extending this)
- `backend/app/crud.py` - Add docstrings (we're extending this)

**Files to delete (scaffolding):**
- `backend/app/api/routes/items.py` - Template CRUD, not needed
- Related item tests and schemas

**Action:** Run `ruff check --fix` to auto-fix what's possible, then manually add docstrings.

### -1.2 Frontend Cleanup Tasks

**Files to delete (replacing with daisyUI):**
- `frontend/src/components/ui/` - Entire shadcn directory
- `frontend/src/components/Items/` - Template CRUD components
- `frontend/src/components/Admin/` - Placeholder admin components

**Files to keep and possibly update:**
- Core routing files
- Auth hooks
- Theme provider (may need daisyUI adaptation)

### -1.3 Commit Strategy

Each implementation section should:
1. Create a feature branch
2. Make changes
3. Run `pre-commit run --all-files` before committing
4. Fix any violations
5. Commit with passing hooks
6. Merge to main

**Pre-commit command:** `pre-commit run --all-files`

---

## Phase 0: Design Foundation

### 0.1 Design Research

**Goal:** Establish visual direction for "Grain & Gradient / Lo-Fi Organic" aesthetic

**Tasks:**
1. Research and collect reference images/websites with the target aesthetic
2. Document color palette (muted, earthy tones)
3. Define texture patterns (grain, noise overlays)
4. Identify typography that fits the style
5. Create mood board in Figma

**Deliverables:**
- Figma mood board with 10-15 reference images
- Documented color palette (primary, secondary, accent, backgrounds)
- Typography selection (heading, body fonts)

### 0.2 UI Mockups

**Goal:** Complete Figma mockups before any UI implementation

**Screens to Design:**
1. **Game Board** (main gameplay)
   - 4x5 tile grid with organic styling
   - Selected tiles / word formation zone
   - Score display and timer
   - Submit button
   - Found words sidebar (grouped by tile count)

2. **Leaderboard**
   - Today's rankings
   - Player's position highlighted
   - Time format: M:SS

3. **Game Complete**
   - Final score and time
   - Option to continue finding words
   - Share functionality

4. **States**
   - Tile hover state (gentle wobble)
   - Tile selected state
   - Tile in quartile state
   - Invalid word shake
   - Success celebration

**Deliverables:**
- Complete Figma file with all screens
- Component library (buttons, tiles, cards)
- Animation specifications
- Dark/light mode variants

### 0.3 daisyUI Theme Configuration

**Goal:** Translate Figma design to daisyUI theme

**Tasks:**
1. Create custom daisyUI theme in `tailwind.config.js`
2. Define semantic color tokens:
   - `primary`, `secondary`, `accent`
   - `base-100` through `base-300` (backgrounds)
   - `neutral`, `info`, `success`, `warning`, `error`
3. Configure dark mode variant
4. Add custom CSS for grain/texture effects

**File:** `frontend/tailwind.config.js`
```javascript
module.exports = {
  daisyui: {
    themes: [
      {
        quartiles: {
          "primary": "#...",    // From Figma
          "secondary": "#...",
          "accent": "#...",
          "neutral": "#...",
          "base-100": "#...",
          // ... etc
        },
        "quartiles-dark": {
          // Dark mode colors
        }
      }
    ]
  }
}
```

---

## Phase 1: Game Core (Pure Python)

### 1.1 Domain Types

**Goal:** Define core game types as pure Python dataclasses

**File:** `backend/app/game/types.py`

```python
from dataclasses import dataclass
from typing import List, Set, Optional

@dataclass(frozen=True)
class Tile:
    """A single tile containing 2-4 letters."""
    id: int
    letters: str  # 2-4 uppercase letters

@dataclass(frozen=True)
class Word:
    """A valid word formed from tiles."""
    text: str
    tile_ids: tuple[int, ...]  # Which tiles form this word
    points: int  # Calculated from tile count

@dataclass
class Puzzle:
    """A complete puzzle configuration."""
    tiles: tuple[Tile, ...]  # Exactly 20 tiles
    quartile_words: tuple[str, ...]  # Exactly 5 target words
    valid_words: frozenset[str]  # All valid words findable
    total_points: int  # Sum of all valid word points

@dataclass
class GameSession:
    """Active game state for a player."""
    puzzle: Puzzle
    found_words: Set[str]
    current_score: int
    hints_used: int
    start_time_ms: int
    solve_time_ms: Optional[int]  # None until solved
```

**Constraints:**
- No imports from FastAPI, SQLModel, or Pydantic
- All types should be serializable to JSON
- Use `frozen=True` for immutable value objects

### 1.2 Dictionary Module

**Goal:** Trie-based dictionary for efficient word validation and prefix checking

**File:** `backend/app/game/dictionary.py`

**Data Structures:**

```python
class TrieNode:
    """Node in prefix tree."""
    children: dict[str, 'TrieNode']
    is_word: bool
    definition: Optional[str]

class Dictionary:
    """Trie-backed word dictionary."""
    root: TrieNode

    def contains(self, word: str) -> bool:
        """Check if word exists in dictionary."""

    def contains_prefix(self, prefix: str) -> bool:
        """Check if any words start with prefix."""

    def get_definition(self, word: str) -> Optional[str]:
        """Get WordNet definition for word."""

    def words_with_prefix(self, prefix: str) -> List[str]:
        """Get all words starting with prefix."""
```

**Dictionary Building Pipeline:**

1. **Source:** SCOWL size 60 word list
2. **Filter:**
   - Remove words < 3 letters
   - Remove words with frequency rank > 30,000 (COCA)
   - Remove profanity (blocklist)
3. **Enrich:** Add WordNet definitions
4. **Serialize:** Save as binary format for fast loading

**Build Script:** `backend/scripts/build_dictionary.py`
- Input: SCOWL word list, COCA frequencies, WordNet
- Output: `backend/data/dictionary.bin` (trie serialized)

### 1.3 Puzzle Generator

**Goal:** Generate valid puzzles with exactly 5 quartile words

**File:** `backend/app/game/generator.py`

**Algorithm: Generate-First with CSP**

```python
def generate_puzzle(dictionary: Dictionary, excluded_quartiles: Set[str]) -> Optional[Puzzle]:
    """
    Generate a puzzle using constraint satisfaction.

    1. Select 5 quartile words (8-16 letters, not in cooldown)
    2. Decompose each into 4 tiles (2-4 letters each)
    3. Verify no duplicate tiles across words
    4. Validate: solver finds exactly these 5 quartiles
    5. Check total points >= 130
    """

    for attempt in range(MAX_ATTEMPTS):
        # Step 1: Select candidate quartile words
        quartile_candidates = select_quartile_candidates(
            dictionary,
            excluded_quartiles,
            count=5
        )

        # Step 2: Decompose into tiles using MRV heuristic
        tiles = decompose_words_to_tiles(quartile_candidates)
        if tiles is None:
            continue  # Couldn't find valid decomposition

        # Step 3: Build puzzle and validate
        puzzle = Puzzle(
            tiles=tuple(tiles),
            quartile_words=tuple(quartile_candidates),
            valid_words=frozenset(),  # Filled by solver
            total_points=0
        )

        # Step 4: Run solver to find all valid words
        valid_words = find_all_valid_words(puzzle.tiles, dictionary)

        # Step 5: Validate constraints
        quartiles_found = [w for w in valid_words if len(get_tiles(w)) == 4]
        if set(quartiles_found) != set(quartile_candidates):
            continue  # Wrong quartiles found

        total_points = sum(score_word(w) for w in valid_words)
        if total_points < 130:
            continue  # Not enough points available

        return Puzzle(
            tiles=puzzle.tiles,
            quartile_words=puzzle.quartile_words,
            valid_words=frozenset(valid_words),
            total_points=total_points
        )

    return None  # Failed to generate
```

**Tile Decomposition Algorithm:**

```python
def decompose_word_to_tiles(word: str) -> Optional[List[str]]:
    """
    Split 8-16 letter word into exactly 4 tiles of 2-4 letters.
    Uses backtracking with forward checking.
    """
    # Example: "QUARTERMASTER" -> ["QUA", "RTER", "MAS", "TER"]
    # Constraints:
    # - Exactly 4 tiles
    # - Each tile 2-4 letters
    # - Concatenation = original word
```

### 1.4 Solver Module

**Goal:** Find all valid words, calculate scores, validate solutions

**File:** `backend/app/game/solver.py`

```python
def find_all_valid_words(tiles: tuple[Tile, ...], dictionary: Dictionary) -> Set[str]:
    """
    Find all valid words using state space exploration.

    Uses cursor-based iteration with prefix pruning:
    - Generate all 1-4 tile permutations
    - For each permutation, check if prefix exists in dictionary
    - If prefix invalid, skip all extensions
    - If valid word, add to results
    """

def score_word(word: str, tile_count: int) -> int:
    """Calculate points for a word."""
    POINTS = {1: 2, 2: 4, 3: 7, 4: 10}
    return POINTS.get(tile_count, 0)

def calculate_hint_penalty(hint_number: int) -> int:
    """Calculate time penalty for nth hint (1-indexed)."""
    PENALTIES = {1: 30_000, 2: 60_000, 3: 120_000, 4: 240_000, 5: 480_000}
    return PENALTIES.get(hint_number, 480_000)

def get_unfound_quartile_hint(puzzle: Puzzle, found_words: Set[str]) -> Optional[str]:
    """Get definition of an unfound quartile word."""
    unfound = set(puzzle.quartile_words) - found_words
    if unfound:
        word = next(iter(unfound))
        return dictionary.get_definition(word)
    return None
```

### 1.5 Unit Tests

**Goal:** Comprehensive test coverage for game logic

**File:** `backend/app/game/tests/`

**Test Categories:**

1. **Dictionary Tests**
   - Trie insertion and lookup
   - Prefix checking
   - Definition retrieval
   - Edge cases (empty string, single char)

2. **Generator Tests**
   - Word decomposition
   - Tile uniqueness validation
   - Quartile word selection
   - CSP constraint satisfaction

3. **Solver Tests**
   - Permutation generation
   - Word finding accuracy
   - Scoring calculation
   - Hint penalty calculation

4. **Integration Tests**
   - Generate puzzle → solve → verify 5 quartiles
   - End-to-end word validation

---

## Phase 2: Backend API

### 2.1 Database Models

**Goal:** Add game-specific database tables

**File:** `backend/app/models.py` (extend existing)

```python
# New tables to add:

class Puzzle(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    date: date = Field(unique=True, index=True)
    tiles_json: str  # JSON array of tile objects
    quartile_words_json: str  # JSON array of 5 words
    valid_words_json: str  # JSON array of all valid words
    total_available_points: int
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Relationships
    game_sessions: list["GameSession"] = Relationship(back_populates="puzzle")

class Player(SQLModel, table=True):
    """Anonymous or authenticated player."""
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    display_name: str  # AdjectiveNoun (e.g., "ChubbyPenguin")
    device_fingerprint: Optional[str] = None  # For anonymous players
    user_id: Optional[uuid.UUID] = Field(foreign_key="user.id", default=None)  # If authenticated
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Relationships
    game_sessions: list["GameSession"] = Relationship(back_populates="player")

class GameSession(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    puzzle_id: uuid.UUID = Field(foreign_key="puzzle.id")
    player_id: uuid.UUID = Field(foreign_key="player.id")  # UUID, NOT display name
    start_time: datetime  # Server-recorded, used to calculate solve_time
    solve_time_ms: Optional[int] = None  # Server-calculated: (completed_at - start_time) + penalties
    final_score: int = 0  # Server-calculated from words_found
    hints_used: int = 0
    hint_penalty_ms: int = 0  # Accumulated hint penalties
    words_found_json: str = "[]"  # JSON array, updated per-word validation
    completed_at: Optional[datetime] = None

    # Relationships
    puzzle: Puzzle = Relationship(back_populates="game_sessions")
    player: Player = Relationship(back_populates="game_sessions")

class QuartileCooldown(SQLModel, table=True):
    word: str = Field(primary_key=True)
    last_used_date: date

class LeaderboardEntry(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    puzzle_id: uuid.UUID = Field(foreign_key="puzzle.id", index=True)
    player_id: uuid.UUID = Field(foreign_key="player.id")  # Links to Player table
    solve_time_ms: int  # Server-calculated, includes hint penalties
    rank: Optional[int] = None  # Computed
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Relationships
    player: Player = Relationship()  # For display_name lookup
```

**Migration:** Create Alembic migration for new tables

### 2.2 Name Generator

**Goal:** Generate memorable AdjectiveNoun player names

**File:** `backend/app/services/name_generator.py`

```python
ADJECTIVES = [
    "Chubby", "Sleepy", "Grumpy", "Happy", "Sneaky", "Fluffy",
    "Bouncy", "Wobbly", "Jazzy", "Cozy", "Mighty", "Tiny",
    "Rotund", "Peppy", "Mellow", "Zesty", "Quirky", "Dapper"
    # ... 100+ adjectives
]

NOUNS = [
    "Penguin", "Unicorn", "Mango", "Pancake", "Walrus", "Hedgehog",
    "Narwhal", "Cupcake", "Platypus", "Turnip", "Koala", "Avocado"
    # ... 100+ nouns
]

def generate_player_name() -> str:
    """Generate unique AdjectiveNoun name."""
    adjective = random.choice(ADJECTIVES)
    noun = random.choice(NOUNS)
    return f"{adjective}{noun}"
```

### 2.3 Game API Endpoints

**Goal:** REST API for game functionality

**File:** `backend/app/api/routes/game.py`

```python
router = APIRouter(prefix="/game", tags=["game"])

@router.post("/start", response_model=GameStartResponse)
async def start_game(
    request: GameStartRequest,
    session: SessionDep
) -> GameStartResponse:
    """
    Start a new game session.

    - Gets today's puzzle
    - Generates player name if anonymous (AdjectiveNoun)
    - Creates game session in database with start_time
    - Returns puzzle tiles only (NO valid words - security)
    """

@router.post("/sessions/{session_id}/word", response_model=WordValidationResponse)
async def validate_word(
    session_id: uuid.UUID,
    request: WordValidationRequest,
    session: SessionDep
) -> WordValidationResponse:
    """
    Validate a single word (per-word feedback).

    - Checks if word is valid for this puzzle
    - Returns points if valid, error reason if not
    - Records word in game session if valid
    - Checks if solve threshold reached
    - Does NOT expose word list to client
    """

@router.post("/sessions/{session_id}/submit", response_model=GameSubmitResponse)
async def submit_game(
    session_id: uuid.UUID,
    session: SessionDep
) -> GameSubmitResponse:
    """
    Finalize and submit game for leaderboard.

    - Server calculates final score from recorded words
    - Server calculates solve time: now() - start_time + hint_penalties
    - Updates leaderboard if solved
    - Enforces first-play-wins rule
    - Client does NOT submit score or time (server authoritative)
    """

@router.post("/sessions/{session_id}/hint", response_model=HintResponse)
async def get_hint(
    session_id: uuid.UUID,
    session: SessionDep
) -> HintResponse:
    """
    Request a hint.

    - Returns definition of unfound quartile word
    - Increments hint count in session
    - Returns time penalty (tracked server-side)
    """
```

**Request/Response Schemas:**

```python
class GameStartRequest(BaseModel):
    device_fingerprint: str
    player_id: Optional[str] = None  # UUID for returning players

class GameStartResponse(BaseModel):
    session_id: uuid.UUID
    player_id: str  # UUID (stable identifier)
    display_name: str  # AdjectiveNoun (for display only)
    tiles: list[TileSchema]
    already_played: bool  # True if first-play-wins triggered
    previous_result: Optional[PreviousResultSchema]  # If already_played
    # NOTE: valid_words intentionally NOT included (security)

class WordValidationRequest(BaseModel):
    word: str

class WordValidationResponse(BaseModel):
    is_valid: bool
    points: Optional[int]  # Points earned if valid
    reason: Optional[str]  # Error reason if invalid
    is_quartile: bool  # True if this was a 4-tile word
    current_score: int  # Updated total score
    is_solved: bool  # True if reached 100 points

class GameSubmitResponse(BaseModel):
    success: bool
    final_score: int  # Server-calculated
    solve_time_ms: Optional[int]  # Server-calculated, None if not solved
    leaderboard_rank: Optional[int]  # None if not solved or not on leaderboard
    message: str
```

### 2.4 Puzzle API Endpoints

**File:** `backend/app/api/routes/puzzle.py`

```python
router = APIRouter(prefix="/puzzle", tags=["puzzle"])

@router.get("/today", response_model=PuzzleResponse)
async def get_todays_puzzle(session: SessionDep) -> PuzzleResponse:
    """Get today's puzzle (creates if doesn't exist)."""

@router.get("/{date}", response_model=PuzzleResponse)
async def get_puzzle_by_date(
    date: date,
    session: SessionDep
) -> PuzzleResponse:
    """Get puzzle for specific date (practice mode, post-MVP)."""
```

### 2.5 Leaderboard API Endpoints

**File:** `backend/app/api/routes/leaderboard.py`

```python
router = APIRouter(prefix="/leaderboard", tags=["leaderboard"])

@router.get("/today", response_model=LeaderboardResponse)
async def get_todays_leaderboard(
    session: SessionDep,
    limit: int = 100
) -> LeaderboardResponse:
    """Get today's leaderboard rankings."""

@router.get("/{date}", response_model=LeaderboardResponse)
async def get_leaderboard_by_date(
    date: date,
    session: SessionDep,
    limit: int = 100
) -> LeaderboardResponse:
    """Get leaderboard for specific date."""
```

### 2.6 Puzzle Scheduler

**Goal:** Automatic daily puzzle generation

**File:** `backend/app/services/puzzle_scheduler.py`

```python
async def ensure_puzzle_exists_for_date(date: date, db: Session) -> Puzzle:
    """
    Get or create puzzle for given date.

    1. Check if puzzle exists for date
    2. If not, generate new puzzle
    3. Update quartile cooldowns
    4. Save to database
    """

async def generate_upcoming_puzzles(days_ahead: int = 7):
    """
    Pre-generate puzzles for upcoming days.
    Called by background task/cron.
    """
```

**Scheduling Options:**
1. **Lazy generation:** Generate when first player requests
2. **Pre-generation:** Cron job generates puzzles ahead of time
3. **Hybrid:** Lazy with pre-generation for reliability

**Recommended:** Hybrid approach with 7-day pre-generation

---

## Phase 3: Frontend Game UI

### 3.1 Remove shadcn/ui, Install daisyUI

**Goal:** Replace component library

**Tasks:**
1. Remove shadcn/ui dependencies from `package.json`
2. Remove `frontend/src/components/ui/` directory
3. Install daisyUI: `npm install daisyui`
4. Update `tailwind.config.js` with daisyUI plugin
5. Apply custom Quartiles theme (from Phase 0)

**Files to modify:**
- `frontend/package.json`
- `frontend/tailwind.config.js`
- `frontend/src/index.css`

### 3.2 Game Route

**Goal:** Main game page route

**File:** `frontend/src/routes/_layout/game.tsx`

```typescript
export const Route = createFileRoute('/_layout/game')({
  component: GamePage,
  beforeLoad: async () => {
    // Ensure player has ID (create if new)
  }
})

function GamePage() {
  return (
    <div className="container mx-auto p-4">
      <GameBoard />
    </div>
  )
}
```

### 3.3 Game State Management

**Goal:** React state for game logic with persistence and error handling

**File:** `frontend/src/hooks/useGame.ts`

```typescript
interface GameState {
  // Session info
  sessionId: string | null;
  playerId: string | null;
  displayName: string | null;

  // Puzzle data
  puzzle: Puzzle | null;
  selectedTiles: number[];
  foundWords: string[];
  currentScore: number;

  // Timer (client-side display only, server is authoritative)
  timerMs: number;
  isTimerRunning: boolean;

  // Game progress
  isSolved: bool;
  hintsUsed: number;
  phase: 'loading' | 'playing' | 'solved' | 'completed' | 'already_played';

  // Error handling
  error: string | null;
  isSubmitting: boolean;
}

// localStorage key for persistence
const STORAGE_KEY = 'quartiles_game_state';

export function useGame() {
  // Rehydrate from localStorage on mount
  const [state, dispatch] = useReducer(gameReducer, initialState, (initial) => {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        // Validate session is still for today's puzzle
        if (isSessionValid(parsed)) {
          return { ...initial, ...parsed };
        }
      } catch (e) {
        localStorage.removeItem(STORAGE_KEY);
      }
    }
    return initial;
  });

  // Persist to localStorage on state changes
  useEffect(() => {
    if (state.sessionId) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify({
        sessionId: state.sessionId,
        playerId: state.playerId,
        displayName: state.displayName,
        foundWords: state.foundWords,
        currentScore: state.currentScore,
        timerMs: state.timerMs,
        isSolved: state.isSolved,
        hintsUsed: state.hintsUsed,
        phase: state.phase,
      }));
    }
  }, [state]);

  // Actions
  const selectTile = (tileId: number) => { /* toggle selection */ };
  const submitWord = async () => {
    /* Call POST /game/sessions/{id}/word
       Handle success: update foundWords, currentScore
       Handle error: show toast, set error state */
  };
  const requestHint = async () => { /* get hint via API */ };
  const clearSelection = () => { /* clear selected tiles */ };
  const finalizeGame = async () => { /* Call POST /game/sessions/{id}/submit */ };

  // Timer effect (client-side display)
  useEffect(() => { /* increment timer while running */ }, [state.isTimerRunning]);

  return {
    state,
    selectTile,
    submitWord,
    requestHint,
    clearSelection,
    finalizeGame,
  };
}
```

### 3.3.1 Error Handling

**Goal:** User-friendly error feedback

```typescript
// Use daisyUI toast component for errors
import { toast } from 'sonner';  // Or daisyUI alert

function handleApiError(error: Error) {
  if (error.message === 'Network Error') {
    toast.error('Connection lost. Please check your internet.');
  } else if (error.message.includes('already played')) {
    toast.info('You already completed today\'s puzzle!');
  } else {
    toast.error('Something went wrong. Please try again.');
  }
}
```

### 3.4 Tile Grid Component

**Goal:** 4x5 grid of interactive tiles

**File:** `frontend/src/components/Game/TileGrid.tsx`

```typescript
interface TileGridProps {
  tiles: Tile[];
  selectedIds: number[];
  quartileFoundIds: number[];  // Tiles that formed quartile words
  onTileClick: (id: number) => void;
}

export function TileGrid({ tiles, selectedIds, quartileFoundIds, onTileClick }: TileGridProps) {
  return (
    <div className="grid grid-cols-5 gap-2">
      {tiles.map((tile, index) => (
        <TileButton
          key={tile.id}
          tile={tile}
          isSelected={selectedIds.includes(tile.id)}
          isQuartileFound={quartileFoundIds.includes(tile.id)}
          onClick={() => onTileClick(tile.id)}
          gridPosition={index}  // For keyboard navigation
        />
      ))}
    </div>
  );
}
```

### 3.5 Tile Button Component

**Goal:** Individual tile with animations

**File:** `frontend/src/components/Game/TileButton.tsx`

```typescript
interface TileButtonProps {
  tile: Tile;
  isSelected: boolean;
  isQuartileFound: boolean;
  onClick: () => void;
  gridPosition: number;
}

export function TileButton({ tile, isSelected, isQuartileFound, onClick, gridPosition }: TileButtonProps) {
  return (
    <button
      className={cn(
        "btn btn-lg aspect-square font-bold text-lg",
        "transition-all duration-200",
        "animate-float",  // Subtle ambient animation
        isSelected && "btn-primary ring-2 ring-primary",
        isQuartileFound && "bg-success/20",
        "hover:animate-wobble"
      )}
      onClick={onClick}
      data-grid-position={gridPosition}
    >
      {tile.letters}
    </button>
  );
}
```

**CSS Animations:** `frontend/src/styles/animations.css`

```css
@keyframes float {
  0%, 100% { transform: translateY(0px); }
  50% { transform: translateY(-2px); }
}

@keyframes wobble {
  0%, 100% { transform: rotate(0deg); }
  25% { transform: rotate(-2deg); }
  75% { transform: rotate(2deg); }
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-4px); }
  75% { transform: translateX(4px); }
}

.animate-float {
  animation: float 3s ease-in-out infinite;
}

.animate-wobble {
  animation: wobble 0.3s ease-in-out;
}

.animate-shake {
  animation: shake 0.3s ease-in-out;
}
```

### 3.6 Word Formation Zone

**Goal:** Display currently selected word

**File:** `frontend/src/components/Game/WordFormation.tsx`

```typescript
interface WordFormationProps {
  selectedTiles: Tile[];
  isValid: boolean;
  onSubmit: () => void;
  onClear: () => void;
}

export function WordFormation({ selectedTiles, isValid, onSubmit, onClear }: WordFormationProps) {
  const word = selectedTiles.map(t => t.letters).join('');

  return (
    <div className="flex items-center gap-4 p-4 bg-base-200 rounded-lg">
      <div className="text-2xl font-bold min-w-[200px]">
        {word || <span className="text-base-content/50">Select tiles...</span>}
      </div>
      <button
        className="btn btn-primary"
        onClick={onSubmit}
        disabled={selectedTiles.length === 0}
      >
        Submit
      </button>
      <button
        className="btn btn-ghost"
        onClick={onClear}
        disabled={selectedTiles.length === 0}
      >
        Clear
      </button>
    </div>
  );
}
```

### 3.7 Score and Timer Display

**File:** `frontend/src/components/Game/ScoreDisplay.tsx`

```typescript
interface ScoreDisplayProps {
  currentScore: number;
  solveThreshold: number;
  timerMs: number;
  isSolved: boolean;
  hintsUsed: number;
}

export function ScoreDisplay({ currentScore, solveThreshold, timerMs, isSolved, hintsUsed }: ScoreDisplayProps) {
  const formatTime = (ms: number) => {
    const seconds = Math.floor(ms / 1000);
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  return (
    <div className="stats shadow">
      <div className="stat">
        <div className="stat-title">Score</div>
        <div className="stat-value">{currentScore} / {solveThreshold}</div>
      </div>
      <div className="stat">
        <div className="stat-title">Time</div>
        <div className="stat-value">{formatTime(timerMs)}</div>
      </div>
      {hintsUsed > 0 && (
        <div className="stat">
          <div className="stat-title">Hints</div>
          <div className="stat-value">{hintsUsed}</div>
        </div>
      )}
    </div>
  );
}
```

### 3.8 Found Words List

**File:** `frontend/src/components/Game/FoundWordsList.tsx`

```typescript
interface FoundWordsListProps {
  words: string[];
  tiles: Tile[];
}

export function FoundWordsList({ words, tiles }: FoundWordsListProps) {
  // Group words by tile count
  const grouped = useMemo(() => {
    return words.reduce((acc, word) => {
      const tileCount = getTileCount(word, tiles);
      if (!acc[tileCount]) acc[tileCount] = [];
      acc[tileCount].push(word);
      return acc;
    }, {} as Record<number, string[]>);
  }, [words, tiles]);

  return (
    <div className="space-y-4">
      {[4, 3, 2, 1].map(count => (
        grouped[count]?.length > 0 && (
          <div key={count}>
            <h3 className="font-bold text-sm text-base-content/70">
              {count}-tile words ({grouped[count].length})
            </h3>
            <div className="flex flex-wrap gap-1">
              {grouped[count].map(word => (
                <span key={word} className="badge badge-outline">{word}</span>
              ))}
            </div>
          </div>
        )
      ))}
    </div>
  );
}
```

### 3.9 Keyboard Navigation

**Goal:** Arrow keys + vim-style navigation

**File:** `frontend/src/hooks/useKeyboardNavigation.ts`

```typescript
export function useKeyboardNavigation(
  tiles: Tile[],
  onSelect: (id: number) => void,
  onSubmit: () => void,
  onClear: () => void
) {
  const [focusIndex, setFocusIndex] = useState(0);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const COLS = 5;
      const ROWS = 4;

      switch (e.key) {
        // Arrow keys
        case 'ArrowUp':
        case 'k':  // vim
          setFocusIndex(i => Math.max(0, i - COLS));
          break;
        case 'ArrowDown':
        case 'j':  // vim
          setFocusIndex(i => Math.min(19, i + COLS));
          break;
        case 'ArrowLeft':
        case 'h':  // vim
          setFocusIndex(i => Math.max(0, i - 1));
          break;
        case 'ArrowRight':
        case 'l':  // vim
          setFocusIndex(i => Math.min(19, i + 1));
          break;
        case 'Enter':
        case ' ':
          if (e.shiftKey) {
            onSubmit();
          } else {
            onSelect(tiles[focusIndex].id);
          }
          break;
        case 'Escape':
          onClear();
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [tiles, focusIndex, onSelect, onSubmit, onClear]);

  return focusIndex;
}
```

### 3.10 Game Board (Main Component)

**File:** `frontend/src/components/Game/GameBoard.tsx`

```typescript
export function GameBoard() {
  const { state, selectTile, submitWord, requestHint, clearSelection } = useGame();
  const focusIndex = useKeyboardNavigation(
    state.puzzle?.tiles ?? [],
    selectTile,
    submitWord,
    clearSelection
  );

  if (!state.puzzle) {
    return <Loading />;
  }

  return (
    <div className="flex flex-col lg:flex-row gap-6">
      {/* Main game area */}
      <div className="flex-1 space-y-4">
        <ScoreDisplay
          currentScore={state.currentScore}
          solveThreshold={100}
          timerMs={state.timerMs}
          isSolved={state.isSolved}
          hintsUsed={state.hintsUsed}
        />

        <TileGrid
          tiles={state.puzzle.tiles}
          selectedIds={state.selectedTiles}
          quartileFoundIds={getQuartileFoundTileIds(state)}
          onTileClick={selectTile}
          focusIndex={focusIndex}
        />

        <WordFormation
          selectedTiles={getSelectedTiles(state)}
          isValid={isCurrentWordValid(state)}
          onSubmit={submitWord}
          onClear={clearSelection}
        />

        <button
          className="btn btn-secondary"
          onClick={requestHint}
          disabled={state.hintsUsed >= 5 || allQuartilesFound(state)}
        >
          Get Hint (+{getHintPenalty(state.hintsUsed + 1)}s)
        </button>
      </div>

      {/* Sidebar */}
      <div className="w-64">
        <FoundWordsList
          words={state.foundWords}
          tiles={state.puzzle.tiles}
        />
      </div>
    </div>
  );
}
```

### 3.11 Leaderboard Component

**File:** `frontend/src/components/Game/Leaderboard.tsx`

```typescript
interface LeaderboardProps {
  entries: LeaderboardEntry[];
  currentPlayerId?: string;
}

export function Leaderboard({ entries, currentPlayerId }: LeaderboardProps) {
  return (
    <div className="overflow-x-auto">
      <table className="table table-zebra">
        <thead>
          <tr>
            <th>Rank</th>
            <th>Player</th>
            <th>Time</th>
          </tr>
        </thead>
        <tbody>
          {entries.map((entry, index) => (
            <tr
              key={entry.id}
              className={entry.player_id === currentPlayerId ? 'bg-primary/10' : ''}
            >
              <td>{index + 1}</td>
              <td>{entry.display_name}</td>
              <td>{formatTime(entry.solve_time_ms)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

---

## Phase 4: Daily System Integration

### 4.1 First-Play-Wins Logic

**Goal:** Enforce single submission per player per puzzle

**Backend logic:**
```python
async def check_first_play(player_id: str, puzzle_id: uuid.UUID, db: Session) -> bool:
    """Check if player has already submitted for this puzzle."""
    existing = db.exec(
        select(GameSession)
        .where(GameSession.player_id == player_id)
        .where(GameSession.puzzle_id == puzzle_id)
        .where(GameSession.completed_at.is_not(None))
    ).first()
    return existing is None
```

**Frontend handling:**
- Store `player_id` in localStorage
- On game start, check if already played today
- Show previous result instead of starting new game

### 4.2 Automatic Puzzle Generation

**Cron Job / Background Task:**

```python
# Using APScheduler or similar
@scheduler.scheduled_job('cron', hour=0, minute=0)
async def generate_daily_puzzles():
    """Generate puzzles for next 7 days."""
    async with get_db_session() as db:
        for days_ahead in range(7):
            target_date = date.today() + timedelta(days=days_ahead)
            await ensure_puzzle_exists_for_date(target_date, db)
```

### 4.3 Timezone Handling

**Strategy:** Store all times in UTC, convert on client

**Backend:**
- Puzzle `date` field is calendar date (no time component)
- All timestamps stored in UTC

**Frontend:**
- Detect user's timezone
- Calculate "today" based on local midnight
- Request appropriate puzzle date

```typescript
function getTodaysPuzzleDate(): string {
  const now = new Date();
  // Format as YYYY-MM-DD in local timezone
  return now.toLocaleDateString('en-CA'); // ISO format
}
```

---

## Phase 5: Testing & Polish

### 5.1 Unit Test Suite

**Backend Tests:**

```bash
backend/app/game/tests/
├── test_types.py
├── test_dictionary.py
├── test_generator.py
├── test_solver.py
└── test_integration.py
```

**Key Test Cases:**
- Puzzle generation produces valid puzzles
- Solver finds all valid words
- Scoring is accurate
- Hint penalties calculate correctly
- First-play-wins enforcement works

### 5.2 E2E Test Suite

**File:** `frontend/e2e/game.spec.ts`

```typescript
test.describe('Quartiles Game', () => {
  test('complete game flow', async ({ page }) => {
    await page.goto('/game');

    // Verify puzzle loads
    await expect(page.locator('[data-testid="tile-grid"]')).toBeVisible();

    // Select tiles and submit word
    await page.click('[data-testid="tile-0"]');
    await page.click('[data-testid="tile-1"]');
    await page.click('[data-testid="submit-word"]');

    // Verify score updates
    await expect(page.locator('[data-testid="current-score"]')).not.toHaveText('0');
  });

  test('keyboard navigation works', async ({ page }) => {
    await page.goto('/game');

    // Use arrow keys
    await page.keyboard.press('ArrowRight');
    await page.keyboard.press('ArrowDown');
    await page.keyboard.press('Enter');  // Select tile

    // Verify tile selected
    await expect(page.locator('[data-testid="tile-6"]')).toHaveClass(/selected/);
  });

  test('first-play-wins prevents replay', async ({ page }) => {
    // Play once
    await page.goto('/game');
    // ... complete game

    // Try to play again
    await page.goto('/game');
    await expect(page.locator('[data-testid="already-played-message"]')).toBeVisible();
  });
});
```

### 5.3 Performance Optimization

**Targets:**
- Puzzle generation: <50ms
- Word validation: <10ms
- Page load: <2s
- Time to interactive: <3s

**Optimizations:**
- Pre-generate puzzles (avoid generation at request time)
- Binary dictionary format for fast loading
- Lazy load leaderboard
- Code splitting for game components

### 5.4 Accessibility Audit

**Checklist:**
- [ ] Color contrast meets WCAG AA
- [ ] All interactive elements have focus states
- [ ] Keyboard navigation complete
- [ ] Screen reader announcements for score changes
- [ ] Reduced motion option (post-MVP)

---

## File Summary

### New Files to Create

**Backend:**
- `backend/app/game/types.py`
- `backend/app/game/dictionary.py`
- `backend/app/game/generator.py`
- `backend/app/game/solver.py`
- `backend/app/game/tests/` (directory)
- `backend/app/api/routes/game.py`
- `backend/app/api/routes/puzzle.py`
- `backend/app/api/routes/leaderboard.py`
- `backend/app/services/name_generator.py`
- `backend/app/services/puzzle_scheduler.py`
- `backend/scripts/build_dictionary.py`
- `backend/data/dictionary.bin`

**Frontend:**
- `frontend/src/routes/_layout/game.tsx`
- `frontend/src/components/Game/GameBoard.tsx`
- `frontend/src/components/Game/TileGrid.tsx`
- `frontend/src/components/Game/TileButton.tsx`
- `frontend/src/components/Game/WordFormation.tsx`
- `frontend/src/components/Game/ScoreDisplay.tsx`
- `frontend/src/components/Game/FoundWordsList.tsx`
- `frontend/src/components/Game/Leaderboard.tsx`
- `frontend/src/hooks/useGame.ts`
- `frontend/src/hooks/useKeyboardNavigation.ts`
- `frontend/src/styles/animations.css`
- `frontend/e2e/game.spec.ts`

**Files to Modify:**
- `backend/app/models.py` (add game tables)
- `backend/app/api/main.py` (register new routes)
- `frontend/package.json` (remove shadcn, add daisyui)
- `frontend/tailwind.config.js` (add daisyui, custom theme)
- `frontend/src/index.css` (import animations)

---

## Dependencies

### Backend
- No new Python packages required (FastAPI, SQLModel already present)
- NLTK for WordNet (one-time dictionary build)

### Frontend
- Remove: All `@radix-ui/*`, `cmdk`, `lucide-react`, etc. (shadcn deps)
- Add: `daisyui@^4`

---

## Risk Mitigation

### Risk 1: Puzzle generation fails to find valid puzzles
**Mitigation:**
- Pre-generate puzzles well in advance
- Have fallback pool of manually curated puzzles
- Log generation failures for analysis

### Risk 2: Dictionary too large for client
**Mitigation:**
- Use Bloom filter for quick rejection (~5KB)
- Only send words relevant to current puzzle
- Lazy load full dictionary if needed

### Risk 3: daisyUI migration breaks existing pages
**Mitigation:**
- Most existing pages are placeholders
- Create migration checklist for each component
- Test thoroughly before merging

### Risk 4: Leaderboard gaming/cheating
**Mitigation:**
- Server validates all submissions
- Basic timing checks (too fast = suspicious)
- For casual game, accept some risk
- Log suspicious activity for manual review

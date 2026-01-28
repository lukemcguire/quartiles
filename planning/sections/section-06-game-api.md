# Section 06: Game API Endpoints

## Background

The Quartiles game requires a REST API that enables clients to play the daily word puzzle while maintaining server-authoritative game state. This is critical for several reasons:

1. **Security**: The client should never know the valid word list - this would allow trivial cheating. All word validation must happen server-side.

2. **Leaderboard Integrity**: Solve times and scores must be calculated server-side. The client displays a timer for UX, but the authoritative time is `completed_at - start_time + hint_penalties`.

3. **First-Play-Wins**: Each player gets exactly one competitive attempt per daily puzzle. The server enforces this by tracking completed sessions.

4. **Stateless Client**: The client can lose state (refresh, close tab) and resume. The server holds the source of truth for found words, hints used, and session state.

The API bridges the pure Python game logic (Section 04) with HTTP clients via FastAPI, converting between Pydantic schemas and game domain dataclasses.

---

## Requirements

When this section is complete:

1. All game API endpoints are functional and return correct responses
2. Word validation happens server-side without exposing the valid word list
3. Solve time is calculated server-side (including hint penalties)
4. Player names are auto-generated using AdjectiveNoun format
5. First-play-wins is enforced at the API level
6. All endpoints have proper request/response schemas with validation
7. The API integrates with the database models from Section 05
8. Pre-commit hooks pass for all new code

---

## Dependencies

### Requires (must be completed first)
- **Section 04: Pure Python Game Logic** - Provides domain types, dictionary, solver functions
- **Section 05: Database Models & Migrations** - Provides SQLModel tables for persistence

### Blocks (cannot start until this completes)
- **Section 07: Frontend Game UI** - Needs API endpoints to call
- **Section 08: Daily Puzzle System** - Needs game/puzzle endpoints for scheduling integration

---

## Implementation Details

### 2.2 Name Generator

Create a service to generate memorable player display names in `AdjectiveNoun` format.

**File:** `backend/app/services/name_generator.py`

```python
"""Player name generation service."""

import random
from typing import Optional

ADJECTIVES = [
    "Chubby", "Sleepy", "Grumpy", "Happy", "Sneaky", "Fluffy",
    "Bouncy", "Wobbly", "Jazzy", "Cozy", "Mighty", "Tiny",
    "Rotund", "Peppy", "Mellow", "Zesty", "Quirky", "Dapper",
    "Plucky", "Snappy", "Breezy", "Crispy", "Dizzy", "Frosty",
    "Giddy", "Hasty", "Icy", "Jolly", "Kooky", "Lively",
    "Merry", "Nifty", "Perky", "Rusty", "Sassy", "Toasty",
    "Wacky", "Zippy", "Chunky", "Funky", "Groovy", "Lumpy",
    "Murky", "Nutty", "Pudgy", "Quirky", "Spunky", "Swanky",
    "Tacky", "Yucky", "Zany", "Bumpy", "Dusty", "Foggy",
    "Gloomy", "Hazy", "Icky", "Jumpy", "Lucky", "Messy",
    "Noisy", "Picky", "Rocky", "Salty", "Tricky", "Windy",
    "Brainy", "Clumsy", "Dreamy", "Feisty", "Grouchy", "Hangry",
    "Itchy", "Jittery", "Lanky", "Moody", "Nerdy", "Peppy",
    "Rowdy", "Snooty", "Testy", "Woozy", "Yappy", "Zonked",
    "Antsy", "Bushy", "Cranky", "Dopey", "Edgy", "Fizzy",
    "Gassy", "Huffy", "Inky", "Jerky", "Kinky", "Loopy"
]

NOUNS = [
    "Penguin", "Unicorn", "Mango", "Pancake", "Walrus", "Hedgehog",
    "Narwhal", "Cupcake", "Platypus", "Turnip", "Koala", "Avocado",
    "Badger", "Biscuit", "Cactus", "Dolphin", "Falcon", "Gopher",
    "Hamster", "Iguana", "Jackal", "Kitten", "Lemur", "Moose",
    "Newt", "Otter", "Panda", "Quail", "Rabbit", "Salmon",
    "Turtle", "Vulture", "Wombat", "Yak", "Zebra", "Alpaca",
    "Beaver", "Clam", "Donkey", "Emu", "Ferret", "Goose",
    "Hippo", "Ibis", "Jellyfish", "Kangaroo", "Llama", "Meerkat",
    "Numbat", "Octopus", "Parrot", "Quokka", "Raccoon", "Seal",
    "Toucan", "Urchin", "Viper", "Walnut", "Yeti", "Zucchini",
    "Acorn", "Bagel", "Carrot", "Donut", "Eclair", "Falafel",
    "Gumball", "Hotdog", "Icecream", "Jelly", "Kiwi", "Lemon",
    "Muffin", "Nugget", "Olive", "Pickle", "Quinoa", "Raisin",
    "Sushi", "Taco", "Udon", "Waffle", "Yogurt", "Ziti",
    "Asteroid", "Blizzard", "Comet", "Doodle", "Eclipse", "Firefly",
    "Galaxy", "Hurricane", "Icicle", "Jumble", "Kazoo", "Lollipop"
]


def generate_player_name() -> str:
    """
    Generate a unique AdjectiveNoun player display name.

    Returns:
        A name like "ChubbyPenguin" or "SleepyMango"
    """
    adjective = random.choice(ADJECTIVES)
    noun = random.choice(NOUNS)
    return f"{adjective}{noun}"


def generate_unique_player_name(existing_names: set[str], max_attempts: int = 100) -> Optional[str]:
    """
    Generate a player name that doesn't conflict with existing names.

    Args:
        existing_names: Set of names already in use
        max_attempts: Maximum generation attempts before returning None

    Returns:
        A unique name, or None if max_attempts exceeded
    """
    for _ in range(max_attempts):
        name = generate_player_name()
        if name not in existing_names:
            return name
    return None
```

### 2.3 Game API Endpoints

Create the main game routes for starting games, validating words, submitting results, and requesting hints.

**File:** `backend/app/api/routes/game.py`

```python
"""Game session management API endpoints."""

import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from sqlmodel import select

from app.api.deps import SessionDep
from app.game.solver import find_word_in_puzzle, score_word, calculate_hint_penalty
from app.game.types import Tile as GameTile
from app.models import GameSession, Player, Puzzle, LeaderboardEntry
from app.services.name_generator import generate_player_name
from app.services.puzzle_scheduler import ensure_puzzle_exists_for_date


router = APIRouter(prefix="/game", tags=["game"])

SOLVE_THRESHOLD = 100  # Points needed to "solve" the puzzle


# --- Request/Response Schemas ---

class TileSchema(BaseModel):
    """A single tile in the puzzle grid."""
    id: int
    letters: str


class PreviousResultSchema(BaseModel):
    """Result from a previous game session."""
    final_score: int
    solve_time_ms: Optional[int]
    words_found: list[str]
    leaderboard_rank: Optional[int]


class GameStartRequest(BaseModel):
    """Request to start a new game session."""
    device_fingerprint: str
    player_id: Optional[str] = None  # UUID string for returning players


class GameStartResponse(BaseModel):
    """Response when starting a new game."""
    session_id: str  # UUID as string
    player_id: str  # UUID as string (stable identifier)
    display_name: str  # AdjectiveNoun format for display
    tiles: list[TileSchema]
    already_played: bool
    previous_result: Optional[PreviousResultSchema] = None
    # NOTE: valid_words intentionally NOT included (security)


class WordValidationRequest(BaseModel):
    """Request to validate a submitted word."""
    word: str


class WordValidationResponse(BaseModel):
    """Response after validating a word."""
    is_valid: bool
    points: Optional[int] = None  # Points earned if valid
    reason: Optional[str] = None  # Error reason if invalid
    is_quartile: bool = False  # True if 4-tile word
    current_score: int  # Updated total score
    is_solved: bool  # True if reached solve threshold


class GameSubmitResponse(BaseModel):
    """Response after submitting/finalizing a game."""
    success: bool
    final_score: int  # Server-calculated
    solve_time_ms: Optional[int] = None  # Server-calculated, None if not solved
    leaderboard_rank: Optional[int] = None  # None if not solved or not ranked
    message: str


class HintResponse(BaseModel):
    """Response after requesting a hint."""
    hint_number: int  # Which hint this is (1-5)
    definition: Optional[str] = None  # WordNet definition of unfound quartile
    time_penalty_ms: int  # Penalty added to solve time
    quartiles_remaining: int  # How many quartile words still unfound


# --- Helper Functions ---

def _get_or_create_player(
    db: SessionDep,
    device_fingerprint: str,
    player_id: Optional[str] = None
) -> Player:
    """Get existing player or create new one."""
    # Try to find by player_id first
    if player_id:
        try:
            player_uuid = uuid.UUID(player_id)
            player = db.exec(
                select(Player).where(Player.id == player_uuid)
            ).first()
            if player:
                return player
        except ValueError:
            pass  # Invalid UUID, fall through

    # Try to find by device fingerprint
    player = db.exec(
        select(Player).where(Player.device_fingerprint == device_fingerprint)
    ).first()
    if player:
        return player

    # Create new player
    player = Player(
        display_name=generate_player_name(),
        device_fingerprint=device_fingerprint,
    )
    db.add(player)
    db.commit()
    db.refresh(player)
    return player


def _get_existing_session(
    db: SessionDep,
    player_id: uuid.UUID,
    puzzle_id: uuid.UUID
) -> Optional[GameSession]:
    """Check if player has already played this puzzle."""
    return db.exec(
        select(GameSession)
        .where(GameSession.player_id == player_id)
        .where(GameSession.puzzle_id == puzzle_id)
        .where(GameSession.completed_at.is_not(None))
    ).first()


def _parse_tiles_json(tiles_json: str) -> list[TileSchema]:
    """Parse tiles from JSON storage format."""
    import json
    tiles_data = json.loads(tiles_json)
    return [TileSchema(id=t["id"], letters=t["letters"]) for t in tiles_data]


def _parse_words_json(words_json: str) -> list[str]:
    """Parse words list from JSON storage format."""
    import json
    return json.loads(words_json)


def _save_words_json(words: list[str]) -> str:
    """Serialize words list to JSON storage format."""
    import json
    return json.dumps(words)


def _calculate_leaderboard_rank(
    db: SessionDep,
    puzzle_id: uuid.UUID,
    solve_time_ms: int
) -> int:
    """Calculate rank for a solve time on today's leaderboard."""
    faster_count = db.exec(
        select(LeaderboardEntry)
        .where(LeaderboardEntry.puzzle_id == puzzle_id)
        .where(LeaderboardEntry.solve_time_ms < solve_time_ms)
    ).all()
    return len(faster_count) + 1


# --- Endpoints ---

@router.post("/start", response_model=GameStartResponse)
async def start_game(
    request: GameStartRequest,
    db: SessionDep
) -> GameStartResponse:
    """
    Start a new game session.

    - Gets today's puzzle (creates if doesn't exist)
    - Gets or creates player based on device_fingerprint/player_id
    - Checks if player already completed today's puzzle
    - Creates game session in database with server-recorded start_time
    - Returns puzzle tiles only (NOT valid words - security)
    """
    from datetime import date as date_type

    # Get or create today's puzzle
    today = date_type.today()
    puzzle = await ensure_puzzle_exists_for_date(today, db)

    # Get or create player
    player = _get_or_create_player(db, request.device_fingerprint, request.player_id)

    # Check if already played
    existing_session = _get_existing_session(db, player.id, puzzle.id)
    if existing_session:
        # Return previous result
        previous_words = _parse_words_json(existing_session.words_found_json)

        # Get leaderboard rank if solved
        rank = None
        if existing_session.solve_time_ms:
            entry = db.exec(
                select(LeaderboardEntry)
                .where(LeaderboardEntry.puzzle_id == puzzle.id)
                .where(LeaderboardEntry.player_id == player.id)
            ).first()
            if entry:
                rank = entry.rank

        return GameStartResponse(
            session_id=str(existing_session.id),
            player_id=str(player.id),
            display_name=player.display_name,
            tiles=_parse_tiles_json(puzzle.tiles_json),
            already_played=True,
            previous_result=PreviousResultSchema(
                final_score=existing_session.final_score,
                solve_time_ms=existing_session.solve_time_ms,
                words_found=previous_words,
                leaderboard_rank=rank,
            ),
        )

    # Create new session
    session = GameSession(
        puzzle_id=puzzle.id,
        player_id=player.id,
        start_time=datetime.now(timezone.utc),
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    return GameStartResponse(
        session_id=str(session.id),
        player_id=str(player.id),
        display_name=player.display_name,
        tiles=_parse_tiles_json(puzzle.tiles_json),
        already_played=False,
    )


@router.post("/sessions/{session_id}/word", response_model=WordValidationResponse)
async def validate_word(
    session_id: uuid.UUID,
    request: WordValidationRequest,
    db: SessionDep
) -> WordValidationResponse:
    """
    Validate a submitted word.

    Server-authoritative validation:
    - Checks if word exists in puzzle's valid word set
    - Checks if word was already found
    - Returns points if valid, error reason if not
    - Records valid word in session
    - Checks if solve threshold reached

    Does NOT expose the valid word list to the client.
    """
    # Get session
    session = db.get(GameSession, session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Game session not found"
        )

    # Check if session already completed
    if session.completed_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Game session already completed"
        )

    # Get puzzle
    puzzle = db.get(Puzzle, session.puzzle_id)
    if not puzzle:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Puzzle not found"
        )

    # Normalize word
    word = request.word.upper().strip()

    # Parse current state
    found_words = set(_parse_words_json(session.words_found_json))
    valid_words = set(_parse_words_json(puzzle.valid_words_json))
    quartile_words = set(_parse_words_json(puzzle.quartile_words_json))

    # Check if already found
    if word in found_words:
        return WordValidationResponse(
            is_valid=False,
            reason="Word already found",
            current_score=session.final_score,
            is_solved=session.final_score >= SOLVE_THRESHOLD,
        )

    # Check if valid
    if word not in valid_words:
        return WordValidationResponse(
            is_valid=False,
            reason="Not a valid word for this puzzle",
            current_score=session.final_score,
            is_solved=session.final_score >= SOLVE_THRESHOLD,
        )

    # Word is valid - calculate points
    # Parse tiles to determine tile count for scoring
    tiles_data = _parse_tiles_json(puzzle.tiles_json)
    tile_count = find_word_in_puzzle(word, [GameTile(t.id, t.letters) for t in tiles_data])
    points = score_word(tile_count)
    is_quartile = word in quartile_words

    # Update session
    found_words.add(word)
    new_score = session.final_score + points
    session.words_found_json = _save_words_json(list(found_words))
    session.final_score = new_score
    db.add(session)
    db.commit()

    return WordValidationResponse(
        is_valid=True,
        points=points,
        is_quartile=is_quartile,
        current_score=new_score,
        is_solved=new_score >= SOLVE_THRESHOLD,
    )


@router.post("/sessions/{session_id}/submit", response_model=GameSubmitResponse)
async def submit_game(
    session_id: uuid.UUID,
    db: SessionDep
) -> GameSubmitResponse:
    """
    Finalize and submit game for leaderboard.

    Server-authoritative scoring:
    - Calculates final solve time: now() - start_time + hint_penalties
    - Updates leaderboard if solved (score >= 100)
    - Enforces first-play-wins (cannot resubmit)
    - Client does NOT submit score or time
    """
    # Get session
    session = db.get(GameSession, session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Game session not found"
        )

    # Check if already completed
    if session.completed_at:
        return GameSubmitResponse(
            success=False,
            final_score=session.final_score,
            solve_time_ms=session.solve_time_ms,
            message="Game already submitted",
        )

    # Calculate final time
    now = datetime.now(timezone.utc)
    elapsed_ms = int((now - session.start_time).total_seconds() * 1000)
    total_time_ms = elapsed_ms + session.hint_penalty_ms

    # Mark session complete
    session.completed_at = now

    # Check if solved (reached threshold)
    is_solved = session.final_score >= SOLVE_THRESHOLD
    if is_solved:
        session.solve_time_ms = total_time_ms

        # Add to leaderboard
        rank = _calculate_leaderboard_rank(db, session.puzzle_id, total_time_ms)
        entry = LeaderboardEntry(
            puzzle_id=session.puzzle_id,
            player_id=session.player_id,
            solve_time_ms=total_time_ms,
            rank=rank,
        )
        db.add(entry)

    db.add(session)
    db.commit()

    return GameSubmitResponse(
        success=True,
        final_score=session.final_score,
        solve_time_ms=session.solve_time_ms,
        leaderboard_rank=rank if is_solved else None,
        message="Congratulations! You solved it!" if is_solved else "Game completed",
    )


@router.post("/sessions/{session_id}/hint", response_model=HintResponse)
async def get_hint(
    session_id: uuid.UUID,
    db: SessionDep
) -> HintResponse:
    """
    Request a hint (definition of unfound quartile word).

    - Returns WordNet definition of one unfound quartile word
    - Increments hint count in session
    - Adds time penalty (30s, 60s, 120s, 240s, 480s)
    - Maximum 5 hints per game
    """
    from app.game.dictionary import get_dictionary

    # Get session
    session = db.get(GameSession, session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Game session not found"
        )

    # Check if session already completed
    if session.completed_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Game session already completed"
        )

    # Check hint limit
    if session.hints_used >= 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum hints (5) already used"
        )

    # Get puzzle
    puzzle = db.get(Puzzle, session.puzzle_id)
    if not puzzle:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Puzzle not found"
        )

    # Find unfound quartile words
    found_words = set(_parse_words_json(session.words_found_json))
    quartile_words = set(_parse_words_json(puzzle.quartile_words_json))
    unfound_quartiles = quartile_words - found_words

    if not unfound_quartiles:
        return HintResponse(
            hint_number=session.hints_used,
            definition=None,
            time_penalty_ms=0,
            quartiles_remaining=0,
        )

    # Get hint for one unfound quartile
    hint_word = sorted(unfound_quartiles)[0]  # Deterministic order
    dictionary = get_dictionary()
    definition = dictionary.get_definition(hint_word)

    # Calculate and apply penalty
    new_hint_count = session.hints_used + 1
    penalty_ms = calculate_hint_penalty(new_hint_count)

    # Update session
    session.hints_used = new_hint_count
    session.hint_penalty_ms += penalty_ms
    db.add(session)
    db.commit()

    return HintResponse(
        hint_number=new_hint_count,
        definition=definition or f"No definition available for this {len(hint_word)}-letter word",
        time_penalty_ms=penalty_ms,
        quartiles_remaining=len(unfound_quartiles) - 1,
    )
```

### 2.4 Puzzle API Endpoints

Create endpoints for fetching puzzles by date.

**File:** `backend/app/api/routes/puzzle.py`

```python
"""Puzzle retrieval API endpoints."""

from datetime import date
from typing import Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from sqlmodel import select

from app.api.deps import SessionDep
from app.models import Puzzle
from app.services.puzzle_scheduler import ensure_puzzle_exists_for_date


router = APIRouter(prefix="/puzzle", tags=["puzzle"])


# --- Schemas ---

class TileSchema(BaseModel):
    """A single tile in the puzzle grid."""
    id: int
    letters: str


class PuzzleResponse(BaseModel):
    """Puzzle data returned to client."""
    id: str  # UUID as string
    date: date
    tiles: list[TileSchema]
    total_available_points: int
    # NOTE: valid_words and quartile_words NOT included (security)


# --- Helper Functions ---

def _parse_tiles_json(tiles_json: str) -> list[TileSchema]:
    """Parse tiles from JSON storage format."""
    import json
    tiles_data = json.loads(tiles_json)
    return [TileSchema(id=t["id"], letters=t["letters"]) for t in tiles_data]


def _puzzle_to_response(puzzle: Puzzle) -> PuzzleResponse:
    """Convert database puzzle to API response."""
    return PuzzleResponse(
        id=str(puzzle.id),
        date=puzzle.date,
        tiles=_parse_tiles_json(puzzle.tiles_json),
        total_available_points=puzzle.total_available_points,
    )


# --- Endpoints ---

@router.get("/today", response_model=PuzzleResponse)
async def get_todays_puzzle(db: SessionDep) -> PuzzleResponse:
    """
    Get today's puzzle.

    Creates the puzzle if it doesn't exist yet (lazy generation).
    Returns tiles only - valid words are never exposed to client.
    """
    today = date.today()
    puzzle = await ensure_puzzle_exists_for_date(today, db)
    return _puzzle_to_response(puzzle)


@router.get("/{puzzle_date}", response_model=PuzzleResponse)
async def get_puzzle_by_date(
    puzzle_date: date,
    db: SessionDep
) -> PuzzleResponse:
    """
    Get puzzle for a specific date.

    For practice mode (post-MVP) or viewing past puzzles.
    Only returns puzzles that already exist (no generation).
    """
    puzzle = db.exec(
        select(Puzzle).where(Puzzle.date == puzzle_date)
    ).first()

    if not puzzle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No puzzle found for date {puzzle_date}"
        )

    return _puzzle_to_response(puzzle)
```

### 2.5 Leaderboard API Endpoints

Create endpoints for fetching leaderboard rankings.

**File:** `backend/app/api/routes/leaderboard.py`

```python
"""Leaderboard API endpoints."""

from datetime import date
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel
from sqlmodel import select

from app.api.deps import SessionDep
from app.models import LeaderboardEntry, Player, Puzzle


router = APIRouter(prefix="/leaderboard", tags=["leaderboard"])


# --- Schemas ---

class LeaderboardEntrySchema(BaseModel):
    """A single leaderboard entry."""
    rank: int
    player_id: str  # UUID as string
    display_name: str  # AdjectiveNoun format
    solve_time_ms: int


class LeaderboardResponse(BaseModel):
    """Leaderboard data for a puzzle."""
    puzzle_id: str
    puzzle_date: date
    entries: list[LeaderboardEntrySchema]
    total_entries: int
    player_rank: Optional[int] = None  # Current player's rank, if on board


# --- Endpoints ---

@router.get("/today", response_model=LeaderboardResponse)
async def get_todays_leaderboard(
    db: SessionDep,
    limit: int = Query(default=100, ge=1, le=500),
    player_id: Optional[str] = None,
) -> LeaderboardResponse:
    """
    Get today's leaderboard rankings.

    - Returns top `limit` entries sorted by solve time
    - Optionally includes current player's rank if not in top results
    """
    today = date.today()

    # Get today's puzzle
    puzzle = db.exec(
        select(Puzzle).where(Puzzle.date == today)
    ).first()

    if not puzzle:
        return LeaderboardResponse(
            puzzle_id="",
            puzzle_date=today,
            entries=[],
            total_entries=0,
        )

    # Get top entries
    entries = db.exec(
        select(LeaderboardEntry)
        .where(LeaderboardEntry.puzzle_id == puzzle.id)
        .order_by(LeaderboardEntry.solve_time_ms)
        .limit(limit)
    ).all()

    # Get player info for each entry
    entry_schemas = []
    for i, entry in enumerate(entries):
        player = db.get(Player, entry.player_id)
        entry_schemas.append(LeaderboardEntrySchema(
            rank=i + 1,
            player_id=str(entry.player_id),
            display_name=player.display_name if player else "Unknown",
            solve_time_ms=entry.solve_time_ms,
        ))

    # Get total count
    total_count = len(db.exec(
        select(LeaderboardEntry)
        .where(LeaderboardEntry.puzzle_id == puzzle.id)
    ).all())

    # Find current player's rank if specified
    player_rank = None
    if player_id:
        try:
            from uuid import UUID
            player_uuid = UUID(player_id)
            player_entry = db.exec(
                select(LeaderboardEntry)
                .where(LeaderboardEntry.puzzle_id == puzzle.id)
                .where(LeaderboardEntry.player_id == player_uuid)
            ).first()
            if player_entry:
                # Count entries with faster time
                faster_count = len(db.exec(
                    select(LeaderboardEntry)
                    .where(LeaderboardEntry.puzzle_id == puzzle.id)
                    .where(LeaderboardEntry.solve_time_ms < player_entry.solve_time_ms)
                ).all())
                player_rank = faster_count + 1
        except ValueError:
            pass  # Invalid UUID

    return LeaderboardResponse(
        puzzle_id=str(puzzle.id),
        puzzle_date=today,
        entries=entry_schemas,
        total_entries=total_count,
        player_rank=player_rank,
    )


@router.get("/{leaderboard_date}", response_model=LeaderboardResponse)
async def get_leaderboard_by_date(
    leaderboard_date: date,
    db: SessionDep,
    limit: int = Query(default=100, ge=1, le=500),
    player_id: Optional[str] = None,
) -> LeaderboardResponse:
    """
    Get leaderboard for a specific date.

    For viewing historical rankings.
    """
    # Get puzzle for date
    puzzle = db.exec(
        select(Puzzle).where(Puzzle.date == leaderboard_date)
    ).first()

    if not puzzle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No puzzle found for date {leaderboard_date}"
        )

    # Get entries (same logic as today)
    entries = db.exec(
        select(LeaderboardEntry)
        .where(LeaderboardEntry.puzzle_id == puzzle.id)
        .order_by(LeaderboardEntry.solve_time_ms)
        .limit(limit)
    ).all()

    entry_schemas = []
    for i, entry in enumerate(entries):
        player = db.get(Player, entry.player_id)
        entry_schemas.append(LeaderboardEntrySchema(
            rank=i + 1,
            player_id=str(entry.player_id),
            display_name=player.display_name if player else "Unknown",
            solve_time_ms=entry.solve_time_ms,
        ))

    total_count = len(db.exec(
        select(LeaderboardEntry)
        .where(LeaderboardEntry.puzzle_id == puzzle.id)
    ).all())

    # Find player rank if specified
    player_rank = None
    if player_id:
        try:
            from uuid import UUID
            player_uuid = UUID(player_id)
            player_entry = db.exec(
                select(LeaderboardEntry)
                .where(LeaderboardEntry.puzzle_id == puzzle.id)
                .where(LeaderboardEntry.player_id == player_uuid)
            ).first()
            if player_entry:
                faster_count = len(db.exec(
                    select(LeaderboardEntry)
                    .where(LeaderboardEntry.puzzle_id == puzzle.id)
                    .where(LeaderboardEntry.solve_time_ms < player_entry.solve_time_ms)
                ).all())
                player_rank = faster_count + 1
        except ValueError:
            pass

    return LeaderboardResponse(
        puzzle_id=str(puzzle.id),
        puzzle_date=leaderboard_date,
        entries=entry_schemas,
        total_entries=total_count,
        player_rank=player_rank,
    )
```

### 2.6 Puzzle Scheduler Service

Create the service for lazy puzzle generation.

**File:** `backend/app/services/puzzle_scheduler.py`

```python
"""Puzzle scheduling and generation service."""

import json
from datetime import date, timedelta
from typing import Set

from sqlmodel import Session, select

from app.game.generator import generate_puzzle
from app.game.dictionary import get_dictionary
from app.models import Puzzle, QuartileCooldown


COOLDOWN_DAYS = 30  # Days before a quartile word can be reused


async def get_cooled_down_quartiles(db: Session) -> Set[str]:
    """Get set of quartile words currently in cooldown."""
    cutoff_date = date.today() - timedelta(days=COOLDOWN_DAYS)
    cooldowns = db.exec(
        select(QuartileCooldown)
        .where(QuartileCooldown.last_used_date > cutoff_date)
    ).all()
    return {c.word for c in cooldowns}


async def update_quartile_cooldowns(db: Session, quartile_words: list[str]) -> None:
    """Update cooldown records for used quartile words."""
    today = date.today()
    for word in quartile_words:
        existing = db.exec(
            select(QuartileCooldown).where(QuartileCooldown.word == word)
        ).first()
        if existing:
            existing.last_used_date = today
            db.add(existing)
        else:
            cooldown = QuartileCooldown(word=word, last_used_date=today)
            db.add(cooldown)
    db.commit()


async def ensure_puzzle_exists_for_date(target_date: date, db: Session) -> Puzzle:
    """
    Get or create puzzle for given date.

    Uses lazy generation - creates puzzle on first request if not exists.

    Args:
        target_date: The date to get/create puzzle for
        db: Database session

    Returns:
        The puzzle for the given date
    """
    # Check if puzzle exists
    existing = db.exec(
        select(Puzzle).where(Puzzle.date == target_date)
    ).first()
    if existing:
        return existing

    # Generate new puzzle
    dictionary = get_dictionary()
    excluded_quartiles = await get_cooled_down_quartiles(db)

    game_puzzle = generate_puzzle(dictionary, excluded_quartiles)
    if game_puzzle is None:
        raise RuntimeError(f"Failed to generate puzzle for {target_date}")

    # Convert to database format
    tiles_json = json.dumps([
        {"id": t.id, "letters": t.letters}
        for t in game_puzzle.tiles
    ])
    quartile_words_json = json.dumps(list(game_puzzle.quartile_words))
    valid_words_json = json.dumps(list(game_puzzle.valid_words))

    puzzle = Puzzle(
        date=target_date,
        tiles_json=tiles_json,
        quartile_words_json=quartile_words_json,
        valid_words_json=valid_words_json,
        total_available_points=game_puzzle.total_points,
    )
    db.add(puzzle)
    db.commit()
    db.refresh(puzzle)

    # Update cooldowns for used quartile words
    await update_quartile_cooldowns(db, list(game_puzzle.quartile_words))

    return puzzle


async def generate_upcoming_puzzles(days_ahead: int = 7) -> None:
    """
    Pre-generate puzzles for upcoming days.

    Called by background task/cron job for reliability.

    Args:
        days_ahead: Number of days to generate puzzles for
    """
    from app.core.db import get_session

    async with get_session() as db:
        for offset in range(days_ahead):
            target_date = date.today() + timedelta(days=offset)
            try:
                await ensure_puzzle_exists_for_date(target_date, db)
            except RuntimeError as e:
                # Log but continue with other dates
                print(f"Warning: {e}")
```

### Register Routes

Update the main API router to include new game routes.

**File:** `backend/app/api/main.py` (modify existing)

Add these imports and route registrations:

```python
from app.api.routes import game, puzzle, leaderboard

# In the router setup section:
api_router.include_router(game.router)
api_router.include_router(puzzle.router)
api_router.include_router(leaderboard.router)
```

---

## Request/Response Schema Reference

### Game Endpoints

| Endpoint | Method | Request | Response |
|----------|--------|---------|----------|
| `/game/start` | POST | `GameStartRequest` | `GameStartResponse` |
| `/game/sessions/{id}/word` | POST | `WordValidationRequest` | `WordValidationResponse` |
| `/game/sessions/{id}/submit` | POST | (none) | `GameSubmitResponse` |
| `/game/sessions/{id}/hint` | POST | (none) | `HintResponse` |

### Puzzle Endpoints

| Endpoint | Method | Request | Response |
|----------|--------|---------|----------|
| `/puzzle/today` | GET | (none) | `PuzzleResponse` |
| `/puzzle/{date}` | GET | (none) | `PuzzleResponse` |

### Leaderboard Endpoints

| Endpoint | Method | Query Params | Response |
|----------|--------|--------------|----------|
| `/leaderboard/today` | GET | `limit`, `player_id` | `LeaderboardResponse` |
| `/leaderboard/{date}` | GET | `limit`, `player_id` | `LeaderboardResponse` |

---

## Acceptance Criteria

- [ ] Name generator creates valid `AdjectiveNoun` names
- [ ] Name generator has 100+ adjectives and 100+ nouns
- [ ] `/game/start` creates new session with server timestamp
- [ ] `/game/start` returns `already_played=true` for repeat players
- [ ] `/game/start` does NOT return valid word list
- [ ] `/game/sessions/{id}/word` validates words server-side
- [ ] `/game/sessions/{id}/word` rejects duplicate word submissions
- [ ] `/game/sessions/{id}/word` correctly identifies quartile words
- [ ] `/game/sessions/{id}/word` updates score atomically
- [ ] `/game/sessions/{id}/submit` calculates solve time server-side
- [ ] `/game/sessions/{id}/submit` includes hint penalties in solve time
- [ ] `/game/sessions/{id}/submit` creates leaderboard entry for solvers
- [ ] `/game/sessions/{id}/submit` enforces first-play-wins
- [ ] `/game/sessions/{id}/hint` returns quartile definitions
- [ ] `/game/sessions/{id}/hint` applies correct penalties (30s, 60s, 120s, 240s, 480s)
- [ ] `/game/sessions/{id}/hint` enforces 5-hint maximum
- [ ] `/puzzle/today` creates puzzle lazily if not exists
- [ ] `/puzzle/{date}` returns 404 for non-existent puzzles
- [ ] `/leaderboard/today` returns entries sorted by solve time
- [ ] `/leaderboard/today` includes requesting player's rank
- [ ] Puzzle scheduler respects quartile cooldown (30 days)
- [ ] All endpoints return proper HTTP status codes
- [ ] All endpoints have docstrings
- [ ] Pre-commit hooks pass (ruff linting)

---

## Files to Create

| File | Purpose |
|------|---------|
| `backend/app/services/name_generator.py` | AdjectiveNoun player name generation |
| `backend/app/api/routes/game.py` | Game session endpoints (start, word, submit, hint) |
| `backend/app/api/routes/puzzle.py` | Puzzle retrieval endpoints |
| `backend/app/api/routes/leaderboard.py` | Leaderboard endpoints |
| `backend/app/services/puzzle_scheduler.py` | Lazy puzzle generation service |

## Files to Modify

| File | Changes |
|------|---------|
| `backend/app/api/main.py` | Register new route modules |

---

## Testing Notes

After implementation, verify with these manual tests:

```bash
# Start a game
curl -X POST http://localhost:8000/api/game/start \
  -H "Content-Type: application/json" \
  -d '{"device_fingerprint": "test-device-123"}'

# Validate a word (replace session_id)
curl -X POST http://localhost:8000/api/game/sessions/{session_id}/word \
  -H "Content-Type: application/json" \
  -d '{"word": "TEST"}'

# Get hint
curl -X POST http://localhost:8000/api/game/sessions/{session_id}/hint

# Submit game
curl -X POST http://localhost:8000/api/game/sessions/{session_id}/submit

# Get today's puzzle
curl http://localhost:8000/api/puzzle/today

# Get today's leaderboard
curl http://localhost:8000/api/leaderboard/today
```

Run the test suite:
```bash
cd backend && uv run pytest app/api/routes/tests/ -v
```

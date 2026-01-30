"""Game session management API endpoints."""

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from sqlmodel import select

from app.api.deps import SessionDep
from app.game.dictionary import get_dictionary
from app.game.solver import (
    calculate_hint_penalty,
    get_tile_count,
    score_word,
)
from app.game.types import Tile as GameTile
from app.models import (
    GameSession,
    LeaderboardEntry,
    Player,
    Puzzle,
)
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
    solve_time_ms: int | None = None
    words_found: list[str]
    leaderboard_rank: int | None = None


class GameStartRequest(BaseModel):
    """Request to start a new game session."""

    device_fingerprint: str
    player_id: str | None = None  # UUID string for returning players


class GameStartResponse(BaseModel):
    """Response when starting a new game."""

    session_id: str  # UUID as string
    player_id: str  # UUID as string (stable identifier)
    display_name: str  # AdjectiveNoun format for display
    tiles: list[TileSchema]
    already_played: bool
    previous_result: PreviousResultSchema | None = None
    # NOTE: valid_words intentionally NOT included (security)


class WordValidationRequest(BaseModel):
    """Request to validate a submitted word."""

    word: str


class WordValidationResponse(BaseModel):
    """Response after validating a word."""

    is_valid: bool
    points: int | None = None  # Points earned if valid
    reason: str | None = None  # Error reason if invalid
    is_quartile: bool = False  # True if 4-tile word
    current_score: int  # Updated total score
    is_solved: bool  # True if reached solve threshold


class GameSubmitResponse(BaseModel):
    """Response after submitting/finalizing a game."""

    success: bool
    final_score: int  # Server-calculated
    solve_time_ms: int | None = None  # Server-calculated, None if not solved
    leaderboard_rank: int | None = None  # None if not solved or not ranked
    message: str


class HintResponse(BaseModel):
    """Response after requesting a hint."""

    hint_number: int  # Which hint this is (1-5)
    definition: str | None = None  # WordNet definition of unfound quartile
    time_penalty_ms: int  # Penalty added to solve time
    quartiles_remaining: int  # How many quartile words still unfound


# --- Helper Functions ---


def _get_or_create_player(
    db: SessionDep,
    device_fingerprint: str,
    player_id: str | None = None,
) -> Player:
    """Get existing player or create new one.

    Args:
        db: Database session
        device_fingerprint: Device fingerprint for identification
        player_id: Optional UUID string for returning players

    Returns:
        The Player instance
    """
    # Try to find by player_id first
    if player_id:
        try:
            player_uuid = uuid.UUID(player_id)
            player = db.exec(select(Player).where(Player.id == player_uuid)).first()
            if player:
                return player
        except ValueError:
            pass  # Invalid UUID, fall through

    # Try to find by device fingerprint
    player = db.exec(select(Player).where(Player.device_fingerprint == device_fingerprint)).first()
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
    puzzle_id: uuid.UUID,
) -> GameSession | None:
    """Check if player has already played this puzzle.

    Args:
        db: Database session
        player_id: Player UUID
        puzzle_id: Puzzle UUID

    Returns:
        Existing completed session or None
    """
    return db.exec(
        select(GameSession)
        .where(GameSession.player_id == player_id)
        .where(GameSession.puzzle_id == puzzle_id)
        .where(GameSession.completed_at.is_not(None))
    ).first()


def _parse_tiles_json(tiles_json: str) -> list[TileSchema]:
    """Parse tiles from JSON storage format.

    Args:
        tiles_json: JSON string containing tile data

    Returns:
        List of TileSchema objects
    """
    import json

    tiles_data = json.loads(tiles_json)
    return [TileSchema(id=t["id"], letters=t["letters"]) for t in tiles_data]


def _parse_words_json(words_json: str) -> list[str]:
    """Parse words list from JSON storage format.

    Args:
        words_json: JSON string containing words array

    Returns:
        List of words
    """
    import json

    return json.loads(words_json)


def _save_words_json(words: list[str]) -> str:
    """Serialize words list to JSON storage format.

    Args:
        words: List of words to serialize

    Returns:
        JSON string
    """
    import json

    return json.dumps(words)


def _parse_game_tiles(tiles_json: str) -> list[GameTile]:
    """Parse game tiles from JSON storage format.

    Args:
        tiles_json: JSON string containing tile data

    Returns:
        List of GameTile objects (pure Python game types)
    """
    import json

    tiles_data = json.loads(tiles_json)
    return [GameTile(id=t["id"], letters=t["letters"]) for t in tiles_data]


def _calculate_leaderboard_rank(
    db: SessionDep,
    puzzle_id: uuid.UUID,
    solve_time_ms: int,
) -> int:
    """Calculate rank for a solve time on today's leaderboard.

    Args:
        db: Database session
        puzzle_id: Puzzle UUID
        solve_time_ms: Solve time in milliseconds

    Returns:
        Rank (1-indexed)
    """
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
    db: SessionDep,
) -> GameStartResponse:
    """Start a new game session.

    - Gets today's puzzle (creates if doesn't exist)
    - Gets or creates player based on device_fingerprint/player_id
    - Checks if player already completed today's puzzle
    - Creates game session in database with server-recorded start_time
    - Returns puzzle tiles only (NOT valid words - security)

    Returns:
        GameStartResponse: Session info, player data, and puzzle tiles.
    """
    from datetime import UTC, datetime

    # Get or create today's puzzle
    today = datetime.now(UTC).date()
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
                # Calculate rank dynamically
                rank = _calculate_leaderboard_rank(db, puzzle.id, existing_session.solve_time_ms)

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
        start_time=datetime.now(UTC),
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
    db: SessionDep,
) -> WordValidationResponse:
    """Validate a submitted word.

    Server-authoritative validation:
    - Checks if word exists in puzzle's valid word set
    - Checks if word was already found
    - Returns points if valid, error reason if not
    - Records valid word in session
    - Checks if solve threshold reached

    Does NOT expose the valid word list to the client.

    Returns:
        WordValidationResponse: Validation result with points and score.

    Raises:
        HTTPException: If session not found, already completed, or puzzle not found.
    """
    # Get session
    session = db.get(GameSession, session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Game session not found",
        )

    # Check if session already completed
    if session.completed_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Game session already completed",
        )

    # Get puzzle
    puzzle = db.get(Puzzle, session.puzzle_id)
    if not puzzle:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Puzzle not found",
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
    game_tiles = _parse_game_tiles(puzzle.tiles_json)
    try:
        tile_count = get_tile_count(word, game_tiles)
    except ValueError:
        # Word cannot be formed from tiles (shouldn't happen if in valid_words)
        return WordValidationResponse(
            is_valid=False,
            reason="Not a valid word for this puzzle",
            current_score=session.final_score,
            is_solved=session.final_score >= SOLVE_THRESHOLD,
        )

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
    db: SessionDep,
) -> GameSubmitResponse:
    """Finalize and submit game for leaderboard.

    Server-authoritative scoring:
    - Calculates final solve time: now() - start_time + hint_penalties
    - Updates leaderboard if solved (score >= 100)
    - Enforces first-play-wins (cannot resubmit)
    - Client does NOT submit score or time

    Returns:
        GameSubmitResponse: Final score, solve time, and leaderboard rank.

    Raises:
        HTTPException: If session not found.
    """
    # Get session
    session = db.get(GameSession, session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Game session not found",
        )

    # Check if already completed
    if session.completed_at:
        return GameSubmitResponse(
            success=False,
            final_score=session.final_score,
            solve_time_ms=session.solve_time_ms,
            leaderboard_rank=None,
            message="Game already submitted",
        )

    # Calculate final time
    now = datetime.now(UTC)
    elapsed_ms = int((now - session.start_time).total_seconds() * 1000)
    total_time_ms = elapsed_ms + session.hint_penalty_ms

    # Mark session complete
    session.completed_at = now

    # Check if solved (reached threshold)
    is_solved = session.final_score >= SOLVE_THRESHOLD
    rank = None
    if is_solved:
        session.solve_time_ms = total_time_ms

        # Add to leaderboard
        entry = LeaderboardEntry(
            puzzle_id=session.puzzle_id,
            player_id=session.player_id,
            solve_time_ms=total_time_ms,
        )
        db.add(entry)

        # Calculate rank
        rank = _calculate_leaderboard_rank(db, session.puzzle_id, total_time_ms)

    db.add(session)
    db.commit()

    return GameSubmitResponse(
        success=True,
        final_score=session.final_score,
        solve_time_ms=session.solve_time_ms,
        leaderboard_rank=rank,
        message="Congratulations! You solved it!" if is_solved else "Game completed",
    )


@router.post("/sessions/{session_id}/hint", response_model=HintResponse)
async def get_hint(
    session_id: uuid.UUID,
    db: SessionDep,
) -> HintResponse:
    """Request a hint (definition of unfound quartile word).

    - Returns WordNet definition of one unfound quartile word
    - Increments hint count in session
    - Adds time penalty (30s, 60s, 120s, 240s, 480s)
    - Maximum 5 hints per game

    Returns:
        HintResponse: Hint number, definition, time penalty, and remaining quartiles.

    Raises:
        HTTPException: If session not found, already completed, or max hints reached.
    """
    # Get session
    session = db.get(GameSession, session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Game session not found",
        )

    # Check if session already completed
    if session.completed_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Game session already completed",
        )

    # Check hint limit
    if session.hints_used >= 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum hints (5) already used",
        )

    # Get puzzle
    puzzle = db.get(Puzzle, session.puzzle_id)
    if not puzzle:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Puzzle not found",
        )

    # Find unfound quartile words
    found_words = set(_parse_words_json(session.words_found_json))
    quartile_words = set(_parse_words_json(puzzle.quartile_words_json))
    unfound_quartiles = quartile_words - found_words

    if not unfound_quartiles:
        return HintResponse(
            hint_number=session.hints_used + 1,
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

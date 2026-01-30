"""Puzzle retrieval API endpoints."""

from datetime import date

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
    """Parse tiles from JSON storage format.

    Args:
        tiles_json: JSON string containing tile data

    Returns:
        List of TileSchema objects
    """
    import json

    tiles_data = json.loads(tiles_json)
    return [TileSchema(id=t["id"], letters=t["letters"]) for t in tiles_data]


def _puzzle_to_response(puzzle: Puzzle) -> PuzzleResponse:
    """Convert database puzzle to API response.

    Args:
        puzzle: Database Puzzle model

    Returns:
        PuzzleResponse for API
    """
    return PuzzleResponse(
        id=str(puzzle.id),
        date=puzzle.date,
        tiles=_parse_tiles_json(puzzle.tiles_json),
        total_available_points=puzzle.total_available_points,
    )


# --- Endpoints ---


@router.get("/today", response_model=PuzzleResponse)
async def get_todays_puzzle(
    db: SessionDep,
) -> PuzzleResponse:
    """Get today's puzzle.

    Creates the puzzle if it doesn't exist yet (lazy generation).
    Returns tiles only - valid words are never exposed to client.

    Returns:
        PuzzleResponse: Today's puzzle with tiles and metadata.
    """
    from datetime import UTC, datetime

    today = datetime.now(UTC).date()
    puzzle = ensure_puzzle_exists_for_date(today, db)
    return _puzzle_to_response(puzzle)


@router.get("/{puzzle_date}", response_model=PuzzleResponse)
async def get_puzzle_by_date(
    puzzle_date: date,
    db: SessionDep,
) -> PuzzleResponse:
    """Get puzzle for a specific date.

    For practice mode (post-MVP) or viewing past puzzles.
    Only returns puzzles that already exist (no generation).

    Returns:
        PuzzleResponse: The requested puzzle with tiles and metadata.

    Raises:
        HTTPException: If puzzle not found for the given date.
    """
    puzzle = db.exec(select(Puzzle).where(Puzzle.date == puzzle_date)).first()

    if not puzzle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No puzzle found for date {puzzle_date}",
        )

    return _puzzle_to_response(puzzle)

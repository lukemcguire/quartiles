"""Leaderboard API endpoints."""

from datetime import date

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
    player_rank: int | None = None  # Current player's rank, if on board


# --- Helper Functions ---


def _calculate_player_rank(
    db: SessionDep,
    puzzle_id: str,
    solve_time_ms: int,
) -> int:
    """Calculate player's rank on the leaderboard.

    Args:
        db: Database session
        puzzle_id: Puzzle UUID as string
        solve_time_ms: Player's solve time

    Returns:
        Player's rank (1-indexed)
    """
    from uuid import UUID

    puzzle_uuid = UUID(puzzle_id)
    faster_count = len(
        db.exec(
            select(LeaderboardEntry)
            .where(LeaderboardEntry.puzzle_id == puzzle_uuid)
            .where(LeaderboardEntry.solve_time_ms < solve_time_ms)
        ).all()
    )
    return faster_count + 1


# --- Endpoints ---


@router.get("/today", response_model=LeaderboardResponse)
async def get_todays_leaderboard(
    db: SessionDep,
    limit: int = Query(default=100, ge=1, le=500),
    player_id: str | None = None,
) -> LeaderboardResponse:
    """Get today's leaderboard rankings.

    - Returns top `limit` entries sorted by solve time
    - Optionally includes current player's rank if not in top results

    Returns:
        LeaderboardResponse: Today's leaderboard entries and player rank.
    """
    from datetime import UTC, datetime

    today = datetime.now(UTC).date()

    # Get today's puzzle
    puzzle = db.exec(select(Puzzle).where(Puzzle.date == today)).first()

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
        entry_schemas.append(
            LeaderboardEntrySchema(
                rank=i + 1,
                player_id=str(entry.player_id),
                display_name=player.display_name if player else "Unknown",
                solve_time_ms=entry.solve_time_ms,
            )
        )

    # Get total count
    total_count = len(db.exec(select(LeaderboardEntry).where(LeaderboardEntry.puzzle_id == puzzle.id)).all())

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
                player_rank = _calculate_player_rank(db, str(puzzle.id), player_entry.solve_time_ms)
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
    player_id: str | None = None,
) -> LeaderboardResponse:
    """Get leaderboard for a specific date.

    For viewing historical rankings.

    Returns:
        LeaderboardResponse: Leaderboard entries and player rank.

    Raises:
        HTTPException: If puzzle not found for the given date.
    """
    # Get puzzle for date
    puzzle = db.exec(select(Puzzle).where(Puzzle.date == leaderboard_date)).first()

    if not puzzle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No puzzle found for date {leaderboard_date}",
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
        entry_schemas.append(
            LeaderboardEntrySchema(
                rank=i + 1,
                player_id=str(entry.player_id),
                display_name=player.display_name if player else "Unknown",
                solve_time_ms=entry.solve_time_ms,
            )
        )

    total_count = len(db.exec(select(LeaderboardEntry).where(LeaderboardEntry.puzzle_id == puzzle.id)).all())

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
                player_rank = _calculate_player_rank(db, str(puzzle.id), player_entry.solve_time_ms)
        except ValueError:
            pass

    return LeaderboardResponse(
        puzzle_id=str(puzzle.id),
        puzzle_date=leaderboard_date,
        entries=entry_schemas,
        total_entries=total_count,
        player_rank=player_rank,
    )

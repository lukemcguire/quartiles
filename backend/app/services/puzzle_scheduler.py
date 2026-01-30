"""Puzzle scheduling and generation service."""

import json
from datetime import date, timedelta

from sqlmodel import Session, select

from app.game.dictionary import get_dictionary
from app.game.generator import generate_puzzle
from app.models import Puzzle, QuartileCooldown

COOLDOWN_DAYS = 30  # Days before a quartile word can be reused


def get_cooled_down_quartiles(db: Session) -> set[str]:
    """Get set of quartile words currently in cooldown.

    Args:
        db: Database session

    Returns:
        Set of quartile words that are in cooldown period
    """
    from datetime import UTC, datetime

    cutoff_date = datetime.now(UTC).date() - timedelta(days=COOLDOWN_DAYS)
    cooldowns = db.exec(select(QuartileCooldown).where(QuartileCooldown.last_used_date > cutoff_date)).all()
    return {c.word for c in cooldowns}


def update_quartile_cooldowns(db: Session, quartile_words: list[str]) -> None:
    """Update cooldown records for used quartile words.

    Args:
        db: Database session
        quartile_words: List of quartile words to update cooldowns for
    """
    from datetime import UTC, datetime

    today = datetime.now(UTC).date()
    for word in quartile_words:
        existing = db.exec(select(QuartileCooldown).where(QuartileCooldown.word == word)).first()
        if existing:
            existing.last_used_date = today
            db.add(existing)
        else:
            cooldown = QuartileCooldown(word=word, last_used_date=today)
            db.add(cooldown)
    db.commit()


def ensure_puzzle_exists_for_date(target_date: date, db: Session) -> Puzzle:
    """Get or create puzzle for given date.

    Uses lazy generation - creates puzzle on first request if not exists.

    Args:
        target_date: The date to get/create puzzle for
        db: Database session

    Returns:
        The puzzle for the given date

    Raises:
        RuntimeError: If puzzle generation fails
    """
    # Check if puzzle exists
    existing = db.exec(select(Puzzle).where(Puzzle.date == target_date)).first()
    if existing:
        return existing

    # Generate new puzzle
    dictionary = get_dictionary()
    excluded_quartiles = get_cooled_down_quartiles(db)

    game_puzzle = generate_puzzle(dictionary, excluded_quartiles)
    if game_puzzle is None:
        msg = f"Failed to generate puzzle for {target_date}"
        raise RuntimeError(msg)

    # Convert to database format
    tiles_json = json.dumps([{"id": t.id, "letters": t.letters} for t in game_puzzle.tiles])
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
    update_quartile_cooldowns(db, list(game_puzzle.quartile_words))

    return puzzle


def generate_upcoming_puzzles(days_ahead: int = 7) -> None:
    """Pre-generate puzzles for upcoming days.

    Called by background task/cron job for reliability.

    Args:
        days_ahead: Number of days to generate puzzles for
    """
    from datetime import UTC, datetime

    from app.core.db import engine

    with Session(engine) as db:
        for offset in range(days_ahead):
            target_date = datetime.now(UTC).date() + timedelta(days=offset)
            try:
                ensure_puzzle_exists_for_date(target_date, db)
            except RuntimeError as e:
                # Log but continue with other dates
                print(f"Warning: {e}")

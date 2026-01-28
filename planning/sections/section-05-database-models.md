# Section 05: Database Models & Migrations

## Background

The Quartiles game requires persistent storage for:
1. **Players** - Anonymous (AdjectiveNoun) or authenticated users
2. **Puzzles** - Daily puzzle configurations with tiles and valid words
3. **Game Sessions** - Player attempts with found words, scores, timing
4. **Leaderboard** - Ranked entries for each puzzle
5. **Quartile Cooldown** - Track which words were recently used as quartiles

The existing codebase uses SQLModel (SQLAlchemy ORM + Pydantic validation) with PostgreSQL and Alembic migrations.

## Dependencies

| Type | Section | Description |
|------|---------|-------------|
| **requires** | 01 | Codebase cleanup ensures models.py is ready to extend |
| **requires** | 04 | Game logic types inform database schema design |
| **blocks** | 06 | API endpoints need database models for CRUD |

## Requirements

When this section is complete:
1. All game tables are defined in `models.py`
2. Alembic migration creates the new tables
3. Migration runs successfully against local database
4. Foreign key relationships work correctly

---

## Implementation Details

### 5.1 New Database Tables

**File:** `backend/app/models.py` (add to existing file)

```python
"""
SQLModel database tables for Quartiles game.

Tables:
- Player: Anonymous or authenticated players
- Puzzle: Daily puzzle configurations
- GameSession: Player game attempts
- LeaderboardEntry: Ranked solve times
- QuartileCooldown: Word usage tracking
"""

from datetime import date, datetime, timezone
from typing import Optional
import uuid

from sqlmodel import Field, Relationship, SQLModel


# ============================================================================
# PLAYER
# ============================================================================

class Player(SQLModel, table=True):
    """
    Anonymous or authenticated player.

    Anonymous players are identified by device_fingerprint and assigned
    a display_name (AdjectiveNoun format like "ChubbyPenguin").

    Authenticated players link to the User table.
    """

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    display_name: str = Field(max_length=50)  # e.g., "ChubbyPenguin"
    device_fingerprint: Optional[str] = Field(default=None, max_length=255)
    user_id: Optional[uuid.UUID] = Field(
        default=None,
        foreign_key="user.id",
        index=True,
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    game_sessions: list["GameSession"] = Relationship(back_populates="player")


# ============================================================================
# PUZZLE
# ============================================================================

class Puzzle(SQLModel, table=True):
    """
    Daily puzzle configuration.

    Each date has exactly one puzzle. Tiles and words are stored as JSON
    for flexibility (not normalized) since they're read-heavy and rarely
    change after creation.
    """

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    date: date = Field(unique=True, index=True)
    tiles_json: str  # JSON array of {"id": int, "letters": str}
    quartile_words_json: str  # JSON array of 5 words
    valid_words_json: str  # JSON array of all valid words
    total_available_points: int
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    game_sessions: list["GameSession"] = Relationship(back_populates="puzzle")


# ============================================================================
# GAME SESSION
# ============================================================================

class GameSession(SQLModel, table=True):
    """
    A player's game session for a specific puzzle.

    Tracks the progression of a game: start time, words found, hints used,
    and final results. The server is authoritative for timing and scoring.
    """

    __tablename__ = "game_session"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    puzzle_id: uuid.UUID = Field(foreign_key="puzzle.id", index=True)
    player_id: uuid.UUID = Field(foreign_key="player.id", index=True)

    # Timing (server-authoritative)
    start_time: datetime  # When player started the game
    completed_at: Optional[datetime] = None  # When player finished/submitted
    solve_time_ms: Optional[int] = None  # Server-calculated: (completed_at - start_time) + penalties

    # Game state
    final_score: int = 0  # Server-calculated from words_found
    hints_used: int = 0
    hint_penalty_ms: int = 0  # Accumulated hint time penalties
    words_found_json: str = Field(default="[]")  # JSON array of found words

    # Relationships
    puzzle: Puzzle = Relationship(back_populates="game_sessions")
    player: Player = Relationship(back_populates="game_sessions")

    class Config:
        """SQLModel config."""

        # Unique constraint: one completed session per player per puzzle
        # Note: This is enforced in application logic, not DB constraint,
        # because we allow incomplete sessions


# ============================================================================
# LEADERBOARD
# ============================================================================

class LeaderboardEntry(SQLModel, table=True):
    """
    Leaderboard entry for a solved puzzle.

    Only players who reach the 100-point solve threshold get leaderboard entries.
    Rank is computed when querying (not stored) for simplicity.
    """

    __tablename__ = "leaderboard_entry"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    puzzle_id: uuid.UUID = Field(foreign_key="puzzle.id", index=True)
    player_id: uuid.UUID = Field(foreign_key="player.id", index=True)
    solve_time_ms: int  # Server-calculated, includes hint penalties
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    # Note: rank is computed at query time using ROW_NUMBER() OVER (ORDER BY solve_time_ms)


# ============================================================================
# QUARTILE COOLDOWN
# ============================================================================

class QuartileCooldown(SQLModel, table=True):
    """
    Tracks when a word was last used as a quartile target.

    Words used as quartiles cannot be reused for 30 days to ensure
    puzzle variety.
    """

    __tablename__ = "quartile_cooldown"

    word: str = Field(primary_key=True, max_length=20)
    last_used_date: date


# ============================================================================
# PYDANTIC SCHEMAS (for API)
# ============================================================================

class TileSchema(SQLModel):
    """Tile data for API responses."""

    id: int
    letters: str


class PuzzleResponse(SQLModel):
    """Puzzle data for API responses (excludes valid_words for security)."""

    id: uuid.UUID
    date: date
    tiles: list[TileSchema]
    # Note: valid_words intentionally excluded - security


class GameStartResponse(SQLModel):
    """Response when starting a new game."""

    session_id: uuid.UUID
    player_id: uuid.UUID
    display_name: str
    tiles: list[TileSchema]
    already_played: bool
    previous_result: Optional["PreviousResultSchema"] = None


class PreviousResultSchema(SQLModel):
    """Previous game result if player already played."""

    final_score: int
    solve_time_ms: Optional[int]
    leaderboard_rank: Optional[int]


class WordValidationResponse(SQLModel):
    """Response when validating a word."""

    is_valid: bool
    points: Optional[int] = None
    reason: Optional[str] = None
    is_quartile: bool = False
    current_score: int
    is_solved: bool


class GameSubmitResponse(SQLModel):
    """Response when finalizing a game."""

    success: bool
    final_score: int
    solve_time_ms: Optional[int]
    leaderboard_rank: Optional[int]
    message: str


class LeaderboardEntrySchema(SQLModel):
    """Leaderboard entry for API responses."""

    rank: int
    player_id: uuid.UUID
    display_name: str
    solve_time_ms: int


class LeaderboardResponse(SQLModel):
    """Leaderboard data for API responses."""

    date: date
    entries: list[LeaderboardEntrySchema]
```

### 5.2 Alembic Migration

**Create migration:**
```bash
cd backend
uv run alembic revision --autogenerate -m "add game tables"
```

**Expected migration content:**

```python
"""add game tables

Revision ID: xxxx
Revises: yyyy
Create Date: 2025-xx-xx
"""

from alembic import op
import sqlalchemy as sa
import sqlmodel


def upgrade() -> None:
    # Player table
    op.create_table(
        'player',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('display_name', sa.String(50), nullable=False),
        sa.Column('device_fingerprint', sa.String(255), nullable=True),
        sa.Column('user_id', sa.Uuid(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_player_user_id', 'player', ['user_id'])

    # Puzzle table
    op.create_table(
        'puzzle',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('tiles_json', sa.Text(), nullable=False),
        sa.Column('quartile_words_json', sa.Text(), nullable=False),
        sa.Column('valid_words_json', sa.Text(), nullable=False),
        sa.Column('total_available_points', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('date'),
    )
    op.create_index('ix_puzzle_date', 'puzzle', ['date'])

    # GameSession table
    op.create_table(
        'game_session',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('puzzle_id', sa.Uuid(), nullable=False),
        sa.Column('player_id', sa.Uuid(), nullable=False),
        sa.Column('start_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('solve_time_ms', sa.Integer(), nullable=True),
        sa.Column('final_score', sa.Integer(), nullable=False, default=0),
        sa.Column('hints_used', sa.Integer(), nullable=False, default=0),
        sa.Column('hint_penalty_ms', sa.Integer(), nullable=False, default=0),
        sa.Column('words_found_json', sa.Text(), nullable=False, default='[]'),
        sa.ForeignKeyConstraint(['puzzle_id'], ['puzzle.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['player_id'], ['player.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_game_session_puzzle_id', 'game_session', ['puzzle_id'])
    op.create_index('ix_game_session_player_id', 'game_session', ['player_id'])

    # LeaderboardEntry table
    op.create_table(
        'leaderboard_entry',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('puzzle_id', sa.Uuid(), nullable=False),
        sa.Column('player_id', sa.Uuid(), nullable=False),
        sa.Column('solve_time_ms', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['puzzle_id'], ['puzzle.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['player_id'], ['player.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_leaderboard_entry_puzzle_id', 'leaderboard_entry', ['puzzle_id'])
    op.create_index('ix_leaderboard_entry_player_id', 'leaderboard_entry', ['player_id'])

    # QuartileCooldown table
    op.create_table(
        'quartile_cooldown',
        sa.Column('word', sa.String(20), nullable=False),
        sa.Column('last_used_date', sa.Date(), nullable=False),
        sa.PrimaryKeyConstraint('word'),
    )


def downgrade() -> None:
    op.drop_table('quartile_cooldown')
    op.drop_table('leaderboard_entry')
    op.drop_table('game_session')
    op.drop_table('puzzle')
    op.drop_table('player')
```

### 5.3 Run Migration

```bash
# Make sure database is running
make dev

# Run migration
cd backend
uv run alembic upgrade head

# Verify tables exist
uv run python -c "from app.core.db import engine; from sqlmodel import inspect; print(inspect(engine).get_table_names())"
```

---

## Acceptance Criteria

- [ ] `Player` table defined with display_name, device_fingerprint, user_id
- [ ] `Puzzle` table defined with date, tiles_json, quartile_words_json, valid_words_json
- [ ] `GameSession` table defined with timing, scoring, words_found fields
- [ ] `LeaderboardEntry` table defined with solve_time_ms
- [ ] `QuartileCooldown` table defined with word and last_used_date
- [ ] All foreign key relationships defined correctly
- [ ] Pydantic schemas defined for API responses
- [ ] Alembic migration generated successfully
- [ ] Migration runs without errors (`alembic upgrade head`)
- [ ] Tables visible in database
- [ ] `pre-commit run --all-files` passes

## Files Summary

### Modify
- `backend/app/models.py` - Add new tables and schemas

### Create
- `backend/app/alembic/versions/xxxx_add_game_tables.py` - Migration file (auto-generated)

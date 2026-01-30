"""SQLModel database models and Pydantic schemas for API requests/responses."""

import uuid
from datetime import UTC, datetime

# Import date as date_type to avoid naming conflicts
from datetime import date as date_type
from typing import Optional

from pydantic import EmailStr
from sqlalchemy import DateTime
from sqlmodel import Field, Relationship, SQLModel


def get_datetime_utc() -> datetime:
    """Get current UTC datetime.

    Returns:
        datetime: Current datetime in UTC timezone.
    """
    return datetime.now(UTC)


def get_utc_date() -> date_type:
    """Get current UTC date.

    Returns:
        date: Current date in UTC timezone.
    """
    return datetime.now(UTC).date()


# Shared properties
class UserBase(SQLModel):
    """Base user model with shared properties."""

    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on creation
class UserCreate(UserBase):
    """Schema for creating a new user."""

    password: str = Field(min_length=8, max_length=128)


class UserRegister(SQLModel):
    """Schema for user self-registration."""

    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on update, all are optional
class UserUpdate(UserBase):
    """Schema for updating a user (admin)."""

    email: EmailStr | None = Field(default=None, max_length=255)
    password: str | None = Field(default=None, min_length=8, max_length=128)


class UserUpdateMe(SQLModel):
    """Schema for users updating their own information."""

    full_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = Field(default=None, max_length=255)


class UpdatePassword(SQLModel):
    """Schema for password update request."""

    current_password: str = Field(min_length=8, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


# Database model, database table inferred from class name
class User(UserBase, table=True):
    """User database model."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore[arg-type]
    )


# Properties to return via API, id is always required
class UserPublic(UserBase):
    """Public user information returned by API."""

    id: uuid.UUID
    created_at: datetime | None = None


class UsersPublic(SQLModel):
    """List of public user information with pagination count."""

    data: list[UserPublic]
    count: int


# Generic message
class Message(SQLModel):
    """Generic message response."""

    message: str


# JSON payload containing access token
class Token(SQLModel):
    """OAuth2 token response."""

    access_token: str
    token_type: str = "bearer"  # noqa: S105


# Contents of JWT token
class TokenPayload(SQLModel):
    """JWT token payload data."""

    sub: str | None = None


class NewPassword(SQLModel):
    """Schema for password reset with token."""

    token: str
    new_password: str = Field(min_length=8, max_length=128)


# ============================================================================
# GAME DATABASE MODELS
# ============================================================================


class Player(SQLModel, table=True):
    """Anonymous or authenticated player.

    Anonymous players are identified by device_fingerprint and assigned
    a display_name (AdjectiveNoun format like "ChubbyPenguin").

    Authenticated players link to the User table.
    """

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    display_name: str = Field(max_length=50)  # e.g., "ChubbyPenguin"
    device_fingerprint: str | None = Field(default=None, max_length=255)
    user_id: uuid.UUID | None = Field(
        default=None,
        foreign_key="user.id",
        index=True,
    )
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore[arg-type]
    )

    # Relationships - use string for forward reference
    game_sessions: list["GameSession"] = Relationship(back_populates="player")


class Puzzle(SQLModel, table=True):
    """Daily puzzle configuration.

    Each date has exactly one puzzle. Tiles and words are stored as JSON
    for flexibility (not normalized) since they're read-heavy and rarely
    change after creation.
    """

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    date: date_type = Field(unique=True, index=True)
    tiles_json: str  # JSON array of {"id": int, "letters": str}
    quartile_words_json: str  # JSON array of 5 words
    valid_words_json: str  # JSON array of all valid words
    total_available_points: int
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore[arg-type]
    )

    # Relationships - use string for forward reference
    game_sessions: list["GameSession"] = Relationship(back_populates="puzzle")


class GameSession(SQLModel, table=True):
    """A player's game session for a specific puzzle.

    Tracks the progression of a game: start time, words found, hints used,
    and final results. The server is authoritative for timing and scoring.
    """

    __tablename__ = "game_session"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    puzzle_id: uuid.UUID = Field(foreign_key="puzzle.id", index=True)
    player_id: uuid.UUID = Field(foreign_key="player.id", index=True)

    # Timing (server-authoritative)
    start_time: datetime  # When player started the game
    completed_at: datetime | None = None  # When player finished/submitted
    solve_time_ms: int | None = None  # Server-calculated: (completed_at - start_time) + penalties

    # Game state
    final_score: int = 0  # Server-calculated from words_found
    hints_used: int = 0
    hint_penalty_ms: int = 0  # Accumulated hint time penalties
    words_found_json: str = Field(default="[]")  # JSON array of found words

    # Relationships - use strings for forward references
    puzzle: "Puzzle" = Relationship(back_populates="game_sessions")
    player: "Player" = Relationship(back_populates="game_sessions")


class LeaderboardEntry(SQLModel, table=True):
    """Leaderboard entry for a solved puzzle.

    Only players who reach the 100-point solve threshold get leaderboard entries.
    Rank is computed when querying (not stored) for simplicity.
    """

    __tablename__ = "leaderboard_entry"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    puzzle_id: uuid.UUID = Field(foreign_key="puzzle.id", index=True)
    player_id: uuid.UUID = Field(foreign_key="player.id", index=True)
    solve_time_ms: int  # Server-calculated, includes hint penalties
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore[arg-type]
    )


class QuartileCooldown(SQLModel, table=True):
    """Tracks when a word was last used as a quartile target.

    Words used as quartiles cannot be reused for 30 days to ensure
    puzzle variety.
    """

    __tablename__ = "quartile_cooldown"

    word: str = Field(primary_key=True, max_length=20)
    last_used_date: date_type


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
    date: date_type
    tiles: list[TileSchema]


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
    solve_time_ms: int | None
    leaderboard_rank: int | None


class WordValidationResponse(SQLModel):
    """Response when validating a word."""

    is_valid: bool
    points: int | None = None
    reason: str | None = None
    is_quartile: bool = False
    current_score: int
    is_solved: bool


class GameSubmitResponse(SQLModel):
    """Response when finalizing a game."""

    success: bool
    final_score: int
    solve_time_ms: int | None
    leaderboard_rank: int | None
    message: str


class LeaderboardEntrySchema(SQLModel):
    """Leaderboard entry for API responses."""

    rank: int
    player_id: uuid.UUID
    display_name: str
    solve_time_ms: int


class LeaderboardResponse(SQLModel):
    """Leaderboard data for API responses."""

    date: date_type
    entries: list[LeaderboardEntrySchema]

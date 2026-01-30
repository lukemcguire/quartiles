"""Tests for database models and Pydantic schemas."""

import json
import uuid
from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.models import (
    GameSession,
    GameStartResponse,
    GameSubmitResponse,
    LeaderboardEntry,
    LeaderboardEntrySchema,
    LeaderboardResponse,
    Player,
    PreviousResultSchema,
    Puzzle,
    PuzzleResponse,
    QuartileCooldown,
    TileSchema,
    WordValidationResponse,
)


class TestTileSchema:
    """Tests for TileSchema Pydantic model."""

    def test_valid_tile(self) -> None:
        """Test creating a valid tile."""
        tile = TileSchema(id=1, letters="ABC")
        assert tile.id == 1
        assert tile.letters == "ABC"

    def test_tile_validation(self) -> None:
        """Test tile schema validation."""
        # Valid tiles
        TileSchema(id=1, letters="AB")
        TileSchema(id=2, letters="ABCD")
        TileSchema(id=3, letters="A")


class TestPlayer:
    """Tests for Player SQLModel."""

    def test_create_player(self) -> None:
        """Test creating a player."""
        player = Player(
            id=uuid.uuid4(),
            display_name="ChubbyPenguin",
            device_fingerprint="abc123",
            user_id=None,
        )
        assert player.display_name == "ChubbyPenguin"
        assert player.device_fingerprint == "abc123"
        assert player.user_id is None

    def test_player_with_user_id(self) -> None:
        """Test creating a player with a user_id."""
        user_id = uuid.uuid4()
        player = Player(
            id=uuid.uuid4(),
            display_name="TestUser",
            user_id=user_id,
        )
        assert player.user_id == user_id


class TestPuzzle:
    """Tests for Puzzle SQLModel."""

    def test_create_puzzle(self) -> None:
        """Test creating a puzzle."""
        tiles = [{"id": 1, "letters": "AB"}, {"id": 2, "letters": "CD"}]
        quartile_words = ["WORD1", "WORD2", "WORD3", "WORD4", "WORD5"]
        valid_words = ["WORD1", "WORD2", "WORD3", "WORD4", "WORD5", "EXTRA"]

        puzzle = Puzzle(
            id=uuid.uuid4(),
            date=datetime.now(UTC).date(),
            tiles_json=json.dumps(tiles),
            quartile_words_json=json.dumps(quartile_words),
            valid_words_json=json.dumps(valid_words),
            total_available_points=100,
        )
        assert puzzle.date == datetime.now(UTC).date()
        assert puzzle.total_available_points == 100

    def test_puzzle_json_fields(self) -> None:
        """Test puzzle JSON serialization."""
        tiles = [{"id": 1, "letters": "AB"}]
        puzzle = Puzzle(
            id=uuid.uuid4(),
            date=datetime.now(UTC).date(),
            tiles_json=json.dumps(tiles),
            quartile_words_json='["WORD"]',
            valid_words_json='["WORD"]',
            total_available_points=50,
        )
        assert json.loads(puzzle.tiles_json) == tiles


class TestGameSession:
    """Tests for GameSession SQLModel."""

    def test_create_game_session(self) -> None:
        """Test creating a game session."""
        puzzle_id = uuid.uuid4()
        player_id = uuid.uuid4()
        start_time = datetime.now(UTC)

        session = GameSession(
            id=uuid.uuid4(),
            puzzle_id=puzzle_id,
            player_id=player_id,
            start_time=start_time,
            final_score=0,
            hints_used=0,
            hint_penalty_ms=0,
            words_found_json="[]",
        )
        assert session.puzzle_id == puzzle_id
        assert session.player_id == player_id
        assert session.final_score == 0
        assert session.hints_used == 0

    def test_game_session_with_progress(self) -> None:
        """Test game session with progress."""
        session = GameSession(
            id=uuid.uuid4(),
            puzzle_id=uuid.uuid4(),
            player_id=uuid.uuid4(),
            start_time=datetime.now(UTC),
            final_score=25,
            hints_used=1,
            hint_penalty_ms=30000,
            words_found_json='["WORD1", "WORD2"]',
        )
        assert session.final_score == 25
        assert session.hints_used == 1
        assert session.hint_penalty_ms == 30000

    def test_game_session_completion(self) -> None:
        """Test completing a game session."""
        start_time = datetime.now(UTC)
        completed_at = datetime.now(UTC)

        session = GameSession(
            id=uuid.uuid4(),
            puzzle_id=uuid.uuid4(),
            player_id=uuid.uuid4(),
            start_time=start_time,
            completed_at=completed_at,
            solve_time_ms=60000,
            final_score=100,
            hints_used=0,
            hint_penalty_ms=0,
            words_found_json='["WORD1", "WORD2", "WORD3"]',
        )
        assert session.completed_at is not None
        assert session.solve_time_ms == 60000
        assert session.final_score == 100


class TestLeaderboardEntry:
    """Tests for LeaderboardEntry SQLModel."""

    def test_create_leaderboard_entry(self) -> None:
        """Test creating a leaderboard entry."""
        puzzle_id = uuid.uuid4()
        player_id = uuid.uuid4()

        entry = LeaderboardEntry(
            id=uuid.uuid4(),
            puzzle_id=puzzle_id,
            player_id=player_id,
            solve_time_ms=45000,
        )
        assert entry.puzzle_id == puzzle_id
        assert entry.player_id == player_id
        assert entry.solve_time_ms == 45000


class TestQuartileCooldown:
    """Tests for QuartileCooldown SQLModel."""

    def test_create_quartile_cooldown(self) -> None:
        """Test creating a quartile cooldown entry."""
        cooldown = QuartileCooldown(
            word="EXAMPLE",
            last_used_date=datetime.now(UTC).date(),
        )
        assert cooldown.word == "EXAMPLE"
        assert cooldown.last_used_date == datetime.now(UTC).date()


class TestPuzzleResponse:
    """Tests for PuzzleResponse Pydantic schema."""

    def test_puzzle_response(self) -> None:
        """Test creating a puzzle response."""
        puzzle_id = uuid.uuid4()
        tiles = [TileSchema(id=1, letters="AB"), TileSchema(id=2, letters="CD")]

        response = PuzzleResponse(
            id=puzzle_id,
            date=datetime.now(UTC).date(),
            tiles=tiles,
        )
        assert response.id == puzzle_id
        assert len(response.tiles) == 2
        assert response.tiles[0].letters == "AB"


class TestGameStartResponse:
    """Tests for GameStartResponse Pydantic schema."""

    def test_game_start_response_new_player(self) -> None:
        """Test game start response for new player."""
        session_id = uuid.uuid4()
        player_id = uuid.uuid4()
        tiles = [TileSchema(id=1, letters="AB")]

        response = GameStartResponse(
            session_id=session_id,
            player_id=player_id,
            display_name="ChubbyPenguin",
            tiles=tiles,
            already_played=False,
            previous_result=None,
        )
        assert response.session_id == session_id
        assert response.display_name == "ChubbyPenguin"
        assert response.already_played is False
        assert response.previous_result is None

    def test_game_start_response_previous_play(self) -> None:
        """Test game start response with previous result."""
        session_id = uuid.uuid4()
        player_id = uuid.uuid4()
        tiles = [TileSchema(id=1, letters="AB")]
        previous_result = PreviousResultSchema(
            final_score=75,
            solve_time_ms=90000,
            leaderboard_rank=5,
        )

        response = GameStartResponse(
            session_id=session_id,
            player_id=player_id,
            display_name="ChubbyPenguin",
            tiles=tiles,
            already_played=True,
            previous_result=previous_result,
        )
        assert response.already_played is True
        assert response.previous_result is not None
        assert response.previous_result.final_score == 75
        assert response.previous_result.leaderboard_rank == 5


class TestWordValidationResponse:
    """Tests for WordValidationResponse Pydantic schema."""

    def test_valid_word_response(self) -> None:
        """Test response for valid word."""
        response = WordValidationResponse(
            is_valid=True,
            points=4,
            reason=None,
            is_quartile=False,
            current_score=25,
            is_solved=False,
        )
        assert response.is_valid is True
        assert response.points == 4
        assert response.is_quartile is False

    def test_invalid_word_response(self) -> None:
        """Test response for invalid word."""
        response = WordValidationResponse(
            is_valid=False,
            points=None,
            reason="Word not found in puzzle",
            is_quartile=False,
            current_score=25,
            is_solved=False,
        )
        assert response.is_valid is False
        assert response.points is None
        assert response.reason == "Word not found in puzzle"

    def test_quartile_word_response(self) -> None:
        """Test response for quartile word."""
        response = WordValidationResponse(
            is_valid=True,
            points=10,
            reason=None,
            is_quartile=True,
            current_score=95,
            is_solved=True,
        )
        assert response.is_valid is True
        assert response.points == 10
        assert response.is_quartile is True
        assert response.is_solved is True


class TestGameSubmitResponse:
    """Tests for GameSubmitResponse Pydantic schema."""

    def test_successful_submission(self) -> None:
        """Test successful game submission."""
        response = GameSubmitResponse(
            success=True,
            final_score=100,
            solve_time_ms=60000,
            leaderboard_rank=3,
            message="Congratulations! You solved the puzzle!",
        )
        assert response.success is True
        assert response.final_score == 100
        assert response.leaderboard_rank == 3

    def test_incomplete_submission(self) -> None:
        """Test incomplete game submission."""
        response = GameSubmitResponse(
            success=False,
            final_score=75,
            solve_time_ms=None,
            leaderboard_rank=None,
            message="Game not solved yet. Keep trying!",
        )
        assert response.success is False
        assert response.final_score == 75
        assert response.solve_time_ms is None


class TestLeaderboardResponse:
    """Tests for LeaderboardResponse Pydantic schema."""

    def test_leaderboard_response(self) -> None:
        """Test leaderboard response."""
        entries = [
            LeaderboardEntrySchema(
                rank=1,
                player_id=uuid.uuid4(),
                display_name="FastPlayer",
                solve_time_ms=30000,
            ),
            LeaderboardEntrySchema(
                rank=2,
                player_id=uuid.uuid4(),
                display_name="SlowPlayer",
                solve_time_ms=90000,
            ),
        ]

        response = LeaderboardResponse(
            date=datetime.now(UTC).date(),
            entries=entries,
        )
        assert response.date == datetime.now(UTC).date()
        assert len(response.entries) == 2
        assert response.entries[0].rank == 1
        assert response.entries[0].display_name == "FastPlayer"


class TestPydanticValidation:
    """Tests for Pydantic validation of schemas."""

    def test_missing_required_field(self) -> None:
        """Test validation error on missing required field."""
        with pytest.raises(ValidationError):
            TileSchema(id=1)  # Missing 'letters' field

    def test_invalid_type(self) -> None:
        """Test validation error on invalid type."""
        with pytest.raises(ValidationError):
            TileSchema(id="not_an_int", letters="AB")

    def test_optional_fields(self) -> None:
        """Test that optional fields can be None."""
        response = WordValidationResponse(
            is_valid=False,
            points=None,
            reason=None,
            is_quartile=False,
            current_score=0,
            is_solved=False,
        )
        assert response.points is None
        assert response.reason is None

"""Tests for game API endpoints."""

import json
from datetime import UTC, date, datetime
from unittest.mock import patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.models import GameSession, Player, Puzzle

# --- Fixtures ---


@pytest.fixture(scope="session")
def sample_tiles() -> list[dict]:
    """Create sample tile data.

    Returns:
        list[dict]: Sample tile data with id and letters.
    """
    return [
        {"id": 0, "letters": "CH"},
        {"id": 1, "letters": "UB"},
        {"id": 2, "letters": "BY"},
        {"id": 3, "letters": "PE"},
        {"id": 4, "letters": "NG"},
        {"id": 5, "letters": "UI"},
        {"id": 6, "letters": "NI"},
        {"id": 7, "letters": "CO"},
        {"id": 8, "letters": "RN"},
        {"id": 9, "letters": "WA"},
        {"id": 10, "letters": "LF"},
        {"id": 11, "letters": "LS"},
        {"id": 12, "letters": "DO"},
        {"id": 13, "letters": "PH"},
        {"id": 14, "letters": "IN"},
        {"id": 15, "letters": "AL"},
        {"id": 16, "letters": "ES"},
        {"id": 17, "letters": "KA"},
        {"id": 18, "letters": "TE"},
        {"id": 19, "letters": "ST"},
    ]


@pytest.fixture
def sample_puzzle(session: Session, sample_tiles: list[dict]) -> Puzzle:
    """Create a sample puzzle in the database.

    Args:
        session: Database session.
        sample_tiles: Sample tile data.

    Returns:
        Puzzle: A sample puzzle with test data.
    """
    import uuid

    quartile_words = ["CHUBBY", "PENGUIN", "UNICORN", "WALRUS", "NARWHAL"]
    valid_words = [
        "CHUBBY",
        "PENGUIN",
        "UNICORN",
        "WALRUS",
        "NARWHAL",
        "PEN",
        "GUIN",
        "CORN",
        "HORN",
        "WAL",
        "RUS",
    ]

    # Use a fixed test date that won't conflict with the puzzle scheduler
    # The scheduler creates puzzles for today, so use a date in the past
    test_date = date(2024, 1, 1)

    puzzle = Puzzle(
        id=uuid.uuid4(),
        date=test_date,
        tiles_json=json.dumps(sample_tiles),
        quartile_words_json=json.dumps(quartile_words),
        valid_words_json=json.dumps(valid_words),
        total_available_points=150,
    )
    session.add(puzzle)
    session.commit()
    session.refresh(puzzle)
    return puzzle


@pytest.fixture
def sample_player(session: Session) -> Player:
    """Create a sample player in the database.

    Args:
        session: Database session.

    Returns:
        Player: A sample player with test data.
    """
    import uuid

    player = Player(
        id=uuid.uuid4(),
        display_name="TestPlayer",
        device_fingerprint="test-device-123",
    )
    session.add(player)
    session.commit()
    session.refresh(player)
    return player


@pytest.fixture
def sample_session(session: Session, sample_puzzle: Puzzle, sample_player: Player) -> GameSession:
    """Create a sample game session in the database.

    Args:
        session: Database session.
        sample_puzzle: Sample puzzle.
        sample_player: Sample player.

    Returns:
        GameSession: A sample game session with test data.
    """
    import uuid

    game_session = GameSession(
        id=uuid.uuid4(),
        puzzle_id=sample_puzzle.id,
        player_id=sample_player.id,
        start_time=datetime.now(UTC),
        final_score=0,
        hints_used=0,
        hint_penalty_ms=0,
        words_found_json="[]",
    )
    session.add(game_session)
    session.commit()
    session.refresh(game_session)
    return game_session


class TestNameGenerator:
    """Tests for name generator service."""

    def test_generate_player_name(self) -> None:
        """Test that generate_player_name creates valid names."""
        from app.services.name_generator import generate_player_name

        name = generate_player_name()
        assert isinstance(name, str)
        assert len(name) > 0
        # Check it's in AdjectiveNoun format (starts with capital, no space)
        assert name[0].isupper()
        assert " " not in name

    def test_generate_unique_player_name(self) -> None:
        """Test that generate_unique_player_name avoids conflicts."""
        from app.services.name_generator import generate_unique_player_name

        existing_names = {"ChubbyPenguin", "SleepyMango"}
        name = generate_unique_player_name(existing_names)
        assert name is not None
        assert name not in existing_names

    def test_generate_unique_player_name_exhausted(self) -> None:
        """Test that generate_unique_player_name returns None when exhausted."""
        from app.services.name_generator import generate_unique_player_name

        # Create a set that's likely to cause collision
        existing_names_set: set[str] = {
            name for name in (generate_unique_player_name(set()) for _ in range(100)) if name is not None
        }
        # Try to generate with very few attempts
        # This might return None if collision occurs
        _ = generate_unique_player_name(existing_names_set, max_attempts=2)


class TestGameStart:
    """Tests for POST /game/start endpoint."""

    def test_start_new_game(self, client: TestClient, sample_puzzle: Puzzle) -> None:
        """Test starting a new game session."""
        # Mock ensure_puzzle_exists_for_date to return our sample puzzle
        with patch(
            "app.api.routes.game.ensure_puzzle_exists_for_date",
            return_value=sample_puzzle,
        ):
            response = client.post(
                "/api/v1/game/start",
                json={"device_fingerprint": "test-device-123"},
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "session_id" in data
        assert "player_id" in data
        assert "display_name" in data
        assert "tiles" in data
        assert data["already_played"] is False
        assert data["previous_result"] is None
        # Verify valid_words is NOT in response
        assert "valid_words" not in data
        # Verify tiles are present
        assert len(data["tiles"]) == 20

    def test_start_game_returning_player(
        self,
        client: TestClient,
        sample_puzzle: Puzzle,
        sample_player: Player,
    ) -> None:
        """Test starting a game with a returning player."""
        with patch(
            "app.api.routes.game.ensure_puzzle_exists_for_date",
            return_value=sample_puzzle,
        ):
            response = client.post(
                "/api/v1/game/start",
                json={
                    "device_fingerprint": sample_player.device_fingerprint,
                    "player_id": str(sample_player.id),
                },
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["player_id"] == str(sample_player.id)
        assert data["display_name"] == sample_player.display_name

    def test_start_game_already_played(
        self,
        client: TestClient,
        sample_puzzle: Puzzle,
        sample_player: Player,
        session: Session,
    ) -> None:
        """Test starting a game when player already completed today's puzzle."""
        from app.models import GameSession

        # Create a completed session
        completed_session = GameSession(
            puzzle_id=sample_puzzle.id,
            player_id=sample_player.id,
            start_time=datetime.now(UTC),
            completed_at=datetime.now(UTC),
            solve_time_ms=60000,
            final_score=100,
            hints_used=0,
            hint_penalty_ms=0,
            words_found_json='["WORD1", "WORD2"]',
        )
        session.add(completed_session)
        session.commit()

        with patch(
            "app.api.routes.game.ensure_puzzle_exists_for_date",
            return_value=sample_puzzle,
        ):
            response = client.post(
                "/api/v1/game/start",
                json={
                    "device_fingerprint": sample_player.device_fingerprint,
                    "player_id": str(sample_player.id),
                },
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["already_played"] is True
        assert data["previous_result"] is not None
        assert data["previous_result"]["final_score"] == 100


class TestWordValidation:
    """Tests for POST /game/sessions/{id}/word endpoint."""

    def test_validate_valid_word(
        self,
        client: TestClient,
        sample_session: GameSession,
        sample_puzzle: Puzzle,
    ) -> None:
        """Test validating a valid word."""
        # Get a valid word from the puzzle
        valid_words = json.loads(sample_puzzle.valid_words_json)
        test_word = valid_words[0]

        response = client.post(
            f"/api/v1/game/sessions/{sample_session.id}/word",
            json={"word": test_word},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["is_valid"] is True
        assert data["points"] is not None
        assert data["current_score"] > 0

    def test_validate_invalid_word(
        self,
        client: TestClient,
        sample_session: GameSession,
    ) -> None:
        """Test validating an invalid word."""
        response = client.post(
            f"/api/v1/game/sessions/{sample_session.id}/word",
            json={"word": "NOTVALID"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["is_valid"] is False
        assert data["points"] is None
        assert data["reason"] is not None

    def test_validate_duplicate_word(
        self,
        client: TestClient,
        sample_session: GameSession,
        sample_puzzle: Puzzle,
        session: Session,
    ) -> None:
        """Test validating a word that was already found."""
        valid_words = json.loads(sample_puzzle.valid_words_json)
        test_word = valid_words[0]

        # Add word to found words
        sample_session.words_found_json = json.dumps([test_word])
        sample_session.final_score = 10
        session.add(sample_session)
        session.commit()

        response = client.post(
            f"/api/v1/game/sessions/{sample_session.id}/word",
            json={"word": test_word},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["is_valid"] is False
        assert "already found" in data["reason"].lower()

    def test_validate_word_completed_session(
        self,
        client: TestClient,
        sample_session: GameSession,
        session: Session,
    ) -> None:
        """Test validating a word for a completed session."""
        sample_session.completed_at = datetime.now(UTC)
        session.add(sample_session)
        session.commit()

        response = client.post(
            f"/api/v1/game/sessions/{sample_session.id}/word",
            json={"word": "TEST"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_validate_word_session_not_found(
        self,
        client: TestClient,
    ) -> None:
        """Test validating a word for a non-existent session."""
        import uuid

        fake_id = uuid.uuid4()
        response = client.post(
            f"/api/v1/game/sessions/{fake_id}/word",
            json={"word": "TEST"},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestGameSubmit:
    """Tests for POST /game/sessions/{id}/submit endpoint."""

    def test_submit_solved_game(
        self,
        client: TestClient,
        sample_session: GameSession,
        session: Session,
    ) -> None:
        """Test submitting a solved game."""
        # Set up session as solved
        sample_session.final_score = 100
        session.add(sample_session)
        session.commit()

        response = client.post(f"/api/v1/game/sessions/{sample_session.id}/submit")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["final_score"] == 100
        assert data["solve_time_ms"] is not None
        assert "congratulations" in data["message"].lower()

    def test_submit_unsolved_game(
        self,
        client: TestClient,
        sample_session: GameSession,
    ) -> None:
        """Test submitting an unsolved game."""
        response = client.post(f"/api/v1/game/sessions/{sample_session.id}/submit")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["solve_time_ms"] is None

    def test_submit_already_submitted(
        self,
        client: TestClient,
        sample_session: GameSession,
        session: Session,
    ) -> None:
        """Test submitting a game that was already submitted."""
        sample_session.completed_at = datetime.now(UTC)
        sample_session.solve_time_ms = 60000
        session.add(sample_session)
        session.commit()

        response = client.post(f"/api/v1/game/sessions/{sample_session.id}/submit")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is False
        assert "already submitted" in data["message"].lower()

    def test_submit_session_not_found(
        self,
        client: TestClient,
    ) -> None:
        """Test submitting a non-existent session."""
        import uuid

        fake_id = uuid.uuid4()
        response = client.post(f"/api/v1/game/sessions/{fake_id}/submit")

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestGetHint:
    """Tests for POST /game/sessions/{id}/hint endpoint."""

    def test_get_hint(
        self,
        client: TestClient,
        sample_session: GameSession,
    ) -> None:
        """Test getting a hint."""
        response = client.post(f"/api/v1/game/sessions/{sample_session.id}/hint")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["hint_number"] == 1
        assert data["time_penalty_ms"] > 0
        assert data["quartiles_remaining"] >= 0

    def test_get_hint_completed_session(
        self,
        client: TestClient,
        sample_session: GameSession,
        session: Session,
    ) -> None:
        """Test getting a hint for a completed session."""
        sample_session.completed_at = datetime.now(UTC)
        session.add(sample_session)
        session.commit()

        response = client.post(f"/api/v1/game/sessions/{sample_session.id}/hint")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_get_hint_max_hints(
        self,
        client: TestClient,
        sample_session: GameSession,
        session: Session,
    ) -> None:
        """Test getting a hint when max hints already used."""
        sample_session.hints_used = 5
        session.add(sample_session)
        session.commit()

        response = client.post(f"/api/v1/game/sessions/{sample_session.id}/hint")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "maximum" in response.json()["detail"].lower()

    def test_get_hint_session_not_found(
        self,
        client: TestClient,
    ) -> None:
        """Test getting a hint for a non-existent session."""
        import uuid

        fake_id = uuid.uuid4()
        response = client.post(f"/api/v1/game/sessions/{fake_id}/hint")

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestPuzzleEndpoints:
    """Tests for puzzle endpoints."""

    def test_get_todays_puzzle(
        self,
        client: TestClient,
        sample_puzzle: Puzzle,
    ) -> None:
        """Test getting today's puzzle."""
        with patch(
            "app.api.routes.puzzle.ensure_puzzle_exists_for_date",
            return_value=sample_puzzle,
        ):
            response = client.get("/api/v1/puzzle/today")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "id" in data
        assert "date" in data
        assert "tiles" in data
        assert len(data["tiles"]) == 20
        # Verify valid_words is NOT in response
        assert "valid_words" not in data
        assert "quartile_words" not in data

    def test_get_puzzle_by_date(
        self,
        client: TestClient,
        sample_puzzle: Puzzle,
    ) -> None:
        """Test getting puzzle by date."""
        response = client.get(f"/api/v1/puzzle/{sample_puzzle.date}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == str(sample_puzzle.id)

    def test_get_puzzle_by_date_not_found(
        self,
        client: TestClient,
    ) -> None:
        """Test getting puzzle for non-existent date."""
        future_date = date(2099, 12, 31)
        response = client.get(f"/api/v1/puzzle/{future_date}")

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestLeaderboardEndpoints:
    """Tests for leaderboard endpoints."""

    def test_get_todays_leaderboard_empty(
        self,
        client: TestClient,
    ) -> None:
        """Test getting today's leaderboard when empty."""
        response = client.get("/api/v1/leaderboard/today")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["entries"] == []
        assert data["total_entries"] == 0

    def test_get_todays_leaderboard_with_entries(
        self,
        client: TestClient,
        sample_puzzle: Puzzle,
        sample_player: Player,
        session: Session,
    ) -> None:
        """Test getting the leaderboard for the sample puzzle's date."""
        from app.models import LeaderboardEntry

        entry1 = LeaderboardEntry(
            puzzle_id=sample_puzzle.id,
            player_id=sample_player.id,
            solve_time_ms=30000,
        )
        entry2 = LeaderboardEntry(
            puzzle_id=sample_puzzle.id,
            player_id=sample_player.id,
            solve_time_ms=60000,
        )
        session.add(entry1)
        session.add(entry2)
        session.commit()

        # Query the leaderboard for the sample puzzle's date
        response = client.get(f"/api/v1/leaderboard/{sample_puzzle.date}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["entries"]) == 2
        assert data["entries"][0]["rank"] == 1
        assert data["entries"][0]["solve_time_ms"] == 30000

    def test_get_leaderboard_by_date(
        self,
        client: TestClient,
        sample_puzzle: Puzzle,
        sample_player: Player,
        session: Session,
    ) -> None:
        """Test getting leaderboard by date."""
        from app.models import LeaderboardEntry

        entry = LeaderboardEntry(
            puzzle_id=sample_puzzle.id,
            player_id=sample_player.id,
            solve_time_ms=45000,
        )
        session.add(entry)
        session.commit()

        response = client.get(f"/api/v1/leaderboard/{sample_puzzle.date}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["entries"]) == 1
        assert data["entries"][0]["rank"] == 1

    def test_get_leaderboard_with_player_filter(
        self,
        client: TestClient,
        sample_puzzle: Puzzle,
        sample_player: Player,
        session: Session,
    ) -> None:
        """Test getting leaderboard with player_id filter."""
        from app.models import LeaderboardEntry

        entry = LeaderboardEntry(
            puzzle_id=sample_puzzle.id,
            player_id=sample_player.id,
            solve_time_ms=45000,
        )
        session.add(entry)
        session.commit()

        response = client.get(f"/api/v1/leaderboard/{sample_puzzle.date}?player_id={sample_player.id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["player_rank"] is not None

    def test_get_leaderboard_limit(
        self,
        client: TestClient,
        sample_puzzle: Puzzle,
        sample_player: Player,
        session: Session,
    ) -> None:
        """Test getting leaderboard with limit."""
        from app.models import LeaderboardEntry

        for i in range(10):
            entry = LeaderboardEntry(
                puzzle_id=sample_puzzle.id,
                player_id=sample_player.id,
                solve_time_ms=30000 + i * 1000,
            )
            session.add(entry)
        session.commit()

        response = client.get(f"/api/v1/leaderboard/{sample_puzzle.date}?limit=5")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["entries"]) == 5

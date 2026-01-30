"""Fixtures for API tests."""

import json
from collections.abc import Generator
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.engine import Engine
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app.main import app
from app.models import (
    GameSession,
    Player,
    Puzzle,
)


@pytest.fixture(name="engine")
def engine_fixture() -> Generator[Engine]:
    """Create a test database engine.

    Yields:
        Engine: The test database engine.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    yield engine
    SQLModel.metadata.drop_all(engine)


@pytest.fixture(name="session")
def session_fixture(engine: Engine) -> Generator[Session]:
    """Create a test database session.

    Yields:
        Session: A SQLModel database session for testing.
    """
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(engine: Engine) -> Generator[TestClient]:
    """Create a test client with database.

    Yields:
        TestClient: The test client for the FastAPI app.
    """

    def override_get_db():
        with Session(engine) as session:
            yield session

    from app.api.deps import get_db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
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

    puzzle = Puzzle(
        id=uuid.uuid4(),
        date=datetime.now(UTC).date(),
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

import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, delete

# Set test environment before importing app modules
os.environ["ENVIRONMENT"] = "test"

from app.core.config import settings
from app.core.db import engine, init_db
from app.main import app
from app.models import (
    GameSession,
    LeaderboardEntry,
    Player,
    Puzzle,
    QuartileCooldown,
    User,
)
from tests.utils.user import authentication_token_from_email
from tests.utils.utils import get_superuser_token_headers


@pytest.fixture(name="engine")
def engine_fixture() -> Generator:
    """Create a PostgreSQL engine for tests.

    Each test runs in its own transaction that gets rolled back,
    ensuring complete test isolation while using production-like
    PostgreSQL database with proper UUID support.

    Returns:
        Engine: SQLAlchemy engine for database operations.
    """
    # Use production PostgreSQL engine
    return engine


@pytest.fixture(name="session")
def session_fixture(engine) -> Generator[Session]:
    """Create a database session for tests.

    This fixture wraps each test in a transaction that gets rolled back
    after the test completes, ensuring complete test isolation.

    Args:
        engine: The database engine fixture.

    Yields:
        Session: SQLAlchemy session for database operations.
    """
    # Begin a transaction
    connection = engine.connect()
    transaction = connection.begin()

    # Create a session bound to this connection/transaction
    session = Session(bind=connection)

    # Initialize the database with the superuser
    init_db(session)

    yield session

    # Close the session and rollback the transaction to undo any changes
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(session: Session) -> Generator[TestClient]:
    """Create a test client that uses the test database session.

    This fixture overrides the get_db dependency to use the test session,
    ensuring each test uses its own isolated database transaction.

    Args:
        session: The test database session.

    Yields:
        TestClient: The test client for the FastAPI app.
    """

    def override_get_db() -> Generator[Session]:
        yield session

    from app.api.deps import get_db

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def superuser_token_headers(client: TestClient, session: Session) -> dict[str, str]:
    """Get superuser authentication headers.

    The session parameter ensures the database is initialized with the superuser
    before attempting to authenticate.

    Args:
        client: The test client.
        session: The test database session.

    Returns:
        Dictionary with authorization headers for authenticated requests.
    """
    _ = session  # Used for fixture side-effect (database initialization)
    return get_superuser_token_headers(client)


@pytest.fixture
def normal_user_token_headers(client: TestClient, session: Session) -> dict[str, str]:
    """Get normal user authentication headers.

    Args:
        client: The test client.
        session: The test database session.

    Returns:
        Dictionary with authorization headers for authenticated requests.
    """
    return authentication_token_from_email(client=client, email=settings.EMAIL_TEST_USER, session=session)


@pytest.fixture(scope="session", autouse=True)
def cleanup_test_data() -> None:
    """Clean up test data before all tests run.

    This fixture runs once before all tests to ensure any leftover
    test data from previous runs is cleaned up.
    """
    # Clean up any existing test data before running tests
    with Session(engine) as session:
        # Delete in correct order (respect foreign keys)
        session.exec(delete(GameSession))
        session.exec(delete(LeaderboardEntry))
        session.exec(delete(Player))
        session.exec(delete(QuartileCooldown))
        session.exec(delete(Puzzle))
        session.exec(delete(User))
        session.commit()

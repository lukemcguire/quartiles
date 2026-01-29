"""Pytest configuration and fixtures for backend tests."""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, delete

from app.core.db import engine, init_db
from app.main import app
from app.models import User


@pytest.fixture(scope="session", autouse=True)
def db() -> Generator[Session]:
    """Database session fixture for tests.

    Yields:
        Session: A database session for test use.
    """
    with Session(engine) as session:
        init_db(session)
        yield session
        statement = delete(User)
        session.exec(statement)
        session.commit()


@pytest.fixture(scope="module")
def client() -> Generator[TestClient]:
    """Test client fixture.

    Yields:
        TestClient: A FastAPI test client.
    """
    with TestClient(app) as c:
        yield c

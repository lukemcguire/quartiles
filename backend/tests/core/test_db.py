"""Tests for database initialization."""

from sqlmodel import Session, select

from app.core.config import settings
from app.core.db import init_db
from app.models import User


def test_init_db_creates_superuser(db: Session) -> None:
    """Test superuser creation when none exists."""
    # Clear existing superuser
    existing = db.exec(select(User).where(User.email == settings.FIRST_SUPERUSER)).first()
    if existing:
        db.delete(existing)
        db.commit()

    # Initialize DB should create superuser
    init_db(db)

    user = db.exec(select(User).where(User.is_superuser)).first()
    assert user is not None
    assert user.email == settings.FIRST_SUPERUSER


def test_init_db_skips_existing_superuser(db: Session) -> None:
    """Test no duplicate superuser created."""
    from sqlalchemy import func

    # First init
    init_db(db)
    count_before = db.exec(select(func.count()).select_from(User).where(User.is_superuser)).one()

    # Second init should not create another superuser
    init_db(db)
    count_after = db.exec(select(func.count()).select_from(User).where(User.is_superuser)).one()

    assert count_before == count_after

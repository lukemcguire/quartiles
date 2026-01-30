"""Database engine configuration and initialization."""

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, create_engine, select

from app import crud
from app.core.config import settings
from app.models import User, UserCreate

engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))


# make sure all SQLModel models are imported (app.models) before initializing DB
# otherwise, SQLModel might fail to initialize relationships properly
# for more details: https://github.com/fastapi/full-stack-fastapi-template/issues/28


def init_db(session: Session) -> None:
    """Initialize database with first superuser if it doesn't exist.

    Args:
        session: Database session.

    Note:
        Handles concurrent initialization gracefully (e.g., when running
        parallel tests with pytest-xdist) by catching IntegrityError
        if another worker already created the superuser.
    """
    # Tables should be created with Alembic migrations
    # But if you don't want to use migrations, create
    # the tables un-commenting the next lines
    # from sqlmodel import SQLModel

    # This works because the models are already imported and registered from app.models
    # SQLModel.metadata.create_all(engine)

    user = session.exec(select(User).where(User.email == settings.FIRST_SUPERUSER)).first()
    if not user:
        user_in = UserCreate(
            email=settings.FIRST_SUPERUSER,
            password=settings.FIRST_SUPERUSER_PASSWORD,
            is_superuser=True,
        )
        try:
            user = crud.create_user(session=session, user_create=user_in)
        except IntegrityError:
            # Handle race condition when multiple workers initialize concurrently
            # If another worker already created the superuser, just fetch it
            session.rollback()
            user = session.exec(select(User).where(User.email == settings.FIRST_SUPERUSER)).first()

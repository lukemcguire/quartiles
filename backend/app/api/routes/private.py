"""Private API routes for internal services (not exposed publicly)."""

from fastapi import APIRouter
from pydantic import BaseModel

from app.api.deps import SessionDep
from app.core.security import get_password_hash
from app.models import (
    User,
    UserPublic,
)

router = APIRouter(tags=["private"], prefix="/private")


class PrivateUserCreate(BaseModel):
    """Schema for creating a user via private API."""

    email: str
    password: str
    full_name: str
    is_verified: bool = False


@router.post("/users/")
def create_user(user_in: PrivateUserCreate, session: SessionDep) -> UserPublic:
    """Create a new user.

    Args:
        user_in: User creation data.
        session: Database session dependency.

    Returns:
        UserPublic: The created user's public information.
    """
    user = User(
        email=user_in.email,
        full_name=user_in.full_name,
        hashed_password=get_password_hash(user_in.password),
    )

    session.add(user)
    session.commit()

    return user  # type: ignore[return-value]

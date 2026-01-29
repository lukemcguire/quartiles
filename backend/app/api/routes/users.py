"""User management routes."""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import col, func, select

from app import crud
from app.api.deps import (
    CurrentUser,
    SessionDep,
    get_current_active_superuser,
)
from app.core.config import settings
from app.core.security import get_password_hash, verify_password
from app.models import (
    Message,
    UpdatePassword,
    User,
    UserCreate,
    UserPublic,
    UserRegister,
    UsersPublic,
    UserUpdate,
    UserUpdateMe,
)
from app.utils import generate_new_account_email, send_email

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "/",
    dependencies=[Depends(get_current_active_superuser)],
)
def read_users(session: SessionDep, skip: int = 0, limit: int = 100) -> UsersPublic:
    """Retrieve users.

    Args:
        session: Database session dependency.
        skip: Number of users to skip for pagination.
        limit: Maximum number of users to return.

    Returns:
        UsersPublic: List of users with total count.
    """
    count_statement = select(func.count()).select_from(User)
    count = session.exec(count_statement).one()

    statement = select(User).order_by(col(User.created_at).desc()).offset(skip).limit(limit)
    users = session.exec(statement).all()

    return UsersPublic(data=users, count=count)


@router.post("/", dependencies=[Depends(get_current_active_superuser)])
def create_user(*, session: SessionDep, user_in: UserCreate) -> UserPublic:
    """Create new user.

    Args:
        session: Database session dependency.
        user_in: User creation data.

    Returns:
        UserPublic: The created user's public information.

    Raises:
        HTTPException: If user with email already exists.
    """
    user = crud.get_user_by_email(session=session, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system.",
        )

    user = crud.create_user(session=session, user_create=user_in)
    if settings.emails_enabled and user_in.email:
        email_data = generate_new_account_email(
            email_to=user_in.email, username=user_in.email, password=user_in.password
        )
        send_email(
            email_to=user_in.email,
            subject=email_data.subject,
            html_content=email_data.html_content,
        )
    return user  # type: ignore[return-value]


@router.patch("/me")
def update_user_me(*, session: SessionDep, user_in: UserUpdateMe, current_user: CurrentUser) -> UserPublic:
    """Update own user.

    Args:
        session: Database session dependency.
        user_in: User update data.
        current_user: The currently authenticated user.

    Returns:
        UserPublic: The updated user's public information.

    Raises:
        HTTPException: If email already exists for another user.
    """
    if user_in.email:
        existing_user = crud.get_user_by_email(session=session, email=user_in.email)
        if existing_user and existing_user.id != current_user.id:
            raise HTTPException(status_code=409, detail="User with this email already exists")
    user_data = user_in.model_dump(exclude_unset=True)
    current_user.sqlmodel_update(user_data)
    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    return current_user  # type: ignore[return-value]


@router.patch("/me/password")
def update_password_me(*, session: SessionDep, body: UpdatePassword, current_user: CurrentUser) -> Message:
    """Update own password.

    Args:
        session: Database session dependency.
        body: Password update data with current and new password.
        current_user: The currently authenticated user.

    Returns:
        Message: Success message.

    Raises:
        HTTPException: If current password is incorrect or new password is same as current.
    """
    verified, _ = verify_password(body.current_password, current_user.hashed_password)
    if not verified:
        raise HTTPException(status_code=400, detail="Incorrect password")
    if body.current_password == body.new_password:
        raise HTTPException(status_code=400, detail="New password cannot be the same as the current one")
    hashed_password = get_password_hash(body.new_password)
    current_user.hashed_password = hashed_password
    session.add(current_user)
    session.commit()
    return Message(message="Password updated successfully")


@router.get("/me")
def read_user_me(current_user: CurrentUser) -> UserPublic:
    """Get current user.

    Args:
        current_user: The currently authenticated user.

    Returns:
        UserPublic: The current user's public information.
    """
    return current_user  # type: ignore[return-value]


@router.delete("/me")
def delete_user_me(session: SessionDep, current_user: CurrentUser) -> Message:
    """Delete own user.

    Args:
        session: Database session dependency.
        current_user: The currently authenticated user.

    Returns:
        Message: Success message.

    Raises:
        HTTPException: If user is a superuser (superusers cannot delete themselves).
    """
    if current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Super users are not allowed to delete themselves")
    session.delete(current_user)
    session.commit()
    return Message(message="User deleted successfully")


@router.post("/signup")
def register_user(session: SessionDep, user_in: UserRegister) -> UserPublic:
    """Create new user without the need to be logged in.

    Args:
        session: Database session dependency.
        user_in: User registration data.

    Returns:
        UserPublic: The created user's public information.

    Raises:
        HTTPException: If user with email already exists.
    """
    user = crud.get_user_by_email(session=session, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system",
        )
    user_create = UserCreate.model_validate(user_in)
    return crud.create_user(session=session, user_create=user_create)  # type: ignore[return-value]


@router.get("/{user_id}")
def read_user_by_id(user_id: uuid.UUID, session: SessionDep, current_user: CurrentUser) -> UserPublic:
    """Get a specific user by id.

    Args:
        user_id: The UUID of the user to retrieve.
        session: Database session dependency.
        current_user: The currently authenticated user.

    Returns:
        UserPublic: The requested user's public information.

    Raises:
        HTTPException: If user not found or current user lacks privileges.
    """
    user = session.get(User, user_id)
    if user == current_user:
        return user  # type: ignore[return-value]
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403,
            detail="The user doesn't have enough privileges",
        )
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user  # type: ignore[return-value]


@router.patch(
    "/{user_id}",
    dependencies=[Depends(get_current_active_superuser)],
)
def update_user(
    *,
    session: SessionDep,
    user_id: uuid.UUID,
    user_in: UserUpdate,
) -> UserPublic:
    """Update a user.

    Args:
        session: Database session dependency.
        user_id: The UUID of the user to update.
        user_in: User update data.

    Returns:
        UserPublic: The updated user's public information.

    Raises:
        HTTPException: If user not found or email already exists for another user.
    """
    db_user = session.get(User, user_id)
    if not db_user:
        raise HTTPException(
            status_code=404,
            detail="The user with this id does not exist in the system",
        )
    if user_in.email:
        existing_user = crud.get_user_by_email(session=session, email=user_in.email)
        if existing_user and existing_user.id != user_id:
            raise HTTPException(status_code=409, detail="User with this email already exists")

    return crud.update_user(session=session, db_user=db_user, user_in=user_in)  # type: ignore[return-value]


@router.delete("/{user_id}", dependencies=[Depends(get_current_active_superuser)])
def delete_user(session: SessionDep, current_user: CurrentUser, user_id: uuid.UUID) -> Message:
    """Delete a user.

    Args:
        session: Database session dependency.
        current_user: The currently authenticated superuser.
        user_id: The UUID of the user to delete.

    Returns:
        Message: Success message.

    Raises:
        HTTPException: If user not found or trying to delete themselves.
    """
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user == current_user:
        raise HTTPException(status_code=403, detail="Super users are not allowed to delete themselves")
    session.delete(user)
    session.commit()
    return Message(message="User deleted successfully")

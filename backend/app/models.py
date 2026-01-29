"""SQLModel database models and Pydantic schemas for API requests/responses."""

import uuid
from datetime import UTC, datetime

from pydantic import EmailStr
from sqlalchemy import DateTime
from sqlmodel import Field, SQLModel


def get_datetime_utc() -> datetime:
    """Get current UTC datetime.

    Returns:
        datetime: Current datetime in UTC timezone.
    """
    return datetime.now(UTC)


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

"""SQLModel database models and Pydantic schemas."""

import uuid

from pydantic import EmailStr
from sqlmodel import Field, SQLModel


# Shared properties
class UserBase(SQLModel):
    """Base user model with shared properties."""

    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on creation
class UserCreate(UserBase):
    """User creation schema."""

    password: str = Field(min_length=8, max_length=40)


class UserRegister(SQLModel):
    """User self-registration schema."""

    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=40)
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on update, all are optional
class UserUpdate(SQLModel):
    """User update schema."""

    email: EmailStr | None = Field(default=None, max_length=255)
    password: str | None = Field(default=None, min_length=8, max_length=40)
    full_name: str | None = Field(default=None, max_length=255)


class UserUpdateMe(SQLModel):
    """User self-update schema."""

    full_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = Field(default=None, max_length=255)


class UpdatePassword(SQLModel):
    """Password update schema."""

    current_password: str = Field(min_length=8, max_length=40)
    new_password: str = Field(min_length=8, max_length=40)


# Database model
class User(UserBase, table=True):
    """User database model."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str


# Properties to return via API
class UserPublic(UserBase):
    """User public response schema."""

    id: uuid.UUID


class UsersPublic(SQLModel):
    """List of users response schema."""

    data: list[UserPublic]
    count: int


# Generic message
class Message(SQLModel):
    """Generic message response schema."""

    message: str


# JSON payload containing access token
class Token(SQLModel):
    """Token response schema."""

    access_token: str
    token_type: str = "bearer"


# Contents of JWT token
class TokenPayload(SQLModel):
    """JWT token payload schema."""

    sub: str | None = None


class NewPassword(SQLModel):
    """New password schema for password reset."""

    token: str
    new_password: str = Field(min_length=8, max_length=40)

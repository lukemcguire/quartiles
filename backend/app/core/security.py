"""Security utilities for password hashing and JWT token management."""

from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher
from pwdlib.hashers.bcrypt import BcryptHasher

from app.core.config import settings

password_hash = PasswordHash(
    (
        Argon2Hasher(),
        BcryptHasher(),
    )
)


ALGORITHM = "HS256"


def create_access_token(subject: str | Any, expires_delta: timedelta) -> str:  # noqa: ANN401
    """Create a JWT access token with the given subject and expiration.

    Args:
        subject: The subject (user ID) to encode in the token.
        expires_delta: How long until the token expires.

    Returns:
        str: Encoded JWT token.
    """
    expire = datetime.now(UTC) + expires_delta
    to_encode = {"exp": expire, "sub": str(subject)}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)


def verify_password(plain_password: str, hashed_password: str) -> tuple[bool, str | None]:
    """Verify a password against its hash, returning updated hash if rehash needed.

    Args:
        plain_password: The plaintext password to verify.
        hashed_password: The hashed password to compare against.

    Returns:
        tuple[bool, str | None]: Tuple of (verified, updated_hash).
            verified is True if password matches.
            updated_hash contains new hash if password needs rehashing, None otherwise.
    """
    return password_hash.verify_and_update(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password using the configured password hasher.

    Args:
        password: The plaintext password to hash.

    Returns:
        str: The hashed password.
    """
    return password_hash.hash(password)

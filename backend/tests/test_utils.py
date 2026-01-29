"""Tests for utility functions."""


def test_verify_password_reset_token_valid() -> None:
    """Test valid token returns email."""
    from app.utils import generate_password_reset_token, verify_password_reset_token

    email = "test@example.com"
    token = generate_password_reset_token(email=email)
    result = verify_password_reset_token(token)

    assert result == email


def test_verify_password_reset_token_invalid() -> None:
    """Test invalid token returns None."""
    from app.utils import verify_password_reset_token

    result = verify_password_reset_token("invalid-token")
    assert result is None


def test_generate_password_reset_token() -> None:
    """Test token generation includes email and expiration."""
    import jwt

    from app.utils import generate_password_reset_token

    email = "test@example.com"
    token = generate_password_reset_token(email=email)

    # Verify token can be decoded with the actual settings
    from app.core.config import settings

    decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    assert decoded["sub"] == email
    assert "exp" in decoded
    assert "nbf" in decoded

"""Tests for configuration settings."""

import warnings

import pytest
from pydantic import ValidationError


def test_parse_cors_comma_separated() -> None:
    """Test parse_cors with comma-separated string."""
    from app.core.config import parse_cors

    result = parse_cors("http://localhost,a.com,https://example.com")
    assert result == ["http://localhost", "a.com", "https://example.com"]


def test_parse_cors_list() -> None:
    """Test parse_cors with list input."""
    from app.core.config import parse_cors

    input_list = ["http://localhost", "https://example.com"]
    result = parse_cors(input_list)
    assert result == input_list


def test_parse_cors_string_list() -> None:
    """Test parse_cors with JSON-like string list."""
    from app.core.config import parse_cors

    result = parse_cors('["http://localhost", "https://example.com"]')
    assert result == '["http://localhost", "https://example.com"]'


def test_check_default_secret_local_warning(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test warning in local env with changethis."""
    # Set environment variables for local environment with changethis
    monkeypatch.setenv("ENVIRONMENT", "local")
    monkeypatch.setenv("SECRET_KEY", "changethis")
    monkeypatch.setenv("POSTGRES_PASSWORD", "changethis")
    monkeypatch.setenv("FIRST_SUPERUSER_PASSWORD", "changethis")
    monkeypatch.setenv("PROJECT_NAME", "test")
    monkeypatch.setenv("POSTGRES_SERVER", "localhost")
    monkeypatch.setenv("POSTGRES_USER", "user")
    monkeypatch.setenv("POSTGRES_DB", "db")
    monkeypatch.setenv("FIRST_SUPERUSER", "admin@example.com")

    # Import Settings after setting environment variables
    # This will trigger the model_validator
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        from app.core.config import Settings

        # Create a new Settings instance to trigger validation
        Settings()  # type: ignore[call-arg]

        # Should produce warnings, not raise errors
        assert len(w) >= 3
        warning_messages = [str(warning.message) for warning in w]
        assert any("changethis" in msg for msg in warning_messages)


def test_check_default_secret_production_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test error in production with changethis."""
    # Set environment variables for production with changethis
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("SECRET_KEY", "changethis")
    monkeypatch.setenv("POSTGRES_PASSWORD", "changethis")
    monkeypatch.setenv("FIRST_SUPERUSER_PASSWORD", "changethis")
    monkeypatch.setenv("PROJECT_NAME", "test")
    monkeypatch.setenv("POSTGRES_SERVER", "localhost")
    monkeypatch.setenv("POSTGRES_USER", "user")
    monkeypatch.setenv("POSTGRES_DB", "db")
    monkeypatch.setenv("FIRST_SUPERUSER", "admin@example.com")

    # Import Settings after setting environment variables
    # This should raise ValidationError due to model_validator
    from app.core.config import Settings

    with pytest.raises(ValidationError, match="changethis"):
        Settings()  # type: ignore[call-arg]


def test_all_cors_origins_includes_frontend() -> None:
    """Test all_cors_origins includes frontend host."""
    from app.core.config import Settings

    s = Settings.model_construct(
        BACKEND_CORS_ORIGINS=["http://localhost:8000"],
        FRONTEND_HOST="http://localhost:5173",
        PROJECT_NAME="test",
        POSTGRES_SERVER="localhost",
        POSTGRES_USER="user",
        POSTGRES_DB="db",
        FIRST_SUPERUSER="admin@example.com",
        POSTGRES_PASSWORD="pass",  # noqa: S106
        FIRST_SUPERUSER_PASSWORD="pass",  # noqa: S106
        SECRET_KEY="test",  # noqa: S106
    )
    assert "http://localhost:5173" in s.all_cors_origins


def test_emails_enabled_true() -> None:
    """Test emails_enabled returns True when SMTP configured."""
    from app.core.config import Settings

    s = Settings.model_construct(
        SMTP_HOST="smtp.example.com",
        EMAILS_FROM_EMAIL="from@example.com",
        PROJECT_NAME="test",
        POSTGRES_SERVER="localhost",
        POSTGRES_USER="user",
        POSTGRES_DB="db",
        FIRST_SUPERUSER="admin@example.com",
        POSTGRES_PASSWORD="pass",  # noqa: S106
        FIRST_SUPERUSER_PASSWORD="pass",  # noqa: S106
        SECRET_KEY="test",  # noqa: S106
    )
    assert s.emails_enabled is True


def test_emails_enabled_false() -> None:
    """Test emails_enabled returns False when SMTP not configured."""
    from app.core.config import Settings

    s = Settings.model_construct(
        SMTP_HOST=None,
        EMAILS_FROM_EMAIL=None,
        PROJECT_NAME="test",
        POSTGRES_SERVER="localhost",
        POSTGRES_USER="user",
        POSTGRES_DB="db",
        FIRST_SUPERUSER="admin@example.com",
        POSTGRES_PASSWORD="pass",  # noqa: S106
        FIRST_SUPERUSER_PASSWORD="pass",  # noqa: S106
        SECRET_KEY="test",  # noqa: S106
    )
    assert s.emails_enabled is False


def test_parse_cors_invalid_value() -> None:
    """Test parse_cors raises ValueError for invalid value."""
    import pytest

    from app.core.config import parse_cors

    with pytest.raises(ValueError, match="invalid"):
        parse_cors({"invalid": "dict"})


def test_set_default_emails_from_name(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that EMAILS_FROM_NAME defaults to PROJECT_NAME when not set."""
    monkeypatch.setenv("PROJECT_NAME", "TestProject")
    monkeypatch.setenv("POSTGRES_SERVER", "localhost")
    monkeypatch.setenv("POSTGRES_USER", "user")
    monkeypatch.setenv("POSTGRES_DB", "db")
    monkeypatch.setenv("FIRST_SUPERUSER", "admin@example.com")
    monkeypatch.setenv("POSTGRES_PASSWORD", "pass")
    monkeypatch.setenv("FIRST_SUPERUSER_PASSWORD", "pass")
    monkeypatch.setenv("SECRET_KEY", "test")
    # Don't set EMAILS_FROM_NAME - should default to PROJECT_NAME

    from app.core.config import Settings

    s = Settings()  # type: ignore[call-arg]
    assert s.EMAILS_FROM_NAME == "TestProject"

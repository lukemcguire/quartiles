"""Tests for utility routes."""

from unittest.mock import patch

from fastapi.testclient import TestClient


def test_health_check_endpoint(client: TestClient) -> None:
    """Test GET /health-check/ returns True."""
    from app.core.config import settings

    r = client.get(f"{settings.API_V1_STR}/utils/health-check/")
    assert r.status_code == 200
    assert r.json() is True


def test_test_email_superuser(client: TestClient, superuser_token_headers: dict) -> None:
    """Test POST /test-email/ with superuser auth."""
    from app.core.config import settings

    with patch("app.api.routes.utils.send_email"):
        r = client.post(
            f"{settings.API_V1_STR}/utils/test-email/",
            params={"email_to": "test@example.com"},
            headers=superuser_token_headers,
        )
        assert r.status_code == 201


def test_test_email_unauthorized(client: TestClient) -> None:
    """Test /test-email/ without superuser returns 401."""
    from app.core.config import settings

    r = client.post(
        f"{settings.API_V1_STR}/utils/test-email/",
        params={"email_to": "test@example.com"},
    )
    assert r.status_code == 401

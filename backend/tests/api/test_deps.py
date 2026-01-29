"""Tests for API dependencies."""

from fastapi.testclient import TestClient


def test_get_current_user_invalid_token(client: TestClient) -> None:
    """Test 403 on invalid token."""
    from app.core.config import settings

    response = client.get(
        f"{settings.API_V1_STR}/users/me",
        headers={"Authorization": "Bearer invalid-token"},
    )
    assert response.status_code == 403


def test_get_current_user_missing_token(client: TestClient) -> None:
    """Test 401/403 on missing token."""
    from app.core.config import settings

    response = client.get(f"{settings.API_V1_STR}/users/me")
    # Should get 401 or 403 depending on OAuth2 scheme
    assert response.status_code in (401, 403)


def test_get_current_active_superuser_normal_user(client: TestClient, db) -> None:
    """Test normal user cannot access superuser endpoints."""
    from app import crud
    from app.core.config import settings
    from app.models import UserCreate
    from tests.utils.user import user_authentication_headers
    from tests.utils.utils import random_email, random_lower_string

    # Create normal user
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password, is_superuser=False)
    crud.create_user(session=db, user_create=user_in)

    headers = user_authentication_headers(client=client, email=email, password=password)

    # Try to access superuser-only endpoint
    response = client.post(
        f"{settings.API_V1_STR}/utils/test-email/",
        params={"email_to": "test@example.com"},
        headers=headers,
    )
    assert response.status_code == 403

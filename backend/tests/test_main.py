"""Tests for main application configuration."""

from unittest.mock import MagicMock


def test_custom_generate_unique_id() -> None:
    """Test custom route ID generation."""
    from fastapi.routing import APIRoute

    from app.main import custom_generate_unique_id

    # Create a mock route with tags
    mock_route = MagicMock(spec=APIRoute)
    mock_route.tags = ["users"]
    mock_route.name = "list"

    result = custom_generate_unique_id(mock_route)
    assert result == "users-list"


def test_app_includes_api_router() -> None:
    """Test app includes API router."""
    import app.main

    # Check that routes are registered
    routes = [getattr(route, "path", "") for route in app.main.app.routes]
    assert any("/api" in route for route in routes)

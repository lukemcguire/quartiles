"""Tests for API router configuration."""


def test_api_router_includes_login_router() -> None:
    """Test login router is always included."""
    import app.api.main

    routes = [getattr(route, "path", "") for route in app.api.main.api_router.routes]
    # Login router should always be included
    assert any("/login" in str(route) for route in routes)


def test_api_router_includes_users_router() -> None:
    """Test users router is always included."""
    import app.api.main

    routes = [getattr(route, "path", "") for route in app.api.main.api_router.routes]
    # Users router should always be included
    assert any("/users" in str(route) for route in routes)


def test_api_router_includes_utils_router() -> None:
    """Test utils router is always included."""
    import app.api.main

    routes = [getattr(route, "path", "") for route in app.api.main.api_router.routes]
    # Utils router should always be included
    assert any("/utils" in str(route) for route in routes)

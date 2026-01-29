"""Tests for initial_data script."""

from unittest.mock import MagicMock

import pytest


def test_init_creates_initial_data(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test init() calls init_db."""
    from app.initial_data import init

    mock_init_db = MagicMock()
    monkeypatch.setattr("app.initial_data.init_db", mock_init_db)

    init()

    mock_init_db.assert_called_once()


def test_main_logs_initialization(monkeypatch: pytest.MonkeyPatch, caplog) -> None:
    """Test main() logs properly."""
    from app.initial_data import main

    mock_init = MagicMock()
    monkeypatch.setattr("app.initial_data.init", mock_init)

    with caplog.at_level("INFO"):
        main()

    mock_init.assert_called_once()
    assert "Creating initial data" in caplog.text or "Initial data created" in caplog.text

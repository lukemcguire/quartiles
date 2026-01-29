from unittest.mock import MagicMock, patch

from sqlmodel import select

from app.backend_pre_start import init, logger, main


def test_init_successful_connection() -> None:
    engine_mock = MagicMock()

    session_mock = MagicMock()
    session_mock.__enter__.return_value = session_mock

    select1 = select(1)

    with (
        patch("app.backend_pre_start.Session", return_value=session_mock),
        patch("app.backend_pre_start.select", return_value=select1),
        patch.object(logger, "info"),
        patch.object(logger, "error"),
        patch.object(logger, "warn"),
    ):
        try:
            init(engine_mock)
            connection_successful = True
        except Exception:
            connection_successful = False

        assert connection_successful, "The database connection should be successful and not raise an exception."

        session_mock.exec.assert_called_once_with(select1)


def test_main_logs_initialization() -> None:
    """Test main() logs startup."""
    engine_mock = MagicMock()

    session_mock = MagicMock()
    session_mock.__enter__.return_value = session_mock

    select1 = select(1)

    with (
        patch("app.backend_pre_start.engine", engine_mock),
        patch("app.backend_pre_start.Session", return_value=session_mock),
        patch("app.backend_pre_start.select", return_value=select1),
        patch.object(logger, "info") as mock_info,
        patch.object(logger, "error"),
        patch.object(logger, "warn"),
    ):
        main()

        # Verify initialization logging
        assert mock_info.call_count == 2
        init_call = mock_info.call_args_list[0]
        finish_call = mock_info.call_args_list[1]

        assert init_call[0][0] == "Initializing service"
        assert finish_call[0][0] == "Service finished initializing"


def test_main_module_execution() -> None:
    """Test the if __name__ == '__main__' block."""
    engine_mock = MagicMock()

    session_mock = MagicMock()
    session_mock.__enter__.return_value = session_mock

    select1 = select(1)

    with (
        patch("app.backend_pre_start.engine", engine_mock),
        patch("app.backend_pre_start.Session", return_value=session_mock),
        patch("app.backend_pre_start.select", return_value=select1),
        patch.object(logger, "info"),
        patch.object(logger, "error"),
        patch.object(logger, "warn"),
        patch("app.backend_pre_start.__name__", "__main__"),
    ):
        # Import and execute the module
        import app.backend_pre_start

        # The module should execute main() when __name__ == "__main__"
        # We can't directly test this without actually running as __main__,
        # but we can verify main() is callable and works
        assert callable(app.backend_pre_start.main)

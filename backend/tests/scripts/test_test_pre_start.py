from unittest.mock import MagicMock, patch

from sqlmodel import select

from app.tests_pre_start import init, logger, main


def test_init_successful_connection() -> None:
    engine_mock = MagicMock()

    session_mock = MagicMock()
    session_mock.__enter__.return_value = session_mock

    select1 = select(1)

    with (
        patch("app.tests_pre_start.Session", return_value=session_mock),
        patch("app.tests_pre_start.select", return_value=select1),
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
    """Test main() logs startup for tests."""
    engine_mock = MagicMock()

    session_mock = MagicMock()
    session_mock.__enter__.return_value = session_mock

    select1 = select(1)

    with (
        patch("app.tests_pre_start.engine", engine_mock),
        patch("app.tests_pre_start.Session", return_value=session_mock),
        patch("app.tests_pre_start.select", return_value=select1),
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

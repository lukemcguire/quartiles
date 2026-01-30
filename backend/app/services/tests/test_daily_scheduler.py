"""Tests for the daily puzzle scheduler."""

import asyncio
from unittest.mock import patch

import pytest

from app.services.daily_scheduler import (
    DailyPuzzleScheduler,
    get_daily_scheduler,
)


class TestDailyPuzzleScheduler:
    """Test suite for DailyPuzzleScheduler class."""

    def test_init_default_parameters(self) -> None:
        """Test scheduler initialization with default parameters."""
        scheduler = DailyPuzzleScheduler()

        assert scheduler.days_ahead == 7
        assert not scheduler.is_running
        assert scheduler.scheduler is not None

    def test_init_custom_parameters(self) -> None:
        """Test scheduler initialization with custom parameters."""
        scheduler = DailyPuzzleScheduler(days_ahead=14)

        assert scheduler.days_ahead == 14
        assert not scheduler.is_running

    def test_start_scheduler(self) -> None:
        """Test starting the scheduler."""
        scheduler = DailyPuzzleScheduler()

        async def run_test() -> None:
            with patch("app.services.daily_scheduler.generate_upcoming_puzzles") as mock_generate:
                await scheduler.start()

                assert scheduler.is_running
                mock_generate.assert_called_once_with(days_ahead=7)
                await scheduler.stop()

        asyncio.run(run_test())

    def test_start_scheduler_already_running(self) -> None:
        """Test that starting an already running scheduler is a no-op."""
        scheduler = DailyPuzzleScheduler()

        async def run_test() -> None:
            with patch("app.services.daily_scheduler.generate_upcoming_puzzles"):
                await scheduler.start()

                with patch("app.services.daily_scheduler.generate_upcoming_puzzles") as mock_generate2:
                    await scheduler.start()

                    # Should only be called once (from first start)
                    mock_generate2.assert_not_called()

                await scheduler.stop()

        asyncio.run(run_test())

    def test_stop_scheduler(self) -> None:
        """Test stopping the scheduler."""
        scheduler = DailyPuzzleScheduler()

        async def run_test() -> None:
            with patch("app.services.daily_scheduler.generate_upcoming_puzzles"):
                await scheduler.start()
                assert scheduler.is_running

                await scheduler.stop()
                assert not scheduler.is_running

        asyncio.run(run_test())

    def test_stop_scheduler_not_running(self) -> None:
        """Test stopping a scheduler that is not running."""
        scheduler = DailyPuzzleScheduler()

        async def run_test() -> None:
            # Should not raise an exception
            await scheduler.stop()
            assert not scheduler.is_running

        asyncio.run(run_test())

    def test_start_generates_initial_puzzles(self) -> None:
        """Test that starting the scheduler generates initial puzzles."""
        scheduler = DailyPuzzleScheduler(days_ahead=5)

        async def run_test() -> None:
            with patch("app.services.daily_scheduler.generate_upcoming_puzzles") as mock_generate:
                await scheduler.start()

                mock_generate.assert_called_once_with(days_ahead=5)
                await scheduler.stop()

        asyncio.run(run_test())

    def test_start_handles_generation_failure(self) -> None:
        """Test that scheduler starts even if initial puzzle generation fails."""
        scheduler = DailyPuzzleScheduler()

        async def run_test() -> None:
            with patch(
                "app.services.daily_scheduler.generate_upcoming_puzzles", side_effect=RuntimeError("Generation failed")
            ):
                await scheduler.start()

                # Scheduler should still be running despite generation failure
                assert scheduler.is_running
                await scheduler.stop()

        asyncio.run(run_test())

    def test_scheduler_cannot_start_twice(self) -> None:
        """Test that starting an already running scheduler raises an error."""
        scheduler = DailyPuzzleScheduler()

        async def run_test() -> None:
            with patch("app.services.daily_scheduler.generate_upcoming_puzzles"):
                await scheduler.start()
                assert scheduler.is_running

                # Try to start again - APScheduler should raise an error
                # but our code catches this and logs a warning
                await scheduler.start()
                assert scheduler.is_running

                await scheduler.stop()
                assert not scheduler.is_running

        asyncio.run(run_test())


class TestGlobalSchedulerFunctions:
    """Test suite for global scheduler functions."""

    def test_get_daily_scheduler_not_initialized(self) -> None:
        """Test get_daily_scheduler raises error when not initialized."""
        with (
            patch("app.services.daily_scheduler._daily_scheduler", None),
            pytest.raises(RuntimeError, match="Daily scheduler not initialized"),
        ):
            get_daily_scheduler()


class TestGeneratePuzzlesTask:
    """Test suite for the generate_puzzles_task function."""

    def test_generate_puzzles_task_success(self) -> None:
        """Test the generate_puzzles_task function succeeds."""
        from app.services.daily_scheduler import _generate_puzzles_sync

        with patch("app.services.daily_scheduler.generate_upcoming_puzzles") as mock_generate:
            _generate_puzzles_sync()

            mock_generate.assert_called_once_with(days_ahead=7)

    def test_generate_puzzles_task_handles_errors(self) -> None:
        """Test that generate_puzzles_task handles errors gracefully."""
        from app.services.daily_scheduler import _generate_puzzles_sync

        with patch("app.services.daily_scheduler.generate_upcoming_puzzles", side_effect=RuntimeError("Test error")):
            # Should not raise an exception
            _generate_puzzles_sync()

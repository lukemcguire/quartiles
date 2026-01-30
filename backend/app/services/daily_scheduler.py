"""Daily puzzle scheduler service.

Manages automatic puzzle generation at midnight UTC using APScheduler.
Integrates with FastAPI lifespan for proper startup/shutdown.
"""

import asyncio
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.services.puzzle_scheduler import generate_upcoming_puzzles

logger = logging.getLogger(__name__)

# Default days ahead to pre-generate puzzles for
DEFAULT_GENERATION_DAYS_AHEAD = 7


def _generate_puzzles_sync() -> None:
    """Synchronous puzzle generation task.

    Called by scheduler at midnight UTC to pre-generate puzzles.
    Logs success/failure for monitoring.
    """
    try:
        logger.info("Starting scheduled puzzle generation...")
        generate_upcoming_puzzles(days_ahead=DEFAULT_GENERATION_DAYS_AHEAD)
        logger.info("Completed scheduled puzzle generation")
    except Exception:
        logger.exception("Failed to generate puzzles")


async def generate_puzzles_task() -> None:
    """Async wrapper for puzzle generation task.

    Called by scheduler at midnight UTC to pre-generate puzzles.
    Logs success/failure for monitoring.
    """
    # Run the sync function in an executor to avoid blocking
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _generate_puzzles_sync)


class DailyPuzzleScheduler:
    """Manages daily puzzle generation scheduling.

    Uses APScheduler to trigger puzzle generation at midnight UTC.
    Integrates with FastAPI lifespan for proper startup/shutdown.
    """

    def __init__(self, days_ahead: int = DEFAULT_GENERATION_DAYS_AHEAD) -> None:
        """Initialize the daily puzzle scheduler.

        Args:
            days_ahead: Number of days ahead to generate puzzles for.
        """
        self.days_ahead = days_ahead
        self.scheduler = AsyncIOScheduler(timezone="UTC")
        self._running = False

    async def start(self) -> None:
        """Start the scheduler and generate initial puzzles.

        Should be called during FastAPI startup event.
        """
        if self._running:
            logger.warning("Scheduler already running, skipping start")
            return

        logger.info("Starting daily puzzle scheduler...")

        # Schedule daily generation at midnight UTC
        self.scheduler.add_job(
            generate_puzzles_task,
            "cron",
            hour=0,
            minute=0,
            id="daily_puzzle_generation",
            replace_existing=True,
        )

        # Generate puzzles for today and upcoming days on startup
        logger.info("Generating initial puzzles on startup...")
        try:
            generate_upcoming_puzzles(days_ahead=self.days_ahead)
        except Exception:
            logger.exception("Failed to generate initial puzzles")

        self.scheduler.start()
        self._running = True
        logger.info("Daily puzzle scheduler started")

    async def stop(self) -> None:
        """Stop the scheduler.

        Should be called during FastAPI shutdown event.
        """
        if not self._running:
            return

        logger.info("Stopping daily puzzle scheduler...")
        self.scheduler.shutdown(wait=True)
        self._running = False
        logger.info("Daily puzzle scheduler stopped")

    @property
    def is_running(self) -> bool:
        """Check if the scheduler is currently running.

        Returns:
            True if scheduler is running, False otherwise.
        """
        return self._running


# Global scheduler instance
_daily_scheduler: DailyPuzzleScheduler | None = None


def get_daily_scheduler() -> DailyPuzzleScheduler:
    """Get the global daily scheduler instance.

    Returns:
        The global DailyPuzzleScheduler instance.

    Raises:
        RuntimeError: If scheduler has not been initialized.
    """
    if _daily_scheduler is None:
        msg = "Daily scheduler not initialized. Call start_daily_scheduler() first."
        raise RuntimeError(msg)
    return _daily_scheduler


async def start_daily_scheduler() -> DailyPuzzleScheduler:
    """Start the global daily scheduler instance.

    Should be called during FastAPI startup.

    Returns:
        The started DailyPuzzleScheduler instance.
    """
    global _daily_scheduler

    if _daily_scheduler is None:
        _daily_scheduler = DailyPuzzleScheduler()

    await _daily_scheduler.start()
    return _daily_scheduler


async def stop_daily_scheduler() -> None:
    """Stop the global daily scheduler instance.

    Should be called during FastAPI shutdown.
    """
    global _daily_scheduler

    if _daily_scheduler is not None:
        await _daily_scheduler.stop()
        _daily_scheduler = None

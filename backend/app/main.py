"""FastAPI application entry point with CORS and Sentry configuration."""

import logging
from contextlib import asynccontextmanager

import sentry_sdk
from fastapi import FastAPI
from fastapi.routing import APIRoute
from starlette.middleware.cors import CORSMiddleware

from app.api.main import api_router
from app.core.config import settings

logger = logging.getLogger(__name__)


def custom_generate_unique_id(route: APIRoute) -> str:
    """Generate unique operation IDs for OpenAPI routes.

    Args:
        route: FastAPI route to generate ID for.

    Returns:
        str: Unique ID in format "tag-name".
    """
    return f"{route.tags[0]}-{route.name}"


@asynccontextmanager
async def lifespan(_app: FastAPI) -> None:
    """Application lifespan manager.

    Handles startup and shutdown events for the FastAPI application.

    Yields:
        None
    """
    # Startup
    logger.info("Starting up application...")
    if settings.ENVIRONMENT != "test":
        from app.services.daily_scheduler import start_daily_scheduler

        await start_daily_scheduler()
        logger.info("Daily puzzle scheduler started")
    yield
    # Shutdown
    logger.info("Shutting down application...")
    if settings.ENVIRONMENT != "test":
        from app.services.daily_scheduler import stop_daily_scheduler

        await stop_daily_scheduler()
        logger.info("Daily puzzle scheduler stopped")


if settings.SENTRY_DSN and settings.ENVIRONMENT != "local":
    sentry_sdk.init(dsn=str(settings.SENTRY_DSN), enable_tracing=True)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    generate_unique_id_function=custom_generate_unique_id,
    lifespan=lifespan,
)

# Set all CORS enabled origins
if settings.all_cors_origins:
    app.add_middleware(
        CORSMiddleware,  # type: ignore[arg-type]
        allow_origins=settings.all_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix=settings.API_V1_STR)

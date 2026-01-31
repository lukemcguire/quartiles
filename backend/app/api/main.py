"""API router configuration and route registration."""

from fastapi import APIRouter

from app.api.routes import game, leaderboard, login, private, puzzle, users, utils
from app.core.config import settings

api_router = APIRouter()
api_router.include_router(login.router)
api_router.include_router(users.router)
api_router.include_router(utils.router)
api_router.include_router(game.router)
api_router.include_router(puzzle.router)
api_router.include_router(leaderboard.router)


if settings.ENVIRONMENT in ("local", "test"):
    api_router.include_router(private.router)

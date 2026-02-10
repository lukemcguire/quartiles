# Backend Dockerfile
# Multi-stage build for Python 3.13 with UV

FROM python:3.14-slim AS builder

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set environment variables
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

WORKDIR /app

# Install dependencies (workspace setup: root has uv.lock)
COPY uv.lock pyproject.toml ./
COPY backend/pyproject.toml ./backend/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

# Copy application code
COPY backend/ ./backend/

# Sync the project
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# Production stage
FROM python:3.14-slim

# Install curl for health checks
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app/backend

# Copy installed packages and application from workspace root
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/backend /app/backend

# Set PATH to use the virtual environment
ENV PATH="/app/.venv/bin:$PATH"

# Expose port
EXPOSE 8000

# Default command (can be overridden)
CMD ["fastapi", "run", "app/main.py", "--host", "0.0.0.0", "--port", "8000"]

# Backend Dockerfile
# Multi-stage build for Python 3.13 with UV

FROM python:3.13-slim AS builder

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set environment variables
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

WORKDIR /app/backend

# Install dependencies
COPY pyproject.toml ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

# Copy application code
COPY . .

# Sync the project
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# Production stage
FROM python:3.13-slim

WORKDIR /app/backend

# Copy installed packages and application
COPY --from=builder /app/backend/.venv /app/backend/.venv
COPY --from=builder /app/backend /app/backend

# Set PATH to use the virtual environment
ENV PATH="/app/backend/.venv/bin:$PATH"

# Expose port
EXPOSE 8000

# Default command (can be overridden)
CMD ["fastapi", "run", "app/main.py", "--host", "0.0.0.0", "--port", "8000"]

#!/usr/bin/env bash

# Pre-start script to run database migrations and initialize data

set -e

echo "Running database migrations..."
if [ -d "/app/backend" ]; then
  cd /app/backend
fi

# Run alembic migrations
python -m alembic upgrade head

echo "Initializing database..."
# Initialize database with first superuser
python <<'EOF'
from sqlmodel import Session
from app.core.db import engine, init_db

with Session(engine) as session:
    init_db(session)
    print("Database initialized successfully")
EOF

echo "Pre-start completed successfully"

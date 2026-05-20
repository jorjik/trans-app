#!/bin/sh
set -e

echo "=== TransApp API Entrypoint ==="
echo "Running database migrations..."
alembic upgrade head
echo "Migrations applied successfully"

echo "Starting uvicorn..."
exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}

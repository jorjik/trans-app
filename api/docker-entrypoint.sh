#!/bin/sh
set -e

echo "=== TransApp API Entrypoint ==="
echo "Running database migrations..."

# Пробуем накатить миграции; если не получается — пробуем stamp + upgrade
if ! alembic upgrade head 2>&1; then
    echo "First migration attempt failed, trying stamp + upgrade..."
    alembic stamp head
    alembic upgrade head
fi

echo "Migrations applied successfully"
echo "Starting uvicorn..."

exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}

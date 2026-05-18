#!/bin/sh
set -e

echo "=== TransApp API Entrypoint ==="
echo "Running database migrations..."
if alembic upgrade head; then
    echo "Migrations applied successfully"
else
    echo "WARNING: Migrations failed — starting without migrations."
    echo "Run 'alembic upgrade head' manually via Railway Shell."
fi

echo "Starting uvicorn..."
exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}

#!/bin/sh
set -e

echo "=== TransApp API Entrypoint ==="
echo "Running database migrations..."
if alembic upgrade head 2>/dev/null; then
    echo "Migrations applied successfully"
else
    echo "No Alembic migrations found — creating tables via Python..."
    python -c "
import asyncio
from db.session import engine, Base
import models

async def main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print('Tables created successfully')
    await engine.dispose()

asyncio.run(main())
"
fi

echo "Starting uvicorn..."
exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}

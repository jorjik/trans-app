FROM python:3.12-slim

WORKDIR /app

# tini для корректной обработки сигналов
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev tini \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Не-root пользователь
USER nobody

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["sh", "-c", "alembic upgrade head 2>/dev/null || (alembic stamp head && alembic upgrade head) && uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"

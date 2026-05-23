FROM python:3.12-slim

WORKDIR /app

# tini для корректной обработки сигналов (SIGTERM → graceful shutdown)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc tini \
    && rm -rf /var/lib/apt/lists/*

# Зависимости Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Код бота
COPY . .

# Не-root пользователь
USER nobody

# No HEALTHCHECK — bot runs in polling mode with no HTTP server.
# restart: unless-stopped in docker-compose handles crash recovery.

ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["python", "main.py"]

FROM python:3.12-slim

WORKDIR /app

# tini для корректной обработки сигналов (SIGTERM → graceful shutdown)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc tini \
    && rm -rf /var/lib/apt/lists/*

COPY bot/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY bot/ .

# Не-root пользователь для безопасности
USER nobody

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')" || exit 1

ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["python", "main.py"]

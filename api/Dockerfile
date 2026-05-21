FROM python:3.12-slim

WORKDIR /app

# tini для корректной обработки сигналов
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev tini \
    && rm -rf /var/lib/apt/lists/*

COPY api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY api/ .

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["/bin/sh", "docker-entrypoint.sh"]

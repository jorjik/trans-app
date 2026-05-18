# ⚠️ Этот Dockerfile НЕЛЬЗЯ менять/удалять — Railway ищет файл с именем "Dockerfile" в корне.
# Этот файл собирает API-сервис. Для деплоя bot/miniapp — переключите Config File
# в Railway UI на соответствующий .toml и добавьте сюда содержимое другого Dockerfile.

FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY api/ .

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]

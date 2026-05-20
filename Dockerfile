FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY bot/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY bot/ .

CMD ["python", "main.py"]

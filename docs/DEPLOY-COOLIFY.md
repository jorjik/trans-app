# Деплой TransApp на Coolify

Единый Docker Compose стек (`docker-compose.coolify.yml`) разворачивает все сервисы
приложения на одном сервере под управлением Coolify. Заменяет ручные SFTP-скрипты
из `scripts/deploy_*.py` и `docker-compose.prod.yml`.

## Архитектура

| Сервис   | Назначение                         | Порт (внутр.) | Публичный домен |
|----------|------------------------------------|---------------|-----------------|
| `db`     | PostgreSQL 16                      | 5432          | — (внутр.)      |
| `redis`  | Redis 7 (кэш)                      | 6379          | — (внутр.)      |
| `api`    | FastAPI (backend + webhooks)       | 8000          | `api.transapp.dev` |
| `bot`    | Telegram-бот (aiogram, polling)    | —             | — (нет HTTP)    |
| `miniapp`| Telegram Mini App (nginx + SPA)    | 80            | `transapp777.xyz` |

- **api** публикуется наружу ради платёжных вебхуков (`/webhook/monobank`,
  `/webhook/kofi`, `/webhook/paypal`) и админ-эндпоинтов.
- **bot** работает в режиме polling (long-polling к Telegram), HTTP-сервера нет,
  поэтому помечен `exclude_from_hc: true` и не участвует в health-проверке стека.
- **db/redis** доступны только внутри сети стека по именам сервисов.
- **miniapp** ходит в **api** напрямую (`http://api:8000`), а браузер пользователя —
  на `https://api.transapp.dev` (значение `VITE_API_URL`, запекается при сборке).

## Разовая настройка в Coolify
### 1. Подключить сервер и домены

1. **Servers → Create** → подключи VPS по SSH (Coolify сам поставит Docker + Traefik).
2. **Resources → Domains / Wildcard**: настрой DNS
   - `transapp777.xyz`  → A-запись на IP сервера
   - `api.transapp.dev` → A/CNAME на IP сервера
   SSL (Let's Encrypt) Coolify выпустит автоматически после деплоя.

### 2. Создать приложение

1. **Project → + New → Applications → Public Repository / GitHub App**
   (репозиторий `jorjik/trans-app`).
2. **Build Pack** → `Docker Compose`.
3. **Base Directory** → `/`
4. **Docker Compose Location** → `docker-compose.coolify.yml`
5. Сохрани → Coolify распарсит стек и покажет список сервисов.

### 3. Домены сервисов (Domains)

В настройках приложения, в блоке каждого сервиса:

- `miniapp` → `https://transapp777.xyz`
- `api`     → `https://api.transapp.dev`
- `db`, `redis`, `bot` → пусто (не публиковать)

> Не выставляй `ports:` в compose — Coolify роутит через Traefik по доменам.
> Если внутренний порт не 80, добавь суффикс: `https://api.transapp.dev:8000`.

### 4. Переменные окружения

Coolify создаст переменные из `${VAR}` в compose. Заполни их в **Environment Variables**
(значения `:?` обязательны — без них деплой заблокируется).

| Переменная | Обяз. | Комментарий |
|------------|:-----:|-------------|
| `POSTGRES_PASSWORD` | ✅ | Пароль БД. Сгенерируй надёжный. |
| `BOT_TOKEN` | ✅ | Токен Telegram-бота. |
| `BOT_INTERNAL_SECRET` | ✅ | Общий секрет bot↔api. Одинаковый в обоих. |
| `SECRET_KEY` | ✅ | JWT-секрет API (≥64 симв.). |
| `TELEGRAM_ID_ENCRYPTION_KEY` | ⭕ | AES-ключ (base64, 32 байта), если используется. |
| `VITE_API_URL` | ⭕ | Дефолт `https://api.transapp.dev`. |
| `CORS_ORIGINS` | ⭕ | JSON-массив. Дефолт `["https://transapp777.xyz"]`. |
| `MINI_APP_URL` | ⭕ | Ссылка на Mini App из бота. |
| `MONOBANK_TOKEN`, `KOFI_VERIFICATION_TOKEN`, `PAYPAL_CLIENT_ID/SECRET` | ⭕ | Платежи. |
| `DEEPL_API_KEY`, `GOOGLE_TRANSLATE_API_KEY`, `OPENAI_API_KEY` | ⭕ | Переводчики. |
| `ADMIN_TG_IDS` | ⭕ | JSON-массив ID админов. |
| `ENV`, `DEBUG`, `LOG_LEVEL`, `USE_REDIS`, лимиты квот | ⭕ | Есть безопасные дефолты. |
### 5. Первый деплой

**Deploy** → дождись green. Порядок старта: db+redis (healthy) → api (migrations
запускает entrypoint, потом uvicorn) → bot + miniapp.

Проверка:
```bash
# на сервере
docker ps --format 'table {{.Names}}\t{{.Status}}' | grep -i transapp
curl https://api.transapp.dev/health
curl -I https://transapp777.xyz
```

## Обновления

- **Автоматом**: включи Webhook в Git-провайдере (Settings → Source → Webhook URL)
  — push в ветку триггерит редеплой.
- **Вручную**: кнопка **Redeploy** в приложении.
- Изменения env — правь в Environment Variables, потом Redeploy.

Сборки кэшируются; миграции БД накатываются автоматически при старте `api`
(`docker-entrypoint.sh` → `alembic upgrade head`).

## Миграция данных с текущего сервера

Текущий прод (`193.168.175.92`, `/opt/trans-app`) → новый стек Coolify.

### PostgreSQL

```bash
# на старом сервере: дамп
docker exec trans-app-db-1 pg_dump -U postgres -d transapp -Fc -f /tmp/transapp.dump
docker cp trans-app-db-1:/tmp/transapp.dump ./transapp.dump

# скопируй файл на новый сервер, затем:
docker cp ./transapp.dump <coolify-db-container>:/tmp/
docker exec <coolify-db-container> pg_restore -U postgres -d transapp --clean --if-exists /tmp/transapp.dump
```

### Redis

Только кэш — переносить необязательно. Если нужно:
```bash
docker exec trans-app-redis-1 redis-cli BGSAVE
docker cp trans-app-redis-1:/data/dump.rdb ./dump.rdb
# останови redis в coolify-стеке, замени dump.rdb в volume, запусти обратно
```

### Переключение трафика (cutover)

1. Деплой стека на Coolify, домены указывают туда же (DNS ещё смотрит на старый сервер —
   это ок, Traefik получит сертификат после смены DNS).
2. Залей дамп БД (см. выше).
3. Смени DNS A-записи `transapp777.xyz` и `api.transapp.dev` на IP нового сервера.
4. Проверь: `/health`, Mini App, перевод, платёжный вебхук Monobank
   (URL вебхука у монобанка менять не нужно, если домен тот же).
5. Останови старый стек: `cd /opt/trans-app && docker compose -f docker-compose.prod.yml down`
   (volumes оставь на пару дней как бэкап).

## Бэкапы

Coolify → проект → `db` → **Backups**: включи Scheduled S3/disk-бэкапы Postgres.
Рекомендация: daily, retention 7–14 дней.

## Мониторинг и доступ

- Логи сервисов: приложение → **Logs** (или `docker logs` на сервере).
- Terminal в браузере: **Terminal** у нужного контейнера.
- Алерты: Servers → **Sentinel/Metrics** (CPU/RAM/disk).

## Что удалено / устарело

- `scripts/deploy_all.py`, `deploy_admin.py`, `deploy_locales.py` — ручной SFTP-деплой
  (и вшитые root-пароли — больше не нужны и небезопасны).
- `docker-compose.prod.yml` — заменён `docker-compose.coolify.yml`.
- `Dockerfile.bak` — мусор.

Локальная разработка не меняется: `infra/docker-compose.yml` как был для dev, так и остался.
## Управление через API (без UI)

Доступ хранится в переменных окружения пользователя (не в репозитории):

| Переменная | Значение |
|------------|----------|
| `COOLIFY_URL` | `https://jenya.website` |
| `COOLIFY_API_TOKEN` | токен из Coolify → Settings → API |
| `COOLIFY_APP_UUID` | `tpnridaztlzcfcyfmcipqdlq` (дефолт в скрипте) |

Хелпер `scripts/coolify.py` покрывает частые операции:

```bash
python scripts/coolify.py status                    # build pack, домены, статус
python scripts/coolify.py envs                      # список переменных
python scripts/coolify.py set KEY=value KEY2=value2 # задать переменные
python scripts/coolify.py domain miniapp https://transapp777.xyz
python scripts/coolify.py deploy                    # запустить редеплой
python scripts/coolify.py logs                      # логи последнего деплоя
python scripts/coolify.py dedupe                    # убрать дубли env
```

Особенности API, найденные на практике:
- переменные задаются только через `PATCH /applications/{uuid}/envs/bulk`
  (в `PATCH /applications/{uuid}` поле `environment_variables` запрещено);
- домены — `docker_compose_domains` массивом: `[{"name": "miniapp", "domain": "https://..."}]`;
- при каждом парсинге compose Coolify добавляет новые строки env → появляются дубли
  с пустыми значениями, их убирает `dedupe`.

Также подключён MCP-сервер Coolify (`~/.config/opencode/opencode.json`, секция `mcp.coolify`)
для чтения состояния: серверы, проекты, приложения, базы, сервисы.
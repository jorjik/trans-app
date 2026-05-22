# Deploy TransApp to Oracle Cloud Infrastructure (OCI)

## Архитектура деплоя

```
┌──────────────────────────────────────────────────┐
│              OCI Compute VM (Ampere A1)           │
│  ┌─────────┐  ┌──────────┐  ┌──────────────┐    │
│  │ Postgres│  │  Redis   │  │   Nginx :80   │    │
│  │ :5432   │  │  :6379   │  │   → :8000     │    │
│  └─────────┘  └──────────┘  │   → :3000     │    │
│                              └──────────────┘    │
│  ┌─────────┐  ┌──────────┐  ┌──────────────┐    │
│  │   API   │  │   Bot    │  │   Mini App   │    │
│  │  :8000  │  │          │  │    :3000     │    │
│  └─────────┘  └──────────┘  └──────────────┘    │
│                                                  │
│  Все сервисы — docker compose                    │
└──────────────────────────────────────────────────┘
```

## Шаг 1: Создание VM в OCI

1. Зайди в [Oracle Cloud Console](https://cloud.oracle.com) → Compute → Instances
2. Нажми **Create instance**
3. Заполни:
   - **Name**: `trans-app`
   - **Placement**: оставь по умолчанию
   - **Image**: `Ubuntu 24.04` (или 22.04)
   - **Shape**: `VM.Standard.A1.Flex` (Ampere, **Always Free**)
     - OCPU: 4, Memory: 24 GB — бесплатно
4. **Add SSH keys**: загрузи свой публичный ключ (`~/.ssh/id_rsa.pub`)
5. Разверни **Advanced options** → **Cloud-init script** → вставь содержимое `infra/oci/cloud-init.yaml`
6. Нажми **Create**

Через ~2 минуты VM будет готова. Cloud-init автоматически установит Docker, Docker Compose и настроит firewall.

## Шаг 2: Настройка OCI Security List (открытие портов)

По умолчанию OCI блокирует все входящие порты кроме 22 (SSH):

1. В OCI Console: **Networking** → **Virtual Cloud Networks** → выбери VCN
2. **Resources** → **Security Lists** → выбери Default Security List
3. **Add Ingress Rules**:

| Source Type | Source CIDR | IP Protocol | Dest Port | Description |
|---|---|---|---|---|
| CIDR | 0.0.0.0/0 | TCP | 80 | HTTP |
| CIDR | 0.0.0.0/0 | TCP | 443 | HTTPS |
| CIDR | 0.0.0.0/0 | TCP | 8000 | API |
| CIDR | 0.0.0.0/0 | TCP | 3000 | Mini App |

## Шаг 3: Настройка .env

Скопируй и заполни `.env` на основе `.env.example`:

```bash
cp .env.example .env
# Отредактируй .env — укажи BOT_TOKEN, DEEPL_API_KEY, и т.д.
```

**Важно для OCI:**
```env
DATABASE_URL=postgresql+asyncpg://postgres:<пароль>@db:5432/transapp
REDIS_URL=redis://redis:6379/0
ENV=production
MINI_APP_URL=http://<твой-ip>:3000
```

## Шаг 4: Деплой (Windows)

```powershell
.\deploy-oci.ps1 -Host <публичный-ip-твоей-vm> -KeyPath ~\.ssh\id_rsa
```

С флагами:
```powershell
.\deploy-oci.ps1 -Host 129.151.100.50             # деплой с пересборкой
.\deploy-oci.ps1 -Host 129.151.100.50 --skip-build # деплой без пересборки
.\deploy-oci.ps1 -Host 129.151.100.50 --logs       # деплой + логи
.\deploy-oci.ps1 -Host 129.151.100.50 --restart    # полный перезапуск
.\deploy-oci.ps1 -Host 129.151.100.50 --dry-run    # показать что будет сделано
```

## Шаг 4 (alt): Деплой (Linux/Mac)

```bash
chmod +x deploy-oci.sh
./deploy-oci.sh -h <публичный-ip> [-k ~/.ssh/id_rsa]
```

## Шаг 5: Проверка

```bash
# API health check
curl http://<ip>:8000/health

# Mini App
curl http://<ip>:3000

# Статус контейнеров
ssh ubuntu@<ip> "cd /opt/trans-app && docker compose -f docker-compose.prod.yml ps"
```

## Шаг 6: Настройка Telegram Webhook

```bash
curl "https://api.telegram.org/bot<BOT_TOKEN>/setWebhook?url=http://<ip>:8000/webhook"
```

Проверить статус:
```bash
curl "https://api.telegram.org/bot<BOT_TOKEN>/getWebhookInfo"
```

## Шаг 7 (рекомендуется): Nginx + HTTPS

На VM:
```bash
ssh ubuntu@<ip>
sudo apt-get install -y nginx certbot python3-certbot-nginx
```

Пример конфига `/etc/nginx/sites-available/trans-app`:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /webhook {
        proxy_pass http://localhost:8000/webhook;
        proxy_set_header Host $host;
    }

    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/trans-app /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
sudo certbot --nginx -d your-domain.com
```

После этого обнови Telegram webhook на HTTPS-URL.

## Полезные команды

```bash
# SSH на VM
ssh ubuntu@<ip>

# Смотреть логи
cd /opt/trans-app
docker compose -f docker-compose.prod.yml logs -f api
docker compose -f docker-compose.prod.yml logs -f bot

# Рестарт одного сервиса
docker compose -f docker-compose.prod.yml restart api

# Обновление с гита (если клонировал репо на VM)
git pull && docker compose -f docker-compose.prod.yml up -d --build

# Очистка старых образов
docker system prune -af
```

## Ресурсы OCI Always Free

| Ресурс | Лимит |
|---|---|
| Ampere A1 Compute | 4 OCPU, 24 GB RAM |
| Boot volume | 200 GB |
| Outbound traffic | 10 TB/мес |
| Public IPv4 | 1 бесплатный |

Для TransApp этого более чем достаточно.

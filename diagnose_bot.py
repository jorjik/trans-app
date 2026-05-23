import paramiko, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

host='193.168.175.92'
port=22
username='root'
password='5rvLB5!Q2kmoVpG#uX77fI7lwcGA3'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(host, port, username, password, timeout=15)

print("=== Container status ===")
stdin, stdout, stderr = ssh.exec_command("docker ps --filter name=bot --format '{{.Names}} {{.Status}} {{.Ports}}' 2>&1")
print(stdout.read().decode('utf-8', errors='replace').strip())

print("\n=== Check webhook info ===")
stdin, stdout, stderr = ssh.exec_command(
    'docker compose -f /opt/trans-app/docker-compose.prod.yml exec -T bot python -c "'
    'import asyncio, logging; logging.disable(logging.CRITICAL); '
    'from aiogram import Bot; '
    'import os; '
    'bot = Bot(token=os.environ[\"BOT_TOKEN\"]); '
    'info = asyncio.run(bot.get_webhook_info()); '
    'print(\"url:\", info.url); '
    'print(\"pending:\", info.pending_update_count); '
    'print(\"allowed_updates:\", info.allowed_updates)'
    '" 2>&1 | tail -15'
)
print(stdout.read().decode('utf-8', errors='replace').strip()[:1000])

print("\n=== Check resolve_used_update_types ===")
stdin, stdout, stderr = ssh.exec_command(
    'docker compose -f /opt/trans-app/docker-compose.prod.yml exec -T bot python -c "'
    'import asyncio, logging; logging.disable(logging.CRITICAL); '
    'from aiogram import Dispatcher; '
    'from handlers import start, translate, inline, errors, billing; '
    'dp = Dispatcher(); '
    'dp.include_router(errors.router); '
    'dp.include_router(billing.router); '
    'dp.include_router(start.router); '
    'dp.include_router(translate.router); '
    'dp.include_router(inline.router); '
    'print(\\\"Resolved:\\\", dp.resolve_used_update_types())'
    '" 2>&1 | tail -5'
)
print(stdout.read().decode('utf-8', errors='replace').strip()[:1000])

print("\n=== Check set_webhook (delete if exists) ===")
stdin, stdout, stderr = ssh.exec_command(
    'docker compose -f /opt/trans-app/docker-compose.prod.yml exec -T bot python -c "'
    'import asyncio, logging; logging.disable(logging.CRITICAL); '
    'from aiogram import Bot; '
    'import os; '
    'bot = Bot(token=os.environ[\"BOT_TOKEN\"]); '
    'info = asyncio.run(bot.get_webhook_info()); '
    'if info.url: '
    '    asyncio.run(bot.delete_webhook(drop_pending_updates=True)); '
    '    print(\"Webhook deleted!\"); '
    'else: '
    '    print(\"No webhook, all good\")'
    '" 2>&1 | tail -5'
)
print(stdout.read().decode('utf-8', errors='replace').strip()[:500])

ssh.close()

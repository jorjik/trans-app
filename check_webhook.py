import paramiko, io, sys, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

host='193.168.175.92'
port=22
username='root'
password='5rvLB5!Q2kmoVpG#uX77fI7lwcGA3'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(host, port, username, password, timeout=15)

# Check webhook status
print("=== Webhook check via bot API ===")
stdin, stdout, stderr = ssh.exec_command(
    "cd /opt/trans-app && docker compose -f docker-compose.prod.yml exec bot sh -c "
    '"python -c \\"import asyncio; from aiogram import Bot; from config import settings; import os; os.environ[\'BOT_TOKEN\'] = settings.bot_token; bot = Bot(token=settings.bot_token); print(asyncio.run(bot.get_webhook_info()))\\"" 2>&1 | tail -10'
)
stdout.channel.recv_exit_status()
print(stdout.read().decode('utf-8', errors='replace').strip()[:2000])

# Check ALL bot logs - full raw output
print("\n=== Full bot logs ===")
stdin, stdout, stderr = ssh.exec_command(
    "cd /opt/trans-app && docker compose -f docker-compose.prod.yml logs --tail=300 bot 2>&1"
)
stdout.channel.recv_exit_status()
out = stdout.read().decode('utf-8', errors='replace')
print(out[-5000:])

ssh.close()

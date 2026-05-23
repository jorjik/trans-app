import paramiko, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('193.168.175.92', 22, 'root', '5rvLB5!Q2kmoVpG#uX77fI7lwcGA3', timeout=15)

# Use Python inside container to check webhook via Telegram API
print("=== Webhook info ===")
stdin, stdout, stderr = ssh.exec_command(
    'docker compose -f /opt/trans-app/docker-compose.prod.yml exec -T bot python -c "'
    'import asyncio, logging, urllib.request, json, os; '
    'logging.disable(logging.CRITICAL); '
    'token = os.environ[\"BOT_TOKEN\"]; '
    'resp = urllib.request.urlopen(f\"https://api.telegram.org/bot{token}/getWebhookInfo\"); '
    'data = json.loads(resp.read()); '
    'print(json.dumps(data, indent=2))'
    '" 2>&1'
)
stdout.channel.recv_exit_status()
print(stdout.read().decode('utf-8', errors='replace').strip()[:2000])

# Delete webhook if exists
print("\n=== Delete webhook ===")
stdin2, stdout2, stderr2 = ssh.exec_command(
    'docker compose -f /opt/trans-app/docker-compose.prod.yml exec -T bot python -c "'
    'import asyncio, logging, urllib.request, json, os; '
    'logging.disable(logging.CRITICAL); '
    'token = os.environ[\"BOT_TOKEN\"]; '
    'resp = urllib.request.urlopen(f\"https://api.telegram.org/bot{token}/deleteWebhook?drop_pending_updates=true\"); '
    'data = json.loads(resp.read()); '
    'print(json.dumps(data, indent=2))'
    '" 2>&1'
)
stdout2.channel.recv_exit_status()
print(stdout2.read().decode('utf-8', errors='replace').strip()[:500])

# Restart bot after cleanup
print("\n=== Restart bot ===")
stdin3, stdout3, stderr3 = ssh.exec_command(
    'docker compose -f /opt/trans-app/docker-compose.prod.yml restart bot 2>&1'
)
stdout3.channel.recv_exit_status()
print(stdout3.read().decode('utf-8', errors='replace').strip()[:300])

ssh.close()

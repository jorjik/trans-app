import paramiko, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('193.168.175.92', 22, 'root', '5rvLB5!Q2kmoVpG#uX77fI7lwcGA3', timeout=15)

# Step 1: Check webhook info using API directly
print("=== Step 1: Get webhook info from Telegram ===")
stdin, stdout, stderr = ssh.exec_command(
    'curl -s "https://api.telegram.org/bot$(docker compose -f /opt/trans-app/docker-compose.prod.yml exec -T bot env | grep BOT_TOKEN | head -1 | cut -d= -f2)/getWebhookInfo"'
)
stdout.channel.recv_exit_status()
import time
time.sleep(2)
# Sometimes the command substitution is tricky, let's try differently
stdin2, stdout2, stderr2 = ssh.exec_command(
    'cd /opt/trans-app && docker compose -f docker-compose.prod.yml exec -T bot sh -c "curl -s \\"https://api.telegram.org/bot$BOT_TOKEN/getWebhookInfo\\"" 2>&1'
)
stdout2.channel.recv_exit_status()
print(stdout2.read().decode('utf-8', errors='replace').strip()[:2000])

# Step 2: If webhook exists, delete it
print("\n=== Step 2: Delete webhook if exists ===")
stdin3, stdout3, stderr3 = ssh.exec_command(
    'cd /opt/trans-app && docker compose -f docker-compose.prod.yml exec -T bot sh -c "curl -s \\"https://api.telegram.org/bot$BOT_TOKEN/deleteWebhook?drop_pending_updates=true\\"" 2>&1'
)
stdout3.channel.recv_exit_status()
print(stdout3.read().decode('utf-8', errors='replace').strip()[:500])

ssh.close()

import paramiko, io, sys, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('193.168.175.92', 22, 'root', '5rvLB5!Q2kmoVpG#uX77fI7lwcGA3', timeout=15)

# Get BOT_TOKEN
stdin, stdout, stderr = ssh.exec_command(
    'docker compose -f /opt/trans-app/docker-compose.prod.yml exec -T bot env | grep ^BOT_TOKEN= | cut -d= -f2'
)
token = stdout.read().decode('utf-8', errors='replace').strip()
print(f"BOT_TOKEN starts with: {token[:15]}...")

import urllib.request

# Step 1: Check full webhook info with allowed_updates
print("\n=== Full webhook info ===")
resp = urllib.request.urlopen(f"https://api.telegram.org/bot{token}/getWebhookInfo", timeout=10)
data = json.loads(resp.read())
print(json.dumps(data, indent=2))

# Step 2: Delete webhook with drop_pending_updates
print("\n=== Delete webhook ===")
resp = urllib.request.urlopen(f"https://api.telegram.org/bot{token}/deleteWebhook?drop_pending_updates=true", timeout=10)
print(json.loads(resp.read()))

# Step 3: Get updates (to see if callback queries are pending)
print("\n=== Get pending updates (offset=0, limit=10, timeout=0) ===")
allowed = ["callback_query", "message", "inline_query", "pre_checkout_query"]
params = {
    "offset": 0,
    "limit": 10,
    "timeout": 0,
    "allowed_updates": json.dumps(allowed)
}
url = f"https://api.telegram.org/bot{token}/getUpdates?" + "&".join(f"{k}={urllib.parse.quote(str(v))}" for k, v in params.items())
resp = urllib.request.urlopen(url, timeout=15)
data = json.loads(resp.read())
print(json.dumps(data, indent=2) if data else "No data")

ssh.close()

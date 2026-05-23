import paramiko, io, sys, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('193.168.175.92', 22, 'root', '5rvLB5!Q2kmoVpG#uX77fI7lwcGA3', timeout=15)

# Get BOT_TOKEN from docker env
stdin, stdout, stderr = ssh.exec_command(
    'docker compose -f /opt/trans-app/docker-compose.prod.yml exec -T bot env | grep ^BOT_TOKEN= | cut -d= -f2'
)
token = stdout.read().decode('utf-8', errors='replace').strip()
stdin, stdout, stderr = ssh.exec_command(
    'docker compose -f /opt/trans-app/docker-compose.prod.yml exec -T bot env | grep ^BACKEND_API_URL='
)
api_url = stdout.read().decode('utf-8', errors='replace').strip()
print(f"BOT_TOKEN starts with: {token[:10]}...")
print(f"BACKEND_API_URL: {api_url}")

# Check webhook on host machine using urllib
import urllib.request
if token:
    print("\n=== Webhook info ===")
    try:
        resp = urllib.request.urlopen(f"https://api.telegram.org/bot{token}/getWebhookInfo", timeout=10)
        data = json.loads(resp.read())
        print(json.dumps(data, indent=2))
    except Exception as e:
        print(f"Error: {e}")
    
    # If webhook exists, delete it
    if data.get('result', {}).get('url'):
        print("\n=== Deleting webhook ===")
        resp2 = urllib.request.urlopen(f"https://api.telegram.org/bot{token}/deleteWebhook?drop_pending_updates=true", timeout=10)
        print(json.loads(resp2.read()))
else:
    print("Could not get BOT_TOKEN")

ssh.close()

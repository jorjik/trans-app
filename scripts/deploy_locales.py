"""Deploy all locale and language changes to the production server."""
import paramiko
import os
import time
import sys

sys.stdout.reconfigure(encoding='utf-8')

HOST = '193.168.175.92'
PORT = 22
USER = 'root'
PASSWORD = '5rvLB5!Q2kmoVpG#uX77fI7lwcGA3'

PROJECT_ROOT = 'C:/dev/tg/trans-app'
REMOTE_ROOT = '/opt/trans-app'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, PORT, USER, PASSWORD, timeout=15)
sftp = ssh.open_sftp()

def run(cmd, timeout=120):
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    stdout.channel.recv_exit_status()
    out = stdout.read().decode('utf-8', errors='replace').strip()
    err = stderr.read().decode('utf-8', errors='replace').strip()
    return out if out else err

def put_file(local, remote):
    local_path = os.path.join(PROJECT_ROOT, local)
    remote_path = os.path.join(REMOTE_ROOT, remote)
    sftp.put(local_path, remote_path)
    print(f'  ✅ {remote}')

# === 1. Upload bot locale files ===
print('=== Uploading bot locale files ===')
locale_files = ['de.json', 'fr.json', 'es.json', 'it.json', 'pt.json', 'pl.json', 'tr.json']
for f in locale_files:
    put_file(f'bot/locales/{f}', f'bot/locales/{f}')

# === 2. Upload bot Python files ===
print()
print('=== Uploading bot Python files ===')
bot_files = [
    'utils/languages.py',
    'keyboards/inline_kb.py',
    'handlers/start.py',
    'middlewares/throttle.py',
]
for f in bot_files:
    put_file(f'bot/{f}', f'bot/{f}')

# === 3. Upload API Python files ===
print()
print('=== Uploading API Python files ===')
api_files = [
    'routers/internal.py',
    'services/auth.py',
    'services/user_service.py',
]
for f in api_files:
    put_file(f'api/{f}', f'api/{f}')

# === 4. Upload miniapp dist ===
print()
print('=== Uploading miniapp dist ===')
# First create dist/assets dir on remote
run('mkdir -p /opt/trans-app/miniapp/dist/assets')

# Upload index.html
put_file('miniapp/dist/index.html', 'miniapp/dist/index.html')

# Upload assets
import glob
assets = glob.glob(os.path.join(PROJECT_ROOT, 'miniapp/dist/assets/*'))
for asset_path in assets:
    filename = os.path.basename(asset_path)
    remote_path = f'miniapp/dist/assets/{filename}'
    sftp.put(asset_path, os.path.join(REMOTE_ROOT, remote_path))
    print(f'  ✅ miniapp/dist/assets/{filename}')

sftp.close()

# === 5. Rebuild and restart bot container ===
print()
print('=== Rebuilding bot container ===')
out = run('cd /opt/trans-app && docker compose -f docker-compose.prod.yml build bot 2>&1')
print(out)

print()
print('=== Restarting bot container ===')
out = run('cd /opt/trans-app && docker compose -f docker-compose.prod.yml up -d --no-deps bot 2>&1')
print(out)

# === 6. Restart API container ===
print()
print('=== Restarting API container ===')
out = run('cd /opt/trans-app && docker compose -f docker-compose.prod.yml up -d --no-deps api 2>&1')
print(out)

print()
print('Waiting 10 seconds...')
time.sleep(10)

print()
print('=== Checking containers ===')
out = run('docker ps --format "{{.Names}}\t{{.Status}}" 2>&1 | grep trans-app')
print(out)

print()
print('=== Checking bot logs (last 5 lines) ===')
out = run('docker logs trans-app-bot-1 2>&1 | tail -5')
print(out)

print()
print('=== Checking API health ===')
out = run('curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health 2>&1')
print(f'  Health check: {out}')

ssh.close()
print()
print('✅ Deployment complete!')

"""Deploy all locale and language changes to the production server."""
import paramiko
import os
import glob
import time
import sys

sys.stdout.reconfigure(encoding='utf-8')

HOST = '193.168.175.92'
PORT = 22
USER = 'root'
PASSWORD = '5rvLB5!Q2kmoVpG#uX77fI7lwcGA3'

PROJECT_ROOT = r'C:\dev\tg\trans-app'
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

def put_file(local_rel, remote_rel):
    local_path = os.path.join(PROJECT_ROOT, local_rel)
    remote_path = REMOTE_ROOT + '/' + remote_rel.replace(os.sep, '/')
    if not os.path.exists(local_path):
        print(f'  MISSING: {local_rel}')
        return False
    local_size = os.path.getsize(local_path)
    try:
        sftp.put(local_path, remote_path)
        print(f'  OK {remote_rel} ({local_size} bytes)')
        return True
    except Exception as e:
        print(f'  FAIL {remote_rel}: {e}')
        return False

# === 1. Upload bot locale files ===
print('=== 1. Uploading locale files ===')
all_locales = ['en.json', 'ru.json', 'uk.json', 'de.json', 'fr.json', 'es.json', 'it.json', 'pt.json', 'pl.json', 'tr.json']
for f in all_locales:
    put_file('bot/locales/' + f, 'bot/locales/' + f)

# === 2. Upload bot Python files ===
print()
print('=== 2. Uploading bot Python files ===')
for f in ['utils/languages.py', 'keyboards/inline_kb.py', 'handlers/start.py', 'handlers/admin.py', 'handlers/billing.py', 'services/billing.py', 'middlewares/throttle.py']:
    put_file('bot/' + f, 'bot/' + f)

# === 3. Upload API Python files ===
print()
print('=== 3. Uploading API Python files ===')
for f in ['routers/internal.py', 'routers/admin.py', 'routers/kofi.py', 'routers/webhook.py', 'routers/__init__.py', 'routers/billing.py', 'services/auth.py', 'services/user_service.py', 'services/kofi.py', 'services/paypal.py', 'services/monobank.py', 'models/__init__.py', 'core/config.py', 'requirements.txt']:
    put_file('api/' + f, 'api/' + f)

# === 4. Upload API database migration files ===
print()
print('=== 4. Uploading API database migration files ===')
migrations = sorted(os.listdir(os.path.join(PROJECT_ROOT, 'api/db/versions')))
for f in migrations:
    if f.endswith('.py'):
        put_file(f'api/db/versions/{f}', f'api/db/versions/{f}')

# === 5. Upload miniapp dist ===
print()
print('=== 5. Uploading miniapp dist ===')
put_file('miniapp/dist/index.html', 'miniapp/dist/index.html')
assets = glob.glob(os.path.join(PROJECT_ROOT, 'miniapp/dist/assets/*'))
for asset_path in assets:
    filename = os.path.basename(asset_path)
    put_file('miniapp/dist/assets/' + filename, 'miniapp/dist/assets/' + filename)

sftp.close()

# === 6. Rebuild API (requirements.txt changed — ecdsa added) ===
print()
print('=== 6. Rebuilding API container ===')
out = run('cd /opt/trans-app && docker compose -f docker-compose.prod.yml build api 2>&1')
print(out[-1500:] if len(out) > 1500 else out)

# === 7. Rebuild bot ===
print()
print('=== 7. Rebuilding bot container ===')
out = run('cd /opt/trans-app && docker compose -f docker-compose.prod.yml build bot 2>&1')
print(out[-1500:] if len(out) > 1500 else out)

# === 8. Restart containers ===
print()
print('=== 8. Restarting API ===')
out = run('cd /opt/trans-app && docker compose -f docker-compose.prod.yml up -d --no-deps api 2>&1')
print(out)

print()
print('=== 9. Restarting bot ===')
out = run('cd /opt/trans-app && docker compose -f docker-compose.prod.yml up -d --no-deps bot 2>&1')
print(out)

# === 10. Wait and verify ===
print()
print('Waiting 10 seconds...')
time.sleep(10)

print()
print('=== 10. Container status ===')
out = run("docker ps --format '{{.Names}}\t{{.Status}}' | grep trans-app")
print(out)

print()
print('=== 11. Bot logs (last 5) ===')
out = run('docker logs trans-app-bot-1 2>&1 | tail -5')
print(out)

print()
print('=== 12. API health ===')
out = run('curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health 2>&1')
print('  Health:', out)

print()
print('=== 13. API logs (last 3) ===')
out = run('docker logs trans-app-api-1 2>&1 | tail -3')
print(out)

ssh.close()
print()
print('DONE!')

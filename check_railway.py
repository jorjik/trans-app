import paramiko, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('193.168.175.92', 22, 'root', '5rvLB5!Q2kmoVpG#uX77fI7lwcGA3', timeout=15)

# Check VITE_API_URL in env
print("=== VITE_API_URL ===")
stdin, stdout, stderr = ssh.exec_command('grep VITE_API_URL /opt/trans-app/.env || echo NOT_IN_ENV')
print(stdout.read().decode('utf-8', errors='replace').strip())

# Check API URL in built JS
print("\n=== Built JS API URLs ===")
stdin, stdout, stderr = ssh.exec_command(
    "docker compose -f /opt/trans-app/docker-compose.prod.yml exec -T miniapp grep -oh 'https\\?://[^\"'\"' ]*railway[^\"'\"' ]*' /usr/share/nginx/html/ 2>&1 | head -10"
)
print(stdout.read().decode('utf-8', errors='replace').strip()[:1000])

# Check MINI_APP_URL in bot
print("\n=== MINI_APP_URL in bot ===")
stdin, stdout, stderr = ssh.exec_command(
    'docker compose -f /opt/trans-app/docker-compose.prod.yml exec -T bot env | grep MINI_APP_URL'
)
print(stdout.read().decode('utf-8', errors='replace').strip()[:500])

# Check nginx proxy config
print("\n=== Nginx proxy config ===")
stdin, stdout, stderr = ssh.exec_command('cat /etc/nginx/sites-enabled/default 2>&1 || cat /etc/nginx/conf.d/default.conf 2>&1 || find /etc/nginx -name "*.conf" -exec echo "--- {} ---" \\; -exec cat {} \\; 2>&1 | head -80')
print(stdout.read().decode('utf-8', errors='replace').strip()[:3000])

ssh.close()

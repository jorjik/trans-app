import paramiko, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('193.168.175.92', 22, 'root', '5rvLB5!Q2kmoVpG#uX77fI7lwcGA3', timeout=15)

# Check VITE_API_URL in .env
print("=== VITE_API_URL in .env ===")
stdin, stdout, stderr = ssh.exec_command('grep VITE_API_URL /opt/trans-app/.env 2>&1 || echo "NOT SET"')
print(stdout.read().decode('utf-8', errors='replace').strip())

# Check inside miniapp container for Railway references
print("\n=== Railway refs in miniapp container ===")
stdin2, stdout2, stderr2 = ssh.exec_command(
    'docker compose -f /opt/trans-app/docker-compose.prod.yml exec -T miniapp grep -r "railway\\|railway.app" /usr/share/nginx/html/ 2>&1 | head -20 || echo "No Railway refs in html"'
)
print(stdout2.read().decode('utf-8', errors='replace').strip()[:1000])

# Check built JS files for API URL
print("\n=== API URL in built JS ===")
stdin3, stdout3, stderr3 = ssh.exec_command(
    'docker compose -f /opt/trans-app/docker-compose.prod.yml exec -T miniapp grep -roh "https\\?://[^/]*railway[^\"\\'\"']*" /usr/share/nginx/html/ 2>&1 | head -10 || echo "No railway URLs"'
)
print(stdout3.read().decode('utf-8', errors='replace').strip()[:1000])

# Check the built config
print("\n=== Check VITE_API_URL inside built files ===")
stdin4, stdout4, stderr4 = ssh.exec_command(
    'docker compose -f /opt/trans-app/docker-compose.prod.yml exec -T miniapp grep -r "api" /usr/share/nginx/html/assets/ 2>&1 | grep -v "\.json" | head -20'
)
print(stdout4.read().decode('utf-8', errors='replace').strip()[:2000])

# Also check bot main menu button URL
print("\n=== MINI_APP_URL inside bot container ===")
stdin5, stdout5, stderr5 = ssh.exec_command(
    'docker compose -f /opt/trans-app/docker-compose.prod.yml exec -T bot env | grep MINI_APP_URL 2>&1'
)
print(stdout5.read().decode('utf-8', errors='replace').strip()[:500])

ssh.close()

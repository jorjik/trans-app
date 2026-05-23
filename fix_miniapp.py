import paramiko, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('193.168.175.92', 22, 'root', '5rvLB5!Q2kmoVpG#uX77fI7lwcGA3', timeout=15)

# Find all nginx configs
print("=== Find nginx configs ===")
stdin, stdout, stderr = ssh.exec_command('find /etc/nginx -name "*.conf" -type f 2>&1')
for line in stdout.read().decode('utf-8', errors='replace').strip().split('\n'):
    print(f"  {line}")

print("\n=== Active nginx config excerpts ===")
stdin, stdout, stderr = ssh.exec_command(
    'find /etc/nginx -name "*.conf" -type f -exec echo "--- {} ---" \\; -exec grep -l "proxy_pass\\|server_name\\|listen" {} \\; 2>&1 | head -20'
)
print(stdout.read().decode('utf-8', errors='replace').strip()[:500])

print("\n=== Full nginx config with proxy ===")
stdin, stdout, stderr = ssh.exec_command(
    'grep -r "proxy_pass\\|server_name\\|listen" /etc/nginx/ 2>&1 | head -30'
)
print(stdout.read().decode('utf-8', errors='replace').strip()[:2000])

print("\n=== Test miniapp via nginx ===")
stdin, stdout, stderr = ssh.exec_command(
    'curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1/miniapp/ 2>&1'
)
print("HTTP /miniapp/: ", stdout.read().decode('utf-8', errors='replace').strip())

# Check local .env for VITE_API_URL
print("\n=== Local VITE_API_URL ===")
stdin, stdout, stderr = ssh.exec_command(
    'grep VITE_API_URL /opt/trans-app/.env 2>&1; grep VITE_API_URL /opt/trans-app/miniapp/.env 2>&1 || echo "not found"'
)
print(stdout.read().decode('utf-8', errors='replace').strip())

ssh.close()

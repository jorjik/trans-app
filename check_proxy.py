import paramiko, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('193.168.175.92', 22, 'root', '5rvLB5!Q2kmoVpG#uX77fI7lwcGA3', timeout=15)

print("=== Nginx on host ===")
stdin, stdout, stderr = ssh.exec_command('which nginx 2>&1 && nginx -t 2>&1 || echo "nginx not found"')
print(stdout.read().decode('utf-8', errors='replace').strip()[:500])

print("\n=== Check for other proxy services ===")
stdin2, stdout2, stderr2 = ssh.exec_command(
    'ss -tlnp | grep -E "80|443|3000|8000" | head -20'
)
print(stdout2.read().decode('utf-8', errors='replace').strip()[:1000])

print("\n=== Check iptables ===")
stdin3, stdout3, stderr3 = ssh.exec_command('iptables -t nat -L -n 2>&1 | head -20')
print(stdout3.read().decode('utf-8', errors='replace').strip()[:1000])

print("\n=== Check if xip.io domain resolves ===")
stdin4, stdout4, stderr4 = ssh.exec_command(
    'getent hosts 193-168-175-92.eu-ml-cloud-xip.com 2>&1 || nslookup 193-168-175-92.eu-ml-cloud-xip.com 2>&1 || echo "dns check failed"'
)
print(stdout4.read().decode('utf-8', errors='replace').strip()[:500])

print("\n=== Check for existing proxy configs ===")
stdin5, stdout5, stderr5 = ssh.exec_command(
    'ls -la /etc/nginx/ 2>&1; echo "---"; cat /etc/nginx/sites-enabled/* 2>&1 | head -50 || echo "no sites-enabled"'
)
print(stdout5.read().decode('utf-8', errors='replace').strip()[:2000])

print("\n=== Test miniapp locally ===")
stdin6, stdout6, stderr6 = ssh.exec_command('curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:3000/ 2>&1')
print("Local miniapp status:", stdout6.read().decode('utf-8', errors='replace').strip())

ssh.close()

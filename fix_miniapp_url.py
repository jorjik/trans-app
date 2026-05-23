import paramiko, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('193.168.175.92', 22, 'root', '5rvLB5!Q2kmoVpG#uX77fI7lwcGA3', timeout=15)

# Check current .env
print("=== Current .env (relevant vars) ===")
stdin, stdout, stderr = ssh.exec_command(
    'grep -E "MINI_APP_URL|RAILWAY|DOMAIN" /opt/trans-app/.env 2>&1 || echo "No matches"'
)
stdout.channel.recv_exit_status()
print(stdout.read().decode('utf-8', errors='replace').strip())

# Check nginx config for domain
print("\n=== Nginx config ===")
stdin2, stdout2, stderr2 = ssh.exec_command(
    'cat /opt/trans-app/miniapp/nginx.conf 2>&1'
)
stdout2.channel.recv_exit_status()
print(stdout2.read().decode('utf-8', errors='replace').strip()[:1000])

# Check what port miniapp is on
print("\n=== Miniapp port binding ===")
stdin3, stdout3, stderr3 = ssh.exec_command(
    'docker port trans-app-miniapp-1 2>&1 || docker inspect trans-app-miniapp-1 --format="{{range $p, $c := .NetworkSettings.Ports}}{{$p}} -> {{(index $c 0).HostPort}}{{\"\\n\"}}{{end}}" 2>&1'
)
stdout3.channel.recv_exit_status()
print(stdout3.read().decode('utf-8', errors='replace').strip()[:500])

# Check docker-compose for miniapp config
print("\n=== Docker compose miniapp config ===")
stdin4, stdout4, stderr4 = ssh.exec_command(
    'grep -A 20 "miniapp:" /opt/trans-app/docker-compose.prod.yml 2>&1'
)
stdout4.channel.recv_exit_status()
print(stdout4.read().decode('utf-8', errors='replace').strip()[:2000])

ssh.close()

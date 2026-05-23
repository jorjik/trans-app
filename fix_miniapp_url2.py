import paramiko, io, sys, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('193.168.175.92', 22, 'root', '5rvLB5!Q2kmoVpG#uX77fI7lwcGA3', timeout=15)

# Update MINI_APP_URL in .env
print("=== Current MINI_APP_URL ===")
stdin, stdout, stderr = ssh.exec_command('grep MINI_APP_URL /opt/trans-app/.env')
print(stdout.read().decode('utf-8', errors='replace').strip())

print("\n=== Update MINI_APP_URL ===")
stdin, stdout, stderr = ssh.exec_command(
    'sed -i "s|MINI_APP_URL=.*|MINI_APP_URL=https://193-168-175-92.eu-ml-cloud-xip.com/|" /opt/trans-app/.env'
)
print(stdout.read().decode('utf-8', errors='replace').strip())

print("\n=== Verify ===")
stdin, stdout, stderr = ssh.exec_command('grep MINI_APP_URL /opt/trans-app/.env')
print(stdout.read().decode('utf-8', errors='replace').strip())

# Restart bot to pick up new URL
print("\n=== Restart bot ===")
stdin, stdout, stderr = ssh.exec_command('cd /opt/trans-app && docker compose -f docker-compose.prod.yml restart bot')
stdout.channel.recv_exit_status()
print(stdout.read().decode('utf-8', errors='replace').strip()[:300])

time.sleep(3)

print("\n=== Bot status ===")
stdin, stdout, stderr = ssh.exec_command('cd /opt/trans-app && docker compose -f docker-compose.prod.yml ps bot')
print(stdout.read().decode('utf-8', errors='replace').strip()[:500])

# Also test the miniapp URL
print("\n=== Test miniapp URL via nginx ===")
stdin, stdout, stderr = ssh.exec_command(
    'curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1/ 2>&1'
)
print("Root (miniapp): ", stdout.read().decode('utf-8', errors='replace').strip())

ssh.close()

import paramiko, io, sys, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('193.168.175.92', 22, 'root', '5rvLB5!Q2kmoVpG#uX77fI7lwcGA3', timeout=15)

sftp = ssh.open_sftp()
sftp.put('bot/main.py', '/opt/trans-app/bot/main.py')
sftp.put('bot/handlers/start.py', '/opt/trans-app/bot/handlers/start.py')
sftp.put('bot/keyboards/inline_kb.py', '/opt/trans-app/bot/keyboards/inline_kb.py')
sftp.close()
print("Uploaded all files")

# Rebuild and restart
stdin, stdout, stderr = ssh.exec_command(
    'cd /opt/trans-app && docker compose -f docker-compose.prod.yml build bot --no-cache 2>&1 | tail -5'
)
stdout.channel.recv_exit_status()
print("Build:", stdout.read().decode('utf-8', errors='replace').strip()[-500:])

stdin2, stdout2, stderr2 = ssh.exec_command(
    'cd /opt/trans-app && docker compose -f docker-compose.prod.yml up -d bot 2>&1'
)
stdout2.channel.recv_exit_status()
print("Up:", stdout2.read().decode('utf-8', errors='replace').strip()[:300])

time.sleep(5)

stdin3, stdout3, stderr3 = ssh.exec_command(
    'cd /opt/trans-app && docker compose -f docker-compose.prod.yml ps bot 2>&1'
)
print("Status:", stdout3.read().decode('utf-8', errors='replace').strip()[:500])

ssh.close()

import paramiko, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('193.168.175.92', 22, 'root', '5rvLB5!Q2kmoVpG#uX77fI7lwcGA3', timeout=15)

# Check ALL bot logs since the last rebuild
print("=== All bot logs since last restart ===")
stdin, stdout, stderr = ssh.exec_command(
    'cd /opt/trans-app && docker compose -f docker-compose.prod.yml logs --tail=500 bot 2>&1'
)
stdout.channel.recv_exit_status()
out = stdout.read().decode('utf-8', errors='replace')
print(out[-8000:])

ssh.close()

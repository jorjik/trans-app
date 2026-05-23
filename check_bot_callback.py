"""
Check bot logs for callback handling errors after user clicks language button.
"""
import paramiko
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

HOST = "193.168.175.92"
PORT = 22
USERNAME = "root"
PASSWORD = '5rvLB5!Q2kmoVpG#uX77fI7lwcGA3'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, PORT, USERNAME, PASSWORD, timeout=15)

# Full bot logs (especially for callback errors)
print("=== Bot Logs (last 60 lines) ===")
stdin, stdout, stderr = ssh.exec_command(
    "cd /opt/trans-app && docker compose -f docker-compose.prod.yml logs --tail=60 bot 2>&1"
)
stdout.channel.recv_exit_status()
print(stdout.read().decode('utf-8', errors='replace').strip()[:5000])

# Also check API logs
print("\n\n=== API Logs (last 30 lines) ===")
stdin, stdout, stderr = ssh.exec_command(
    "cd /opt/trans-app && docker compose -f docker-compose.prod.yml logs --tail=30 api 2>&1"
)
stdout.channel.recv_exit_status()
print(stdout.read().decode('utf-8', errors='replace').strip()[:3000])

ssh.close()

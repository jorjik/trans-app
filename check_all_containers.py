import paramiko, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('193.168.175.92', 22, 'root', '5rvLB5!Q2kmoVpG#uX77fI7lwcGA3', timeout=15)

print("=== All containers ===")
stdin, stdout, stderr = ssh.exec_command(
    'cd /opt/trans-app && docker compose -f docker-compose.prod.yml ps'
)
print(stdout.read().decode('utf-8', errors='replace').strip())

print("\n=== Miniapp logs (tail 20) ===")
stdin2, stdout2, stderr2 = ssh.exec_command(
    'cd /opt/trans-app && docker compose -f docker-compose.prod.yml logs --tail=30 miniapp 2>&1'
)
print(stdout2.read().decode('utf-8', errors='replace').strip()[:2000])

print("\n=== API logs (tail 10) ===")
stdin3, stdout3, stderr3 = ssh.exec_command(
    'cd /opt/trans-app && docker compose -f docker-compose.prod.yml logs --tail=10 api 2>&1'
)
print(stdout3.read().decode('utf-8', errors='replace').strip()[:1000])

ssh.close()

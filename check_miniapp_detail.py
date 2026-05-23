import paramiko, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('193.168.175.92', 22, 'root', '5rvLB5!Q2kmoVpG#uX77fI7lwcGA3', timeout=15)

print("=== Miniapp container status ===")
stdin, stdout, stderr = ssh.exec_command('docker ps --filter name=miniapp --format "{{.Names}} {{.Status}} {{.Ports}}"')
print(stdout.read().decode('utf-8', errors='replace').strip())

print("\n=== Direct test of miniapp on port 3000 ===")
stdin, stdout, stderr = ssh.exec_command(
    'curl -s -o /dev/null -w "HTTP %{http_code}" http://127.0.0.1:3000/ 2>&1'
)
print(stdout.read().decode('utf-8', errors='replace').strip())

print("\n=== Via nginx ===")
stdin, stdout, stderr = ssh.exec_command(
    'curl -s -o /dev/null -w "HTTP %{http_code}" http://127.0.0.1/ 2>&1'
)
print(stdout.read().decode('utf-8', errors='replace').strip())

print("\n=== Test full URL ===")
stdin, stdout, stderr = ssh.exec_command(
    'curl -s -H "Host: 193-168-175-92.eu-ml-cloud-xip.com" -o /dev/null -w "HTTP %{http_code}" http://127.0.0.1/ 2>&1'
)
print(stdout.read().decode('utf-8', errors='replace').strip())

print("\n=== Check nginx error.log ===")
stdin, stdout, stderr = ssh.exec_command(
    'tail -20 /var/log/nginx/error.log 2>&1 || echo "no error log"'
)
print(stdout.read().decode('utf-8', errors='replace').strip()[:1000])

print("\n=== Check nginx access.log recent ===")
stdin, stdout, stderr = ssh.exec_command(
    'tail -10 /var/log/nginx/access.log 2>&1'
)
print(stdout.read().decode('utf-8', errors='replace').strip()[:1000])

print("\n=== Check what nginx serves on host ===")
stdin, stdout, stderr = ssh.exec_command(
    'curl -s http://127.0.0.1/ 2>&1 | head -20'
)
print(stdout.read().decode('utf-8', errors='replace').strip()[:1000])

ssh.close()

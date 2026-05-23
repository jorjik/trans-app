import paramiko, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('193.168.175.92', 22, 'root', '5rvLB5!Q2kmoVpG#uX77fI7lwcGA3', timeout=15)

print("=== Full nginx config ===")
stdin, stdout, stderr = ssh.exec_command('cat /etc/nginx/sites-available/trans-app 2>&1')
print(stdout.read().decode('utf-8', errors='replace').strip()[:5000])

print("\n=== nginx.conf ===")
stdin, stdout, stderr = ssh.exec_command('cat /etc/nginx/nginx.conf 2>&1')
print(stdout.read().decode('utf-8', errors='replace').strip()[:2000])

print("\n=== Symlink check ===")
stdin, stdout, stderr = ssh.exec_command('ls -la /etc/nginx/sites-enabled/ 2>&1')
print(stdout.read().decode('utf-8', errors='replace').strip()[:500])

ssh.close()

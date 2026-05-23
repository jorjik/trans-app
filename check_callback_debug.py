import paramiko, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('193.168.175.92', 22, 'root', '5rvLB5!Q2kmoVpG#uX77fI7lwcGA3', timeout=15)

# Get ALL bot logs and search for CALLBACK DEBUG
stdin, stdout, stderr = ssh.exec_command(
    'cd /opt/trans-app && docker compose -f docker-compose.prod.yml logs --tail=500 bot 2>&1 | grep -i "CALLBACK DEBUG\\|cb_set_ui_lang\\|set_ui_lang\\|callback_query" || echo "NO_MATCHING_LINES"'
)
stdout.channel.recv_exit_status()
out = stdout.read().decode('utf-8', errors='replace').strip()
print("=== Matching lines ===")
print(out if out else "(empty)")

# Also check: what's the user's language code?
print("\n=== Check user start flow ===")
stdin2, stdout2, stderr2 = ssh.exec_command(
    'cd /opt/trans-app && docker compose -f docker-compose.prod.yml logs --tail=500 bot 2>&1 | grep -i "Update id=\\|cmd_start\\|start_greeting" | tail -20'
)
print(stdout2.read().decode('utf-8', errors='replace').strip()[:2000])

ssh.close()

#!/usr/bin/env bash
#
# deploy-oci.sh — Deploy TransApp to Oracle Cloud Infrastructure (OCI) Compute VM
#
# Usage:
#   ./deploy-oci.sh -h <host> [-u <user>] [-k <key_path>] [--skip-build] [--logs]
#
# See deploy-oci.ps1 for the full-featured Windows version.

set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
info()  { echo -e "${CYAN}[INFO]${NC}  $*"; }
ok()    { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
err()   { echo -e "${RED}[ERROR]${NC} $*"; }

HOST=""; USER="ubuntu"; KEY="$HOME/.ssh/id_rsa"; SKIP_BUILD=false; RESTART=false; SHOW_LOGS=false; DRY_RUN=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        -h|--host)       HOST="$2"; shift 2 ;;
        -u|--user)       USER="$2"; shift 2 ;;
        -k|--key)        KEY="$2"; shift 2 ;;
        --skip-build)    SKIP_BUILD=true; shift ;;
        --restart)       RESTART=true; shift ;;
        --logs)          SHOW_LOGS=true; shift ;;
        --dry-run)       DRY_RUN=true; shift ;;
        *) err "Unknown option: $1"; exit 1 ;;
    esac
done

if [[ -z "$HOST" ]]; then
    err "Host required. Usage: $0 -h <oci-vm-ip>"
    exit 1
fi

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REMOTE_DIR="/opt/trans-app"
COMPOSE_FILE="docker-compose.prod.yml"
SSH_OPTS="-o StrictHostKeyChecking=accept-new -o ConnectTimeout=10"
if [[ -f "$KEY" ]]; then SSH_OPTS="$SSH_OPTS -i $KEY"; fi
TARGET="${USER}@${HOST}"

run_ssh() { info "$2"; if $DRY_RUN; then echo "  [DRY] ssh $TARGET $1"; else ssh $SSH_OPTS "$TARGET" "$1"; fi; }

# Check connection
info "Checking SSH connection to $HOST..."
if ! ssh $SSH_OPTS "$TARGET" 'echo OK' &>/dev/null; then
    err "Cannot SSH to $HOST"; exit 1
fi
ok "SSH connection OK"

# Set up remote dir
run_ssh "sudo mkdir -p $REMOTE_DIR && sudo chown -R \$USER:\$USER $REMOTE_DIR" "Creating remote directory"

# Sync files
echo ""
RSYNC_EXCLUDES=(
    --exclude '.git' --exclude 'node_modules' --exclude '__pycache__' --exclude '*.pyc'
    --exclude 'venv' --exclude '.venv' --exclude '.env' --exclude '*.session'
    --exclude 'dist' --exclude 'dist-ssr' --exclude '.vscode' --exclude '.idea' --exclude '*.tsbuildinfo'
)
info "Syncing project files to $HOST..."
if $DRY_RUN; then
    echo "  [DRY] rsync $PROJECT_DIR/ → $REMOTE_DIR/"
else
    rsync -avz --delete "${RSYNC_EXCLUDES[@]}" -e "ssh $SSH_OPTS" "$PROJECT_DIR/" "$TARGET:$REMOTE_DIR/"
    ok "Files synced"
fi

# Upload .env
echo ""
if [[ -f "$PROJECT_DIR/.env" ]]; then
    info "Uploading .env..."
    if ! $DRY_RUN; then
        scp $SSH_OPTS "$PROJECT_DIR/.env" "$TARGET:$REMOTE_DIR/.env" && ok ".env uploaded" || warn ".env upload failed"
    fi
else
    warn ".env not found — create it on the VM"
fi

# Docker compose up
echo ""
BUILD_FLAG=""; if ! $SKIP_BUILD; then BUILD_FLAG="--build"; fi
RECREATE_FLAG=""; if $RESTART; then RECREATE_FLAG="--force-recreate"; fi

run_ssh "cd $REMOTE_DIR && docker compose -f $COMPOSE_FILE up -d $BUILD_FLAG $RECREATE_FLAG --remove-orphans" "Starting containers..."

# Status
echo ""
run_ssh "cd $REMOTE_DIR && docker compose -f $COMPOSE_FILE ps" "Container status"

# Logs
if $SHOW_LOGS; then
    echo ""
    run_ssh "cd $REMOTE_DIR && docker compose -f $COMPOSE_FILE logs --tail=50" "Recent logs"
fi

# Done
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
ok "Deployment complete!"
echo ""
echo -e "${CYAN}Health checks:${NC}"
echo "  API:       curl http://${HOST}:8000/health"
echo "  Mini App:  curl http://${HOST}:3000"
echo "  SSH:       ssh ${SSH_OPTS} ${TARGET}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "  1. Set up OCI Security List for ports 8000, 3000"
echo "  2. Configure Telegram webhook"
echo "  3. Set up Nginx + Let's Encrypt for HTTPS"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

#!/usr/bin/env bash
#
# deploy.sh — Deploy TransApp services to Railway via CLI
#
# Usage:
#   ./deploy.sh [-e <env>]              Deploy all services
#   ./deploy.sh [-e <env>] api          Deploy only the API service
#   ./deploy.sh [-e <env>] bot          Deploy only the Bot service
#   ./deploy.sh [-e <env>] miniapp      Deploy only the Miniapp service
#   ./deploy.sh status                  Show deployment status
#   ./deploy.sh logs <svc>              Show logs for a service
#   ./deploy.sh link                    Link local repo to Railway project
#   ./deploy.sh login                   Login to Railway
#   ./deploy.sh setup                   Create services in Railway project
#   ./deploy.sh help                    Show this help
#

set -euo pipefail

# ── Colors ─────────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ── Services ───────────────────────────────────────────────────────────────────
SERVICES=("api" "bot" "miniapp")
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ── Defaults ───────────────────────────────────────────────────────────────────
ENVIRONMENT=""

# ── Helpers ────────────────────────────────────────────────────────────────────

info()  { echo -e "${CYAN}[INFO]${NC}  $*"; }
ok()    { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; }

check_prerequisites() {
    if ! command -v railway &>/dev/null; then
        error "Railway CLI is not installed."
        echo "  Install it: npm install -g @railway/cli"
        echo "  Or via:     curl -fsSL https://railway.app/install.sh | sh"
        exit 1
    fi

    if ! railway whoami &>/dev/null; then
        error "Not logged into Railway. Run: ./deploy.sh login"
        exit 1
    fi

    if [ ! -d "$PROJECT_DIR/.railway" ]; then
        error "Project not linked. Run: ./deploy.sh link"
        echo ""
        echo "  This opens an interactive prompt to select your Railway project."
        echo "  After linking once, you can deploy without re-linking."
        exit 1
    fi
}

env_flag() {
    if [ -n "$ENVIRONMENT" ]; then
        echo "--environment $ENVIRONMENT"
    fi
}

deploy_service() {
    local svc="$1"
    local svc_dir="$PROJECT_DIR/$svc"

    if [ ! -d "$svc_dir" ]; then
        error "Service directory '$svc_dir' not found."
        exit 1
    fi

    local env_opt
    env_opt=$(env_flag)

    info "Deploying '$svc' service${ENVIRONMENT:+" → $ENVIRONMENT"}..."

    if ! (cd "$svc_dir" && railway up --service "$svc" $env_opt); then
        error "Failed to deploy '$svc'."
        exit 1
    fi

    ok "'$svc' deployed successfully${ENVIRONMENT:+" to $ENVIRONMENT"}!"
}

deploy_all() {
    info "Deploying all services${ENVIRONMENT:+" → $ENVIRONMENT"}..."
    for svc in "${SERVICES[@]}"; do
        echo ""
        deploy_service "$svc"
    done
    echo ""
    ok "All services deployed!"
}

show_status() {
    check_prerequisites
    info "Deployment status${ENVIRONMENT:+" ($ENVIRONMENT)"}:"
    local env_opt; env_opt=$(env_flag)
    railway service status $env_opt 2>&1
}

show_logs() {
    local svc="$1"
    if [ -z "$svc" ]; then
        error "Specify a service: $0 logs <api|bot|miniapp>"
        exit 1
    fi
    local env_opt; env_opt=$(env_flag)
    railway logs --service "$svc" $env_opt
}

do_link() {
    info "Linking project to Railway..."
    railway link
    if [ -d "$PROJECT_DIR/.railway" ]; then
        ok "Project linked!"
    else
        error "Link failed or was cancelled."
        exit 1
    fi
}

do_login() {
    info "Opening Railway login..."
    railway login
}

do_setup() {
    check_prerequisites
    info "Setting up services in Railway project..."

    for svc in "${SERVICES[@]}"; do
        info "Creating service '$svc'..."
        railway service add "$svc" 2>&1 || {
            warn "Service '$svc' may already exist — skipping."
        }
    done

    echo ""
    ok "Setup complete! Services created: ${SERVICES[*]}"
    echo ""
    echo "Next steps:"
    echo "  1. Set environment variables in Railway dashboard or via:"
    for svc in "${SERVICES[@]}"; do
        echo "     railway variables set KEY=VALUE --service $svc"
    done
    echo "  2. Deploy: $0"
}

print_usage() {
    cat <<USAGE
Usage:
  $0 [-e <env>]              Deploy all services
  $0 [-e <env>] <service>    Deploy a specific service (api|bot|miniapp)
  $0 status                   Show deployment status
  $0 logs <svc>               Show logs for a service
  $0 link                     Link local repo to Railway project
  $0 login                    Login to Railway
  $0 setup                    Create services in Railway project
  $0 help                     Show this help

Options:
  -e, --environment <env>    Target environment (production, staging, etc.)

Examples:
  $0                          Deploy all to default environment
  $0 -e production api        Deploy only API to production
  $0 -e staging all           Deploy all to staging
  $0 status                   Check status
  $0 logs api                 View API logs
USAGE
}

# ── Parse options ──────────────────────────────────────────────────────────────

POSITIONAL=()
while [[ $# -gt 0 ]]; do
    case "$1" in
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -e=*|--environment=*)
            ENVIRONMENT="${1#*=}"
            shift
            ;;
        -h|--help|help)
            print_usage
            exit 0
            ;;
        *)
            POSITIONAL+=("$1")
            shift
            ;;
    esac
done

set -- "${POSITIONAL[@]}"

# ── Main ───────────────────────────────────────────────────────────────────────

case "${1:-all}" in
    all)
        check_prerequisites
        deploy_all
        ;;
    api|bot|miniapp)
        check_prerequisites
        deploy_service "$1"
        ;;
    status)
        check_prerequisites
        show_status
        ;;
    logs)
        check_prerequisites
        show_logs "${2:-}"
        ;;
    link)
        do_link
        ;;
    login)
        do_login
        ;;
    setup)
        do_setup
        ;;
    *)
        error "Unknown command: $1"
        print_usage
        exit 1
        ;;
esac

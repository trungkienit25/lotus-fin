#!/usr/bin/env bash
# ==============================================================================
# Lotus Fin — run-container.sh
# Production Container Orchestrator:
# Runs the production multi-container stack exposed on Port 80 via Nginx.
# Supports lifecycle commands: start, stop, restart, status, logs, clean.
# ==============================================================================

set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"
PROD_COMPOSE="${ROOT_DIR}/docker/production/compose.prod.yml"
ENV_FILE="${ROOT_DIR}/docker/production/.env.production"

CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m'

print_step() { echo -e "\n${CYAN}${BOLD}>>> [$1] $2${NC}"; }
print_success() { echo -e "${GREEN}${BOLD}✔ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠ $1${NC}"; }
print_error() { echo -e "${RED}${BOLD}✖ $1${NC}"; }

check_docker() {
    if ! command -v docker >/dev/null 2>&1; then
        print_error "Docker is not installed or not in PATH!"
        exit 1
    fi
}

start_prod() {
    check_docker
    print_step "1/3" "Starting Lotus Fin Production Stack on Port 80..."

    # Ensure production environment file exists
    if [ ! -f "$ENV_FILE" ]; then
        print_warning "No .env.production file found. Generating default..."
        cat << 'EOF' > "$ENV_FILE"
SERVER_NAME=_
PROD_PORT=80
LOTUS_SITE=frontend
DB_PASSWORD=admin
ADMIN_PASSWORD=admin
LOTUS_AI_PROVIDER=gemini
LOTUS_LLM_PROVIDER=gemini
LOTUS_LLM_MODEL=gemini-flash-lite-latest
EOF
    fi

    # Check if frontend gateway image exists; if not, build it automatically
    if ! docker image inspect lotus-fin/gateway:latest >/dev/null 2>&1; then
        print_warning "Image lotus-fin/gateway:latest not found. Running packaging step..."
        "${ROOT_DIR}/scripts/packaging/run-packaging.sh"
    fi


    print_step "2/3" "Launching production containers via Docker Compose..."
    docker compose --env-file "$ENV_FILE" -f "$PROD_COMPOSE" up -d

    print_step "3/3" "Verifying application status..."
    SERVER_IP=$(curl -s --connect-timeout 3 https://ifconfig.me 2>/dev/null || hostname -I | awk '{print $1}' 2>/dev/null || echo "127.0.0.1")

    echo -e "\n${GREEN}${BOLD}====================================================================="
    echo "       🎉 LOTUS FIN PRODUCTION CONTAINER IS LIVE!                   "
    echo "=====================================================================${NC}"
    echo -e "  • Public Web Access:         ${CYAN}${BOLD}http://${SERVER_IP}:${PROD_PORT:-80}/${NC}"
    echo -e "  • Frappe ERPNext Desk:       ${CYAN}http://${SERVER_IP}:${PROD_PORT:-80}/desk${NC}"
    echo -e "  • Gateway:                   Nginx Reverse Proxy (Serving React SPA + Frappe API)"
    echo -e "  • Port:                      ${BOLD}${PROD_PORT:-80}${NC}"
    echo "====================================================================="
    echo "Management commands:"
    echo "  ./run-container.sh status    - View running container status"
    echo "  ./run-container.sh logs      - View live logs"
    echo "  ./run-container.sh stop      - Stop all production containers"
    echo "  ./run-container.sh restart   - Restart all containers"
}

CMD="${1:-start}"
case "$CMD" in
    start|up|"")
        start_prod
        ;;
    stop|down)
        check_docker
        print_step "Stop" "Stopping production containers..."
        docker compose --env-file "$ENV_FILE" -f "$PROD_COMPOSE" stop
        print_success "Containers stopped."
        ;;
    restart)
        check_docker
        print_step "Restart" "Restarting production containers..."
        docker compose --env-file "$ENV_FILE" -f "$PROD_COMPOSE" restart
        print_success "Containers restarted."
        ;;
    status|ps)
        check_docker
        docker compose --env-file "$ENV_FILE" -f "$PROD_COMPOSE" ps
        ;;
    logs)
        check_docker
        docker compose --env-file "$ENV_FILE" -f "$PROD_COMPOSE" logs --tail 100 -f
        ;;
    clean)
        check_docker
        print_warning "Removing production containers and networks..."
        docker compose --env-file "$ENV_FILE" -f "$PROD_COMPOSE" down
        print_success "Containers removed."
        ;;
    *)
        echo "Usage: ./run-container.sh {start|stop|restart|status|logs|clean}"
        exit 1
        ;;
esac


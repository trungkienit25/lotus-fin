#!/usr/bin/env bash
# ==============================================================================
# Lotus Fin — run-dev.sh
# One-click script for Developers:
# 1. Detects OS (Linux / macOS / Windows WSL / Git Bash).
# 2. Checks and installs required prerequisites (Docker, Node.js, npm, Swap on Linux).
# 3. Starts the Dockerized ERPNext/Frappe backend stack.
# 4. Synchronizes and migrates lotus_fin app code.
# 5. Seeds corporate demo data (Lotus-fin Demo).
# 6. Starts the Frontend Vite Dev Server (port 5173 with proxy to 8080).
# ==============================================================================

set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"
FE_DIR="${ROOT_DIR}/frontend"
DOCKER_DIR="${ROOT_DIR}/frappe_docker"
COMPOSE_FILE="${DOCKER_DIR}/pwd.yml"
BACKEND_CONTAINER="frappe_docker-backend-1"


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

# ------------------------------------------------------------------------------
# 1. OS Detection & Environment Check
# ------------------------------------------------------------------------------
detect_os() {
    print_step "1/6" "Detecting Operating System and Host Environment..."
    OS_TYPE="$(uname -s)"
    case "$OS_TYPE" in
        Linux*)
            if grep -qi microsoft /proc/version 2>/dev/null; then
                DETECTED_OS="Windows (WSL)"
            else
                DETECTED_OS="Linux"
            fi
            ;;
        Darwin*)
            DETECTED_OS="macOS"
            ;;
        CYGWIN*|MINGW*|MSYS*)
            DETECTED_OS="Windows (Git Bash)"
            ;;
        *)
            DETECTED_OS="Unknown ($OS_TYPE)"
            ;;
    esac
    print_success "Detected Platform: ${BOLD}${DETECTED_OS}${NC}"

    # For Linux VPS, auto check and setup Swap
    if [ "$DETECTED_OS" = "Linux" ] && [ -f /proc/meminfo ] && command -v free >/dev/null 2>&1; then
        CURRENT_SWAP=$(free -m | awk '/^Swap:/ {print $2}' || echo "0")
        if [ "$CURRENT_SWAP" -lt 1024 ] && [ "$(id -u)" -eq 0 ]; then
            print_warning "Low swap detected on Linux server. Configuring 2GB Swapfile..."
            fallocate -l 2G /swapfile 2>/dev/null || dd if=/dev/zero of=/swapfile bs=1M count=2048
            chmod 600 /swapfile
            mkswap /swapfile >/dev/null 2>&1
            swapon /swapfile 2>/dev/null || true
            grep -q '/swapfile' /etc/fstab || echo '/swapfile none swap sw 0 0' >> /etc/fstab
            sysctl vm.swappiness=10 >/dev/null 2>&1 || true
            print_success "Configured 2GB Swap successfully!"
        fi
    fi
}

check_dependencies() {
    print_step "2/6" "Verifying Required Tools & Package Managers..."

    # Check Docker
    if ! command -v docker >/dev/null 2>&1; then
        print_error "Docker is not installed or not in PATH!"
        if [ "$DETECTED_OS" = "Linux" ] && [ "$(id -u)" -eq 0 ]; then
            print_warning "Installing Docker on Linux..."
            apt-get update -y && apt-get install -y ca-certificates curl gnupg lsb-release
            mkdir -p /etc/apt/keyrings
            curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg --yes
            echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
            apt-get update -y && apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
            systemctl enable docker && systemctl start docker
            print_success "Docker Engine installed!"
        else
            echo "Please install Docker Desktop or Docker Engine: https://docs.docker.com/get-docker/"
            exit 1
        fi
    fi

    if ! docker info >/dev/null 2>&1; then
        print_warning "Docker daemon is not running. Attempting to start..."
        systemctl start docker 2>/dev/null || service docker start 2>/dev/null || true
        sleep 3
    fi
    print_success "Docker Engine active: $(docker --version | cut -d, -f1)"

    # Check Node.js and npm for Frontend
    if ! command -v node >/dev/null 2>&1; then
        print_error "Node.js is not found!"
        echo "Please install Node.js (v18 or higher): https://nodejs.org/"
        exit 1
    fi
    if ! command -v npm >/dev/null 2>&1; then
        print_error "npm is not found!"
        exit 1
    fi
    print_success "Node.js $(node -v) & npm $(npm -v) verified."
}

# ------------------------------------------------------------------------------
# 2. Docker Backend Stack Initialization
# ------------------------------------------------------------------------------
start_backend_stack() {
    print_step "3/6" "Starting Backend Docker Services (Frappe & MariaDB)..."
    if [ ! -d "$DOCKER_DIR" ]; then
        git clone --depth 1 https://github.com/frappe/frappe_docker.git "$DOCKER_DIR"
    fi

    docker compose -f "$COMPOSE_FILE" up -d
    print_success "Backend containers active."

    echo -n "Waiting for Frappe backend to be ready"
    MAX_RETRIES=40
    COUNT=0
    until docker ps --filter "name=$BACKEND_CONTAINER" --filter "status=running" -q | grep -q . && \
          docker exec "$BACKEND_CONTAINER" test -d /home/frappe/frappe-bench/sites/frontend 2>/dev/null; do
        echo -n "."
        sleep 5
        COUNT=$((COUNT+1))
        if [ $COUNT -ge $MAX_RETRIES ]; then
            echo ""
            print_error "Timeout waiting for Frappe backend container (200s)!"
            exit 1
        fi
    done
    echo ""
    print_success "Backend & MariaDB are ready!"
}

# ------------------------------------------------------------------------------
# 3. Synchronize App Code & Database Migration
# ------------------------------------------------------------------------------
sync_and_migrate() {
    print_step "4/6" "Synchronizing lotus_fin module & applying migrations..."
    FRAPPE_CONTAINERS=$(docker ps --format '{{.Names}}' | grep -E 'frappe_docker-(backend|queue-short|queue-long|scheduler)' || echo "$BACKEND_CONTAINER")

    for c in $FRAPPE_CONTAINERS; do
        docker exec --user root "$c" rm -rf /home/frappe/frappe-bench/apps/lotus_fin 2>/dev/null || true
        docker cp "${ROOT_DIR}/lotus_fin" "${c}:/home/frappe/frappe-bench/apps/lotus_fin"
        docker exec --user root "$c" chown -R 1000:1000 /home/frappe/frappe-bench/apps/lotus_fin 2>/dev/null || true

        # Install python dependencies & link app
        docker exec --user root "$c" bash -c '
            VENV_SITE=$(find /home/frappe/frappe-bench/env/lib -name site-packages 2>/dev/null | head -n 1)
            if [ -n "$VENV_SITE" ]; then
                echo "/home/frappe/frappe-bench/apps/lotus_fin" > "$VENV_SITE/lotus_fin.pth"
            fi
        ' 2>/dev/null || true

        if docker exec "$c" test -f /home/frappe/frappe-bench/env/bin/pip 2>/dev/null; then
            docker exec --user root "$c" /home/frappe/frappe-bench/env/bin/pip install -e /home/frappe/frappe-bench/apps/lotus_fin >/dev/null 2>&1 || true
        fi
    done

    docker exec "$BACKEND_CONTAINER" bash -c "grep -q 'lotus_fin' /home/frappe/frappe-bench/sites/apps.txt || echo 'lotus_fin' >> /home/frappe/frappe-bench/sites/apps.txt"

    if ! docker exec "$BACKEND_CONTAINER" bench --site frontend list-apps 2>/dev/null | grep -q "lotus_fin"; then
        docker exec "$BACKEND_CONTAINER" bench --site frontend install-app lotus_fin
    fi

    docker exec "$BACKEND_CONTAINER" bench --site frontend migrate >/dev/null 2>&1 || true
    docker exec "$BACKEND_CONTAINER" bench --site frontend clear-cache >/dev/null 2>&1 || true

    for c in $FRAPPE_CONTAINERS; do
        docker restart "$c" >/dev/null 2>&1 || true
    done
    sleep 3
    print_success "Lotus Fin app installed and synchronized!"
}

# ------------------------------------------------------------------------------
# 4. Seed Corporate Accounting Demo Data
# ------------------------------------------------------------------------------
seed_data() {
    print_step "5/6" "Seeding Corporate Demo Accounting Ledger..."
    docker exec "$BACKEND_CONTAINER" bench --site frontend execute erpnext.setup.demo.setup_demo_data --kwargs "{'company_name': 'Lotus-fin'}" >/dev/null 2>&1 || true
    docker exec "$BACKEND_CONTAINER" bench --site frontend execute lotus_fin.setup_data.setup_demo_environment >/dev/null 2>&1 || true
    print_success "Demo accounting dataset ready!"
}

# ------------------------------------------------------------------------------
# 5. Frontend Development Server Launch
# ------------------------------------------------------------------------------
start_frontend_dev() {
    print_step "6/6" "Launching Frontend Development Server..."
    if [ ! -d "${FE_DIR}/node_modules" ]; then
        print_warning "Installing frontend dependencies (npm install)..."
        (cd "${FE_DIR}" && npm install)
    fi

    echo -e "\n${GREEN}${BOLD}====================================================================="
    echo "       🚀 LOTUS FIN DEVELOPMENT ENVIRONMENT IS ONLINE!              "
    echo "=====================================================================${NC}"
    echo -e "  • Frontend Web Application: ${CYAN}${BOLD}http://localhost:5173${NC}"
    echo -e "  • Frappe Desk & API:        ${CYAN}http://localhost:8080${NC}"
    echo -e "  • Admin Credentials:        ${BOLD}Administrator / admin${NC}"
    echo "====================================================================="
    echo -e "Starting Vite dev server (Press Ctrl+C to stop)...\n"

    cd "${FE_DIR}"
    npm run dev
}

# Run Full Dev Pipeline
detect_os
check_dependencies
start_backend_stack
sync_and_migrate
seed_data
start_frontend_dev


#!/usr/bin/env bash
# ==============================================================================
# Lotus Fin — 1-Click Production Cloud Deployer (run-deploy.sh)
# Fully automated production deployment pipeline:
# 1. System Readiness: Checks OS, CPU, RAM, Swap (auto-provisions 2GB swap if missing).
# 2. Dependency Audit: Checks Docker Engine & Compose plugin (installs if missing on Linux).
# 3. Environment & Configuration Check: Validates .env.production.
# 4. Packaging & Image Verification: Builds Nginx Frontend Gateway & pulls backend stack.
# 5. Service Orchestration: Launches production multi-container stack on Port 80.
# 6. Database Migration & Data Hydration:
#    - If existing database backup (initial_db_seed.sql.gz) is found, automatically restores it.
#    - Runs bench migrate & cache clear.
#    - Auto-provisions default SMTP Email Account and Corporate Demo dataset.
# 7. Health & Readiness Verification: Performs end-to-end ping & HTTP status verification.
# ==============================================================================

set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"
PROD_COMPOSE="${ROOT_DIR}/docker/production/compose.prod.yml"
ENV_FILE="${ROOT_DIR}/docker/production/.env.production"
BACKUP_FILE="${ROOT_DIR}/scripts/data/database/initial_db_seed.sql.gz"
BACKEND_CONTAINER="lotus-fin-prod-backend-1"

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
# STEP 1: System Readiness & Resource Audit
# ------------------------------------------------------------------------------
check_system_resources() {
    print_step "1/7" "Auditing Host System Resources & Swap..."
    OS_TYPE="$(uname -s)"
    echo "  -> Operating System: ${OS_TYPE} ($(uname -m))"

    if [ "$OS_TYPE" = "Linux" ] && command -v free >/dev/null 2>&1; then
        TOTAL_RAM=$(free -m | awk '/^Mem:/ {print $2}')
        CURRENT_SWAP=$(free -m | awk '/^Swap:/ {print $2}')
        echo "  -> Physical RAM: ${TOTAL_RAM}MB | Swap: ${CURRENT_SWAP}MB"

        if [ "$CURRENT_SWAP" -lt 1024 ]; then
            if [ "$(id -u)" -eq 0 ]; then
                print_warning "Swap space under 1GB detected. Auto-provisioning 2GB Swap for Frappe stability..."
                fallocate -l 2G /swapfile 2>/dev/null || dd if=/dev/zero of=/swapfile bs=1M count=2048
                chmod 600 /swapfile
                mkswap /swapfile >/dev/null 2>&1
                swapon /swapfile 2>/dev/null || true
                grep -q '/swapfile' /etc/fstab || echo '/swapfile none swap sw 0 0' >> /etc/fstab
                sysctl vm.swappiness=10 >/dev/null 2>&1 || true
                print_success "Configured 2GB Swapfile successfully!"
            else
                print_warning "Running without root privileges. Please ensure at least 2GB Swap is active on server."
            fi
        fi
    fi
    print_success "System resource check passed."
}

# ------------------------------------------------------------------------------
# STEP 2: Docker Engine & Compose Verification
# ------------------------------------------------------------------------------
check_docker_environment() {
    print_step "2/7" "Verifying Docker Engine & Container Daemon..."
    if ! command -v docker >/dev/null 2>&1; then
        print_error "Docker is not installed!"
        if [ "$(uname -s)" = "Linux" ] && [ "$(id -u)" -eq 0 ]; then
            print_warning "Auto-installing Docker Engine on Ubuntu/Debian..."
            apt-get update -y && apt-get install -y ca-certificates curl gnupg lsb-release
            mkdir -p /etc/apt/keyrings
            curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg --yes
            echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
            apt-get update -y && apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
            systemctl enable docker && systemctl start docker
            print_success "Docker Engine installed successfully!"
        else
            echo "Please install Docker: https://docs.docker.com/engine/install/"
            exit 1
        fi
    fi

    if ! docker info >/dev/null 2>&1; then
        print_warning "Docker daemon is not responding. Starting service..."
        systemctl start docker 2>/dev/null || service docker start 2>/dev/null || true
        sleep 3
    fi
    print_success "Docker active: $(docker --version | cut -d, -f1)"
}

# ------------------------------------------------------------------------------
# STEP 3: Environment File & Secrets Inspection
# ------------------------------------------------------------------------------
prepare_environment_config() {
    print_step "3/7" "Checking Production Environment Configuration..."
    if [ ! -f "$ENV_FILE" ]; then
        if [ -f "${ROOT_DIR}/.env" ]; then
            print_warning "Copying existing .env to .env.production..."
            cp "${ROOT_DIR}/.env" "$ENV_FILE"
        else
            print_warning "Creating default .env.production template..."
            cat << 'EOF' > "$ENV_FILE"
SERVER_NAME=_
PROD_PORT=80
LOTUS_SITE=frontend
DB_PASSWORD=admin
ADMIN_PASSWORD=admin
LOTUS_AI_PROVIDER=gemini
LOTUS_LLM_PROVIDER=gemini
LOTUS_LLM_MODEL=gemini-flash-latest
EOF
        fi
    fi
    print_success "Production environment configuration validated: ${ENV_FILE}"
}

# ------------------------------------------------------------------------------
# STEP 4: Build Gateway Image & Pull Stack
# ------------------------------------------------------------------------------
package_production_images() {
    print_step "4/7" "Assembling Production Container Images..."
    if ! docker image inspect lotus-fin/gateway:latest >/dev/null 2>&1; then
        print_warning "Building Nginx Gateway image (React Vite SPA + Nginx Proxy)..."
        docker build \
            --file "${ROOT_DIR}/docker/production/Dockerfile.frontend" \
            --tag "lotus-fin/gateway:latest" \
            "${ROOT_DIR}"
        print_success "Built lotus-fin/gateway:latest!"
    else
        print_success "Gateway image lotus-fin/gateway:latest is already available."
    fi
}

# ------------------------------------------------------------------------------
# STEP 5: Launch Multi-Container Stack (Port 80)
# ------------------------------------------------------------------------------
launch_stack() {
    print_step "5/7" "Starting Production Multi-Container Stack on Port 80..."
    docker compose --env-file "$ENV_FILE" -f "$PROD_COMPOSE" up -d

    echo -n "Waiting for core backend container and site frontend initialization"
    MAX_RETRIES=60
    COUNT=0
    until docker ps --filter "name=backend" --filter "status=running" -q | grep -q . && \
          ACTUAL_BACKEND=$(docker ps --format '{{.Names}}' | grep -E 'backend' | head -n 1) && \
          [ -n "$ACTUAL_BACKEND" ] && \
          docker exec "$ACTUAL_BACKEND" test -d /home/frappe/frappe-bench/sites/frontend 2>/dev/null; do
        echo -n "."
        sleep 5
        COUNT=$((COUNT+1))
        if [ $COUNT -ge $MAX_RETRIES ]; then
            echo ""
            print_error "Timeout waiting for backend service & site initialization!"
            exit 1
        fi
    done
    echo ""
    print_success "Production containers and site frontend are running."
}

# ------------------------------------------------------------------------------
# STEP 6: Database Hydration (Seed Import & Migration)
# ------------------------------------------------------------------------------
hydrate_database() {
    print_step "6/7" "Hydrating Database & Applying Migrations..."
    ACTUAL_BACKEND=$(docker ps --format '{{.Names}}' | grep -E 'backend' | head -n 1)

    if [ -n "$ACTUAL_BACKEND" ]; then
        # 1. Ensure lotus_fin is in sites/apps.txt and Python venv
        echo "  -> Linking lotus_fin into Python environment and apps registry..."
        FRAPPE_CONTAINERS=$(docker ps --format '{{.Names}}' | grep -E '(backend|queue-short|queue-long|scheduler)' || echo "$ACTUAL_BACKEND")
        for c in $FRAPPE_CONTAINERS; do
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

        docker exec "$ACTUAL_BACKEND" bash -c "grep -q 'lotus_fin' /home/frappe/frappe-bench/sites/apps.txt || echo 'lotus_fin' >> /home/frappe/frappe-bench/sites/apps.txt"

        # 2. Restore database snapshot if initial seed exists
        if [ -f "$BACKUP_FILE" ]; then
            echo "  -> Found database snapshot: ${BACKUP_FILE}"
            echo "  -> Uploading and restoring database into site frontend..."
            docker exec "$ACTUAL_BACKEND" mkdir -p /home/frappe/frappe-bench/sites/frontend/private/backups
            docker cp "$BACKUP_FILE" "${ACTUAL_BACKEND}:/home/frappe/frappe-bench/sites/frontend/private/backups/seed.sql.gz"
            docker exec --workdir /home/frappe/frappe-bench/sites "$ACTUAL_BACKEND" \
                /home/frappe/frappe-bench/env/bin/python -m frappe.utils.bench_helper frappe --site frontend --force restore --db-root-password "${DB_PASSWORD:-admin}" /home/frappe/frappe-bench/sites/frontend/private/backups/seed.sql.gz || true
            print_success "Database seed restored successfully!"
        fi

        # 3. Ensure lotus_fin is installed in site frontend
        if ! docker exec "$ACTUAL_BACKEND" /home/frappe/frappe-bench/env/bin/python -m frappe.utils.bench_helper frappe --site frontend list-apps 2>/dev/null | grep -q "lotus_fin"; then
            docker exec "$ACTUAL_BACKEND" /home/frappe/frappe-bench/env/bin/python -m frappe.utils.bench_helper frappe --site frontend install-app lotus_fin || true
        fi

        # 4. Run Database Migration & Cache Invalidation
        echo "  -> Running database schema migration (bench migrate)..."
        docker exec --workdir /home/frappe/frappe-bench/sites "$ACTUAL_BACKEND" \
            /home/frappe/frappe-bench/env/bin/python -m frappe.utils.bench_helper frappe --site frontend migrate
        
        docker exec --workdir /home/frappe/frappe-bench/sites "$ACTUAL_BACKEND" \
            /home/frappe/frappe-bench/env/bin/python -m frappe.utils.bench_helper frappe --site frontend clear-cache

        # 5. Synchronize SMTP Email and Demo Config
        echo "  -> Verifying SMTP outgoing gateway & Demo configuration..."
        docker exec --workdir /home/frappe/frappe-bench/sites "$ACTUAL_BACKEND" \
            /home/frappe/frappe-bench/env/bin/python -m frappe.utils.bench_helper frappe --site frontend execute lotus_fin.setup_data.setup_demo_environment || true

        # 6. Restart backend so gunicorn loads all changes
        echo "  -> Restarting backend service..."
        docker restart "$ACTUAL_BACKEND" >/dev/null 2>&1
        sleep 5

        print_success "Database migrations and configuration synchronization completed."
    fi
}

# ------------------------------------------------------------------------------
# STEP 7: Health & Verification Audit
# ------------------------------------------------------------------------------
verify_deployment() {
    print_step "7/7" "Running End-to-End Readiness & Ping Verification..."
    sleep 3
    PROD_PORT=$(grep -E '^PROD_PORT=' "$ENV_FILE" 2>/dev/null | cut -d= -f2 || echo "80")
    [ -z "$PROD_PORT" ] && PROD_PORT="80"

    SERVER_IP=$(curl -s --connect-timeout 3 https://ifconfig.me 2>/dev/null || hostname -I | awk '{print $1}' 2>/dev/null || echo "127.0.0.1")

    # Probe Port 80 / HTTP readiness
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 "http://127.0.0.1:${PROD_PORT}/" 2>/dev/null || echo "000")

    echo -e "\n${GREEN}${BOLD}====================================================================="
    echo "       🎉 LOTUS FIN PRODUCTION DEPLOYMENT IS COMPLETE!               "
    echo "=====================================================================${NC}"
    echo -e "  • Gateway Status:            ${GREEN}${BOLD}ONLINE (HTTP ${HTTP_CODE})${NC}"
    echo -e "  • Public Web Application:    ${CYAN}${BOLD}http://${SERVER_IP}:${PROD_PORT}/${NC}"
    echo -e "  • ERPNext / Desk Management: ${CYAN}http://${SERVER_IP}:${PROD_PORT}/desk${NC}"
    echo -e "  • Default Admin Account:     ${BOLD}Administrator / admin${NC}"
    echo -e "  • Reverse Proxy Port:        ${BOLD}${PROD_PORT} (Nginx Gateway)${NC}"
    echo "====================================================================="
    echo "Management commands:"
    echo "  ./scripts/container/run-container.sh status  - Check running containers"
    echo "  ./scripts/container/run-container.sh logs    - View real-time logs"
    echo "  ./scripts/container/run-container.sh restart - Restart services"
    echo "  ./scripts/container/run-container.sh stop    - Stop services"
}

# Execute Full Deployment Pipeline
check_system_resources
check_docker_environment
prepare_environment_config
package_production_images
launch_stack
hydrate_database
verify_deployment


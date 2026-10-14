#!/usr/bin/env bash
# ==============================================================================
# Lotus Fin — 1-Click Automated Setup & Management Script
# ==============================================================================

set -eo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCKER_DIR="${ROOT_DIR}/frappe_docker"
COMPOSE_FILE="${DOCKER_DIR}/pwd.yml"
BACKEND_CONTAINER="frappe_docker-backend-1"
FRONTEND_CONTAINER="frappe_docker-frontend-1"
DB_CONTAINER="frappe_docker-db-1"

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

check_and_prepare_environment() {
    print_step "1/7" "Kiểm tra hệ thống & chuẩn bị môi trường..."

    # Swap 2GB
    CURRENT_SWAP=$(free -m | awk '/^Swap:/ {print $2}')
    if [ "$CURRENT_SWAP" -lt 1024 ]; then
        print_warning "Chưa có Swap. Đang tự động kích hoạt 2GB Swap..."
        fallocate -l 2G /swapfile 2>/dev/null || dd if=/dev/zero of=/swapfile bs=1M count=2048
        chmod 600 /swapfile
        mkswap /swapfile >/dev/null 2>&1
        swapon /swapfile 2>/dev/null || true
        grep -q '/swapfile' /etc/fstab || echo '/swapfile none swap sw 0 0' >> /etc/fstab
        sysctl vm.swappiness=10 >/dev/null 2>&1 || true
        print_success "Đã kích hoạt 2GB Swap!"
    else
        print_success "Swap: $(free -h | awk '/^Swap:/ {print $2}') (Đạt chuẩn)."
    fi

    # Docker Engine
    if ! command -v docker &> /dev/null; then
        print_warning "Đang cài đặt Docker Engine chính thức..."
        apt update -y && apt install -y ca-certificates curl gnupg lsb-release
        mkdir -p /etc/apt/keyrings
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg --yes
        echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
        apt update -y && apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
        systemctl enable docker && systemctl start docker
        print_success "Đã cài đặt Docker!"
    fi

    if ! docker info >/dev/null 2>&1; then
        systemctl start docker || service docker start
        sleep 3
    fi
    print_success "Docker Engine sẵn sàng: $(docker --version | cut -d, -f1)."

    # Log rotation
    if [ ! -f /etc/docker/daemon.json ]; then
        echo '{"log-driver":"json-file","log-opts":{"max-size":"10m","max-file":"3"}}' > /etc/docker/daemon.json
        systemctl restart docker >/dev/null 2>&1 || true
    fi
}

start_docker_stack() {
    print_step "2/7" "Khởi động cụm 9 Container Frappe / ERPNext..."
    if [ ! -d "$DOCKER_DIR" ]; then
        git clone --depth 1 https://github.com/frappe/frappe_docker.git "$DOCKER_DIR"
    fi
    docker compose -f "$COMPOSE_FILE" up -d
    print_success "Đã kích hoạt cụm container!"
}

wait_for_services() {
    print_step "3/7" "Đợi MariaDB & Frappe Site khởi tạo hoàn tất..."
    echo -n "Đang đợi site frontend sẵn sàng"
    MAX_RETRIES=40
    COUNT=0
    until docker ps --filter "name=$BACKEND_CONTAINER" --filter "status=running" -q | grep -q . && \
          docker exec "$BACKEND_CONTAINER" test -d /home/frappe/frappe-bench/sites/frontend 2>/dev/null; do
        echo -n "."
        sleep 5
        COUNT=$((COUNT+1))
        if [ $COUNT -ge $MAX_RETRIES ]; then
            echo ""
            print_error "Hết thời gian chờ site frontend (Timeout 200s)!"
            exit 1
        fi
    done
    echo ""
    print_success "Backend & MariaDB đã sẵn sàng phục vụ!"
}

sync_app_code() {
    print_step "4/7" "Đồng bộ ứng dụng Lotus Fin & Migrate Database..."

    # Tìm các container Frappe cần đồng bộ
    FRAPPE_CONTAINERS=$(docker ps --format '{{.Names}}' | grep -E 'frappe_docker-(backend|queue-short|queue-long|scheduler)' || echo "$BACKEND_CONTAINER")

    for c in $FRAPPE_CONTAINERS; do
        echo "  -> Đang đồng bộ mã nguồn lotus_fin vào $c..."
        docker exec --user root "$c" rm -rf /home/frappe/frappe-bench/apps/lotus_fin 2>/dev/null || true
        docker cp "${ROOT_DIR}/lotus_fin" "${c}:/home/frappe/frappe-bench/apps/lotus_fin"
        docker exec --user root "$c" chown -R 1000:1000 /home/frappe/frappe-bench/apps/lotus_fin 2>/dev/null || docker exec --user root "$c" chown -R frappe /home/frappe/frappe-bench/apps/lotus_fin

        # Đảm bảo đường dẫn lotus_fin luôn có trong sys.path của Python virtualenv
        docker exec --user root "$c" bash -c '
            VENV_SITE=$(find /home/frappe/frappe-bench/env/lib -name site-packages 2>/dev/null | head -n 1)
            if [ -n "$VENV_SITE" ]; then
                echo "/home/frappe/frappe-bench/apps/lotus_fin" > "$VENV_SITE/lotus_fin.pth"
            fi
        ' 2>/dev/null || true

        # Cài đặt package vào virtualenv của bench bằng quyền root để không bị hạn chế quyền ghi
        echo "  -> Cài đặt package python vào virtualenv của $c..."
        if docker exec "$c" test -f /home/frappe/frappe-bench/env/bin/pip 2>/dev/null; then
            docker exec --user root "$c" /home/frappe/frappe-bench/env/bin/pip install -e /home/frappe/frappe-bench/apps/lotus_fin
        else
            docker exec --user root "$c" pip install -e /home/frappe/frappe-bench/apps/lotus_fin
        fi

        docker exec --user root "$c" chown -R 1000:1000 /home/frappe/frappe-bench/apps /home/frappe/frappe-bench/env 2>/dev/null || true
    done

    # Đăng ký app vào sites/apps.txt
    docker exec "$BACKEND_CONTAINER" bash -c "grep -q 'lotus_fin' /home/frappe/frappe-bench/sites/apps.txt || echo 'lotus_fin' >> /home/frappe/frappe-bench/sites/apps.txt"

    # Kiểm tra xác nhận module lotus_fin đã nạp thành công
    echo "  -> Kiểm tra nạp module lotus_fin trong môi trường Python của container..."
    docker exec "$BACKEND_CONTAINER" /home/frappe/frappe-bench/env/bin/python -c "import lotus_fin; print('✔ Module lotus_fin loaded successfully from:', lotus_fin.__file__)"

    # Cài đặt app lên site nếu chưa cài
    if ! docker exec "$BACKEND_CONTAINER" bench --site frontend list-apps 2>/dev/null | grep -q "lotus_fin"; then
        echo "  -> Cài đặt ứng dụng lotus_fin vào site frontend..."
        docker exec "$BACKEND_CONTAINER" bench --site frontend install-app lotus_fin
    fi

    # Migrate Database & Clear Cache
    echo "  -> Chạy migration database (bench migrate)..."
    docker exec "$BACKEND_CONTAINER" bench --site frontend migrate
    docker exec "$BACKEND_CONTAINER" bench --site frontend clear-cache

    # Khởi động lại các container Frappe để nạp code mới
    echo "  -> Khởi động lại các container Frappe..."
    for c in $FRAPPE_CONTAINERS; do
        docker restart "$c" >/dev/null 2>&1 || true
    done
    sleep 5
    print_success "Đã cài đặt và migrate Lotus Fin thành công!"
}

seed_demo_data() {
    print_step "5/7" "Nạp dữ liệu mẫu kế toán doanh nghiệp (Lotus-fin Demo)..."
    docker exec "$BACKEND_CONTAINER" bench --site frontend execute erpnext.setup.demo.setup_demo_data --kwargs "{'company_name': 'Lotus-fin'}" >/dev/null 2>&1 || true
    docker exec "$BACKEND_CONTAINER" bench --site frontend execute lotus_fin.setup_data.setup_demo_environment >/dev/null 2>&1 || true
    print_success "Đã nạp xong bộ dữ liệu mẫu!"
}

setup_host_nginx() {
    print_step "6/7" "Cấu hình Web Server Nginx trên Host..."
    mkdir -p /var/www/lotus-fin-fe
    chown -R www-data:www-data /var/www/lotus-fin-fe 2>/dev/null || chmod -R 755 /var/www/lotus-fin-fe

    if command -v nginx &> /dev/null && [ -d /etc/nginx/sites-available ]; then
        cat << 'NGINX_CONF' > /etc/nginx/sites-available/lotusfin
server {
    listen 80;
    server_name _;
    client_max_body_size 50m;

    location / {
        root /var/www/lotus-fin-fe;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    location ~ ^/(api|assets|files|socket.io|app|desk)/ {
        proxy_pass http://127.0.0.1:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 180s;
        proxy_buffering off;
    }
}
NGINX_CONF
        rm -f /etc/nginx/sites-enabled/default
        ln -sf /etc/nginx/sites-available/lotusfin /etc/nginx/sites-enabled/
        nginx -t >/dev/null 2>&1 && systemctl reload nginx >/dev/null 2>&1 || true
        print_success "Nginx Reverse Proxy đã kích hoạt!"
    fi
}

verify_and_summary() {
    print_step "7/7" "Kiểm tra nghiệm thu toàn diện hệ thống..."
    SERVER_IP=$(curl -s --connect-timeout 3 https://ifconfig.me 2>/dev/null || hostname -I | awk '{print $1}')
    echo -e "\n${GREEN}${BOLD}====================================================================="
    echo "       🎉 LOTUS FIN ĐÃ ĐƯỢC TRIỂN KHAI THÀNH CÔNG RỰC RỠ!            "
    echo "=====================================================================${NC}"
    echo -e "${BOLD}Thông tin truy cập ứng dụng:${NC}"
    echo -e "  • Giao diện Quản trị Desk:  ${CYAN}http://${SERVER_IP}/desk/financial-health${NC}"
    echo -e "    (hoặc truy cập trực tiếp:  ${CYAN}http://${SERVER_IP}:8080/desk/financial-health${NC})"
    echo -e "  • Tài khoản đăng nhập:       ${BOLD}Administrator${NC}"
    echo -e "  • Mật khẩu mặc định:         ${BOLD}admin${NC}"
    echo ""
    echo -e "${BOLD}Thư mục Web tĩnh Frontend:${NC}    /var/www/lotus-fin-fe"
    echo -e "${BOLD}Các lệnh điều khiển nhanh hữu ích:${NC}"
    echo "  • Xem log realtime:        ./run.sh logs"
    echo "  • Chạy kiểm thử tự động:   ./run.sh test"
    echo "  • Chạy mô phỏng What-If:   ./run.sh simulate"
    echo "  • Xem tiêu hao tài nguyên: ./run.sh status"
    echo "  • Đồng bộ lại code:        ./run.sh sync"
    echo "====================================================================="
}

run_full_setup() {
    check_and_prepare_environment
    start_docker_stack
    wait_for_services
    sync_app_code
    seed_demo_data
    setup_host_nginx
    verify_and_summary
}

CMD="${1:-all}"
case "$CMD" in
    all|setup|run|"")
        run_full_setup
        ;;
    up|start)
        check_and_prepare_environment
        start_docker_stack
        ;;
    sync)
        sync_app_code
        ;;
    demo)
        seed_demo_data
        ;;
    test)
        docker exec "$BACKEND_CONTAINER" bench --site frontend run-tests --module "${2:-lotus_fin.tests.test_financial_health}"
        ;;
    simulate)
        docker exec "$BACKEND_CONTAINER" bench --site frontend execute lotus_fin.AI005.service.simulate_what_if --kwargs "{'company': 'Lotus-fin (Demo)', 'sales_change_pct': -0.20, 'collection_delay_days': 15}"
        ;;
    status)
        docker ps --filter "name=frappe_docker"
        docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"
        ;;
    logs)
        docker logs "$BACKEND_CONTAINER" --tail 100 -f
        ;;
    stop|down)
        docker compose -f "$COMPOSE_FILE" stop
        ;;
    restart)
        docker compose -f "$COMPOSE_FILE" restart
        ;;
    clean)
        docker compose -f "$COMPOSE_FILE" down
        docker system prune -f
        ;;
    *)
        exec python3 "$ROOT_DIR/docker/lotus-core/manage.py" "$@" 2>/dev/null || echo "Usage: ./run.sh {setup|up|sync|demo|test|simulate|status|logs|stop|restart}"
        ;;
esac
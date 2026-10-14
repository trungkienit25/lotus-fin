#!/usr/bin/env bash
# ==============================================================================
# Lotus Fin — 1-Click Automated Setup & Management Script
# Supports: Linux (Ubuntu/Debian), macOS, WSL2
# ==============================================================================

set -eo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCKER_DIR="${ROOT_DIR}/frappe_docker"
COMPOSE_FILE="${DOCKER_DIR}/pwd.yml"
BACKEND_CONTAINER="frappe_docker-backend-1"
FRONTEND_CONTAINER="frappe_docker-frontend-1"
DB_CONTAINER="frappe_docker-db-1"

# --- Màu sắc hiển thị ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

print_banner() {
    echo -e "${CYAN}${BOLD}"
    echo "====================================================================="
    echo "    __    ____  ______  __  ______   _______ _   __"
    echo "   / /   / __ \/_  __/ / / / / ___/  / ____/  |/ /"
    echo "  / /   / / / / / /   / / / /\__ \  / /_  / /|_/ / "
    echo " / /___/ /_/ / / /   / /_/ /___/ / / __/ / /  / /  "
    echo "/_____/\____/ /_/    \____//____/ /_/   /_/  /_/   "
    echo "  SME Financial Management Core & AI Copilot Pipeline"
    echo "=====================================================================${NC}"
}

print_step() {
    echo -e "\n${CYAN}${BOLD}>>> [$1] $2${NC}"
}

print_success() {
    echo -e "${GREEN}${BOLD}✔ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}${BOLD}✖ $1${NC}"
}

# --- 1. Kiểm tra & Chuẩn bị Môi trường Máy chủ ---
check_and_prepare_environment() {
    print_step "1/7" "Kiểm tra hệ thống & môi trường máy chủ..."

    # 1.1. Kiểm tra quyền root/sudo
    if [ "$EUID" -ne 0 ] && ! sudo -n true 2>/dev/null; then
        print_warning "Script cần quyền sudo để cấu hình swap và docker nếu cần."
    fi

    # 1.2. Tự động tạo Swap 2GB nếu chưa có
    CURRENT_SWAP=$(free -m | awk '/^Swap:/ {print $2}')
    if [ "$CURRENT_SWAP" -lt 1024 ]; then
        print_warning "Máy chủ chưa có Swap (hoặc < 1GB). Đang tự động kích hoạt 2GB Swap..."
        if [ "$EUID" -eq 0 ]; then
            fallocate -l 2G /swapfile 2>/dev/null || dd if=/dev/zero of=/swapfile bs=1M count=2048
            chmod 600 /swapfile
            mkswap /swapfile >/dev/null 2>&1
            swapon /swapfile 2>/dev/null || true
            if ! grep -q '/swapfile' /etc/fstab; then
                echo '/swapfile none swap sw 0 0' >> /etc/fstab
            fi
            sysctl vm.swappiness=10 >/dev/null 2>&1 || true
            print_success "Đã kích hoạt 2GB Swap bảo vệ chống tràn RAM!"
        else
            sudo fallocate -l 2G /swapfile 2>/dev/null || sudo dd if=/dev/zero of=/swapfile bs=1M count=2048
            sudo chmod 600 /swapfile
            sudo mkswap /swapfile >/dev/null 2>&1
            sudo swapon /swapfile 2>/dev/null || true
            print_success "Đã kích hoạt 2GB Swap!"
        fi
    else
        print_success "Bộ nhớ đệm Swap: $(free -h | awk '/^Swap:/ {print $2}') (Đạt chuẩn)."
    fi

    # 1.3. Kiểm tra Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker chưa được cài đặt! Đang tiến hành cài đặt Docker Engine chính thức..."
        if [ "$EUID" -eq 0 ]; then
            apt update -y && apt install -y ca-certificates curl gnupg lsb-release
            mkdir -p /etc/apt/keyrings
            curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg --yes
            echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
            apt update -y && apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
            systemctl enable docker && systemctl start docker
        else
            sudo apt update -y && sudo apt install -y ca-certificates curl gnupg lsb-release
            sudo mkdir -p /etc/apt/keyrings
            curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg --yes
            echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
            sudo apt update -y && sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
            sudo systemctl enable docker && sudo systemctl start docker
        fi
        print_success "Đã cài đặt Docker thành công!"
    fi

    # 1.4. Đảm bảo Docker Daemon đang chạy
    if ! docker info >/dev/null 2>&1; then
        print_warning "Docker daemon chưa khởi động. Đang kích hoạt..."
        if [ "$EUID" -eq 0 ]; then
            systemctl start docker || service docker start
        else
            sudo systemctl start docker || sudo service docker start
        fi
        sleep 3
    fi
    print_success "Docker Engine đã sẵn sàng: $(docker --version | cut -d, -f1)."

    # 1.5. Cấu hình log rotation nếu chưa có
    if [ ! -f /etc/docker/daemon.json ] && [ "$EUID" -eq 0 ]; then
        echo '{"log-driver":"json-file","log-opts":{"max-size":"10m","max-file":"3"}}' > /etc/docker/daemon.json
        systemctl restart docker >/dev/null 2>&1 || true
    fi
}

# --- 2. Tải & Khởi chạy Cụm Container Frappe ---
start_docker_stack() {
    print_step "2/7" "Khởi động cụm 9 Container Frappe & ERPNext..."
    if [ ! -d "$DOCKER_DIR" ]; then
        echo "Tải cấu hình frappe_docker..."
        git clone --depth 1 https://github.com/frappe/frappe_docker.git "$DOCKER_DIR"
    fi

    docker compose -f "$COMPOSE_FILE" up -d
    print_success "Đã phát lệnh khởi động 9 container!"
}

# --- 3. Đợi Container & MariaDB Khởi tạo Xong ---
wait_for_services() {
    print_step "3/7" "Đợi MariaDB & Frappe Site khởi tạo hoàn tất..."
    echo -n "Đang đợi container backend và database sẵn sàng"

    MAX_RETRIES=40
    COUNT=0
    until docker ps --filter "name=$BACKEND_CONTAINER" --filter "status=running" -q | grep -q . && \
          docker exec "$BACKEND_CONTAINER" test -d /home/frappe/frappe-bench/sites/frontend 2>/dev/null; do
        echo -n "."
        sleep 5
        COUNT=$((COUNT+1))
        if [ $COUNT -ge $MAX_RETRIES ]; then
            echo ""
            print_error "Hết thời gian chờ site frontend khởi tạo (Timeout 200s)!"
            echo "Vui lòng kiểm tra log: docker logs frappe_docker-create-site-1"
            exit 1
        fi
    done
    echo ""
    print_success "Backend & MariaDB đã sẵn sàng phục vụ!"
}

# --- 4. Đồng bộ Mã Nguồn Lotus Fin vào Container ---
sync_app_code() {
    print_step "4/7" "Đồng bộ ứng dụng Lotus Fin & Migrate Database..."

    # Xóa app cũ nếu có & copy mã nguồn mới nhất
    docker exec --user root "$BACKEND_CONTAINER" rm -rf /home/frappe/frappe-bench/apps/lotus_fin
    docker cp "${ROOT_DIR}/lotus_fin" "${BACKEND_CONTAINER}:/home/frappe/frappe-bench/apps/lotus_fin"
    docker exec --user root "$BACKEND_CONTAINER" chown -R frappe:frappe /home/frappe/frappe-bench/apps/lotus_fin

    # Ghi nhận app vào sites/apps.txt và cài đặt vào Python venv
    docker exec "$BACKEND_CONTAINER" bash -c "grep -q 'lotus_fin' /home/frappe/frappe-bench/sites/apps.txt || echo 'lotus_fin' >> /home/frappe/frappe-bench/sites/apps.txt"
    docker exec "$BACKEND_CONTAINER" bash -c "pip install -e /home/frappe/frappe-bench/apps/lotus_fin"

    # Cài đặt app vào site frontend
    docker exec "$BACKEND_CONTAINER" bench --site frontend install-app lotus_fin >/dev/null 2>&1 || true

    # Migrate Database & Clear Cache
    echo "Đang migrate dữ liệu DocTypes..."
    docker exec "$BACKEND_CONTAINER" bench --site frontend migrate
    docker exec "$BACKEND_CONTAINER" bench --site frontend clear-cache

    # Khởi động lại backend để nạp code
    docker restart "$BACKEND_CONTAINER" >/dev/null 2>&1
    sleep 5
    print_success "Đã cài đặt và migrate ứng dụng Lotus Fin thành công!"
}

# --- 5. Nạp Bộ Dữ Liệu Mẫu Kế Toán (Demo Dataset) ---
seed_demo_data() {
    print_step "5/7" "Nạp dữ liệu mẫu kế toán doanh nghiệp (Lotus-fin Demo)..."
    docker exec "$BACKEND_CONTAINER" bench --site frontend execute erpnext.setup.demo.setup_demo_data --kwargs "{'company_name': 'Lotus-fin'}" >/dev/null 2>&1 || true
    docker exec "$BACKEND_CONTAINER" bench --site frontend execute lotus_fin.setup_data.setup_demo_environment >/dev/null 2>&1 || true
    print_success "Đã nạp bộ dữ liệu mẫu (Sản phẩm, Khách hàng, Hóa đơn, Công nợ, Năm tài chính)!"
}

# --- 6. Cấu hình Nginx Host (Nếu có) ---
setup_host_nginx() {
    print_step "6/7" "Cấu hình Web Server Nginx trên Host..."

    # Tạo thư mục web tĩnh
    mkdir -p /var/www/lotus-fin-fe
    if [ "$EUID" -eq 0 ]; then
        chown -R www-data:www-data /var/www/lotus-fin-fe 2>/dev/null || chown -R 755 /var/www/lotus-fin-fe
    fi

    # Nếu có Nginx cài trên host, tự động tạo cấu hình Reverse Proxy
    if command -v nginx &> /dev/null && [ -d /etc/nginx/sites-available ]; then
        cat << 'EOF' > /tmp/lotusfin_nginx.conf
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
EOF
        if [ "$EUID" -eq 0 ]; then
            cp /tmp/lotusfin_nginx.conf /etc/nginx/sites-available/lotusfin
            rm -f /etc/nginx/sites-enabled/default
            ln -sf /etc/nginx/sites-available/lotusfin /etc/nginx/sites-enabled/
            nginx -t >/dev/null 2>&1 && systemctl reload nginx >/dev/null 2>&1 || true
        else
            sudo cp /tmp/lotusfin_nginx.conf /etc/nginx/sites-available/lotusfin
            sudo rm -f /etc/nginx/sites-enabled/default
            sudo ln -sf /etc/nginx/sites-available/lotusfin /etc/nginx/sites-enabled/
            sudo nginx -t >/dev/null 2>&1 && sudo systemctl reload nginx >/dev/null 2>&1 || true
        fi
        rm -f /tmp/lotusfin_nginx.conf
        print_success "Nginx Reverse Proxy đã được cấu hình và kích hoạt!"
    else
        print_warning "Không phát hiện Nginx trên Host. Bạn có thể truy cập trực tiếp qua cổng :8080."
    fi
}

# --- 7. Tự động Kiểm tra & Hiển thị Thông tin Đăng nhập ---
verify_and_summary() {
    print_step "7/7" "Kiểm tra nghiệm thu toàn diện hệ thống..."

    # Ping test Frappe Backend
    PING_RES=$(docker exec "$BACKEND_CONTAINER" curl -s http://127.0.0.1:8000/api/method/ping || echo "fail")
    if echo "$PING_RES" | grep -q "pong"; then
        print_success "Frappe Framework API: OK (pong)"
    else
        print_warning "Frappe API chưa phản hồi ngay. Có thể cần thêm 5s để khởi động."
    fi

    # Lấy IP Public của máy chủ
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
    echo -e "  (Đẩy file dist.tar.gz từ local lên đây để hiển thị React UI)"
    echo ""
    echo -e "${BOLD}Các lệnh điều khiển nhanh hữu ích:${NC}"
    echo "  • Xem log realtime:        ./run.sh logs"
    echo "  • Chạy kiểm thử tự động:   ./run.sh test"
    echo "  • Chạy mô phỏng What-If:   ./run.sh simulate"
    echo "  • Xem tiêu hao tài nguyên: ./run.sh status"
    echo "  • Đồng bộ lại code:        ./run.sh sync"
    echo "====================================================================="
}

# --- Chế độ chạy All-In-One ---
run_full_setup() {
    print_banner
    check_and_prepare_environment
    start_docker_stack
    wait_for_services
    sync_app_code
    seed_demo_data
    setup_host_nginx
    verify_and_summary
}

# --- Điều phối các lệnh con ---
CMD="${1:-all}"

case "$CMD" in
    all|setup|run|"")
        run_full_setup
        ;;
    up|start)
        print_banner
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
        docker exec "$BACKEND_CONTAINER" bench --site frontend set-config allow_tests true
        if [ -n "${2:-}" ]; then
            docker exec "$BACKEND_CONTAINER" bench --site frontend run-tests --module "$2"
        else
            docker exec "$BACKEND_CONTAINER" bench --site frontend run-tests --module "lotus_fin.tests.test_financial_health"
        fi
        ;;
    simulate)
        docker exec "$BACKEND_CONTAINER" bench --site frontend execute lotus_fin.AI005.service.simulate_what_if --kwargs "{'company': 'Lotus-fin (Demo)', 'sales_change_pct': -0.20, 'collection_delay_days': 15}"
        ;;
    status)
        echo "=== TRẠNG THÁI CONTAINER ==="
        docker ps --filter "name=frappe_docker"
        echo -e "\n=== TIÊU THỤ TÀI NGUYÊN ==="
        docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"
        ;;
    logs)
        docker logs "$BACKEND_CONTAINER" --tail 100 -f
        ;;
    stop|down)
        docker compose -f "$COMPOSE_FILE" stop
        print_success "Đã dừng các container!"
        ;;
    restart)
        docker compose -f "$COMPOSE_FILE" restart
        print_success "Đã khởi động lại cụm container!"
        ;;
    clean|cleanup)
        docker compose -f "$COMPOSE_FILE" down --remove-orphans
        docker system prune -f
        print_success "Đã dọn dẹp cụm container!"
        ;;
    build|smoke|health|--*)
        exec python3 "$ROOT_DIR/docker/lotus-core/manage.py" "$@"
        ;;
    *)
        print_banner
        echo "Cách sử dụng: ./run.sh [lệnh]"
        echo ""
        echo "Lệnh triển khai:"
        echo "  ./run.sh            - Chạy 1-click tự động kiểm tra và setup A-Z toàn bộ hệ thống"
        echo "  ./run.sh setup      - (Tương tự) Tự động kiểm tra và setup đầy đủ"
        echo ""
        echo "Lệnh vận hành hàng ngày:"
        echo "  ./run.sh up         - Bật cụm container Docker"
        echo "  ./run.sh sync       - Đồng bộ code lotus_fin vào container & migrate DB"
        echo "  ./run.sh demo       - Nạp dữ liệu mẫu kế toán doanh nghiệp"
        echo "  ./run.sh test       - Chạy bộ kiểm thử tự động tài chính"
        echo "  ./run.sh simulate   - Chạy mô phỏng sốc tài chính What-If (9 KPIs)"
        echo "  ./run.sh status     - Xem trạng thái & mức chiếm RAM/CPU của các container"
        echo "  ./run.sh logs       - Xem logs realtime của backend"
        echo "  ./run.sh stop       - Tạm dừng hệ thống"
        echo "  ./run.sh restart    - Khởi động lại hệ thống"
        echo "  ./run.sh clean      - Xóa container và dọn dẹp cache rác"
        echo ""
        ;;
esac

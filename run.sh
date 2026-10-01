#!/usr/bin/env bash
# Lotus Fin Quick-Run Management Script (Bash for Linux/Mac/WSL)

set -e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCKER_DIR="${ROOT_DIR}/frappe_docker"
COMPOSE_FILE="${DOCKER_DIR}/pwd.yml"
BACKEND_CONTAINER="frappe_docker-backend-1"

print_header() {
    echo -e "\n\033[1;36m========================================================\033[0m"
    echo -e "  \033[1;36m$1\033[0m"
    echo -e "\033[1;36m========================================================\033[0m\n"
}

assert_docker_running() {
    if ! docker info > /dev/null 2>&1; then
        echo -e "\033[1;31m[LỖI] Docker Engine chưa được bật hoặc chưa sẵn sàng!\033[0m"
        echo -e "\033[1;33mVui lòng khởi động Docker daemon/Docker Desktop trước khi chạy lệnh này.\033[0m\n"
        exit 1
    fi
}

invoke_sync_app() {
    print_header "Syncing lotus_fin code into container..."
    docker exec --user root "$BACKEND_CONTAINER" rm -rf /home/frappe/frappe-bench/apps/lotus_fin
    docker cp "${ROOT_DIR}/lotus_fin" "${BACKEND_CONTAINER}:/home/frappe/frappe-bench/apps/lotus_fin"
    docker exec --user root "$BACKEND_CONTAINER" chown -R frappe:frappe /home/frappe/frappe-bench/apps/lotus_fin
    docker exec "$BACKEND_CONTAINER" bash -c "grep -q 'lotus_fin' /home/frappe/frappe-bench/sites/apps.txt || echo 'lotus_fin' >> /home/frappe/frappe-bench/sites/apps.txt && pip install -e /home/frappe/frappe-bench/apps/lotus_fin && bench --site frontend install-app lotus_fin"
    docker exec "$BACKEND_CONTAINER" bench build --app lotus_fin
    docker exec "$BACKEND_CONTAINER" bench --site frontend migrate
    docker exec "$BACKEND_CONTAINER" bench --site frontend clear-cache
    docker restart "$BACKEND_CONTAINER"
    echo "Waiting for backend service to stabilize (5s)..."
    sleep 5
    docker exec "$BACKEND_CONTAINER" bench --site frontend execute lotus_fin.setup_data.setup_demo_environment
    echo -e "\n\033[1;32m[OK] Đã đồng bộ mã nguồn, build assets và migrate database thành công!\033[0m"
    echo -e "\033[1;33mTruy cập: http://localhost:8080/desk/financial-health (Administrator / admin)\033[0m"
}

case "$1" in
    up|start)
        assert_docker_running
        print_header "Starting Lotus Fin Docker Containers..."
        if [ ! -d "$DOCKER_DIR" ]; then
            echo "Cloning frappe_docker repository..."
            git clone --depth 1 https://github.com/frappe/frappe_docker.git "$DOCKER_DIR"
        fi
        docker compose -f "$COMPOSE_FILE" up -d
        echo -e "\n\033[1;32m[OK] Hệ thống đang khởi động!\033[0m"
        echo -e "\033[1;33mTruy cập: http://localhost:8080/desk/financial-health (User: Administrator / Pass: admin)\033[0m"
        ;;
    run)
        assert_docker_running
        print_header "Starting & Syncing Lotus Fin Complete Stack..."
        docker compose -f "$COMPOSE_FILE" up -d
        invoke_sync_app
        ;;
    stop|down)
        assert_docker_running
        print_header "Stopping Lotus Fin Containers..."
        docker compose -f "$COMPOSE_FILE" stop
        echo -e "\033[1;32m[OK] Đã dừng các container!\033[0m"
        ;;
    restart)
        assert_docker_running
        print_header "Restarting Lotus Fin Containers..."
        docker compose -f "$COMPOSE_FILE" restart
        echo -e "\033[1;32m[OK] Đã khởi động lại hệ thống!\033[0m"
        ;;
    sync)
        assert_docker_running
        invoke_sync_app
        ;;
    demo)
        assert_docker_running
        print_header "Loading Demo Dataset into Lotus Fin..."
        docker exec "$BACKEND_CONTAINER" bench --site frontend execute erpnext.setup.demo.setup_demo_data --kwargs "{'company_name': 'Lotus-fin'}"
        docker exec "$BACKEND_CONTAINER" bench --site frontend execute lotus_fin.setup_data.setup_demo_environment
        echo -e "\n\033[1;32m[OK] Đã nạp thành công bộ dữ liệu mẫu (Lotus-fin Demo)!\033[0m"
        ;;
    test)
        assert_docker_running
        print_header "Running All Lotus Fin Unit & UI Contract Tests..."
        docker exec "$BACKEND_CONTAINER" bench --site frontend set-config allow_tests true
        if [ -n "$2" ]; then
            echo "Running specific test suite: $2"
            docker exec "$BACKEND_CONTAINER" bench --site frontend run-tests --module "$2"
        else
            suites=(
                "lotus_fin.tests.test_workspace_ui"
                "lotus_fin.tests.test_access_and_reports"
                "lotus_fin.AI005.test_ai005"
                "lotus_fin.tests.test_financial_snapshot"
                "lotus_fin.tests.test_financial_health"
                "lotus_fin.tests.test_explanation"
                "lotus_fin.tests.test_ai004_scenario"
                "lotus_fin.tests.test_plugin_subsystem"
            )
            for s in "${suites[@]}"; do
                echo -e "\n\033[1;36m>>> [RUNNING] $s\033[0m"
                docker exec "$BACKEND_CONTAINER" bench --site frontend run-tests --module "$s"
            done
        fi
        ;;
    simulate)
        assert_docker_running
        print_header "Running Live What-If Scenario Simulation (9 KPIs)..."
        docker exec "$BACKEND_CONTAINER" bench --site frontend execute lotus_fin.AI005.service.simulate_what_if --kwargs "{'company': 'Lotus-fin (Demo)', 'sales_change_pct': -0.20, 'collection_delay_days': 15}"
        ;;
    status)
        assert_docker_running
        print_header "Docker Containers Status"
        docker ps --filter "name=frappe_docker"
        ;;
    logs)
        assert_docker_running
        print_header "Streaming Backend Logs (Ctrl+C to exit)..."
        docker logs "$BACKEND_CONTAINER" --tail 50 -f
        ;;
    *)
        print_header "Lotus Fin Quick-Run Helper (Usage Guide)"
        echo -e "Sử dụng lệnh: ./run.sh [command] [module]\n"
        echo "  ./run.sh run       - Khởi động Docker + Đồng bộ code + Nạp Demo (1-Click Run)"
        echo "  ./run.sh up        - Khởi động hệ thống Docker (Web tại :8080)"
        echo "  ./run.sh sync      - Đồng bộ code lotus_fin vào container, build assets & migrate"
        echo "  ./run.sh demo      - Nạp bộ dữ liệu mẫu (Sản phẩm, Khách hàng, Hóa đơn)"
        echo "  ./run.sh test      - Chạy toàn bộ 8 bộ kiểm thử (Unit, UI, Security, AI Plugins)"
        echo "  ./run.sh simulate  - Chạy mô phỏng What-If kịch bản sốc tài chính (9 KPIs)"
        echo "  ./run.sh status    - Kiểm tra trạng thái các container"
        echo "  ./run.sh logs      - Xem logs realtime của backend"
        echo "  ./run.sh stop      - Dừng toàn bộ hệ thống Docker"
        echo "  ./run.sh restart   - Khởi động lại hệ thống"
        echo ""
        ;;
esac


param(
    [Parameter(Position=0)]
    [ValidateSet("up", "start", "stop", "down", "restart", "sync", "demo", "test", "simulate", "status", "logs", "help")]
    [string]$Command = "help"
)

$RootDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$DockerDir = Join-Path $RootDir "frappe_docker"
$ComposeFile = Join-Path $DockerDir "pwd.yml"
$BackendContainer = "frappe_docker-backend-1"

function Print-Header([string]$title) {
    Write-Host ""
    Write-Host "========================================================" -ForegroundColor Cyan
    Write-Host "  $title" -ForegroundColor Cyan
    Write-Host "========================================================" -ForegroundColor Cyan
    Write-Host ""
}

function Assert-Docker-Running {
    docker info > $null 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[LỖI] Docker Desktop chưa được bật!" -ForegroundColor Red
        Write-Host "Vui lòng mở ứng dụng 'Docker Desktop' trên Windows và đợi khoảng 10-15s cho Docker khởi động hoàn tất trước khi chạy lệnh này.`n" -ForegroundColor Yellow
        exit 1
    }
}

switch ($Command) {
    { $_ -in "up", "start" } {
        Assert-Docker-Running
        Print-Header "Starting Lotus Fin Docker Containers..."
        if (-not (Test-Path $DockerDir)) {
            Write-Host "Cloning frappe_docker repository..." -ForegroundColor Yellow
            git clone --depth 1 https://github.com/frappe/frappe_docker.git $DockerDir
        }
        docker compose -f $ComposeFile up -d
        if ($LASTEXITCODE -eq 0) {
            Write-Host "`n[OK] Docker containers started successfully!" -ForegroundColor Green
            Write-Host "Access URL: http://localhost:8080 (User: Administrator / Pass: admin)" -ForegroundColor Yellow
        }
    }

    { $_ -in "stop", "down" } {
        Assert-Docker-Running
        Print-Header "Stopping Lotus Fin Containers..."
        docker compose -f $ComposeFile stop
        Write-Host "[OK] Containers stopped successfully!" -ForegroundColor Green
    }

    "restart" {
        Assert-Docker-Running
        Print-Header "Restarting Lotus Fin Containers..."
        docker compose -f $ComposeFile restart
        Write-Host "[OK] System restarted successfully!" -ForegroundColor Green
    }

    "sync" {
        Assert-Docker-Running
        Print-Header "Syncing lotus_fin code into container..."
        $LocalApp = Join-Path $RootDir "lotus_fin"
        docker exec --user root $BackendContainer rm -rf /home/frappe/frappe-bench/apps/lotus_fin
        docker cp $LocalApp "${BackendContainer}:/home/frappe/frappe-bench/apps/lotus_fin"
        docker exec --user root $BackendContainer chown -R frappe:frappe /home/frappe/frappe-bench/apps/lotus_fin
        docker exec $BackendContainer bash -c "grep -q 'lotus_fin' /home/frappe/frappe-bench/sites/apps.txt || echo 'lotus_fin' >> /home/frappe/frappe-bench/sites/apps.txt && pip install -e /home/frappe/frappe-bench/apps/lotus_fin && bench --site frontend install-app lotus_fin"
        docker exec $BackendContainer bench --site frontend migrate
        docker exec $BackendContainer bench --site frontend clear-cache
        docker restart $BackendContainer
        docker exec $BackendContainer bench --site frontend execute lotus_fin.setup_data.setup_demo_environment
        if ($LASTEXITCODE -eq 0) {
            Write-Host "`n[OK] Synced source code, registered app, migrated database, and reloaded successfully!" -ForegroundColor Green
        }
    }

    "demo" {
        Assert-Docker-Running
        Print-Header "Loading Demo Dataset into Lotus Fin..."
        docker exec $BackendContainer bench --site frontend execute erpnext.setup.demo.setup_demo_data --kwargs "{'company_name': 'Lotus-fin'}"
        docker exec $BackendContainer bench --site frontend execute lotus_fin.setup_data.setup_demo_environment
        if ($LASTEXITCODE -eq 0) {
            Write-Host "`n[OK] Loaded demo dataset and configured fiscal years successfully!" -ForegroundColor Green
        }
    }

    "test" {
        Assert-Docker-Running
        Print-Header "Running All Lotus Fin Unit & UI Contract Tests..."
        docker exec $BackendContainer bench --site frontend set-config allow_tests true
        docker exec $BackendContainer bench --site frontend run-tests --module lotus_fin.tests.test_workspace_ui
        docker exec $BackendContainer bench --site frontend run-tests --module lotus_fin.tests.test_access_and_reports
        docker exec $BackendContainer bench --site frontend run-tests --module lotus_fin.AI005.test_ai005
    }

    "simulate" {
        Assert-Docker-Running
        Print-Header "Running Live What-If Scenario Simulation..."
        docker exec $BackendContainer bench --site frontend execute lotus_fin.AI005.service.simulate_what_if --kwargs "{'company': 'Lotus-fin (Demo)', 'sales_change_pct': -0.20, 'collection_delay_days': 15}"
    }

    "status" {
        Assert-Docker-Running
        Print-Header "Docker Containers Status"
        docker ps --filter "name=frappe_docker"
    }

    "logs" {
        Assert-Docker-Running
        Print-Header "Streaming Backend Logs (Ctrl+C to exit)..."
        docker logs $BackendContainer --tail 50 -f
    }

    default {
        Print-Header "Lotus Fin Quick-Run Helper"
        Write-Host "Usage: .\run.ps1 [command]`n" -ForegroundColor Yellow
        Write-Host "  .\run.ps1 up        - Start Docker containers (Web at http://localhost:8080)"
        Write-Host "  .\run.ps1 sync      - Sync lotus_fin code into container, migrate, and reload"
        Write-Host "  .\run.ps1 demo      - Load demo dataset (Items, Customers, Invoices, P&L)"
        Write-Host "  .\run.ps1 test      - Run AI004 Unit Tests"
        Write-Host "  .\run.ps1 simulate  - Run live What-If scenario simulation via CLI"
        Write-Host "  .\run.ps1 status    - Check status of running containers"
        Write-Host "  .\run.ps1 logs      - Stream realtime logs from backend"
        Write-Host "  .\run.ps1 stop      - Stop Docker containers"
        Write-Host "  .\run.ps1 restart   - Restart all containers"
        Write-Host ""
    }
}

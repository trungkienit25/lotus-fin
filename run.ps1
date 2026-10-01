param(
    [Parameter(Position=0)]
    [ValidateSet("up", "start", "run", "stop", "down", "restart", "sync", "demo", "test", "simulate", "status", "logs", "open", "help")]
    [string]$Command = "help",

    [Parameter(Position=1)]
    [string]$Module = ""
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
        Write-Host "[THONG BAO] Docker Engine chua san sang. Dang kiem tra..." -ForegroundColor Yellow
        $DockerExe = "C:\Program Files\Docker\Docker\Docker Desktop.exe"
        if (Test-Path $DockerExe) {
            Start-Process $DockerExe -ErrorAction SilentlyContinue
            Write-Host "Dang cho Docker Engine san sang (toi da 60s)..." -ForegroundColor Cyan
            $timeout = 60
            $elapsed = 0
            while ($elapsed -lt $timeout) {
                Start-Sleep -Seconds 3
                $elapsed += 3
                docker info > $null 2>&1
                if ($LASTEXITCODE -eq 0) {
                    Write-Host "[OK] Docker Engine da san sang!`n" -ForegroundColor Green
                    return
                }
                Write-Host "  ... dang doi Docker Desktop khoi dong ($elapsed s)" -ForegroundColor Gray
            }
        }
        Write-Host "[LOI] Docker Desktop chua duoc bat!" -ForegroundColor Red
        Write-Host "Vui long mo ung dung Docker Desktop tu Start Menu va doi Docker hien Engine Running, sau do chay lai lenh nay.`n" -ForegroundColor Yellow
        exit 1
    }
}

function Invoke-SyncApp {
    Print-Header "Syncing lotus_fin code into container..."
    $LocalApp = Join-Path $RootDir "lotus_fin"
    docker exec --user root $BackendContainer rm -rf /home/frappe/frappe-bench/apps/lotus_fin
    docker cp $LocalApp "${BackendContainer}:/home/frappe/frappe-bench/apps/lotus_fin"
    docker exec --user root $BackendContainer chown -R frappe:frappe /home/frappe/frappe-bench/apps/lotus_fin
    docker exec $BackendContainer bash -c 'grep -q lotus_fin /home/frappe/frappe-bench/sites/apps.txt || echo lotus_fin >> /home/frappe/frappe-bench/sites/apps.txt'
    docker exec $BackendContainer pip install -e /home/frappe/frappe-bench/apps/lotus_fin
    docker exec $BackendContainer bench --site frontend install-app lotus_fin
    docker exec $BackendContainer bench build --app lotus_fin
    docker exec $BackendContainer bench --site frontend migrate
    docker exec $BackendContainer bench --site frontend clear-cache
    docker restart $BackendContainer
    Write-Host "Waiting for backend service to stabilize (5s)..." -ForegroundColor Gray
    Start-Sleep -Seconds 5
    docker exec $BackendContainer bench --site frontend execute lotus_fin.setup_data.setup_demo_environment
    if ($LASTEXITCODE -eq 0) {
        Write-Host "`n[OK] Synced source code, built assets, migrated DB, and reloaded successfully!" -ForegroundColor Green
        Write-Host "Truy cap ung dung: http://localhost:8080/desk/financial-health" -ForegroundColor Yellow
        Write-Host "Tai khoan: Administrator / Mat khau: admin" -ForegroundColor Yellow
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
            Write-Host "Truy cap URL: http://localhost:8080/desk/financial-health (Administrator / admin)" -ForegroundColor Yellow
        }
    }

    "run" {
        Assert-Docker-Running
        Print-Header "Starting and Syncing Lotus Fin Complete Stack..."
        docker compose -f $ComposeFile up -d
        Invoke-SyncApp
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
        Invoke-SyncApp
    }

    "demo" {
        Assert-Docker-Running
        Print-Header "Loading Demo Dataset into Lotus Fin..."
        docker exec $BackendContainer bench --site frontend execute erpnext.setup.demo.setup_demo_data --kwargs '{\"company_name\": \"Lotus-fin\"}'
        docker exec $BackendContainer bench --site frontend execute lotus_fin.setup_data.setup_demo_environment
        if ($LASTEXITCODE -eq 0) {
            Write-Host "`n[OK] Loaded demo dataset and configured fiscal years successfully!" -ForegroundColor Green
        }
    }

    "test" {
        Assert-Docker-Running
        Print-Header "Running Lotus Fin Test Suites..."
        docker exec $BackendContainer bench --site frontend set-config allow_tests true
        $suites = @(
            "lotus_fin.tests.test_workspace_ui",
            "lotus_fin.tests.test_access_and_reports",
            "lotus_fin.AI005.test_ai005",
            "lotus_fin.tests.test_financial_snapshot",
            "lotus_fin.tests.test_financial_health",
            "lotus_fin.tests.test_explanation",
            "lotus_fin.tests.test_ai004_scenario",
            "lotus_fin.tests.test_cashflow_engine",
            "lotus_fin.tests.test_cashflow_failclosed",
            "lotus_fin.tests.test_cashflow_security",
            "lotus_fin.tests.test_plugin_subsystem"
        )
        if ($Module -ne "") {
            Write-Host "Running specific test suite: $Module" -ForegroundColor Yellow
            docker exec $BackendContainer bench --site frontend run-tests --module $Module
        } else {
            foreach ($s in $suites) {
                Write-Host "`n>>> [RUNNING] $s" -ForegroundColor Cyan
                docker exec $BackendContainer bench --site frontend run-tests --module $s
            }
        }
    }

    "simulate" {
        Assert-Docker-Running
        Print-Header "Running Live What-If Scenario Simulation..."
        docker exec $BackendContainer bench --site frontend execute lotus_fin.AI005.service.simulate_what_if --kwargs '{\"company\": \"Lotus-fin (Demo)\", \"sales_change_pct\": -0.20, \"collection_delay_days\": 15}'
    }

    "open" {
        Print-Header "Opening Lotus Fin in Default Browser..."
        Start-Process "http://localhost:8080/desk/financial-health"
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
        Print-Header "Lotus Fin Quick-Run Helper (Usage Guide)"
        Write-Host "Su dung lenh: .\run.ps1 [command] [module]`n" -ForegroundColor Yellow
        Write-Host "  .\run.ps1 run       - Khoi dong Docker + Dong bo code + Nap Demo (1-Click Run)"
        Write-Host "  .\run.ps1 up        - Khoi dong cac Docker containers"
        Write-Host "  .\run.ps1 sync      - Dong bo code moi nhat vao container, build assets va migrate"
        Write-Host "  .\run.ps1 test      - Chay toan bo 8 bo kiem thu (Unit, UI, Security, AI Plugins)"
        Write-Host "  .\run.ps1 test <mod>- Chay mot module test cu the (VD: .\run.ps1 test test_plugin_subsystem)"
        Write-Host "  .\run.ps1 demo      - Nap bo du lieu mau (San pham, Hoa don, Khach hang)"
        Write-Host "  .\run.ps1 simulate  - Chay mo phong What-If kich ban soc tai chinh (9 KPIs)"
        Write-Host "  .\run.ps1 open      - Mo giao dien web http://localhost:8080/desk/financial-health"
        Write-Host "  .\run.ps1 status    - Xem trang thai cac container"
        Write-Host "  .\run.ps1 logs      - Xem logs realtime cua backend"
        Write-Host "  .\run.ps1 stop      - Dung toan bo he thong Docker"
        Write-Host "  .\run.ps1 restart   - Khoi dong lai cac container"
        Write-Host ""
    }
}


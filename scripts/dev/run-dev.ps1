<#
.SYNOPSIS
    Lotus Fin — Windows PowerShell Development Launcher (run-dev.ps1)
.DESCRIPTION
    Detects Windows environment, verifies Docker & Node.js, starts backend stack,
    seeds corporate accounting data, and launches the Vite development frontend.
#>

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$rootDir = Split-Path -Parent (Split-Path -Parent $scriptDir)
$dockerDir = Join-Path $rootDir "frappe_docker"
$composeFile = Join-Path $dockerDir "pwd.yml"
$feDir = Join-Path $rootDir "frontend"


Write-Host "`n>>> [1/5] Detecting System & Prerequisites..." -ForegroundColor Cyan
Write-Host "Operating System: Microsoft Windows ($( [System.Environment]::OSVersion.VersionString ))" -ForegroundColor Green

# Check Docker
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "[ERROR] Docker is not installed or not in PATH. Please install Docker Desktop for Windows." -ForegroundColor Red
    exit 1
}
try {
    docker info > $null 2>&1
    Write-Host "✔ Docker Engine is running." -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Docker Desktop is installed but not running. Please start Docker Desktop first." -ForegroundColor Red
    exit 1
}

# Check Node.js
if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Host "[ERROR] Node.js is not found. Please install Node.js (v18+) from https://nodejs.org/" -ForegroundColor Red
    exit 1
}
Write-Host "✔ Node.js $(node -v) & npm $(npm -v) found." -ForegroundColor Green

Write-Host "`n>>> [2/5] Starting Backend Containers (Frappe & MariaDB)..." -ForegroundColor Cyan
if (-not (Test-Path $dockerDir)) {
    git clone --depth 1 https://github.com/frappe/frappe_docker.git $dockerDir
}
docker compose -f $composeFile up -d

Write-Host "`n>>> [3/5] Waiting for Frappe Backend..." -ForegroundColor Cyan
$retries = 30
$count = 0
do {
    Start-Sleep -Seconds 4
    $count++
    $running = docker ps --filter "name=frappe_docker-backend-1" --filter "status=running" -q
} until ($running -or ($count -ge $retries))

Write-Host "`n>>> [4/5] Synchronizing Lotus Fin App & Seed Demo Ledger..." -ForegroundColor Cyan
docker exec frappe_docker-backend-1 bench --site frontend execute erpnext.setup.demo.setup_demo_data --kwargs "{'company_name': 'Lotus-fin'}" 2>$null
docker exec frappe_docker-backend-1 bench --site frontend execute lotus_fin.setup_data.setup_demo_environment 2>$null

Write-Host "`n>>> [5/5] Launching Frontend Development Server..." -ForegroundColor Cyan
if (-not (Test-Path (Join-Path $feDir "node_modules"))) {
    Write-Host "Installing frontend dependencies..." -ForegroundColor Yellow
    Push-Location $feDir
    npm install
    Pop-Location
}

Write-Host "`n=====================================================================" -ForegroundColor Green
Write-Host "       🚀 LOTUS FIN DEV ENVIRONMENT ONLINE (WINDOWS)                 " -ForegroundColor Green
Write-Host "=====================================================================" -ForegroundColor Green
Write-Host "  • Frontend Web App:   http://localhost:5173" -ForegroundColor Cyan
Write-Host "  • Frappe Desk:        http://localhost:8080" -ForegroundColor Cyan
Write-Host "  • Admin Credentials:  Administrator / admin" -ForegroundColor White
Write-Host "=====================================================================`n"

Push-Location $feDir
npm run dev
Pop-Location


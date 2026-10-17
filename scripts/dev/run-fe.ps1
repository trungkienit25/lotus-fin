<#
.SYNOPSIS
    Lotus Fin — Frontend Management Script (PowerShell for Windows)
.DESCRIPTION
    Convenience script to start, build, and manage the Lotus Fin React/TailAdmin frontend.
.EXAMPLE
    .\run-fe.ps1
    .\run-fe.ps1 dev
    .\run-fe.ps1 build
    .\run-fe.ps1 check
#>

param (
    [Parameter(Position=0)]
    [ValidateSet("dev", "start", "build", "install", "check", "typecheck", "preview", "clean", "help")]
    [string]$Action = "dev"
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir = Split-Path -Parent (Split-Path -Parent $ScriptDir)
$FeDir = Join-Path $RootDir "frontend"


function Print-Header([string]$Title) {
    Write-Host ""
    Write-Host "========================================================" -ForegroundColor Cyan
    Write-Host "  $Title" -ForegroundColor Cyan
    Write-Host "========================================================" -ForegroundColor Cyan
    Write-Host ""
}

function Assert-NodeInstalled {
    if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
        Write-Host "[ERROR] Node.js is not installed or not found in PATH!" -ForegroundColor Red
        Write-Host "Please install Node.js (v18 or higher recommended) from https://nodejs.org/" -ForegroundColor Yellow
        exit 1
    }
}

function Ensure-Dependencies {
    $NodeModules = Join-Path $FeDir "node_modules"
    if (-not (Test-Path $NodeModules)) {
        Print-Header "node_modules not found. Installing dependencies..."
        Push-Location $FeDir
        try {
            npm install
        } finally {
            Pop-Location
        }
    }
}

switch ($Action) {
    { $_ -in @("dev", "start") } {
        Assert-NodeInstalled
        Ensure-Dependencies
        Print-Header "Starting Lotus Fin TailAdmin Frontend (Vite Dev Server)..."
        Write-Host "[INFO] Dev server launching at http://localhost:5173" -ForegroundColor Green
        Write-Host "[INFO] Proxying API calls to Frappe Backend at http://localhost:8080`n" -ForegroundColor Yellow
        Push-Location $FeDir
        try {
            npm run dev
        } finally {
            Pop-Location
        }
    }

    "build" {
        Assert-NodeInstalled
        Ensure-Dependencies
        Print-Header "Building Lotus Fin Frontend for Production..."
        Push-Location $FeDir
        try {
            npm run build
            Write-Host "`n[OK] Production build created successfully in frontend/dist/" -ForegroundColor Green
        } finally {
            Pop-Location
        }
    }

    "install" {
        Assert-NodeInstalled
        Print-Header "Installing / Updating Frontend Dependencies..."
        Push-Location $FeDir
        try {
            npm install
            Write-Host "`n[OK] Dependencies installed successfully!" -ForegroundColor Green
        } finally {
            Pop-Location
        }
    }

    { $_ -in @("check", "typecheck") } {
        Assert-NodeInstalled
        Print-Header "Running TypeScript Type Check..."
        Push-Location $FeDir
        try {
            npx tsc --noEmit
            Write-Host "`n[OK] Type check passed with 0 errors!" -ForegroundColor Green
        } finally {
            Pop-Location
        }
    }

    "preview" {
        Assert-NodeInstalled
        Print-Header "Previewing Production Build..."
        Push-Location $FeDir
        try {
            npm run preview
        } finally {
            Pop-Location
        }
    }

    "clean" {
        Print-Header "Cleaning Build Artifacts & Vite Cache..."
        $DistDir = Join-Path $FeDir "dist"
        $ViteCache = Join-Path $FeDir "node_modules\.vite"
        if (Test-Path $DistDir) { Remove-Item -Recurse -Force $DistDir }
        if (Test-Path $ViteCache) { Remove-Item -Recurse -Force $ViteCache }
        Write-Host "[OK] Cleaned dist and .vite cache!" -ForegroundColor Green
    }

    "help" {
        Print-Header "Lotus Fin Frontend Management Commands"
        Write-Host "Usage: .\run-fe.ps1 [Action]"
        Write-Host ""
        Write-Host "Actions:"
        Write-Host "  dev | start  (default) Start Vite development server (http://localhost:5173)"
        Write-Host "  build                  Run TypeScript check & production build"
        Write-Host "  install                Install/update npm dependencies"
        Write-Host "  check                  Run TypeScript type checking (tsc --noEmit)"
        Write-Host "  preview                Preview the production build (vite preview)"
        Write-Host "  clean                  Remove dist\ and .vite build caches"
        Write-Host "  help                   Show this help menu"
        Write-Host ""
    }
}


<#
.SYNOPSIS
    Lotus Fin — Windows Operations Dispatcher (run.ps1)
.DESCRIPTION
    Dispatches operational commands to specialized scripts:
    - .\run.ps1 dev         -> Start local development stack (backend + Vite frontend)
    - .\run.ps1 deploy      -> Cloud / server deployment
    - .\run.ps1 packaging   -> Package container images
    - .\run.ps1 fe          -> Frontend management (run-fe.ps1)
#>

[CmdletBinding()]
param(
    [Parameter(Position=0)]
    [string]$Command = "help",
    [Parameter(ValueFromRemainingArguments=$true)]
    [string[]]$RemainingArgs
)

$ErrorActionPreference = "Stop"
$rootDir = Split-Path -Parent $MyInvocation.MyCommand.Path

switch ($Command.ToLower()) {
    { $_ -in "dev", "start", "local" } {
        & (Join-Path $rootDir "scripts\dev\run-dev.ps1") @RemainingArgs
        break
    }
    { $_ -in "fe", "frontend" } {
        & (Join-Path $rootDir "scripts\dev\run-fe.ps1") @RemainingArgs
        break
    }
    { $_ -in "package", "packaging", "build" } {
        Write-Host "Invoking packaging pipeline via bash..." -ForegroundColor Cyan
        & bash (Join-Path $rootDir "scripts\packaging\run-packaging.sh") @RemainingArgs
        break
    }
    { $_ -in "container", "prod", "production" } {
        Write-Host "Invoking container orchestrator via bash..." -ForegroundColor Cyan
        & bash (Join-Path $rootDir "scripts\container\run-container.sh") @RemainingArgs
        break
    }
    { $_ -in "deploy", "prod-deploy" } {
        Write-Host "Invoking 1-click cloud deployer via bash..." -ForegroundColor Cyan
        & bash (Join-Path $rootDir "scripts\deploy\run-deploy.sh") @RemainingArgs
        break
    }
    default {
        Write-Host "=====================================================================" -ForegroundColor Cyan
        Write-Host "                Lotus Fin Operations CLI (Windows)                   " -ForegroundColor Cyan
        Write-Host "=====================================================================" -ForegroundColor Cyan
        Write-Host "Usage: .\run.ps1 [command]"
        Write-Host ""
        Write-Host "Available Commands:"
        Write-Host "  .\run.ps1 dev         - Start local dev stack (Frappe + MariaDB + Vite frontend)"
        Write-Host "  .\run.ps1 fe          - Manage frontend (dev, build, preview)"
        Write-Host "  .\run.ps1 deploy      - 1-Click cloud deployment pipeline"
        Write-Host "  .\run.ps1 packaging   - Build production container images"
        Write-Host "  .\run.ps1 container   - Manage production containers on Port 80"
        Write-Host "=====================================================================" -ForegroundColor Cyan
    }
}

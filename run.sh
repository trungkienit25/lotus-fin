#!/usr/bin/env bash
# ==============================================================================
# Lotus Fin — Unified Dispatcher
# Backward-compatible router to the specialized operational scripts:
#   - ./run-dev.sh        (Development setup and local environment)
#   - ./run-packaging.sh  (Package production Docker container images)
#   - ./run-container.sh  (Deploy and run production containers on port 80)
# ==============================================================================

set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

case "$1" in
    deploy|prod-deploy)
        shift
        exec "${SCRIPT_DIR}/scripts/deploy/run-deploy.sh" "$@"
        ;;
    dev|start|local)
        shift
        exec "${SCRIPT_DIR}/scripts/dev/run-dev.sh" "$@"
        ;;
    package|packaging|build)
        shift
        exec "${SCRIPT_DIR}/scripts/packaging/run-packaging.sh" "$@"
        ;;
    container|prod|production)
        shift
        exec "${SCRIPT_DIR}/scripts/container/run-container.sh" "$@"
        ;;
    status)
        if docker compose -f "${SCRIPT_DIR}/docker/production/compose.prod.yml" ps -q 2>/dev/null | grep -q .; then
            exec "${SCRIPT_DIR}/scripts/container/run-container.sh" status
        else
            docker ps --filter "name=frappe_docker"
        fi
        ;;
    logs)
        shift
        if docker compose -f "${SCRIPT_DIR}/docker/production/compose.prod.yml" ps -q 2>/dev/null | grep -q .; then
            exec "${SCRIPT_DIR}/scripts/container/run-container.sh" logs "$@"
        else
            docker logs "frappe_docker-backend-1" --tail 100 -f
        fi
        ;;
    stop|down)
        if docker compose -f "${SCRIPT_DIR}/docker/production/compose.prod.yml" ps -q 2>/dev/null | grep -q .; then
            exec "${SCRIPT_DIR}/scripts/container/run-container.sh" stop
        else
            docker compose -f "${SCRIPT_DIR}/frappe_docker/pwd.yml" stop
        fi
        ;;
    *)
        echo "====================================================================="
        echo "                🌿 Lotus Fin Operations CLI                         "
        echo "====================================================================="
        echo "Usage: ./run.sh [command]"
        echo ""
        echo "Core Operational Scripts:"
        echo "  ./run.sh deploy      - 🚀 1-Click Cloud Deploy: Check env, migrate & seed DB, launch port 80"
        echo "  ./run.sh dev         - 💻 Local Dev: Auto-detect OS, check env, start backend & Vite dev server"
        echo "  ./run.sh packaging   - 📦 Package: Build production Docker gateway image"
        echo "  ./run.sh container   - 🐳 Container: Run production multi-container stack on Port 80"
        echo ""
        echo "Quick Utilities:"
        echo "  ./run.sh status      - Check running container status"
        echo "  ./run.sh logs        - View backend and gateway logs"
        echo "  ./run.sh stop        - Gracefully stop containers"
        echo "====================================================================="
        ;;
esac
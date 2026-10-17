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
    dev|start|local)
        shift
        exec "${SCRIPT_DIR}/run-dev.sh" "$@"
        ;;
    package|packaging|build)
        shift
        exec "${SCRIPT_DIR}/run-packaging.sh" "$@"
        ;;
    container|prod|production|deploy)
        shift
        exec "${SCRIPT_DIR}/run-container.sh" "$@"
        ;;
    status)
        if docker compose -f "${SCRIPT_DIR}/docker/production/compose.prod.yml" ps -q 2>/dev/null | grep -q .; then
            exec "${SCRIPT_DIR}/run-container.sh" status
        else
            docker ps --filter "name=frappe_docker"
        fi
        ;;
    logs)
        shift
        if docker compose -f "${SCRIPT_DIR}/docker/production/compose.prod.yml" ps -q 2>/dev/null | grep -q .; then
            exec "${SCRIPT_DIR}/run-container.sh" logs "$@"
        else
            docker logs "frappe_docker-backend-1" --tail 100 -f
        fi
        ;;
    stop|down)
        if docker compose -f "${SCRIPT_DIR}/docker/production/compose.prod.yml" ps -q 2>/dev/null | grep -q .; then
            exec "${SCRIPT_DIR}/run-container.sh" stop
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
        echo "  ./run.sh dev         - Auto-detect OS, check env, start backend & frontend (same as ./run-dev.sh)"
        echo "  ./run.sh packaging   - Build & package all production Docker images (same as ./run-packaging.sh)"
        echo "  ./run.sh container   - Run production multi-container stack on Port 80 (same as ./run-container.sh)"
        echo ""
        echo "Quick Utilities:"
        echo "  ./run.sh status      - Check running container status"
        echo "  ./run.sh logs        - View backend and gateway logs"
        echo "  ./run.sh stop        - Gracefully stop containers"
        echo "====================================================================="
        ;;
esac
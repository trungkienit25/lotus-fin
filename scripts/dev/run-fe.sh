#!/usr/bin/env bash
# ==============================================================================
# Lotus Fin — Frontend Management Script (Bash for Linux / macOS / WSL / Git Bash)
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"
FE_DIR="${ROOT_DIR}/frontend"


print_header() {
    echo -e "\n\033[1;36m========================================================\033[0m"
    echo -e "  \033[1;36m$1\033[0m"
    echo -e "\033[1;36m========================================================\033[0m\n"
}

assert_node_installed() {
    if ! command -v node > /dev/null 2>&1; then
        echo -e "\033[1;31m[ERROR] Node.js is not installed or not found in PATH!\033[0m"
        echo -e "\033[1;33mPlease install Node.js (v18 or higher recommended) from https://nodejs.org/\033[0m\n"
        exit 1
    fi
    if ! command -v npm > /dev/null 2>&1; then
        echo -e "\033[1;31m[ERROR] npm package manager is not installed or not found in PATH!\033[0m"
        exit 1
    fi
}

ensure_dependencies() {
    if [ ! -d "${FE_DIR}/node_modules" ]; then
        print_header "node_modules not found. Installing dependencies..."
        cd "${FE_DIR}"
        npm install
    fi
}

case "$1" in
    dev|start|"")
        assert_node_installed
        ensure_dependencies
        print_header "Starting Lotus Fin TailAdmin Frontend (Vite Dev Server)..."
        echo -e "\033[1;32m[INFO] Dev server launching at http://localhost:5173\033[0m"
        echo -e "\033[1;33m[INFO] Proxying API calls to Frappe Backend at http://localhost:8080\033[0m\n"
        cd "${FE_DIR}"
        npm run dev
        ;;
    build)
        assert_node_installed
        ensure_dependencies
        print_header "Building Lotus Fin Frontend for Production..."
        cd "${FE_DIR}"
        npm run build
        echo -e "\n\033[1;32m[OK] Production build created successfully in frontend/dist/\033[0m"
        ;;
    install)
        assert_node_installed
        print_header "Installing / Updating Frontend Dependencies..."
        cd "${FE_DIR}"
        npm install
        echo -e "\n\033[1;32m[OK] Dependencies installed successfully!\033[0m"
        ;;
    check|typecheck)
        assert_node_installed
        print_header "Running TypeScript Type Check..."
        cd "${FE_DIR}"
        npx tsc --noEmit
        echo -e "\n\033[1;32m[OK] Type check passed with 0 errors!\033[0m"
        ;;
    preview)
        assert_node_installed
        print_header "Previewing Production Build..."
        cd "${FE_DIR}"
        npm run preview
        ;;
    clean)
        print_header "Cleaning Build Artifacts & Vite Cache..."
        rm -rf "${FE_DIR}/dist"
        rm -rf "${FE_DIR}/node_modules/.vite"
        echo -e "\033[1;32m[OK] Cleaned dist and .vite cache!\033[0m"
        ;;
    help|--help|-h)
        print_header "Lotus Fin Frontend Management Commands"
        echo "Usage: ./run-fe.sh [command]"
        echo ""
        echo "Commands:"
        echo "  dev | start | (empty)  Start Vite development server (http://localhost:5173)"
        echo "  build                  Run TypeScript check & production build"
        echo "  install                Install/update npm dependencies"
        echo "  check                  Run TypeScript type checking (tsc --noEmit)"
        echo "  preview                Preview the production build (vite preview)"
        echo "  clean                  Remove dist/ and .vite build caches"
        echo "  help                   Show this help menu"
        echo ""
        ;;
    *)
        echo -e "\033[1;31m[ERROR] Unknown command: $1\033[0m"
        echo "Run './run-fe.sh help' for available commands."
        exit 1
        ;;
esac


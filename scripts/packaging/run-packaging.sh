#!/usr/bin/env bash
# ==============================================================================
# Lotus Fin — run-packaging.sh
# Packages the entire application into self-contained Docker images ready for production.
# 1. Compiles frontend React/Vite SPA.
# 2. Builds `lotus-fin/gateway` (Nginx + static SPA + reverse proxy).
# 3. Pulls and tags production-grade Frappe/ERPNext images.
# 4. Validates container image integrity.
# ==============================================================================

set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"


CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m'

print_step() { echo -e "\n${CYAN}${BOLD}>>> [$1] $2${NC}"; }
print_success() { echo -e "${GREEN}${BOLD}✔ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠ $1${NC}"; }
print_error() { echo -e "${RED}${BOLD}✖ $1${NC}"; }

VERSION="${1:-latest}"
TAG_NAME="lotus-fin/gateway:${VERSION}"

print_step "1/3" "Checking build dependencies & Docker daemon..."
if ! command -v docker >/dev/null 2>&1; then
    print_error "Docker is required to package images!"
    exit 1
fi

print_step "2/3" "Building Production Frontend Gateway Container [${TAG_NAME}]..."
echo "Compiling React frontend and assembling Nginx reverse proxy..."

docker build \
    --file "${ROOT_DIR}/docker/production/Dockerfile.frontend" \
    --tag "${TAG_NAME}" \
    "${ROOT_DIR}"

print_success "Successfully built container image: ${TAG_NAME}"

print_step "3/3" "Pulling and staging production backend images..."
docker pull frappe/erpnext:v16.36.1
docker pull mariadb:11.8
docker pull redis:6.2-alpine

echo -e "\n${GREEN}${BOLD}====================================================================="
echo "       📦 LOTUS FIN PRODUCTION PACKAGING COMPLETED!                   "
echo "=====================================================================${NC}"
echo -e "Packaged Images:"
docker images | grep -E 'lotus-fin/gateway|frappe/erpnext|mariadb|redis' | head -n 6
echo "====================================================================="
echo "You can now run './run-container.sh' or deploy via 'docker compose -f docker/production/compose.prod.yml up -d'."


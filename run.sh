#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ "$#" -eq 0 ]; then set -- help; fi
exec python3 "$ROOT_DIR/docker/lotus-core/manage.py" "$@"

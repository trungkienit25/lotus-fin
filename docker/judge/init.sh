#!/usr/bin/env bash
set -euo pipefail
cd /home/frappe/frappe-bench
: "${LOTUS_SITE:?Missing LOTUS_SITE}"
: "${LOTUS_ADMIN_PASSWORD:?Missing LOTUS_ADMIN_PASSWORD}"
: "${LOTUS_DB_PASSWORD:?Missing LOTUS_DB_PASSWORD}"
[[ "$LOTUS_SITE" =~ ^[a-zA-Z0-9][a-zA-Z0-9.-]*$ ]] || { echo 'Invalid LOTUS_SITE' >&2; exit 1; }
env/bin/python -c 'import lotus_fin, frappe; print("Bench app import:", lotus_fin.__file__)'
ls -1 apps > sites/apps.txt
bench set-config -g db_host db
bench set-config -gp db_port 3306
bench set-config -g redis_cache redis://redis-cache:6379
bench set-config -g redis_queue redis://redis-queue:6379
bench set-config -g redis_socketio redis://redis-queue:6379
bench set-config -gp socketio_port 9000
if [[ ! -f "sites/$LOTUS_SITE/site_config.json" ]]; then
    bench new-site "$LOTUS_SITE" --mariadb-user-host-login-scope='%' --admin-password "$LOTUS_ADMIN_PASSWORD" --db-root-username root --db-root-password "$LOTUS_DB_PASSWORD" --install-app erpnext
fi
if ! bench --site "$LOTUS_SITE" list-apps | awk '{print $1}' | grep -qx lotus_fin; then
    bench --site "$LOTUS_SITE" install-app lotus_fin
fi
bench --site "$LOTUS_SITE" migrate
bench --site "$LOTUS_SITE" clear-cache
env/bin/python /home/frappe/judge/smoke.py

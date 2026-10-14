#!/usr/bin/env bash
set -euo pipefail
cd /home/frappe/frappe-bench
: "${LOTUS_SITE:?Required}"
: "${LOTUS_DB_PASSWORD:?Required}"
: "${LOTUS_ADMIN_PASSWORD:?Required}"
[[ "$LOTUS_SITE" =~ ^core-[a-z0-9-]+\.localhost$ ]] || { echo 'Refusing non-isolated site'; exit 2; }
env/bin/python -c 'import frappe, lotus_fin.hooks, importlib.util; assert importlib.util.find_spec("erpnext") is None'
printf 'frappe\nlotus_fin\n' > sites/apps.txt
bench set-config -g db_host db
bench set-config -gp db_port 3306
bench set-config -g redis_cache redis://redis-cache:6379
bench set-config -g redis_queue redis://redis-queue:6379
bench set-config -g redis_socketio redis://redis-queue:6379
bench set-config -gp socketio_port 9000
if [[ ! -f "sites/$LOTUS_SITE/site_config.json" ]]; then
    bench new-site "$LOTUS_SITE" --mariadb-user-host-login-scope='%' --admin-password "$LOTUS_ADMIN_PASSWORD" --db-root-username root --db-root-password "$LOTUS_DB_PASSWORD"
fi
if ! bench --site "$LOTUS_SITE" list-apps | awk '{print $1}' | grep -qx lotus_fin; then
    bench --site "$LOTUS_SITE" install-app lotus_fin
fi
bench --site "$LOTUS_SITE" migrate
bench --site "$LOTUS_SITE" clear-cache
env/bin/python /home/frappe/lotus-core/smoke.py

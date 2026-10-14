# syntax=docker/dockerfile:1
# Low-disk P6 build: retain the pinned build/base runtime once, without a second bench copy.
FROM node:22.22.0-bookworm-slim@sha256:dd9d21971ec4395903fa6143c2b9267d048ae01ca6d3ea96f16cb30df6187d94 AS ui
WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm ci --ignore-scripts --no-audit --no-fund --loglevel=error && npm cache clean --force
COPY frontend/ ./
RUN npm run build -- --base=/assets/lotus_fin/core/

FROM frappe/build:version-16@sha256:e9139c9e399bc5d58b3f6e1988272f435eeb909163140eb735e4cc52697baa76 AS runtime
USER frappe
RUN bench init --frappe-branch=v16.35.0 --frappe-path=https://github.com/frappe/frappe \
    --no-procfile --no-backups --skip-redis-config-generation /home/frappe/frappe-bench \
    && test "$(git -C /home/frappe/frappe-bench/apps/frappe rev-parse HEAD)" = 012667b9c4e7f66d5e1ff5858d2e922331d4300a \
    && yarn cache clean && python3 -m pip cache purge
WORKDIR /home/frappe/frappe-bench
COPY --chown=frappe:frappe lotus_fin/ apps/lotus_fin/
COPY --chown=frappe:frappe docker/lotus-core/requirements.lock /tmp/lotus-requirements.lock
COPY --chown=frappe:frappe docker/lotus-core/framework.lock /tmp/lotus-framework.lock
RUN env/bin/pip install --no-cache-dir --quiet -r /tmp/lotus-framework.lock -r /tmp/lotus-requirements.lock -e apps/lotus_fin \
    && env/bin/pip check && printf 'frappe\nlotus_fin\n' > sites/apps.txt \
    && bench build --app lotus_fin \
    && env/bin/python -c 'import frappe, lotus_fin.hooks, lotus_fin.runtime.boundary, lotus_fin.runtime.health, importlib.util; assert importlib.util.find_spec("erpnext") is None' \
    && env/bin/pip freeze > /home/frappe/runtime-packages.lock \
    && printf '{}\n' > sites/common_site_config.json \
    && yarn cache clean && python3 -m pip cache purge
COPY --from=ui --chown=frappe:0 /frontend/dist/ /home/frappe/frappe-bench/sites/assets/lotus_fin/core/
COPY --from=ui --chown=frappe:0 /frontend/dist/index.html /home/frappe/frappe-bench/apps/lotus_fin/lotus_fin/templates/lotus_spa.html
COPY --chown=frappe:0 docker/lotus-core/ /home/frappe/lotus-core/
COPY --chmod=755 docker/lotus-core/upstream/main-entrypoint.sh /usr/local/bin/entrypoint.sh
COPY --chmod=755 docker/lotus-core/upstream/start.sh /usr/local/bin/start.sh
RUN rm sites/assets/lotus_fin/core/index.html \
    && mv sites/assets assets
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["start.sh"]

# syntax=docker/dockerfile:1
# Verified official Frappe version-16 build/base pair; Linux amd64 qualification.
FROM node:22.22.0-bookworm-slim@sha256:dd9d21971ec4395903fa6143c2b9267d048ae01ca6d3ea96f16cb30df6187d94 AS ui
WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm ci --ignore-scripts --no-audit --no-fund
COPY frontend/ ./
RUN npm run build -- --base=/assets/lotus_fin/core/

FROM frappe/build:version-16@sha256:e9139c9e399bc5d58b3f6e1988272f435eeb909163140eb735e4cc52697baa76 AS builder
USER frappe
RUN bench init --frappe-branch=v16.35.0 --frappe-path=https://github.com/frappe/frappe \
    --no-procfile --no-backups --skip-redis-config-generation --verbose /home/frappe/frappe-bench
WORKDIR /home/frappe/frappe-bench
RUN test "$(git -C apps/frappe rev-parse HEAD)" = 012667b9c4e7f66d5e1ff5858d2e922331d4300a
COPY --chown=frappe:frappe lotus_fin/ apps/lotus_fin/
COPY --chown=frappe:frappe docker/lotus-core/requirements.lock /tmp/lotus-requirements.lock
COPY --chown=frappe:frappe docker/lotus-core/framework.lock /tmp/lotus-framework.lock
RUN env/bin/pip install -r /tmp/lotus-framework.lock -r /tmp/lotus-requirements.lock -e apps/lotus_fin \
    && env/bin/pip check && printf 'frappe\nlotus_fin\n' > sites/apps.txt \
    && bench build --app lotus_fin \
    && env/bin/python -c 'import frappe, lotus_fin.hooks, lotus_fin.runtime.boundary, lotus_fin.runtime.health, importlib.util; assert importlib.util.find_spec("erpnext") is None' \
    && env/bin/pip freeze > /home/frappe/runtime-packages.lock \
    && printf '{}\n' > sites/common_site_config.json

FROM frappe/base:version-16@sha256:1a70d58dcd0d4b919b00626a458b07114efe005e077761daa516bd929fd5568d
COPY --from=builder --chown=frappe:0 /home/frappe/frappe-bench /home/frappe/frappe-bench
COPY --from=builder --chown=frappe:0 /home/frappe/runtime-packages.lock /home/frappe/runtime-packages.lock
COPY --from=ui --chown=frappe:0 /frontend/dist/ /home/frappe/frappe-bench/sites/assets/lotus_fin/core/
COPY --from=ui --chown=frappe:0 /frontend/dist/index.html /home/frappe/frappe-bench/apps/lotus_fin/lotus_fin/templates/lotus_spa.html
COPY --chown=frappe:0 docker/lotus-core/ /home/frappe/lotus-core/
COPY --chmod=755 docker/lotus-core/upstream/main-entrypoint.sh /usr/local/bin/entrypoint.sh
COPY --chmod=755 docker/lotus-core/upstream/start.sh /usr/local/bin/start.sh
USER frappe
WORKDIR /home/frappe/frappe-bench
RUN rm sites/assets/lotus_fin/core/index.html \
    && cp -r sites/assets assets && rm -rf sites/assets
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["start.sh"]

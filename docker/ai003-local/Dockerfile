FROM frappe/erpnext:v16.35.0

USER root
COPY --chown=frappe:frappe lotus_fin/ /home/frappe/frappe-bench/apps/lotus_fin
COPY --chown=frappe:frappe docs/features/AI002/fixture_scripts/direct_confirmed_commitments.json /home/frappe/frappe-bench/apps/lotus_fin/docs/features/AI002/fixture_scripts/direct_confirmed_commitments.json

USER frappe
RUN /home/frappe/frappe-bench/env/bin/pip install --no-deps -e /home/frappe/frappe-bench/apps/lotus_fin

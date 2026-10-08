FROM frappe/erpnext:v16.35.0

USER root
COPY --chown=frappe:frappe lotus_fin/ /home/frappe/frappe-bench/apps/lotus_fin
COPY --chown=frappe:frappe docs/features/AI002/fixture_scripts/direct_confirmed_commitments.json /home/frappe/frappe-bench/apps/lotus_fin/docs/features/AI002/fixture_scripts/direct_confirmed_commitments.json

# Bake the app's static include assets (hooks app_include_js/css) into the
# baked-assets tree that the backend entrypoint symlinks to sites/assets.
RUN mkdir -p /home/frappe/frappe-bench/assets/lotus_fin/js /home/frappe/frappe-bench/assets/lotus_fin/css \
	&& cp /home/frappe/frappe-bench/apps/lotus_fin/lotus_fin/public/js/lotus_fin.js /home/frappe/frappe-bench/assets/lotus_fin/js/lotus_fin.js \
	&& cp /home/frappe/frappe-bench/apps/lotus_fin/lotus_fin/public/css/lotus_fin.css /home/frappe/frappe-bench/assets/lotus_fin/css/lotus_fin.css

USER frappe
RUN /home/frappe/frappe-bench/env/bin/pip install --no-deps -e /home/frappe/frappe-bench/apps/lotus_fin

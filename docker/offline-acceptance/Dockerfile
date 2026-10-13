# Offline core qualification only. No Frappe site, ERPNext, credentials or DB.
FROM python:3.13-slim@sha256:70729b46c69b4f1e97c4822c1af3df53a1476cf5ddc6c087c0c10bc3a5678c2f
WORKDIR /candidate
COPY docker/offline-acceptance/requirements.lock /tmp/requirements.lock
RUN pip install --no-cache-dir -r /tmp/requirements.lock && pip check
COPY lotus_fin /candidate/lotus_fin
ENV PYTHONPATH=/candidate/lotus_fin PYTHONDONTWRITEBYTECODE=1
USER 65532:65532
CMD ["python", "-B", "-c", "import importlib.util; assert importlib.util.find_spec('erpnext') is None; assert importlib.util.find_spec('frappe') is None; import lotus_fin.application.service.search_invoices, lotus_fin.application.service.open_authorized_invoice, lotus_fin.api.invoice_actions_api; print('OFFLINE_CORE_IMPORTS_OK; NO_NATIVE_LIVE_ACCEPTANCE')"]

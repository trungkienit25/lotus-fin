# Integrated technical documentation

Routes: existing `/copilot`, `/ai` and approved drawer share one panel. New server route: `lotus_fin.api.copilot_integration_api.dispatch`, POST only. CORE invoice RPCs retain their existing fail-closed behavior. No ERPNext package is required by this composition.

Layers: `api/copilot_integration_api.py` validates/serializes HTTP and composes authenticated infrastructure; `application/service/copilot_integration.py` coordinates L4 and V1 services and L5 policy review; `infrastructure/persistence/copilot_demo_store.py` persists only isolated simulation state/audit. UI routing lives in `copilotIntentRouter.ts`, message composition in `copilotMessageSender.ts`, transport/session fencing in `copilotIntegrationClient.ts`, and shared views in `IntegratedCapabilities.tsx`.

The demo has fixed V1 observation time `2026-10-13T12:00:00+00:00`, timezone Asia/Ho_Chi_Minh and fictional company Lotus Demo Corp. Eligible gold rows are DEMO-INV-001 (12 overdue days) and DEMO-INV-002 (8); settled, returned and due-today rows are excluded by the actual predicate. Amounts preserve decimal strings and currencies. No native V1 selection reference is generated.

L4 proposals expire after the module's 300-second server TTL. L3 retains its absolute monotonic ten-minute TTL. Simulation storage is private to the new owned site, SQLite transactional and multi-process serialized on its shared sites filesystem. It is not intended as a production write provider. Cold restart and current image source hashes are separate runtime evidence requirements.

Use docker/lotus-core/acceptance.py for source-bound offline gates and the P6 judge runbook for isolated deployment. No default shared site or credential is selected. Secrets remain in ignored `.runtime` files and are omitted from reports.

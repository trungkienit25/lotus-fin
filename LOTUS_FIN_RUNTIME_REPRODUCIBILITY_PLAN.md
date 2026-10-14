# Lotus Fin runtime reproducibility plan

12 October 2026, Asia/Saigon. **RUNTIME_REPRODUCIBILITY = FAIL.** Current source has independently observable HEAD omissions; the latest located final packet records incompatible serving-image source. Clean build, fresh site/worker execution and native integration acceptance are **NOT_RUN in this audit**. This plan performs no rebuild, provisioning, sync, restart or deployment.

Evidence: [audit scope](docs/reviews/product-independence-2026-10-12/AUDIT_SCOPE.json), [source hashes](docs/reviews/product-independence-2026-10-12/SOURCE_HASHES.json), [baseline status](docs/reviews/product-independence-2026-10-12/BASELINE_GIT_STATUS.txt); historical `docs/reviews/evidence/chatbot-final-integration-2026-10-12-01a1303a/REPRODUCIBILITY.json`, `RUNTIME_SOURCE.json`, `RUNTIME_METADATA.json`, `SOURCE_MANIFEST.json` and `final-review/CHATBOT_G10_RELEASE_READINESS.md`. Runtime records are inherited observations, not a fresh serving-image inspection in this turn. Paths below are relative to `E:/lotus-fin`.

## FIN-F02 explained against product independence

| Failure dimension | Concrete evidence | Current conclusion / correction |
| --- | --- | --- |
| Dirty/untracked source | git status and source hashes at HEAD `5f805ef34f788245a3ec0e9c2f44e224eb16c305`; search_invoices, invoice_read, authorizer, controller, request DTO dirty; action/prepare modules untracked | HEAD is not accepted working-tree identity. Preserve user changes; do not reset/clean. Candidate must include reviewed corrections and all required files. |
| Missing files from HEAD | Fresh `git ls-files frontend/src/pages/copilot/actions frontend/src/pages/copilot/prepare` returns no tracked files; prior HEAD archive has no action panel/L3 | Clean clone cannot reproduce tested UI. Later immutable source artifact must include UI, contracts/tests, packaging and native adapter; commit choice belongs to future authorized work. |
| Serving image missing 17/17 modules | Prior RUNTIME_SOURCE.json records absent API/controller/resolver/search/open/authorizer/codecs/config/events/schema/DTO/delivery/port/budget files | Historical current backend was old source without app-source mount. Do not count pip/host import success or copy-in-place as reproducible image proof. Runtime could have changed since record; new inspection needed in qualification. |
| Absent production mount | App routes mount LotusCopilotPage/VercelChatPanel; drawer imports same panel; action/prepare components have no production import path | A successful React build does not prove the action component reaches users. Mount accepted native read chain into explicitly chosen UI entrypoint. L3 optional/excluded unless approved. |
| Missing approved target | No native invoice source/tenant policy/ordinary-user qualification target found | Replace historical ERP target prerequisite with approved **Lotus core** target. Optional ERP fixture/site approval is not native readiness. |
| Image/source/entrypoint mismatch | Dockerfile bases on ERPNext, copies Lotus app/Desk assets; compose uses that recipe; hooks app_home points Desk; frontend source uses React; run.ps1/README commands differ | Select a Frappe-only artifact plus actual React hosting/routing/session origin, bake exact accepted source and assets into serving services. Desk is legacy separate qualification, not a substitute for reviewed React chain. |

The 17 missing paths in historical image evidence are: `api/invoice_actions_api.py`; `presentation/controller/invoice_actions_controller.py`; `application/service/resolve_read_context.py`, `search_invoices.py`, `open_authorized_invoice.py`; `infrastructure/security/frappe_invoice_authorizer.py`, `action_reference_codec.py`, `invoice_reference_codec.py`; `infrastructure/config/invoice_actions_config.py`; `infrastructure/observability/action_events.py`; `domain/schema/invoice_read.py`, `action_outcome.py`; `presentation/dto/invoice_action_request.py`, `invoice_action_response.py`; `presentation/response/invoice_action_delivery.py`; `application/port/i_authorized_invoice_read.py`; `domain/model/invoice_read_budget.py`. These are samples, not the full dependency closure.

## Minimum reproducible Lotus release candidate

Candidate scope recommendation: native authenticated company context → bounded sales-invoice metadata search → explicit selection → fresh authorized minimum reader, on the approved React Page; drawer only if explicitly offered/qualified. No LLM required. Exclude unqualified L3, V1, mutations and financial-source tools until their own gates close. Clearly describe the narrow core scope; never claim whole-product financial readiness from its acceptance.

Candidate must include:

1. Immutable source identity (reviewed commit/archive digest) with all native policy/adapter/API/UI files, approved contract versions, tests and build recipes. Maintain required historical evidence outside runtime payload; prevent evidence-copy modules entering Python imports. Record dirty/untracked reconciliation and exact file hashes.
2. Locked/recorded frontend and Python dependency set, chosen Frappe revision/runtime, DB/Redis versions and immutable base/image digests. Pin required packages through approved packaging; current pyproject's empty dependencies and no-deps install are insufficient. Do not mandate changing DB/framework solely for independence.
3. Frappe-only core image/site with Lotus app and approved owned schema; ERPNext absent from installed package/site app set. Correct core hooks/workspaces/assets and exclude optional ERP UI/RPC/scheduler paths. Framework User/Role/session use is allowed only with approved Lotus entitlements.
4. Chosen production React bundle, base path/routes/static hosting/proxy origin/session/CSRF, actual mounted action panel and exact native HTTP methods. Build recipe must explicitly include this bundle; current Dockerfile only copies Desk assets.
5. Approved native data fixture/service identity, tenant policy version, source/freshness configuration, signing-key identifier and secure secret provisioning, safe audit sink and bounded worker/source I/O. Record secret references/identifiers, never values in evidence.
6. Fresh backend/worker/scheduler/frontend imports and asset hashes from immutable image, readiness/health and ordinary-user real HTTP acceptance. Audit all service images/mounts and resident workers; filesystem bytes alone do not prove loaded module identity.

Readiness must require native source/policy/audit/config qualification, not merely port-open or Python import. Missing authority → safe unready/unavailable; no silent ERP, fixture or Administrator fallback. Optional external integrations need separate readiness indicators, not a core startup prerequisite.

## Conditional execution stages — future authorized work

| Stage | Owner and action | Required evidence / failure behavior |
| --- | --- | --- |
| R0 | Product/Security/Data close native authority, reference migration and release-scope decisions | Approved records; keep integration blocked if absent. |
| R1 | Backend/frontend implement and independently close required defects per handoff | Current hashes and zero required adversarial failures; preserve P1/AI versioned regressions. No approved target yet means no live PASS. |
| R2 | Platform assembles immutable candidate from reviewed complete source | Archive/commit digest, source manifest, package locks, build recipe identity; no host path or preinstalled-package dependency. |
| R3 | Platform builds in isolated approved environment from clean artifact | Image digests/SBOM/build logs and ERP absence; fail on missing source/dependencies/bundle. No copying current working tree into shared containers. |
| R4 | Target owner provisions approved isolated Frappe/Lotus site/schema/data/ordinary users | Native fixture provenance, app list, policy matrix, secret ids, snapshot/cleanup authorization. No ERP demo/setup wizard needed. |
| R5 | Independent reviewer verifies fresh processes and actual production route | Imported module paths/hashes, worker process identity, assets, effective hooks/site app state, readiness, native HTTP/body/header/audit and browser lifecycle. |
| R6 | Independent reviewer executes NI-01–NI-14 plus included feature gold | Captured egress/SQL/permission traces and JUnit/per-case manifests; skips/missing positive native flow fail gate. |
| R7 | Product/Security/Platform release review and G10 walkthrough | Exact accepted source/image/data/policy lineage; ordinary-user demo with denials/outage; rollback/cleanup verified. Independent gate; no deployment implied by audit documents. |

Rollback plan must restore prior owned candidate and configuration and account for any approved schema/data migration. Since no new schema is approved here, migration/rollback details cannot be invented. Keep fixture lifecycle separate from production data. Read-only business tests may still create framework session/access/audit records: disclose and measure them separately from business no-write.

## Read-only checks runnable now

These discovery commands do not build/provision or claim native runtime acceptance:

```powershell
git rev-parse HEAD
git status --short
git ls-files frontend/src/pages/copilot/actions frontend/src/pages/copilot/prepare
Select-String -LiteralPath docker/ai003-local/Dockerfile -Pattern '^FROM'
Select-String -LiteralPath docker/judge/init.sh -Pattern 'install-app erpnext'
```

A future isolated reviewer should reproduce source manifests, then inspect actual selected image/site/app/import/asset state read-only before executing the authorized suite. Do not run `run.ps1 sync/demo/run`, `docker compose up/build`, bench migrate/install-app or restart as an audit shortcut. No current helper is approved as the native recipe.

## Unresolved assumptions and required approvals

The current runtime was not freshly inspected, no clean native build was run, and the core target/data/field policy, exact Frappe-only image recipe, React hosting/base path, hard source deadline and durable audit storage are unapproved. Eight frontend source/test files changed concurrently after baseline hashing; no single immutable candidate or fresh correction acceptance is claimed. Preserve both manifests and obtain one complete source-bound qualification snapshot later. Product approves scope and canonical entrypoint; Data approves owned schema/service/update authority; Security approves policy/reference migration, signing/audit lifecycle and denial behavior; Platform/target owner approves isolated build/provisioning/snapshot/rollback/cleanup. Test success cannot substitute for these records.

Release exit requires reproducibility PASS plus native data authority VERIFIED for every **enabled** operation and native integration READY. Until then retain the four audit verdicts and G10 NO-GO. STOP after audit/design; no rebuild/deploy/commit occurred.

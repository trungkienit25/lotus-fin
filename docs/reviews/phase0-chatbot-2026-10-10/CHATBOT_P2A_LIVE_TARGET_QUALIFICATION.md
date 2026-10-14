# LOTUS FIN — P2-A Live Target Qualification

12/10/2026 · Asia/Saigon · **BLOCKED — bounded read-only readiness evidence.**

|Required gate|Verdict|Execution / basis|
|---|---|---|
|P2A_SOURCE_RUNTIME_MATCH|**FAIL**|Fresh container filesystem comparison:17/17selected P1/P2paths missing;0matching.|
|P2A_REAL_AUTHORIZATION|**BLOCKED**|Live permission tests NOT_RUN: no approved private target/ordinary-user gold.|
|P2AB_HTTP_INTEGRATION|**BLOCKED**|Actual HTTP/CSRF/UI integration tests NOT_RUN.|
|ERP_NO_WRITE|**NOT_RUN**|No approved fixture DB baseline/delta; no-write qualification not inferred from no requests.|
|G10|**BLOCKED**|Independent separate gate, not qualified here.|

Không implementation, build/deployment/restart, site initialization, fixture provisioning, business read/write, permission change hoặc HTTP call. Dừng ở precise target blocker theo request §3/§8.

## 1. Current host correction identity

Branch `develop`, HEAD `5f805ef34f788245a3ec0e9c2f44e224eb16c305`; dirty correction và pre-existing UI được giữ nguyên. Source artifact không được thay bằng HEAD/tag.

[Correction](CHATBOT_P2A_F01_F03_CORRECTION.md) và [frozen wire contract](CHATBOT_P2B_WIRE_CONTRACT.md) khớp exact hashes: **25/25 entries**, gồm13changed/new correction code/tests,3deliverable docs và9protected codec/API/config/resolver/Open/Panel/Drawer files. [Fresh verification](../evidence/chatbot-p2ab-runtime-readiness-2026-10-12/CORRECTION_HASH_VERIFICATION.json). Source hashes vẫn là artifact đã self-verified F01–F03; không có new independent PASS.

Previous correction tests343/343, oracle84/84, A16 14/14, B03 8/8 là **NOT_RERUN / fingerprint-qualified reuse** trong task runtime này. Không report những counts đó như fresh live test. F01/F02/F03 đã corrected; không dùng preflight historical descriptions để mở lại old defects.

## 2. Docker availability và actual runtime

Lần kiểm tra đầu: Docker engine pipe chưa tồn tại, docker ps exit1. User xác nhận Docker đã bật; kiểm tra mới **exit0** và stack `frappe_docker` đang chạy. Docker Desktop processes chạy không thay bằng chứng engine response. Initial availability blocker đã được giải quyết; không còn dùng nó làm final blocker. **Agent không bật/restart Docker hoặc services.**

|Fresh observation|Actual|
|---|---|
|Context|`desktop-linux`, `npipe:////./pipe/dockerDesktopLinuxEngine`|
|Backend|`frappe_docker-backend-1`|
|Container ID|`a857658a101bbe5304d16160d65c5669878e9b5eada9b3d288666236c84f0b55`|
|Image tag|`lotus-fin:ai003-local`|
|Immutable image ID|`sha256:ed6e02f587eb450a0882ecb4b6fbb259d1a1f27f549e1cc4bbe21a660b3017b7`|
|Backend started_at|`2026-10-12T07:58:09.823824219Z` =14:58:09 Asia/Saigon|
|Compose files|`E:/frappe_docker/pwd.yml`, `E:/lotus-fin/docker/ai003-local/compose.override.yml`|
|Backend mounts|Only `frappe_docker_sites` and `frappe_docker_logs` volumes; **no host application-source bind**|
|Runtime Python executable|`/home/frappe/frappe-bench/env/bin/python`, version3.14.7|
|Framework source versions|Frappe16.34.0; ERPNext16.35.0; Lotus0.0.1|
|Bench apps.txt|erpnext, frappe, lotus_fin — filesystem inventory only|
|Site folders/config files|`frontend`, `ai003-verify.localhost`; common default_site=`frontend`|
|Database installed apps/effective hook order|**NOT_RUN**; no site init/DB inspection|
|HTTP principal/session/effective requested site|**NOT_RUN**; shell user `frappe` is not an authenticated ERP actor|

[Backend metadata](../evidence/chatbot-p2ab-runtime-readiness-2026-10-12/BACKEND_METADATA.json), [image metadata](../evidence/chatbot-p2ab-runtime-readiness-2026-10-12/IMAGE_METADATA.json), [runtime source identity](../evidence/chatbot-p2ab-runtime-readiness-2026-10-12/RUNTIME_SOURCE_IDENTITY.json). Fresh inspect confirms same old image; no inference from tag alone. Running user-owned stack is not an approved P2 fixture target.

## 3. Exact host → image mismatch

[Comparison](../evidence/chatbot-p2ab-runtime-readiness-2026-10-12/HOST_RUNTIME_COMPARISON.json) records current host SHA256 and exact container path for each file. All17host files exist; all17container files are missing under `/home/frappe/frappe-bench/apps/lotus_fin/lotus_fin/`:

```text
api/invoice_actions_api.py
presentation/controller/invoice_actions_controller.py
application/service/resolve_read_context.py
application/service/search_invoices.py
application/service/open_authorized_invoice.py
infrastructure/security/frappe_invoice_authorizer.py
infrastructure/security/action_reference_codec.py
infrastructure/security/invoice_reference_codec.py
infrastructure/config/invoice_actions_config.py
infrastructure/observability/action_events.py
domain/schema/invoice_read.py
domain/schema/action_outcome.py
presentation/dto/invoice_action_request.py
presentation/dto/invoice_action_response.py
presentation/response/invoice_action_delivery.py
application/port/i_authorized_invoice_read.py
domain/model/invoice_read_budget.py
```

Source/runtime match is an **observed FAIL**, not a mock or unsupported success. Restarting an old image does not copy host files. No copy/patch into running containers was attempted. Loaded resident application/module lineage is additionally NOT_RUN; filesystem evidence does not prove imported workers/site DB state.

## 4. Installed framework source — static evidence only

Fresh reader executed Python `-B` with stdlib AST/filesystem/package metadata; no Frappe/ERP/Lotus import, no `frappe.init/connect`, no SQL/HTTP. [Targeted source](../evidence/chatbot-p2ab-runtime-readiness-2026-10-12/FRAPPE_STATIC_SOURCE.json) stores file hashes/signatures/line ranges and declares excerpt truncation where applicable. Static API availability is not permission qualification.

|Installed source observation|Implication for conditional adapter|
|---|---|
|`frappe/__init__.py:get_list`1360→`model.qb_query.DatabaseQuery.execute`|Use permission-aware current-principal list, fixed fields/company/filters/bounds. No get_all.|
|`model/qb_query.py:execute`26 defaults ignore_permissions=False|Doctype read gate still needed; list/select support alone insufficient. Do not enable save_user_settings.|
|`database/query.py:get_query`215 defaults ignore_permissions=True|Direct unrestricted QB is not a permitted replacement.|
|`permissions.py:has_permission`81 loads exact doc string via get_lazy_doc|Company/exact invoice rights need current actor and qualified hydration costs.|
|`model/__init__.py:get_permitted_fields`218 distinguishes select/read|Field list alone is not read authority; explicit read/projection/masking gate before predicates/query.|
|`model/document.py:apply_fieldlevel_read_permissions`957 removes/masks fields|Required denied/masked predicate/projection→safe failure; no raw masked value exposure.|
|`Document.load_from_db`252 includes SELECT*, children and __setup__|Do not use full editable document hydration as minimal read; lazy/custom permission paths must qualify SQL/bytes/side effects on private fixtures.|
|`auth.py:validate_csrf_token`81 has early returns for no saved token/ignore_csrf/allowed referrer|Actual session/token/origin behavior needs real negative tests; declaration alone cannot certify CSRF.|

Disk hooks: Frappe literal permission mappings captured; Lotus doc_events names include Sales Invoice/Payment Entry; ERPNext doc_events expression is **not literal-resolved** by this bounded reader. No claim that custom hooks are absent. Effective app installation/order, DB Server Scripts, Custom DocPerm/Property Setter/User Permission/DocShare/disabled users/masks and cache coherence remain **NOT_RUN**.

## 5. Server scope/key/audit readiness

Current host API only uses disabled response helper, not config/resolver/read-port/required audit composition. `InvoiceActionsConfig` is a strict config DTO, **not a connected production loader**; enabled defaultsFalse. Missing17files means this composition is absent from current runtime image.

Presence-only probe of common/site JSON candidate keys `invoice_actions`, enabled/key-id/secret/connections found absent. **No secret values, environment, cookies or SID were output.** Key absence in these candidate files is not proof that no external secret store/environment exists. Approved loader/key custody/rotation/mapping/version policy/sink binding remain NOT_VERIFIED. `time_zone` absence in site_config is not absence of DB System Settings; actual site timezone is NOT_RUN.

No approved current actor/session/product/site/connection/company map, key policy or audit sink was established. Bench apps.txt/Config.User/default_site/role names cannot substitute for that proof.

## 6. Build/deploy/rollback procedure readiness

Read-only fingerprints: [build procedure metadata](../evidence/chatbot-p2ab-runtime-readiness-2026-10-12/BUILD_PROCEDURE_METADATA.json). Existing Dockerfile uses tag `frappe/erpnext:v16.35.0`, copies host `lotus_fin/`, also bundles an AI002 fixture JSON and installs editable Lotus package with no-deps. Adjacent ignore admits Lotus tree and that fixture. Compose override points backend/queues/scheduler/websocket/frontend/configurator at same custom tag; existing sites/logs are shared volumes.

This recipe is **not a frozen private P2 build manifest**: base digest/source inputs/imports/UI artifact provenance and isolation lifecycle are not approved. `run.ps1` contains build/restart/migrate/seed operational paths; not executed. Historical canonical review records setup/entrypoint/packaging conflicts; no new claim they were fixed.

Conditional procedure, **DESIGNED / NOT_EXECUTED**:

1. Owner approves named private compose project/site, immutable source manifest including dirty/untracked required code, pinned base/image digest, allowed outbound policy and exact build recipe. Exclude shared AI003 fixtures/judge/production data; no shared-service rebuild.
2. Provide private-only DB/Redis/sites/logs volumes and reviewed fixture bootstrap; record verified snapshot ID/provenance/restore rehearsal or approved empty-baseline restoration strategy. Supply ordinary users/CompanyA/B/denied doc/masked fields/revocable rights with independently owned expected ledger.
3. Build/start only that approved target, verify source hashes/import paths/installed apps/hooks/timezone/map/key/audit on actual serving workers. Python3.14 compatibility and exact P1/P2 tests must run on the image.
4. Implement/qualify authorized adapter and HTTP composition after fresh GitNexus impact. Actual rights/resources/HTTP/no-write tests and UI explicit select/open only then.
5. Failure: disable isolated capabilities, retire key/bump approved policy where applicable, restore approved private baseline/image; cleanup only exact owned project objects/fixtures/sessions/handlers. Preserve evidence. No shared Redis flush, volume prune, rollback or fixture deletion.

These steps are not authorization to execute. User note that Docker is on does not name/approve a private target or lifecycle.

## 7. Precise unblock packet

|ID|Requirement missing|Closure evidence / owner role|
|---|---|---|
|T01|Current serving image lacks17P1/P2files|Backend/release: approved private artifact build manifest+immutable digest+worker file/import hash match.|
|T02|No named approved P2 private project/site and snapshot/restore/cleanup plan|ERP/Ops: target identity, isolation/new volumes, provenance/snapshot, exact allowed lifecycle and cleanup verification. Do not select frontend/ai003-verify/judge.|
|T03|No ordinary-user sessions and independent permission gold|ERP security/QA: allowed/denied/cross-company/exact-doc/masked/revoked synthetic fixtures and expected results; no credentials in chat/report.|
|T04|Actual installed apps/hooks/site/principal unknown|ERP/Ops: installed-site/app order/customizations/current request routing/principal metadata on approved target.|
|T05|Approved mapping/key loader/audit composition unqualified|Backend/security/Ops: current product/site/connection/company/version/timezone, key lifecycle and healthy/outage required sink evidence.|
|T06|Authorized read adapter not ready on qualified installed target|Backend/ERP: bounded current-principal list/doc/field/mask/hydration/version gates and instrumented physical I/O.|
|T07|HTTP wrapper/status/header/CSRF and no-write/resource qualification absent|QA/backend: real private request matrix, terminal audit and before/after business+side-effect baseline/delta.|

No named human owner invented; no source amendment attempted against imagined APIs. [HTTP evidence matrix](CHATBOT_P2AB_HTTP_INTEGRATION_EVIDENCE.md), [Work→Chat](CHATBOT_P2AB_RUNTIME_WORK_TO_CHAT.md). **Stop at these blockers.**

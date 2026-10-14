# Lotus Fin integration implementation handoff

12 October 2026, Asia/Saigon. **DESIGN ONLY; implementation not authorized by this audit.** PRODUCT_INDEPENDENCE=CHANGES_REQUIRED; LOTUS_NATIVE_DATA_AUTHORITY=UNKNOWN; CHATBOT_NATIVE_INTEGRATION_READINESS=BLOCKED. Architecture and source evidence: [audit](LOTUS_FIN_PRODUCT_INDEPENDENCE_AUDIT.md), [target design](LOTUS_FIN_CHATBOT_NATIVE_INTEGRATION_DESIGN.md), [authority map](LOTUS_FIN_NATIVE_DATA_AUTHORITY_MAP.md). Paths below are relative to `E:/lotus-fin`.

## Ordered work packages and acceptance

| Package / owner role | Prerequisite and concrete scope | Reviewable exit evidence |
| --- | --- | --- |
| N0 — Product/Data + Security | Name native tenant/company/invoice source, update owner and schema/API; approve lifecycle/date/status/version/currency and membership/document/field policy. Decide minimum core release scope. | Signed authority sheet for every enabled flow; no silent schema creation or ERP mirror relabeling. No implementation until this gate closes. |
| N1 — Backend/Security | Repeat fresh exact GitNexus impact for authorizer/context/source/reference/schema/controller symbols. Approve version/migration and fresh-denial semantics. Preserve accepted P1 compatibility. | Reviewed native contract, migration rejection matrix, golden token/source/expiry vectors and old-contract regression record. HIGH/CRITICAL graph risks explicitly reported; UNKNOWN confirmed, never waived. |
| N2 — Backend/Data | Implement one native IReadAuthorizerPort and IAuthorizedInvoiceReadPort against N0 service; count physical source/auth I/O, bytes and deadlines. Keep application search/open orchestration. | Ordinary users, two tenants/companies, row/field rights, revocation, source version changes, consistent ordering/version proof; no raw get_all/fields=* bypass, no ERP mandatory dependency. |
| N3 — Backend/Platform/Security | Compose existing three narrow API declarations/controller with native services and required audit; controller search/open currently disabled. Qualify actual Frappe HTTP wrapping/session/CSRF and body limits. | Real HTTP positive and negative cases, exact one envelope, body/header/event CID consistency, safe statuses, no-store, terminal audit failure denies and exact source proof. Disabled default remains until gates pass. |
| N4 — Frontend | Fix FIN-F01/F06–F09, preserve original positives and denial cases; native mode/version decoders follow approved contract. Implement actual authenticated bounded transport, then mount into chosen Page/Drawer. | Original plus expanded independent Node/React tests green, real HTTP reader flow, exact-expiry/late-callback fences, source mode/timezone and invalid-state cleanup; no production fixture transport. |
| N5 — Product/Frontend/Security, separate optional scope | L3 FIN-F03–F05/F10 correction; review template, monotonic absolute TTL, copy operation/revision ownership, unmount disposal and unavailable-scope behavior. | Approved fact-free local preview contract and independent clock/clipboard/lifecycle oracle. No invoice facts/form.prefill/save/send claims. May be excluded from initial native read release. |
| N6 — Financial feature owners, only for enabled native finance | Translate approved native financial feeds behind existing feature seams; isolate ERP reports/GL/invoice adapters as optional integration. Inventory hooks, worker entrypoints and generic UI routes. | AI001/002/003 numeric gold plus owned-source equivalence/permissions/freshness and known limitations. Core disabled for any unqualified financial feed. No new formula or fabricated forecast. |
| N7 — Platform + independent reviewer | Complete immutable candidate, Frappe-only packaging and ordinary-user isolated test target after approvals. | Runtime/source/bundle lineage and native independence suite pass; G10 separately approved. See reproducibility plan. |

Do not implement an ERP adapter merely to close historical target gates: those gates must be rewritten around the independent core. If Product separately elects optional ERP integration, its old evidence remains relevant to that adapter only. Do not broaden the native release label to cover unqualified financial tools.

## Independence negative-test plan

Tests below are executable acceptance designs, **NOT_RUN**. Missing native fixtures/HTTP composition must fail qualification, not skip or xfail into a PASS. Their prerequisite is a real N0–N3 native flow; successful fake-port or disabled-helper execution cannot qualify native independence.

Create an isolated Frappe + Lotus core profile after approval, with ERPNext absent from package/site app inventories, no ERP secrets/credentials, and no optional ERP adapters enabled. Use synthetic records created through the approved native authority by its fixture owner, visibly labeled synthetic; use two ordinary actors and two tenant/company scopes, plus document/field denials. Keep a named owner and authorized snapshot/cleanup lifecycle. No setup scripts in this audit create these records.

The qualification harness must expose these measured interfaces (to implement later): native ordinary-session HTTP client; source SQL/call trace and before/after business snapshots; active app/package/worker inventory; egress capture/deny rules; permission-engine trace; clock/token signer controlled only by fixtures; required audit sink probe. Instrument worker processes too, not only the host interpreter. Verify instrumentation itself with a deliberate attempted forbidden import/query/egress canary in the test harness, rejected before execution; no canary performs ERP writes.

| Test ID / proposed test function | Setup and action | Required assertions |
| --- | --- | --- |
| NI-01 / test_native_read_without_erpnext | ERPNext package/app absent; ordinary actor native context → bounded search → explicit selected open | Positive permitted path returns actual approved synthetic native row and exact five-field projection. Worker never imports ERPNext; app inventory contains only approved core apps. Fail if positive flow absent; disabled outcome is not a PASS. |
| NI-02 / test_no_erp_endpoint_egress | Capture every browser/server request; block ERP origins/RPC namespaces while exercising native reads and any enabled financial flow | No attempted ERP HTTP/RPC calls, including retries/fallback; only approved native/framework routes. Direct `erpnext.selling...` route absent from core navigation. |
| NI-03 / test_no_erp_schema_access | Trace SQL and resource calls from all workers; exercise positive/deny/error cases | No unavoidable Company/Sales Invoice/Purchase Invoice/GL Entry/Payment Ledger/Party Type ERP schema queries. Source uses only approved native tables/services plus explicitly allowed Frappe core auth/cache/audit operations. Test logical resource names as well as quoted SQL names. |
| NI-04 / test_lotus_policy_independent_of_erp_roles | Native membership permits actor lacking ERP roles; deny a second actor who has arbitrary ERP-like accounting role labels | Native grants control outcome; accounting role strings grant nothing. Permission trace proves owned policy executed. Frappe identity primitives may remain. |
| NI-05 / test_no_administrator_fallback | Missing/Guest/disabled/expired session, missing framework interface, ordinary actor denied company, and native-policy outage | No Administrator/System Manager/default-company substitution, no set_user privilege change, no source reads after pre-read denial; safe null-data denial/unavailable. Probe controller and financial routes included in release, not just strict authorizer. |
| NI-06 / test_no_erp_credentials_required | Start fresh core profile with ERP credential/origin config absent; allow only native config | Positive flow works; no startup/health/worker references to missing ERP keys; secret-access trace confirms none requested. Do not print environment secret values. |
| NI-07 / test_native_denial_precedes_data | Native company, list, document and field policy each rejects; revoke after search then open valid signed selection | No protected payload or unauthorized rows/fields; no document fetch before denial where policy permits preflight. Document/field revocation beats cached/search grant and stale-version messages. Safe audit records actual denial. |
| NI-08 / test_scope_reference_isolation | Swap actor/session/tenant/company/product/site/source/connection/version/key/projection/purpose/context/query/timezone one axis at a time; replay foreign handles | All mismatches reject; no partial repair; zero protected state. Repeat at server and actual React admission, including late callback after scope switch/logout. |
| NI-09 / test_native_source_outage_is_truthful | Stop/fail only approved native source after obtaining context; timeout, malformed schema and stale version separately | SOURCE_ERROR/NOT_AVAILABLE/TIMEOUT/STALE_SELECTION per approved matrix; no ERP/fake/LLM fallback, no fabricated EMPTY_RESULT/zero balances; null protected data. |
| NI-10 / test_expiry_and_revocation_boundaries | Controlled clock at expiry−1, expiry, expiry+1; responses arriving after deadline/expiry; policy/key/source version change | Native approved expiry semantics exact; UI equality denial; no restored protected state or pending handles. P1 compatibility remains separately tested under its historical version. |
| NI-11 / test_audit_delivery_http_privacy | Missing/suppressed/broken/short-write required sink and healthy sink; actual HTTP success/denial | Protected success only after required acknowledgement; exactly one terminal event when successful; CID agreement; no token/secret/raw sid/unauthorized PII in logs/body/browser storage. Durable sink claims only if separately measured. |
| NI-12 / test_business_no_write_and_bounds | Snapshot approved business stores; exercise reads, pagination and rejected mutation/tool names; exceed row/date/byte/deadline limits | No business mutations; all physical I/O accounted and hard bounds qualified. Framework session/access log side effects enumerated separately. No saved draft/send/payment tool/route granted. |
| NI-13 / test_enabled_native_financial_sources | For each explicitly included AI feature, ERP absent; approved native inputs plus outage/partial/unavailable feeds | Existing deterministic gold and typed limits preserved; sources are owned, not translated ERP fixtures passed as native. Missing commitments yield unavailable forecast. If feature excluded, document exclusion, not feature PASS. |
| NI-14 / test_fresh_artifact_and_real_mount | Clean candidate in fresh workers/browser, ordinary actor uses selected production route | Exact accepted code hashes imported; bundle mounts action panel and actual native API. No fixture intercept; page/drawer lifecycle acceptance if both offered. |

Suggested future test packaging: `tests_native_qualification/` under an approved change, with one function per NI identifier and a mandatory native_target fixture. Test manifest records expected cases and refuses empty collection/skips. The directory does not exist as a qualified suite today. After implementation, run from the selected artifact, e.g. `python -m pytest tests_native_qualification --strict-markers -q --junitxml=native-results.xml`, then replay source-bound browser cases with the actual native production route. This command is a proposed runner contract, not a command executed in this audit.

Example harness test body, executable once the documented measurement fixture exists:

```python
def test_native_read_without_erpnext(native_target):
    assert native_target.is_owned_synthetic_fixture
    assert 'erpnext' not in native_target.installed_apps
    assert not native_target.erp_credentials_requested
    outcome = native_target.ordinary_user.search_then_explicit_open()
    assert outcome.status == 'OK'
    assert outcome.source_owner == native_target.approved_owner
    assert outcome.document_id == native_target.authorized_invoice_id
    assert native_target.erp_import_attempts == []
    assert native_target.erp_egress_attempts == []
    assert native_target.erp_schema_accesses == []
```

The measurement fixture must call actual HTTP/worker/native authority, not a mock-returning port, and must fail if instrumentation/identity/source qualification is absent. Additional cases and exact approved mode/version values must follow N1, not be guessed here.

## Existing regression anchors to preserve

- Backend `lotus_fin/lotus_fin/tests/test_search_invoices.py`, `test_open_authorized_invoice.py`, `test_invoice_read_security.py`, `test_invoice_read_references.py`, `test_invoice_read_budgets.py`, `test_invoice_context.py`, `test_invoice_permission_seam.py`, `test_invoice_terminal_delivery.py`, `test_action_reference_privacy.py`. These verify their current offline seams and versioned contracts; do not reinterpret fixtures as native records.
- Latest independent packet `docs/reviews/evidence/chatbot-final-integration-2026-10-12-01a1303a/`: FRESH_ORACLE_RESULTS/BROWSER_EXTENDED_RESULTS and corresponding harnesses, L3_ORACLE_RESULTS/L3_DOM_RESULTS, backend/source/boundary oracle records and feature results. FIN-F01–F10 expected failures remain real failures until corrected; no xfail conversion.
- AI001/AI002/AI003 gold retains current formulas, net/positive exposure distinctions, explicit cutoff, source statuses, currency and DEMO_ONLY restrictions. Legacy adapter tests may stay in optional ERP profile, never counted as native independence acceptance.

## Approval and stop rules

Required Product/Data approvals: N0 authority/schema/update lifecycle, native lifecycle/status mapping, enabled release scope, UI route and separate L3/V1 choices. Required Security approvals: tenant/document/field policy, strict missing-identity behavior, source/reference-version transition, revocation/expiry, audit sink/retention, framework side effects and denied bank/mutation scope. Platform approval: artifact/runtime recipe and isolated target data/cleanup lifecycle.

Unresolved: no approved native target/fixtures/instrumentation or data model exists; future suite is not implemented; FIN-F01–F10 correction status was not reverified here. Eight frontend source/test files changed concurrently after this audit baseline. N4/N5 mean establish fresh independent acceptance and correct remaining failures, not blindly repeat corrections already made elsewhere. See verification ledger and final source hashes. This handoff is actionable design, not authorization to code/provision/build/deploy. STOP at the audit boundary.

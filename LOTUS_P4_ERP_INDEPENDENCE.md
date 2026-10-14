# P4 ERP independence — CORE runtime PASS; FULL_PRODUCT_INDEPENDENCE FAIL

13 October 2026 · Asia/Saigon · Independent targeted P4 acceptance.

Branch `codex/p2a-invoice-read-backend`; HEAD `5f805ef34f788245a3ec0e9c2f44e224eb16c305`. Reviewed current dirty/untracked working-tree bytes, not HEAD. No production source edit, stage, commit, push or merge. Only owned isolated project `lotus-core-p4c-01a13415-r5`, site `core-p4c-01a13415-r5.localhost`, loopback `127.0.0.1:8101` was tested and restarted; volumes retained. N0 remains **BLOCKED**.

## Qualified isolated runtime

The complete selected source manifest has **560 files**, SHA-256 `b3c687067382a5e84bad8d43f6f1f22cd73ebc0691d919fa2b8fd17b8fafafab`: [SOURCE_MANIFEST_COMPLETE.json](docs/reviews/evidence/p4-independent-2026-10-13/SOURCE_MANIFEST_COMPLETE.json). The initial 559-file snapshot omitted a tracked AI002 synthetic fixture; the corrected manifest includes it. The 517-file P4-C image-input manifest has SHA-256 `2600017e48b01eee74b788f2ebbbbb39689baf1a0d2a49851603b92b42244c8e` and **zero current-source drift**. These manifests have different scopes, not conflicting source identities.

Image `sha256:f7eda114867f2ea8803a5dafbef8e9927eeed0cb070b32766723cb1ea92325b3` is used by all seven app containers, including the one-shot init; 334 packaged backend files match frozen bytes. Four actual backend/queue/scheduler containers have identical module hashes, Linux platform, and no source bind mounts: [SERVING_WORKER_MODULE_HASHES.json](docs/reviews/evidence/p4-independent-2026-10-13/SERVING_WORKER_MODULE_HASHES.json). This is disk/module and process provenance, not a Python memory dump. The serving assets/private entry are bound in [RUNTIME_PROVENANCE.json](docs/reviews/evidence/p4-independent-2026-10-13/RUNTIME_PROVENANCE.json):

- JavaScript `assets/index-CeY-kyfF.js`: `52fc47074a33fac873fa56c1b976b6151cbcf12030fedb4cb6fe239a3e0f88ad`.
- CSS `assets/index-j6L4zPa6.css`: `0126d0bd8d95741b35163e1b8a5a4394e2245908b5ddffa445a507663da91f41`.
- Private HTML: `e2e42734b757dee2e703da94b495fa7d2aa1bfbc02f86a75d5a300b4acc2490b`.

Locks and executed test-source/oracle hashes are in [SOURCE_MANIFEST_COMPLETE.json](docs/reviews/evidence/p4-independent-2026-10-13/SOURCE_MANIFEST_COMPLETE.json) and [TEST_ORACLE_HASHES.json](docs/reviews/evidence/p4-independent-2026-10-13/TEST_ORACLE_HASHES.json). The existing r5 build already contains these exact P4 source bytes; independent pre/post-restart provenance confirms it is not the P3 UI. This review did not manufacture a new image or assert a fresh from-scratch Frappe build.

Fresh smoke checks before/after an independent cold stop/start verify installed apps exactly frappe and lotus_fin; erpnext import absent; Company and Sales Invoice DocTypes and invoice tables absent; DB/Redis healthy; legacy doc_events, scheduler_events, fixtures, app_include_js and required_apps empty. Ordinary actor has Lotus Core QA/Desk User framework roles, not ERPNext business roles or System Manager. All seven app services retain the exact image; the database and Redis restart policies are unless-stopped. Commands: isolated-stop (0), isolated-start (0), isolated-post-restart-smoke (0), post-restart-canonical-browser (0), runtime-provenance-post-restart (0).

Authenticated CORE native methods return truthful disabled results without an ERPNext package, business schema, production key, Administrator fallback or fabricated invoice source. Normal profile switching cannot populate DEMO under CORE. These are runtime/disabled-boundary PASS claims only.

## Remaining frontend/product dependence

The real CORE page still emits /api/resource/Company as a best-effort legacy company lookup. It mounts successfully when the schema is absent, so that lookup is not a mandatory startup prerequisite, but **zero ERP-shaped traffic is not verified**. Workspace Sidebar and DocType discovery requests also remain in the app shell. Their presence is recorded in SESSION_SCOPE_BROWSER.json. The session-scope DEMO failure prevents claiming full CORE/DEMO presentation isolation.

Graph concept query was empty/FTS-disabled; source confirmation identifies AI002 adapters querying tabGL Entry and Sales/Purchase Invoice, and AI003 reading Purchase Invoice schedules. AI001 financial reports and other promised financial/route modules still lack qualified native source authority. Frappe-only startup and a disabled legacy route are not a migration of those sources. FULL_PRODUCT_INDEPENDENCE = FAIL. CORE_CHATBOT_ERP_FREE_TRAFFIC = CHANGES_REQUIRED, while CORE_RUNTIME_INDEPENDENCE = PASS.

## Native authority and financial boundaries

LOTUS_FIN_NATIVE_DATA_AUTHORITY_MAP.md identifies native source authority as UNKNOWN; LOTUS_FINAL_N0_APPROVAL_SHEET.md remains pending and unsigned. No schema/tenant/membership/row/field/version/freshness policy was approved by this review. SyntheticFixtureSource and DEMO-SINV records are SYNTHETIC_TEST_ONLY, never production financial truth. Native invoice reads, ledger/AR/AP, live AI001–003 financial claims, full product independence and G10 stay BLOCKED/FAIL as applicable. Offline deterministic numerical suites pass 393 tests and 7 subtests in both main and corrected clean snapshot; this qualifies calculations against test inputs only. Optional integrations/lotus_erpnext is separate and unqualified.

The default hooks fixture deletion preserves its optional integration equivalent; source transfer must remain explicitly reviewed. Do not enable ERP-derived fallback providers or create a synthetic ledger to claim N0 completion.

Independent clean rebuild with the shipped `/assets/lotus_fin/core/` base also passed: its JavaScript and CSS hashes are byte-identical to the serving image. See [CLEAN_SERVING_ASSET_COMPARISON.json](docs/reviews/evidence/p4-independent-2026-10-13/CLEAN_SERVING_ASSET_COMPARISON.json); child exit 0.

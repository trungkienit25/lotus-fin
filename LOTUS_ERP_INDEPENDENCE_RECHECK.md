# Lotus ERP independence recheck

13 October 2026 · Asia/Saigon · Independent acceptance of `E:/lotus-fin`.

Branch `codex/p2a-invoice-read-backend`; HEAD `5f805ef34f788245a3ec0e9c2f44e224eb16c305`. The candidate is current dirty/untracked working-tree bytes, not HEAD. No production source edit, stage, commit, push, merge or deployment was performed. Tests used only local fixtures and the previously qualified isolated `lotus-core-01a13314` / `core-01a13314.localhost` / loopback 8097. N0 remains BLOCKED.

Evidence directory: [p3-independent-2026-10-13](docs/reviews/evidence/p3-independent-2026-10-13). Exact candidate: [CANDIDATE_SOURCE.json](docs/reviews/evidence/p3-independent-2026-10-13/CANDIDATE_SOURCE.json), 616 files, SHA256 `02da08611f41de6e9ceff876e95bf48e11150cf9cdbe8e06819f816ae3cb8c70`. Every executed test command, inner-command exit code and output hash is in [COMMANDS_AND_EXITS.json](docs/reviews/evidence/p3-independent-2026-10-13/COMMANDS_AND_EXITS.json). Collector shells may exit 0 after recording a failed child; use the recorded child exit. Failed attempts are retained.

**CORE_INDEPENDENCE: PASS, framework/disabled native shell only. FULL_PRODUCT_INDEPENDENCE: FAIL.**

Actual image `sha256:de0aa8d8454af7bf0970d39a9610c41d6acf935d9b8918b942b605ab57edca62`: installed site apps exactly frappe + lotus_fin; erpnext module absent; Company and Sales Invoice schemas absent; DB/Redis and workers start. Existing ordinary QA uses a framework Desk role, no business grants. Native handlers return authenticated explicit unavailability without any ERP record query, signing key requirement, native source fabrication or privileged request fallback. Current backend/support source was independently hashed inside the running container: 346/346 match. Local editor metadata and tracked historical bytecode were excluded from this runtime-source claim.

Runtime versions: Python 3.14.8, Frappe 16.35.0 at pinned upstream commit 012667b9c4e7f66d5e1ff5858d2e922331d4300a, Lotus 0.0.1, Pydantic 2.12.5, numpy 2.4.2, pandas 2.3.3. Current frontend package 0.0.0; installed/lock React and react-dom 19.3.0, TypeScript 6.0.3, Vite 8.3.3, oxlint 1.87.0. Host Python 3.13.7 and Node 22.19.0 execute offline/browser tests. Core Docker Node builder is pinned 22.22.0; framework/base/DB/Redis digests and locked runtime dependencies are present.

Core hooks have empty doc_events, scheduler_events, fixtures and legacy JS includes; no ERPNext required_apps. Default run.ps1/run.sh dispatch guarded docker/lotus-core/manage.py, not legacy ERP deployment. Optional integration remains separate under integrations/lotus_erpnext and requires ERPNext plus explicit qualification; it is unqualified and excluded from core. Deleted core Company fixture is semantically identical to the optional transferred fixture; raw hashes differ only by CRLF/LF (both retained in manifest evidence). No unrelated tracked source deletion was observed.

AI001–AI003 current providers, AI004 baseline, financial report pages and dynamic ERP route/catalog families still encode ERP schemas/records or lack approved native equivalents. Hiding/denying them does not migrate the promised full product. Frappe framework generic APIs are legitimate primitives but are not owned native authorization. N0 source/schema/tenant/membership/document/field policy is unapproved; no synthetic ledger, ERP permission shortcut or data-to-zero substitute was introduced by this review. Reusable numerical engines retain offline regression PASS without implying live source acceptance.

Five previously archived source files differ from current P3 bytes: LotusCopilotPage, invoiceActionClient, VercelChatPanel, UniversalPageView and copilot_test_harness. New DEMO/test files are also not the old baked UI. See SOURCE_DRIFT.json. A fresh current-source serving image/browser qualification remains required. The ERP-free backend startup PASS is separable from failing P3 route/session/isolation gates.

| Source | SHA256 of current bytes |
|---|---|
| `frontend/package.json` | `35386677a8ec903a6fd9c75b09e5732603a2a4626eabcb4e528386f7e81da50c` |
| `frontend/package-lock.json` | `4530fd8c3e9496a684a8569ee6a47dd0f3eb8d010b3def7a6d4222db67f23dd9` |
| `frontend/src/App.tsx` | `d97b68ab9574caca541613a96f1862ff1b6f97dabce3cf54e6ee2a9a6e4216a1` |
| `frontend/src/pages/copilot/components/VercelChatPanel.tsx` | `cc740e1a33b117058865f9af603fc0ced60da698554c68394cc7708591dc985c` |
| `frontend/src/pages/copilot/actions/useInvoiceActions.ts` | `e254951a620ec2b91b16a2702d134b39410e4d22910492bab35caa040dab6e5b` |
| `frontend/src/pages/copilot/actions/invoiceActionClient.ts` | `563953db81934bfa68a224f8e34251bba6a494001f59cd6a01d6208fe44e05ba` |
| `frontend/src/pages/copilot/demo/demoInvoiceProvider.ts` | `c97efae391e45c53c8e08410603fc4b92ceb20871132b139f38dfdd059a7586b` |
| `frontend/src/pages/copilot/prepare/FollowupPreview.tsx` | `c02d95699e67b5e985253a48e518efc496139a7adff8b747f60bea9b2d5a8381` |
| `lotus_fin/lotus_fin/runtime/boundary.py` | `c7094a16e6b5336f004813ce70de9c9c04f58db89477ece59cd67bdb0d88e021` |
| `lotus_fin/lotus_fin/api/invoice_actions_api.py` | `5014b7c161b55f98ce6e5128dc9bdc6f1276b0e6e59fed44906a84f5c6a9928d` |
| `lotus_fin/pyproject.toml` | `73640471508a2243d22ce497971bbc922679988b49ecd3137b321a16fa3ff878` |
| `docker/lotus-core/Dockerfile` | `13f2cfbe27d0c314101c71a774cfebd1954e1dba2ef4a69de555ae5ce8d39cad` |
| `docker/compose.lotus-core.yml` | `09f92a5a41f1009465747b3320f531223ca21615b1317fe11b6cecc5d47915a1` |
| `docker/lotus-core/framework.lock` | `c378b14ca9e669989a5e18164ca3084a32a2c6b54e49be34689587f87f9c8e0a` |
| `docker/lotus-core/requirements.lock` | `98a0e096f85b3d99b8ec6d0def15daff317cb850af5598764b5aab911b3c99ac` |
| `run.ps1` | `82959882727c5f358848dc8d36f6346f91adafb6deef9e4e6b4cb4fc54a4b06f` |
| `run.sh` | `f3718ea77bd03c212dd8b211a98321a339ed100585d534478acd9bd508545bea` |

## Graph review and authority

Bound repo/index: `lotus-fin`, `E:/lotus-fin`, indexed 2026-10-12T07:02:27.060Z at the same Git HEAD; working-tree/untracked coverage is incomplete. Concept query returned no definitions with FTS disabled. Explicit UID impact on the actual VercelChatPanel returned **HIGH**, 7 impacted symbols, 3 direct callers (LotusCopilotDrawer, LotusCopilotPage and fixture composition), App/UniversalPageView processes and 4 modules. HIGH is not waived by its LOW shared-axis score. New enforce_request_boundary is absent from the index; text inspection follows that unresolved graph result.

`detect-changes --scope all` reports 23 tracked files, 78 symbols, 12 processes, HIGH risk. Rerun with `--limit 500` still prints only 15 symbols/10 flows. This is not a clean graph gate and cannot cover the 140 unstaged/untracked candidate additions/changes or all unindexed source. No commit was attempted. Refresh the actual source index and obtain complete, non-partial/non-truncated change analysis before a future commit; do not quote the builder's “2 files / no breaking changes” as acceptance.

Final CLI status explicitly reports stale. The mandated `analyze --index-only` refresh was attempted and exited 1 after 375.80 seconds: native parse worker startup failed (5000ms readiness limit; bounded self-heal exhausted). No fresh graph acceptance is claimed. Existing risk receipts and source confirmation remain evidence with this coverage limitation. Global tool reinstall or production source changes were not performed to conceal the failure.

Authorities inspected: AGENTS.md, ADR001, Security Code V3, frozen P1/P2-B references, all seven required platform/runtime/N0/inventory reports and all seven current P3 builder reports. Latest user architecture supersedes legacy ERP assumptions and old transport descriptions. All remaining native source/policy approvals stay BLOCKED. Reports are evidence claims, not source authority or human N0 approval.

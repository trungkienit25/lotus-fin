# P4 GitHub pre-push — BLOCKED

13 October 2026 · Asia/Saigon · Independent targeted P4 acceptance.

Branch `codex/p2a-invoice-read-backend`; HEAD `5f805ef34f788245a3ec0e9c2f44e224eb16c305`. Reviewed current dirty/untracked working-tree bytes, not HEAD. No production source edit, stage, commit, push or merge. Only owned isolated project `lotus-core-p4c-01a13415-r5`, site `core-p4c-01a13415-r5.localhost`, loopback `127.0.0.1:8101` was tested and restarted; volumes retained. N0 remains **BLOCKED**.

| Acceptance dimension | Verdict | Scope / reason |
| --- | --- | --- |
| P1-01 profile and scenario transport isolation | PASS for profile switches; CHANGES_REQUIRED overall | Real page/drawer transitions clear DEMO under CORE; actor/session changes do not clear the mounted DEMO scope. |
| P1-02 disabled/revoked sessions | PASS | Persisted disable, explicit revocation, re-enable with old cookie deny; new valid ordinary session works. |
| P1-03 canonical route / CSRF | PASS | Ordinary login, direct route, refresh, actual one-message 503 POST; guest/invalid CSRF deny; repeated after restart. |
| CORE runtime independence | PASS | Only frappe + lotus_fin; ERPNext import and Company/Sales Invoice schemas absent. |
| CORE chatbot functionality | LIMITED / CHANGES_REQUIRED | Deterministic intents, local prepare and truthful unavailable boundary work; no qualified native financial answers; ERP-shaped Company probe remains. |
| DEMO function / forgery negatives | PASS within a provider/profile scope | All scenarios and four original non-200 forgery negatives pass; synthetic only. |
| DEMO actor/session isolation | FAIL | Three rows and one document survive Guest/new ordinary actor; old handles remain usable on page and drawer. |
| Native financial capability | BLOCKED | N0 approval/source/policy absent; real native context/search/open return 503. |
| FULL_PRODUCT_INDEPENDENCE | FAIL | Legacy financial sources still use ERP schemas/reports. |
| SOURCE_READY | CHANGES_REQUIRED | Session-scope defect, advisories, docs/collection/whitespace/graph/CI debt remain. |
| CLEAN_CLONE_READY | NOT_VERIFIED | Clean selected source/dependency snapshot tested; no reviewed committed Git candidate or clone. |
| SECURITY_PRE_PUSH | FAIL | Required session/actor scope gate fails; supply-chain assessment is not clean. |
| GITHUB_PUSH_READINESS | BLOCKED | No source/push approval; blocking security and reproducibility gates unresolved. |
| MVP_RELEASE_READINESS | BLOCKED | Security/source gates unresolved; no production finance acceptance. |
| G10_JUDGE_READINESS | BLOCKED | Independent gates fail and N0/full-product authority remain unqualified. |

## Exact source identity and preservation

The complete selected source manifest has **560 files**, SHA-256 `b3c687067382a5e84bad8d43f6f1f22cd73ebc0691d919fa2b8fd17b8fafafab`: [SOURCE_MANIFEST_COMPLETE.json](docs/reviews/evidence/p4-independent-2026-10-13/SOURCE_MANIFEST_COMPLETE.json). The initial 559-file snapshot omitted a tracked AI002 synthetic fixture; the corrected manifest includes it. The 517-file P4-C image-input manifest has SHA-256 `2600017e48b01eee74b788f2ebbbbb39689baf1a0d2a49851603b92b42244c8e` and **zero current-source drift**. These manifests have different scopes, not conflicting source identities.

Image `sha256:f7eda114867f2ea8803a5dafbef8e9927eeed0cb070b32766723cb1ea92325b3` is used by all seven app containers, including the one-shot init; 334 packaged backend files match frozen bytes. Four actual backend/queue/scheduler containers have identical module hashes, Linux platform, and no source bind mounts: [SERVING_WORKER_MODULE_HASHES.json](docs/reviews/evidence/p4-independent-2026-10-13/SERVING_WORKER_MODULE_HASHES.json). This is disk/module and process provenance, not a Python memory dump. The serving assets/private entry are bound in [RUNTIME_PROVENANCE.json](docs/reviews/evidence/p4-independent-2026-10-13/RUNTIME_PROVENANCE.json):

- JavaScript `assets/index-CeY-kyfF.js`: `52fc47074a33fac873fa56c1b976b6151cbcf12030fedb4cb6fe239a3e0f88ad`.
- CSS `assets/index-j6L4zPa6.css`: `0126d0bd8d95741b35163e1b8a5a4394e2245908b5ddffa445a507663da91f41`.
- Private HTML: `e2e42734b757dee2e703da94b495fa7d2aa1bfbc02f86a75d5a300b4acc2490b`.

Locks and executed test-source/oracle hashes are in [SOURCE_MANIFEST_COMPLETE.json](docs/reviews/evidence/p4-independent-2026-10-13/SOURCE_MANIFEST_COMPLETE.json) and [TEST_ORACLE_HASHES.json](docs/reviews/evidence/p4-independent-2026-10-13/TEST_ORACLE_HASHES.json). The existing r5 build already contains these exact P4 source bytes; independent pre/post-restart provenance confirms it is not the P3 UI. This review did not manufacture a new image or assert a fresh from-scratch Frappe build.

Initial Git inventory: 20,346 visible paths, 19,644 untracked files and 28 tracked dirty/deleted paths. The selected change plan has **126 paths**: 28 tracked changes/deletion and 98 untracked additions. The complete candidate includes 560 source/test/support inputs; unchanged tracked fixture files still belong in its manifest. The staging area was empty and remains untouched. No blanket staging is safe.

Concrete credential-format scan found zero findings in selected source. This limited scan does not certify arbitrary historical evidence or every secret format. .runtime, .env, caches, node_modules, generated assets, videos and source archives are excluded from the source snapshot. .gitignore does not make thousands of historical evidence/source copies a safe staging scope. Existing tracked __init__.cpython-310.pyc and tests_e2e/videos/ai003_risk_signal_e2e.webm remain in Git history/current tree; they were preserved, not newly staged or silently removed. A final reviewed source commit must explicitly decide their treatment.

## Reproducibility actually tested

A disposable 560-file source copy was checked byte-for-byte outside the main tree. Clean npm ci installed 378 packages; full TypeScript/Vite build and oxlint passed. A fresh Python environment installed the pinned offline lock plus numpy2.4.2/pandas2.3.3; pip check and 438 invoice tests passed. The initial snapshot lacked docs/features/AI002/fixture_scripts/direct_confirmed_commitments.json, causing four numerical failures; adding this unchanged tracked synthetic fixture to the review manifest restored 393 passes/7 subtests. Both failed and corrected receipts are retained. Ten browser fixtures passed using the snapshot frontend dependencies; no main-tree node_modules was used for that frontend install/build.

This is selected-source reproducibility, not a committed Git clone. Existing HEAD lacks 98 selected untracked additions. No disposable Git commit/staging was performed because the request forbids automatic stage/commit. Frappe startup was independently cold-restarted and source/image/assets reverified, but no new from-scratch Frappe installation or Docker rebuild was run by QA. The exact existing P4-C image matches all frozen inputs; its builder log is corroborating history, not a newly inherited PASS. CLEAN_CLONE_READY remains NOT_VERIFIED.

## Remaining checks

**P4-F01 · P1 acceptance blocker — mounted actor/session scope is not bound.** Profile changes are fixed, but the actual page and drawer omit `contextKey`; their invoice scope defaults to company/default/profile/scenario. External logout switches the authoritative server to Guest (bootstrap 401), yet three synthetic rows and one open document remain. Logging in as a second ordinary QA user without remount leaves them intact; an old selection opens DEMO-SINV-2026-001. See ACTOR_SCOPE_BROWSER.json, SESSION_SCOPE_BROWSER.json and page/drawer actor screenshots. This is synthetic presentation/provider leakage, **not demonstrated native financial disclosure or backend authentication bypass**. The requested actor/session clearing acceptance still fails. Bind both mounts and the DEMO provider lifetime to a current authenticated actor/session epoch, clear immediately on auth invalidation/visibility/session change, fence old results, and replay both surfaces without reload.

**P4-F02 · P2 — mobile scenario selector still clips.** At 390px, x=93.984375 and width=332, ending at 425.984375: about 36px outside the viewport. The sidebar, mode tabs and main input are improved; that does not qualify the whole form. Make the profile/scenario row fit and inspect 390px page/drawer control bounds plus keyboard focus. The accessible-name/Enter smoke is not WCAG certification; the builder's broad compliance wording is unsupported.

**P4-F03 · P2 — dependency review is not clean.** Fresh npm audit reports eight high/two moderate affected entries, including production path-to-regexp through @ant-design/pro-layout → @refinedev/antd. Production-only audit retains three high entries. Runtime PyPI metadata flags oauthlib, pdfkit, PyJWT, pypdf, weasyprint and Werkzeug versions. Deduplicate aliases and assess enabled framework/print/OAuth/JWT reachability before minimally updating locks; no blanket major audit fix or exploitation claim.

**P4-F04 · P2 — reproducible source/check gates remain incomplete.** Broad pytest still imports nonexistent BaselineSourceError; three other collection errors require the Frappe test environment. No documented enforced suite boundary resolves that mismatch. README still says invoice/L3 have separate synthetic test mounts; some older transport docs name wrong methods. P4-B lists a nonexistent demo_preview endpoint and 403 CSRF examples while the real server returns framework 400 CSRFTokenError. CI build-and-test is an echo placeholder and SAST continues on error; push triggers omit codex/* branches. Whitespace check fails; ESLint/config are absent (the actual lint gate is oxlint). No P4-D report was found. Correct these concrete gates without hiding security assertions.

**P4-F05 · P2 — graph/commit risk unresolved.** The stale 2026-10-12 index cannot resolve the current boundary; concept queries return empty with FTS disabled. HIGH chat-panel impact has three direct callers (page, drawer and fixture), seven impacted symbols and App/UniversalPageView processes. The aggregate tracked change report is CRITICAL and truncates 99 symbols/16 flows even with limit 500; it omits new/untracked source coverage. Separate-index refresh timed out after 480 seconds. UNKNOWN/empty is not low risk, and LOW shared axes do not waive HIGH. Obtain a current, complete, non-truncated graph review before a commit.

**P4-F06 · P2/P3 product debt — ERP-derived promises remain.** CORE mounts still make a best-effort /api/resource/Company request, although Company schema is absent and no result is used as financial authority. Legacy AI002 GL/Invoice and AI003 Purchase Invoice sources remain. Numerical fixture PASS and a disabled ERP-free HTTP shell do not qualify native finance, full product independence or G10.

Frontend lint is **oxlint**, 91 warnings, zero errors. No actual ESLint package/config exists; an explicit revised gate or configured ESLint remains outstanding. The broad host pytest policy is not clean: framework tests need Frappe, while BaselineSourceError is a real source/test contract mismatch. Preserve tests and specify separate offline/framework environments in enforceable CI. .github/workflows/ci.yml only echoes in build-and-test, SAST continues-on-error, and codex/* direct pushes do not trigger this workflow. No remote required-check/branch-protection status was verified for a future candidate.

## Exact proposed source change list — review only

- `.gitignore` (M; SHA-256 `b88a295e7571fac78266cbb109f4c35347a3920ae978626dc7714e89489d63e9`)
- `frontend/index.html` (M; SHA-256 `30fc9366ee4686c1b6fc7b4fd733a8d89dbea6d04d2c8d426d3971e3051c1b0a`)
- `frontend/src/components/copilot/LotusCopilotDrawer.tsx` (M; SHA-256 `c443a9b6ecd056e0916b3b01a61759dab5cc105d9432810a043e4404a6165966`)
- `frontend/src/components/tailadmin/Header.tsx` (M; SHA-256 `391dd54a70aded6cc5cd38bef1e51a8dbfa5a0c37ac14ad2854c8ede81e28991`)
- `frontend/src/components/tailadmin/Sidebar.tsx` (M; SHA-256 `103b62aa254c1d9a123ebaf7cb88f20376c4ca8813db88469f1f68ca569e0834`)
- `frontend/src/pages/copilot/LotusCopilotPage.tsx` (M; SHA-256 `07c6669e81cc8545734ca6f3c97754569baa9ee59ac0fb166b4ad9af11938f69`)
- `frontend/src/pages/copilot/components/VercelChatPanel.tsx` (M; SHA-256 `dfd975f8582238fae8cd7057145f81645410e7c03f1b2ab024df226682de8b42`)
- `frontend/src/pages/dynamic/UniversalPageView.tsx` (M; SHA-256 `44556bbdce887e0162d82fb35960e64ddf29797ba95d0f7a529fd5e92262fb84`)
- `frontend/src/pages/login/index.tsx` (M; SHA-256 `b2874390546a5db2cb50108a0dd5b3e9c50cba373d61993b8d886655b54848b0`)
- `frontend/src/providers/authProvider.ts` (M; SHA-256 `ff9452f1e140dca4dfbee08522c17a8a9eae2272590f7bf701dc0b56372ce33a`)
- `lotus_fin/lotus_fin/api/invoice_actions_api.py` (M; SHA-256 `5014b7c161b55f98ce6e5128dc9bdc6f1276b0e6e59fed44906a84f5c6a9928d`)
- `lotus_fin/lotus_fin/application/service/search_invoices.py` (M; SHA-256 `3d51430d3c0769178e9e3f141ae79a6517e1122b8a635520798cac4a617817ef`)
- `lotus_fin/lotus_fin/domain/schema/invoice_read.py` (M; SHA-256 `b456ebf98efa9b98e197f13e0549260c6f09592eeb84db4977771494f7da7402`)
- `lotus_fin/lotus_fin/fixtures/custom_field.json` (D; SHA-256 `DELETED`)
- `lotus_fin/lotus_fin/hooks.py` (M; SHA-256 `000097e785f772d2ca2f67b32427fb83a47fea8d1edc60578e3bd6ae4b2ed6c7`)
- `lotus_fin/lotus_fin/infrastructure/config/invoice_actions_config.py` (M; SHA-256 `30a03c9fba7eb48cf357f269027847903a9fed4ab7aa55600931a6394fe0cd23`)
- `lotus_fin/lotus_fin/infrastructure/security/frappe_invoice_authorizer.py` (M; SHA-256 `0f6af5e31a20b8d49a8084e02e9dbcf65b6c0d4b8019e1e9730f8efb10d79a7b`)
- `lotus_fin/lotus_fin/lotus_fin_ai/workspace/lotus_fin_ai/lotus_fin_ai.json` (M; SHA-256 `99f62146ffaa85315035727d7f08701ff3e23fd4dc727f0564afe80c6ed5db23`)
- `lotus_fin/lotus_fin/presentation/controller/invoice_actions_controller.py` (M; SHA-256 `859c56d2b40d1793855ac891f08361d3cc8ddbb3cb1b8db9b435092142111b15`)
- `lotus_fin/lotus_fin/presentation/dto/invoice_action_request.py` (M; SHA-256 `0fead5649c07730ad1741a5fc6bbcd93e7fdfa17567b6bd655b3c7af03f6f684`)
- `lotus_fin/lotus_fin/tests/test_action_reference_privacy.py` (M; SHA-256 `a107119ca0f95ca9d52af4e27fc1ffec4bd27fc9617b8ccf56d04b25e6197f4e`)
- `lotus_fin/lotus_fin/tests/test_invoice_auth_delivery.py` (M; SHA-256 `cf796508ce6cd5aa30baa4b269a8bfabf7dcf801a6ba84ba2947d120152876be`)
- `lotus_fin/lotus_fin/tests/test_invoice_context.py` (M; SHA-256 `bd06caa647c4bcea49f679a866a91fadc306894547ea8b3a1f9ca534f2d3ba22`)
- `lotus_fin/lotus_fin/tests/test_invoice_permission_seam.py` (M; SHA-256 `acfd2d4f013183d1dc180ba50f7f7914bf4a64b695b34749eb317d5cadfd37ab`)
- `lotus_fin/lotus_fin/tests/test_invoice_terminal_delivery.py` (M; SHA-256 `56bb7ecac9d745947bb706a6a41b15a84687b1cd9e1d991841860cbeaf811a52`)
- `lotus_fin/pyproject.toml` (M; SHA-256 `73640471508a2243d22ce497971bbc922679988b49ecd3137b321a16fa3ff878`)
- `run.ps1` (M; SHA-256 `82959882727c5f358848dc8d36f6346f91adafb6deef9e4e6b4cb4fc54a4b06f`)
- `run.sh` (M; SHA-256 `f3718ea77bd03c212dd8b211a98321a339ed100585d534478acd9bd508545bea`)
- `.gitattributes` (??; SHA-256 `f02f86ec7cea164a279f9d16ba8fbb409236124ecff304dddb300eaea36ba337`)
- `README.md` (??; SHA-256 `19ab7250fd5733c573014417424cb5226b0a71d33502c23e4819deebc57d76a2`)
- `docker/compose.lotus-core.yml` (??; SHA-256 `8b00ed0d09e45a424e6801661af523990ab8e48b0470d07d0613d48765ed22f0`)
- `docker/lotus-core/.env.example` (??; SHA-256 `d3d2570935930f07df7b1374fca8c4b419f260b3f5478ee374117b847d453f92`)
- `docker/lotus-core/Dockerfile` (??; SHA-256 `d37bdd654c636c2b262b6713cd730c14a8a410887ce029fb7e0d1d1a820e72e0`)
- `docker/lotus-core/Dockerfile.dockerignore` (??; SHA-256 `fa8f65d5772675e61692de3b15d294e9bbba201e33123a981152fc9b707053e1`)
- `docker/lotus-core/framework.lock` (??; SHA-256 `c378b14ca9e669989a5e18164ca3084a32a2c6b54e49be34689587f87f9c8e0a`)
- `docker/lotus-core/http_qualification.py` (??; SHA-256 `55bcfd20551f940074794f920f9fa4770d33954c1e997f16b0c30d9aae9d74de`)
- `docker/lotus-core/init.sh` (??; SHA-256 `cacecfaf7d26f4514171e1775e777b4892dd3286378cf0f3ffdbd573104db0d7`)
- `docker/lotus-core/manage.py` (??; SHA-256 `6750fe580c634d1a225d503f75e8a5ff0b529043a0791feb50528997bd523d78`)
- `docker/lotus-core/package_release.py` (??; SHA-256 `40b018f158e930375793d26211895a1c2edc17136f2532d3f49ea96e95cd7bf4`)
- `docker/lotus-core/provision_qa.py` (??; SHA-256 `8b8a9be60a9d31077c6736d98dc60b8abac83e8b42d35554339d8190e48976fa`)
- `docker/lotus-core/requirements.lock` (??; SHA-256 `98a0e096f85b3d99b8ec6d0def15daff317cb850af5598764b5aab911b3c99ac`)
- `docker/lotus-core/smoke.py` (??; SHA-256 `7b33fc2669ac1119bf9150f6667d9576be43ac491d264e3e59af732326cf339c`)
- `docker/lotus-core/test_spa.py` (??; SHA-256 `3286e33a642ed03f4aa59bef36fb983df8c32492baaff1df2c598ebbeeaf2a8f`)
- `docker/lotus-core/upstream/main-entrypoint.sh` (??; SHA-256 `bb850ec1e13cccf326c8fdc9bb64a4b90c219d7f39295481822207251f25aebd`)
- `docker/lotus-core/upstream/start.sh` (??; SHA-256 `194a7225d6fb0a49dc0591d1ac450e3ff8060b93ee4a47be503ef40e61bbb48a`)
- `docker/offline-acceptance/Dockerfile` (??; SHA-256 `32814beb833ec2f2950a23e5d6d8f22f0e6d91737c9d0643ad285462e78306e6`)
- `docker/offline-acceptance/requirements.lock` (??; SHA-256 `2e5db0822725e7ec959bdb6ebded286dfcf2104fd64993c3832d1870ee06897b`)
- `frontend/src/pages/copilot/actions/InvoiceActionPanel.tsx` (??; SHA-256 `fd3da8da177b3aa41c8759e71e3c58c291f1421532a6a2dd0ec69ddaea48b3c7`)
- `frontend/src/pages/copilot/actions/InvoiceReadView.tsx` (??; SHA-256 `84559d4162dece8c61093f1a6a25737f171d2c1169aadeafbebb0b1da7974aae`)
- `frontend/src/pages/copilot/actions/InvoiceSearchResults.tsx` (??; SHA-256 `740a7f9448c95c23720b3684d0bb09d8ce1a4652bd8955cf6d9245549ec1134a`)
- `frontend/src/pages/copilot/actions/invoiceActionClient.ts` (??; SHA-256 `45a984aae5c445afc1c30a77aafbd28c69205ebdd56607a896a2f0815b4d1121`)
- `frontend/src/pages/copilot/actions/invoiceActionController.ts` (??; SHA-256 `485341b353915d0e5ec05da9ad1a7247833b5bc2482bc3b3aa0917f8dc176843`)
- `frontend/src/pages/copilot/actions/invoiceActionControllerOps.ts` (??; SHA-256 `7a2a9d5920c21e79c932bdaa017344e72f3247db36dabee87d189dd727cf6c9d`)
- `frontend/src/pages/copilot/actions/invoiceActionControllerState.ts` (??; SHA-256 `8a758c5c1b117c18dd65bf3f94ae413554409d7a2d35551bcdf8f8613878efa7`)
- `frontend/src/pages/copilot/actions/invoiceActionCriteria.ts` (??; SHA-256 `25c3584789ae184b7187ee03795ad0e9e3eed0d81a7e2c887d3edd894859ea32`)
- `frontend/src/pages/copilot/actions/invoiceActionDecoderHelpers.ts` (??; SHA-256 `8f575b3c6471b7a5a7428bc7fabe4366ce11b19e35656eb686564ded5d745f0f`)
- `frontend/src/pages/copilot/actions/invoiceActionDecoders.ts` (??; SHA-256 `96a2a47bf98f111b0e2ec8802f9ad81fbfa753c9e8eca0acc6e26b2c08a117fd`)
- `frontend/src/pages/copilot/actions/invoiceActionPayloadDecoders.ts` (??; SHA-256 `9ef21dfbb8853e1d238e3c8a3d535c0c7d3392019c9e7f40f7eb1909c443afb0`)
- `frontend/src/pages/copilot/actions/invoiceActionPresentation.ts` (??; SHA-256 `c3432aedb3cd46a1f549cccc86a547565236b7e1b7bc720fe9d30bd239bd1861`)
- `frontend/src/pages/copilot/actions/invoiceActionTypes.ts` (??; SHA-256 `6adc5aef03fe99c4f70bdfcc0bb9d1bb833c82c29452919a37c5dcd3aa9b9b2e`)
- `frontend/src/pages/copilot/actions/useInvoiceActions.ts` (??; SHA-256 `d10e6ec4886ab6edd9c68574643c067611dab1de6f1445d5f4f7551930286c7c`)
- `frontend/src/pages/copilot/components/ChatHeaderBar.tsx` (??; SHA-256 `227b0b8789003c1844c3bf5ad30b003e23336aa01deada8a1829e71a29825ebc`)
- `frontend/src/pages/copilot/components/ChatInputComposer.tsx` (??; SHA-256 `3f40577ab3391c2389c88e403bfe077803b18b818ff17a13e24fdd1fafcacc59`)
- `frontend/src/pages/copilot/components/ChatMessageStream.tsx` (??; SHA-256 `ad77cdd867d61ec354750b6a419300e1b0e4d903c7f421caa68d685c0d26d4a9`)
- `frontend/src/pages/copilot/components/CopilotMessageBody.tsx` (??; SHA-256 `20b647b36fe5bad565fecd64fc20228ba0b9eb8371696c2c8f197f44654f554d`)
- `frontend/src/pages/copilot/components/InvoiceActionsTabView.tsx` (??; SHA-256 `99e88417c7a81f1765375b34ef3448827205a99afe6cc09413d83dec764b1d67`)
- `frontend/src/pages/copilot/components/VercelChatPanelTypes.ts` (??; SHA-256 `94a684d1f4e3e5f8a28b2fcdbd6935942941dff2bb8e9c36440c6140c789ee9d`)
- `frontend/src/pages/copilot/components/copilotPresentation.ts` (??; SHA-256 `ebd1218ca7d8249653cfff7b2e789f96ffbab823ec4c39a189da5b329d4d4f0c`)
- `frontend/src/pages/copilot/components/useCopilotRequest.ts` (??; SHA-256 `97365ea11f0cb06be0c3a15435453df99f1c5fd50ab31fccc5aab8e77584be76`)
- `frontend/src/pages/copilot/demo/demoInvoiceProvider.ts` (??; SHA-256 `92c21693cd7d846bf4b09824bb5cbfbfb2e7a4803f7ae5d2f9878c06f31e4a4b`)
- `frontend/src/pages/copilot/demo/demoInvoiceResponses.ts` (??; SHA-256 `283d1ea2af187861100e6614e2f2a3b029c4c9cabf648c15ccd78a1758a679c9`)
- `frontend/src/pages/copilot/demo/demoInvoiceTypes.ts` (??; SHA-256 `8dc2de1b8463e044afecc8cf2920e3686e8f9bf65e6f6c8024080f88f94db65b`)
- `frontend/src/pages/copilot/prepare/FollowupPreview.tsx` (??; SHA-256 `c02d95699e67b5e985253a48e518efc496139a7adff8b747f60bea9b2d5a8381`)
- `frontend/src/pages/copilot/prepare/followupPreview.ts` (??; SHA-256 `04290ace5ae982d1e5c440dcf6377f4c2b18734d3717e2534c1a5c271c269de1`)
- `frontend/src/pages/copilot/prepare/followupPreviewController.ts` (??; SHA-256 `324962915a642110a63d691b2952522203b8e0f721f8125c6a1b3fac1b642c84`)
- `frontend/src/providers/sessionBootstrap.ts` (??; SHA-256 `73d365b7a462a27a528bf373e2152bac9a0ef64e23e6f215abdbf1d08a70999e`)
- `frontend/tests/followupPreview.test.ts` (??; SHA-256 `f638baef2646d425efec230c7693523f9a4f896d547030edf88027404847c871`)
- `frontend/tests/followupPreviewController.test.ts` (??; SHA-256 `9c55e8eba38785e3745dea0633e61b23dc6db969862a81153e6647ec71ed2247`)
- `frontend/tests/p2b/client.test.ts` (??; SHA-256 `133c032985fb146d2164a4735b09150605338fd9a31073fdee4e8df38e05816d`)
- `frontend/tests/p2b/controller.test.ts` (??; SHA-256 `a4c4be043532c88254da57e2449441a8de53173941442c311e40d61e1a26c59d`)
- `frontend/tests/p2b/fixtures.ts` (??; SHA-256 `0d368fb06ca686bcea8c37211212ab8557dd6d8ad9b58028a03d5984bed1584e`)
- `frontend/tests/p2b/presentation.test.ts` (??; SHA-256 `4805c6ce361c469a37aaeddfb283efe3eec9630be18d97ad2939f399cf2dde04`)
- `frontend/tests/p3_transport_and_demo.test.ts` (??; SHA-256 `5777e8ac797769c7388b042d885734d34d6df44ba683c60a3abf3c9088475525`)
- `frontend/tests/p4a_profile_and_demo_security.test.ts` (??; SHA-256 `c9b31b80c842085bc4e1b654c761adc25f27fd40bb5f6f2e11e84533e41e89cb`)
- `frontend/tests/p4c_session_bootstrap.test.ts` (??; SHA-256 `cda870e20cf9ae10829b8a099ef088a18b7e16265aa90103cbad23d28e339d50`)
- `integrations/lotus_erpnext/README.md` (??; SHA-256 `3f8f2806f5995b45ca632f06acaab04abcdb045ab68933c59dfbadd2f2b3ebb6`)
- `integrations/lotus_erpnext/lotus_erpnext/__init__.py` (??; SHA-256 `792269f4c46652ac6886a773e8c240e4cb859b536c19b6994577f34562f80683`)
- `integrations/lotus_erpnext/lotus_erpnext/custom_field.legacy.json` (??; SHA-256 `e688c655d7662d82ce3ac9642529b284fc037bb3315fd79e8c46f4cec3b34941`)
- `integrations/lotus_erpnext/lotus_erpnext/events.py` (??; SHA-256 `eb629436b305de2d11f8b1b13890ad236cdf36e315dd7409dc11d15d7c729f47`)
- `integrations/lotus_erpnext/lotus_erpnext/fixtures/custom_field.json` (??; SHA-256 `e688c655d7662d82ce3ac9642529b284fc037bb3315fd79e8c46f4cec3b34941`)
- `integrations/lotus_erpnext/lotus_erpnext/hooks.py` (??; SHA-256 `e00aef4aaef46e4ce9e3043497e9880e22d343490b28b852480284ff5d7e9adb`)
- `integrations/lotus_erpnext/lotus_erpnext/install.py` (??; SHA-256 `658b280c166de640d2c79d694450e4502ed8937c36ede9864d8ac5d0c6cf6efc`)
- `integrations/lotus_erpnext/lotus_erpnext/modules.txt` (??; SHA-256 `2a0c54354faf6f8581d0ed8f540c928fb7b702bccc8e41d5877ba908668fb2c1`)
- `integrations/lotus_erpnext/lotus_erpnext/workspace.legacy.json` (??; SHA-256 `d4fe3ad8ead5157810c320c99444daee537a80cb0f0e71e52742064ebdec2b7d`)
- `integrations/lotus_erpnext/pyproject.toml` (??; SHA-256 `174df864e3a848ad5d434528be98ffe9abb03520fd4a212f83475023cdb51885`)
- `lotus_fin/.zcodeignore` (??; SHA-256 `3426215d05709084139224c813f4ce85c368786902e6ca9b1ac2663f6d7b759e`)
- `lotus_fin/lotus_fin/infrastructure/config/invoice_actions_config_loader.py` (??; SHA-256 `bb477eafa12b84bd529a29eb109c06510eb255d59988c363f32d177d0fd4ab58`)
- `lotus_fin/lotus_fin/infrastructure/persistence/frappe_cache_session_repository.py` (??; SHA-256 `c0365a5096daa24a7e5888f54e2cabe3d67abc48c9cdbf571c832de644f345a0`)
- `lotus_fin/lotus_fin/presentation/dto/invoice_action_http_request.py` (??; SHA-256 `bb903c0e0d8fb7214cc3ceb409356f7dd69343c08b95d46edce174894a220c86`)
- `lotus_fin/lotus_fin/public/logo.svg` (??; SHA-256 `7735afdbd78762abe90dfdc27ff06471f67e3c40362effd609da370b56213f9e`)
- `lotus_fin/lotus_fin/runtime/__init__.py` (??; SHA-256 `edd477c034f28abb0853859d404a1ddd5ecdc9371fb06b6c6d45cc73b13649f5`)
- `lotus_fin/lotus_fin/runtime/boundary.py` (??; SHA-256 `853d35c0f09299b21c86b51d9a1c2ce4283140ae1bb5b4bdf260380a533e4df2`)
- `lotus_fin/lotus_fin/runtime/health.py` (??; SHA-256 `6987189efae8453943f2bb6828db83dd8c4560e4ed1aea5cfb6de386c653d4bf`)
- `lotus_fin/lotus_fin/runtime/spa.py` (??; SHA-256 `e7dc6038753ab4f1e154a36c73935770ffa778323332d132398618052748f0cb`)
- `lotus_fin/lotus_fin/tests/test_architecture_remediation.py` (??; SHA-256 `f4560a114ea0601bbbbb6059e314247ed472c154d2710e3e6ad8229ab82a38aa`)
- `lotus_fin/lotus_fin/tests/test_disabled_user_revocation.py` (??; SHA-256 `0b53d4595ea7cfb82be529259e97ae87c8d44b31e2a64d377282a8a8ee021140`)
- `lotus_fin/lotus_fin/tests/test_frappe_only_boundary.py` (??; SHA-256 `cea0164fb44800404fb8e41ffc7e12b4b0059afffba664ead4e905bc5b516607`)
- `lotus_fin/lotus_fin/tests/test_invoice_config_loader.py` (??; SHA-256 `5f186961603d2baf238372bdaf837891786ac73739f5404bba07e526d084fd9e`)
- `lotus_fin/lotus_fin/tests/test_invoice_config_rotation_security.py` (??; SHA-256 `2276afe4ab6c87b248141ce1efaeee8ea579ebbfb9ed676e5adc23a37f7b7159`)
- `lotus_fin/lotus_fin/tests/test_invoice_context_data_correction.py` (??; SHA-256 `e3106269c3d240fa769d6a86cfb23d379dfbe2844f22946311b57a83ec0ce38d`)
- `lotus_fin/lotus_fin/tests/test_invoice_controller_context_expiry.py` (??; SHA-256 `227857fc7277abf10813bd1ac352faf2fe7c8453e83af6bb5ebbb4d4e3e6d951`)
- `lotus_fin/lotus_fin/tests/test_invoice_controller_wiring.py` (??; SHA-256 `a5a6b4ab72ec4e2c667db7c3f22e147035bb8043abdaeead51039b89bf6ec94f`)
- `lotus_fin/lotus_fin/tests/test_invoice_http_boundary.py` (??; SHA-256 `ea657d8a322dc1d54e38332040d5b9fbafd2007b2b5a2586c6e44ba0dcbc5b04`)
- `lotus_fin/lotus_fin/tests/test_invoice_read_family_correction.py` (??; SHA-256 `efabedf0ca53ce2b87fb1700122e3c731e49fb7987f38031dd3bc3ac0ee29ed9`)
- `lotus_fin/lotus_fin/tests/test_invoice_request_correction.py` (??; SHA-256 `d3826d9fe17ddb2046fdd949ca98c62e8e579b66784de1415ff810a4df662dae`)
- `lotus_fin/lotus_fin/tests/test_pydantic_b1_hardening.py` (??; SHA-256 `8bcaac35aeb667ab4d0b8c6f3eb222ecf4a111722d988f90e289f0845700950d`)
- `tests_e2e/copilot_fixture/index.html` (??; SHA-256 `d67d5f312a4d51f9c4adb8bb3d8c0960c2d0a7785e0b77aca90a6fc21bbf21b7`)
- `tests_e2e/copilot_fixture/main.tsx` (??; SHA-256 `a11dd58857ec12378dfa573a687fe2016f5b8b10eb2b2afffad957defa4d76b6`)
- `tests_e2e/copilot_fixture/vite.config.ts` (??; SHA-256 `1b973e8bf9c9e5862c3cf3e3848b4e132b01e556116200f3fb9c35365c683085`)
- `tests_e2e/copilot_test_harness.py` (??; SHA-256 `1497312b64b95e538be790410e062d0834436032f77d60ecc8f9ba0f29b2df20`)
- `tests_e2e/followup_preview_fixture/index.html` (??; SHA-256 `965b3dc321baae83d4385490bd9407663920b7dac29ef5323faefcde59ce3e7f`)
- `tests_e2e/followup_preview_fixture/main.tsx` (??; SHA-256 `046e868398e8260bc8c9d4160ac28e063f7ca68713493e7e5a75109d50dff8fb`)
- `tests_e2e/followup_preview_fixture/vite.config.ts` (??; SHA-256 `02c556474d785a047d541839b919cac2b97827f7f6bbce77f13b10b459ecbdfc`)
- `tests_e2e/test_copilot_failclosed.py` (??; SHA-256 `4075d799ec2a1d7f89e3accf82671797e2e96ed03e44ec2dd38c4e128d2dcc09`)
- `tests_e2e/test_followup_preview_e2e.py` (??; SHA-256 `eff1c0aadad3989312475b25ab34194d78cbccbd26054fc4d9ad6b298b339e5b`)
- `tests_e2e/test_invoice_actions_e2e.py` (??; SHA-256 `90754749fe332b9c36ed6fc76042170b55050f99ab6af37a6f6392457bb0ccbe`)

Six requested independent root reports are separate proposed documentation additions. Public evidence should be added individually only after checking PUBLIC_EVIDENCE_MANIFEST.json; exclude disposable source trees, installed dependencies, caches, archives and any runtime credentials. No commit/push authorization is inferred from this list.

## Commands, exits and hashes

| Command receipt | Child exit | Output SHA-256 |
| --- | --- | --- |
| [clean-serving-base-build](docs/reviews/evidence/p4-independent-2026-10-13/clean-serving-base-build.txt) | 0 | `6f54e092760f6a796754033397820ec52f0c20be811602e154c7445b60a231d9` |
| [actor-scope-browser](docs/reviews/evidence/p4-independent-2026-10-13/actor-scope-browser.txt) | 1 | `4ec973e66fe8471917f1417537996a38f35c4ca3ff528414bf1017621e31ccb7` |
| [backend-focused](docs/reviews/evidence/p4-independent-2026-10-13/backend-focused.txt) | 0 | `55ca0d4e2184d0712faedc0f7511c97e16270ca4172c9daba9aceb2a5b61d746` |
| [boundary-renderer-r2](docs/reviews/evidence/p4-independent-2026-10-13/boundary-renderer-r2.txt) | 0 | `100fc0508b8212781dc4bef3b881ec64e527ffd9209b2ad799c49a22731dc8a4` |
| [boundary-renderer](docs/reviews/evidence/p4-independent-2026-10-13/boundary-renderer.txt) | 2 | `e874e288e784d562dfd09bb2eeefa6f84b5d4f9ba3536782a3c5df54dbd4f029` |
| [broad-pytest-collection](docs/reviews/evidence/p4-independent-2026-10-13/broad-pytest-collection.txt) | 2 | `08898d0d24ed7522a5e2b6a1aa4cd9b666a9cac86ccc650528b4eed4f043ea45` |
| [canonical-core-browser](docs/reviews/evidence/p4-independent-2026-10-13/canonical-core-browser.txt) | 0 | `1db328506c2685c84667eb2fd0d989e2206bc62be8f163face3d81e295b87302` |
| [clean-backend-focused](docs/reviews/evidence/p4-independent-2026-10-13/clean-backend-focused.txt) | 0 | `0cad17f58cef07dcb5ec36ab1b9caab902e0fe5b5163e3815bbc8aa0d4a8c118` |
| [clean-browser-fixtures](docs/reviews/evidence/p4-independent-2026-10-13/clean-browser-fixtures.txt) | 0 | `3caf7ab6e71e9c68ad48d353ef102b37a066540de012c7d0cd86a7588062c803` |
| [clean-build](docs/reviews/evidence/p4-independent-2026-10-13/clean-build.txt) | 0 | `769e17815d4437f5e47fe9588d150bf8033701a14c03798c3a7a8296dbeb9de8` |
| [clean-features-current-r2](docs/reviews/evidence/p4-independent-2026-10-13/clean-features-current-r2.txt) | 0 | `09bfcfe3be6f466ab848bd7063ab324f551aad3ec6a593fed99df564b23788e1` |
| [clean-features-current](docs/reviews/evidence/p4-independent-2026-10-13/clean-features-current.txt) | 1 | `972a38703a6408410ea9b01a1ed0d41f6b1a01d7bb0e9413c4bce970e0a7d8e8` |
| [clean-lint](docs/reviews/evidence/p4-independent-2026-10-13/clean-lint.txt) | 0 | `d53571295d52b4f04db8e004aed379fa9d728cc7b3891a6c398a7acfd0e4fb1a` |
| [clean-npm-ci](docs/reviews/evidence/p4-independent-2026-10-13/clean-npm-ci.txt) | 0 | `0d66071a72956870c854709fb2990ac5c802c79efd9b214b6f03748829de7256` |
| [clean-pip-check](docs/reviews/evidence/p4-independent-2026-10-13/clean-pip-check.txt) | 0 | `672aec65a45bed50e70229c70934a7eebf0462595c459b83023027645d57cccf` |
| [clean-python-install](docs/reviews/evidence/p4-independent-2026-10-13/clean-python-install.txt) | 0 | `4d22e92e59ca741c06fb7c0c09ff632182b997bfdc3eb1cac4989ce68a09011e` |
| [clean-python-venv](docs/reviews/evidence/p4-independent-2026-10-13/clean-python-venv.txt) | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| [core-runtime-smoke](docs/reviews/evidence/p4-independent-2026-10-13/core-runtime-smoke.txt) | 0 | `bfe3c2732d0310bcd3fd290a8bb9945bc2e22112d08b4738dcfca35fe4d0e0c7` |
| [diff-check](docs/reviews/evidence/p4-independent-2026-10-13/diff-check.txt) | 2 | `e847a036e1d8227377287dd8db15ddd0052df96ca699f3159c094cb47fe87149` |
| [features-current](docs/reviews/evidence/p4-independent-2026-10-13/features-current.txt) | 0 | `329fa212fcbf27e3806065740a6820ea7818a90a75802c6e0d8e55ec08ff1dcb` |
| [frontend-unit](docs/reviews/evidence/p4-independent-2026-10-13/frontend-unit.txt) | 0 | `68a0bee18831e4a5b4fc414b8dd8b3e2bd7b10ac8213309d1bb935607c7e1de6` |
| [graph-context-boundary](docs/reviews/evidence/p4-independent-2026-10-13/graph-context-boundary.txt) | 1 | `a41ea1a99e96a59664932f3a0d7f18a0028e557555f7137fa745820147ac9bc4` |
| [graph-detect-current](docs/reviews/evidence/p4-independent-2026-10-13/graph-detect-current.txt) | 0 | `a401044070f214de830930fe6ce4ee02c05ec211cda471a6483b312361b26606` |
| [graph-impact-panel](docs/reviews/evidence/p4-independent-2026-10-13/graph-impact-panel.txt) | 0 | `388ef7f537fce0d0302aefbe46b228a77cc8f1ef2a32038c78bedbc2adbfadc4` |
| [graph-query-erp](docs/reviews/evidence/p4-independent-2026-10-13/graph-query-erp.txt) | 0 | `5f9e6bfca9ddeea4e3e85ffc9a3c9bbe6d9fbedcb8c936349c19b507487c5950` |
| [graph-query-fixture](docs/reviews/evidence/p4-independent-2026-10-13/graph-query-fixture.txt) | 0 | `bc2177cbdd7f0280e70488409743d35c9602ee429c068b87773b94385c87998f` |
| [graph-refresh](docs/reviews/evidence/p4-independent-2026-10-13/graph-refresh.txt) | 124 | `60a522b3aad4fdcce9fd0a14ba4a08d09399507bef71aa513c999775c972e522` |
| [graph-status](docs/reviews/evidence/p4-independent-2026-10-13/graph-status.txt) | 0 | `754f9a7a68be0ffa3f9354905c57877c4eee7c80ea323aa9cc5785dcad2a7cd3` |
| [isolated-post-restart-smoke](docs/reviews/evidence/p4-independent-2026-10-13/isolated-post-restart-smoke.txt) | 0 | `e584b4fbd168c6b489abfe51364da41c93c97562db2e31b4d0868caa907eee23` |
| [isolated-start](docs/reviews/evidence/p4-independent-2026-10-13/isolated-start.txt) | 0 | `efe756257575bc2726fd74662a9a566722ee7e6e9309b127e637bb91d1d77628` |
| [isolated-stop](docs/reviews/evidence/p4-independent-2026-10-13/isolated-stop.txt) | 0 | `b470d9993ad476aaecc8002320c4158a9b4101c55b0208d88bcebe95415e8370` |
| [live-security](docs/reviews/evidence/p4-independent-2026-10-13/live-security.txt) | 0 | `7ad7ea331097942293eab505c8860df906c158c80d9bee4acf96076232e5aade` |
| [mounted-browser-r2](docs/reviews/evidence/p4-independent-2026-10-13/mounted-browser-r2.txt) | 0 | `3cafef6bd6303c7a38832c41efa84ea2d9ec0837e2b5be32642fa373ea850c3c` |
| [mounted-browser](docs/reviews/evidence/p4-independent-2026-10-13/mounted-browser.txt) | 1 | `951c717767e78f3a249ba902b6b3816b0d400fc5acd12d645480c46fb4554aa7` |
| [npm-audit-production](docs/reviews/evidence/p4-independent-2026-10-13/npm-audit-production.txt) | 1 | `f2d17398625a7ae373b21850154185e4ff72b07c048e5ad66c1c0484a77e3091` |
| [npm-audit](docs/reviews/evidence/p4-independent-2026-10-13/npm-audit.txt) | 1 | `d4bb8302f8c3c73095c7f30bbf2e77c789c234a147939c9a890f1b391947fc49` |
| [npm-explain](docs/reviews/evidence/p4-independent-2026-10-13/npm-explain.txt) | 0 | `9a04903c5e26f53e3db148410b763adc01bce994407b9e7002d23c8640613e2b` |
| [oracle-demo_negative](docs/reviews/evidence/p4-independent-2026-10-13/oracle-demo_negative.txt) | 0 | `e76c7b49f6e9b79af0236abe6aedfce7ea3e9504bb1159acbab367ecc18698c4` |
| [oracle-fresh_oracle](docs/reviews/evidence/p4-independent-2026-10-13/oracle-fresh_oracle.txt) | 0 | `6039d11cf7ba504dce4f49a423c451e34b3d7860f51317c86820c68a663ec90a` |
| [oracle-l3](docs/reviews/evidence/p4-independent-2026-10-13/oracle-l3.txt) | 0 | `575cbb7cb14a1788de45eb1f7fd528692f258f8fc28447cb49b192ad24378973` |
| [oracle-new_oracle](docs/reviews/evidence/p4-independent-2026-10-13/oracle-new_oracle.txt) | 0 | `22468a01e48c2d47c795616d8338187d5fdaa25995ed66d12fd9d898e337f5a6` |
| [oracle-original23](docs/reviews/evidence/p4-independent-2026-10-13/oracle-original23.txt) | 0 | `93852dbe5ca095cd7b9893a606ad36a099ebebb21a55c7cc41882c5592ffc8dc` |
| [p4b-and-spa-unit](docs/reviews/evidence/p4-independent-2026-10-13/p4b-and-spa-unit.txt) | 0 | `b96062aaf7bf1c0d6481a2a4ca87fb350b5b0d94200837404af5c97932c1dcb5` |
| [post-restart-canonical-browser](docs/reviews/evidence/p4-independent-2026-10-13/post-restart-canonical-browser.txt) | 0 | `1db328506c2685c84667eb2fd0d989e2206bc62be8f163face3d81e295b87302` |
| [python-advisory-review](docs/reviews/evidence/p4-independent-2026-10-13/python-advisory-review.txt) | 0 | `6a7d9f1823d0ca8d88d562e05382d8438b73a6e94cc00946f9ecc2fa6091f1c1` |
| [runtime-installed-packages](docs/reviews/evidence/p4-independent-2026-10-13/runtime-installed-packages.txt) | 0 | `2f5ead75a550f58d290a4e81618e06cfd04856eb9046224bd302b32cb197558e` |
| [runtime-provenance-post-restart](docs/reviews/evidence/p4-independent-2026-10-13/runtime-provenance-post-restart.txt) | 0 | `ac881addc4e83281090bcb5600ace7c7dd755c2d9a85227b41ae21c482bd5fe2` |
| [runtime-provenance](docs/reviews/evidence/p4-independent-2026-10-13/runtime-provenance.txt) | 0 | `ac881addc4e83281090bcb5600ace7c7dd755c2d9a85227b41ae21c482bd5fe2` |
| [scope-browser-r2](docs/reviews/evidence/p4-independent-2026-10-13/scope-browser-r2.txt) | 1 | `cabd2d58f6ed31d0b76eac353ec90dffb6531496f38ddc1a037d2b348e5e7ae2` |
| [scope-browser](docs/reviews/evidence/p4-independent-2026-10-13/scope-browser.txt) | 1 | `3b1d66ad94ad78e74a23044496346cfa9d2ea3580e8fb23289c3f4cfc5c167aa` |
| [worker-identity](docs/reviews/evidence/p4-independent-2026-10-13/worker-identity.txt) | 0 | `778cdec82590f957ea45b2e50caf4448f7728062031de549b7a1a46d7c059b99` |

Independent clean rebuild with the shipped `/assets/lotus_fin/core/` base also passed: its JavaScript and CSS hashes are byte-identical to the serving image. See [CLEAN_SERVING_ASSET_COMPARISON.json](docs/reviews/evidence/p4-independent-2026-10-13/CLEAN_SERVING_ASSET_COMPARISON.json); child exit 0.

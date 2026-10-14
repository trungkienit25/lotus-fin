# P4_SECURITY_CHANGES_REQUIRED

13 October 2026 · Asia/Saigon · Independent targeted P4 acceptance.

Branch `codex/p2a-invoice-read-backend`; HEAD `5f805ef34f788245a3ec0e9c2f44e224eb16c305`. Reviewed current dirty/untracked working-tree bytes, not HEAD. No production source edit, stage, commit, push or merge. Only owned isolated project `lotus-core-p4c-01a13415-r5`, site `core-p4c-01a13415-r5.localhost`, loopback `127.0.0.1:8101` was tested and restarted; volumes retained. N0 remains **BLOCKED**.

**Do not commit or push this candidate.** P4 resolves the original profile transport crossover, disabled-user admission and canonical route/CSRF failures, but required actor/session scope clearing remains broken. N0 is not the sole development-branch blocker.

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

## Candidate identity

The complete selected source manifest has **560 files**, SHA-256 `b3c687067382a5e84bad8d43f6f1f22cd73ebc0691d919fa2b8fd17b8fafafab`: [SOURCE_MANIFEST_COMPLETE.json](docs/reviews/evidence/p4-independent-2026-10-13/SOURCE_MANIFEST_COMPLETE.json). The initial 559-file snapshot omitted a tracked AI002 synthetic fixture; the corrected manifest includes it. The 517-file P4-C image-input manifest has SHA-256 `2600017e48b01eee74b788f2ebbbbb39689baf1a0d2a49851603b92b42244c8e` and **zero current-source drift**. These manifests have different scopes, not conflicting source identities.

Image `sha256:f7eda114867f2ea8803a5dafbef8e9927eeed0cb070b32766723cb1ea92325b3` is used by all seven app containers, including the one-shot init; 334 packaged backend files match frozen bytes. Four actual backend/queue/scheduler containers have identical module hashes, Linux platform, and no source bind mounts: [SERVING_WORKER_MODULE_HASHES.json](docs/reviews/evidence/p4-independent-2026-10-13/SERVING_WORKER_MODULE_HASHES.json). This is disk/module and process provenance, not a Python memory dump. The serving assets/private entry are bound in [RUNTIME_PROVENANCE.json](docs/reviews/evidence/p4-independent-2026-10-13/RUNTIME_PROVENANCE.json):

- JavaScript `assets/index-CeY-kyfF.js`: `52fc47074a33fac873fa56c1b976b6151cbcf12030fedb4cb6fe239a3e0f88ad`.
- CSS `assets/index-j6L4zPa6.css`: `0126d0bd8d95741b35163e1b8a5a4394e2245908b5ddffa445a507663da91f41`.
- Private HTML: `e2e42734b757dee2e703da94b495fa7d2aa1bfbc02f86a75d5a300b4acc2490b`.

Locks and executed test-source/oracle hashes are in [SOURCE_MANIFEST_COMPLETE.json](docs/reviews/evidence/p4-independent-2026-10-13/SOURCE_MANIFEST_COMPLETE.json) and [TEST_ORACLE_HASHES.json](docs/reviews/evidence/p4-independent-2026-10-13/TEST_ORACLE_HASHES.json). The existing r5 build already contains these exact P4 source bytes; independent pre/post-restart provenance confirms it is not the P3 UI. This review did not manufacture a new image or assert a fresh from-scratch Frappe build.

## Fresh verification

| Fresh check | Observed result | Child exit |
| --- | --- | --- |
| P1/P2-A invoice/security backend | 438 passed | 0 |
| AI001–003/numerical regression | 393 passed, 7 subtests passed | 0 |
| Frappe-only boundary units | 21 passed | 0 |
| P4-B principal/revocation + SPA renderer units | 33 passed (24 + 9) | 0 |
| Frontend Node suites | 114 passed, zero skips | 0 |
| Original DEMO forgery oracle | 4 passed | 0 |
| Retained independent UI/decoder/controller oracles | 23, 96, 41 passed; P3 typed sample input retained | 0 each |
| Independent L3 oracle | 16 passed | 0 |
| Clean snapshot browser fixtures | 10 passed; intercepted synthetic HTTP fixtures | 0 |
| Canonical actual browser/HTTP | 19 checks before and 19 after cold restart | 0 each |
| Real disabled/revoked/generic HTTP | 39 observations, all expected statuses, no tracebacks | 0 |
| Real page/drawer mounted transitions and layout smoke | 86 checks passed; 60 directed scenario transitions | 0 |
| Adversarial mounted session/mobile check | 5 PASS, 4 FAIL | 1 |
| Two ordinary actors, page and drawer | 6 FAIL observations; same scope defect | 1 |
| Clean frontend install / full TypeScript + Vite / oxlint | Pass; oxlint 91 warnings, no errors | 0 each |
| npm audit / production-only audit | 8 high + 2 moderate / 3 high affected package entries | 1 each |
| Runtime Python advisory metadata | 134 PyPI version lookups; six packages have records; framework/local app not PyPI-qualified | 0 collector, not clean gate |
| Broad host pytest collection | 901 collected, four collection errors | 2 |
| Clean Python install / pip check / invoice regression | Pass / no broken requirements / 438 passed | 0 each |
| Clean numerical regression, corrected snapshot | 393 passed, 7 subtests passed | 0 |
| Git whitespace | Existing trailing whitespace/EOF findings | 2 |
| GitNexus refresh | Timed out at 480 seconds in separate index location | 124 |
| GitNexus current change analysis | CRITICAL; 28 files, 99 symbols, 16 flows; display truncated | 0 CLI, not acceptance PASS |

Counts overlap across suites; do not sum them as unique tests. No assertion was weakened, skipped or rewritten to turn a failure into PASS.

## Unresolved findings and narrow corrections

**P4-F01 · P1 acceptance blocker — mounted actor/session scope is not bound.** Profile changes are fixed, but the actual page and drawer omit `contextKey`; their invoice scope defaults to company/default/profile/scenario. External logout switches the authoritative server to Guest (bootstrap 401), yet three synthetic rows and one open document remain. Logging in as a second ordinary QA user without remount leaves them intact; an old selection opens DEMO-SINV-2026-001. See ACTOR_SCOPE_BROWSER.json, SESSION_SCOPE_BROWSER.json and page/drawer actor screenshots. This is synthetic presentation/provider leakage, **not demonstrated native financial disclosure or backend authentication bypass**. The requested actor/session clearing acceptance still fails. Bind both mounts and the DEMO provider lifetime to a current authenticated actor/session epoch, clear immediately on auth invalidation/visibility/session change, fence old results, and replay both surfaces without reload.

**P4-F02 · P2 — mobile scenario selector still clips.** At 390px, x=93.984375 and width=332, ending at 425.984375: about 36px outside the viewport. The sidebar, mode tabs and main input are improved; that does not qualify the whole form. Make the profile/scenario row fit and inspect 390px page/drawer control bounds plus keyboard focus. The accessible-name/Enter smoke is not WCAG certification; the builder's broad compliance wording is unsupported.

**P4-F03 · P2 — dependency review is not clean.** Fresh npm audit reports eight high/two moderate affected entries, including production path-to-regexp through @ant-design/pro-layout → @refinedev/antd. Production-only audit retains three high entries. Runtime PyPI metadata flags oauthlib, pdfkit, PyJWT, pypdf, weasyprint and Werkzeug versions. Deduplicate aliases and assess enabled framework/print/OAuth/JWT reachability before minimally updating locks; no blanket major audit fix or exploitation claim.

**P4-F04 · P2 — reproducible source/check gates remain incomplete.** Broad pytest still imports nonexistent BaselineSourceError; three other collection errors require the Frappe test environment. No documented enforced suite boundary resolves that mismatch. README still says invoice/L3 have separate synthetic test mounts; some older transport docs name wrong methods. P4-B lists a nonexistent demo_preview endpoint and 403 CSRF examples while the real server returns framework 400 CSRFTokenError. CI build-and-test is an echo placeholder and SAST continues on error; push triggers omit codex/* branches. Whitespace check fails; ESLint/config are absent (the actual lint gate is oxlint). No P4-D report was found. Correct these concrete gates without hiding security assertions.

**P4-F05 · P2 — graph/commit risk unresolved.** The stale 2026-10-12 index cannot resolve the current boundary; concept queries return empty with FTS disabled. HIGH chat-panel impact has three direct callers (page, drawer and fixture), seven impacted symbols and App/UniversalPageView processes. The aggregate tracked change report is CRITICAL and truncates 99 symbols/16 flows even with limit 500; it omits new/untracked source coverage. Separate-index refresh timed out after 480 seconds. UNKNOWN/empty is not low risk, and LOW shared axes do not waive HIGH. Obtain a current, complete, non-truncated graph review before a commit.

**P4-F06 · P2/P3 product debt — ERP-derived promises remain.** CORE mounts still make a best-effort /api/resource/Company request, although Company schema is absent and no result is used as financial authority. Legacy AI002 GL/Invoice and AI003 Purchase Invoice sources remain. Numerical fixture PASS and a disabled ERP-free HTTP shell do not qualify native finance, full product independence or G10.

## Evidence and execution limits

All executed acceptance command argv/cwd, child exits and output hashes are in [COMMANDS_AND_EXITS.json](docs/reviews/evidence/p4-independent-2026-10-13/COMMANDS_AND_EXITS.json). Inputs are hash-bound in [INPUT_REPORT_HASHES.json](docs/reviews/evidence/p4-independent-2026-10-13/INPUT_REPORT_HASHES.json). P4-A/B/C reports were read as claims, not inherited PASS. P4-D is absent. No new financial records/schema, synthetic production data, approval signature or production release was created. The original QA account was restored enabled and the temporary ordinary actor removed. Prior P3 evidence was preserved.

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

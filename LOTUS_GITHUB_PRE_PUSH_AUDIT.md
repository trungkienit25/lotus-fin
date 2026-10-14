# Lotus GitHub pre-push audit

13 October 2026 · Asia/Saigon · Independent acceptance of `E:/lotus-fin`.

Branch `codex/p2a-invoice-read-backend`; HEAD `5f805ef34f788245a3ec0e9c2f44e224eb16c305`. The candidate is current dirty/untracked working-tree bytes, not HEAD. No production source edit, stage, commit, push, merge or deployment was performed. Tests used only local fixtures and the previously qualified isolated `lotus-core-01a13314` / `core-01a13314.localhost` / loopback 8097. N0 remains BLOCKED.

Evidence directory: [p3-independent-2026-10-13](docs/reviews/evidence/p3-independent-2026-10-13). Exact candidate: [CANDIDATE_SOURCE.json](docs/reviews/evidence/p3-independent-2026-10-13/CANDIDATE_SOURCE.json), 616 files, SHA256 `02da08611f41de6e9ceff876e95bf48e11150cf9cdbe8e06819f816ae3cb8c70`. Every executed test command, inner-command exit code and output hash is in [COMMANDS_AND_EXITS.json](docs/reviews/evidence/p3-independent-2026-10-13/COMMANDS_AND_EXITS.json). Collector shells may exit 0 after recording a failed child; use the recorded child exit. Failed attempts are retained.

**PRE_PUSH_SOURCE_READY: NO — CHANGES_REQUIRED. CLEAN_CLONE_REPRODUCIBILITY_NOT_YET_VERIFIED. SECURITY_PRE_PUSH: FAIL. GITHUB_PUSH_READINESS: CHANGES_REQUIRED.**

Initial full inventory contains 18,037 Git-visible paths: 17,334 untracked, 23 tracked dirty paths, one historical gitlink and the intentional deleted core fixture. The source-only candidate selects 616 files; raw all-files inventory includes evidence copies, skills and archives and is not a staging recommendation. The index is empty of staged changes. Git-visible output lists 28 untracked archive/video/cache artifacts for exclusion, including a 102,993,920-byte HEAD_SOURCE.tar about 98.2 MiB and unsuitable for this source commit. A previously tracked Python 3.10 .pyc exists in HEAD; plan a separate deliberate cache removal, never stage a replacement. Do not use git add -A.

The exact proposed changed-source list has 140 paths and SHA256 for every present file; deleted fixture has null SHA plus optional counterpart evidence. All active source, typed DTOs, config loader, runtime boundary, React panels, DEMO provider, tests, support recipe and lockfiles exist locally. Old HEAD alone misses those inputs. Five archived frontend/harness bytes differ from current, while all 346 current backend/support files match the serving image. Clean npm ci/typecheck/Vite succeeds from a separate copied source tree; this is not a staged/committed clean Git checkout or a newly built current-source Docker artifact. No immutable final release candidate is certified.

Root .gitignore excludes .env/.runtime and Python caches; frontend excludes node_modules/dist. Nested candidate snapshots and my-skills are not globally excluded and create accidental staging risk. All private credentials/volumes and .gitnexus remain out of the plan. No discovered live credential was copied into evidence; 22 primary-source regex findings were inspected as public UI labels and explicit offline synthetic keys. This limited scan does not certify historical snapshots, binary archives or unknown secret formats. The 140-path plan is review-only; old docker/judge and legacy compose additions must be placed in a separately disclosed historical/optional boundary or omitted after dependency review, not made default.

Valid npm lock v3 reproduces the frontend install. pyproject has bounded numerical/Pydantic dependencies compatible with core requirements.lock, and framework.lock pins resolved dependencies; legacy lotus_fin/requirements.txt still has much wider minimums and should not be used as the qualified core install instruction. README names core/N0 limits but predates P3 mounts and lacks truthful current DEMO serving instructions. Builder endpoint/source/CID examples are inconsistent with actual source and require correction. CI build-and-test is a placeholder and SAST uses continue-on-error: current GitHub checks cannot enforce these local gates. No unrelated tracked deletion was observed; Company fixture transfer is intentional and semantically intact.

| Gate | Verdict | Evidence / limit |
|---|---|---|
| `P3_FUNCTIONAL_ACCEPTANCE` | **FAIL** | Qualified /copilot returns 404; real mount lacks CSRF initialization; CORE/DEMO controller crossover; mobile clipping. |
| `CORE_AUTHENTICATED_HTTP` | **FAIL** | Ordinary real POST/CSRF/503/CID/no-store work; disabled existing users still admitted. Current React-to-CORE journey fails. |
| `P2B_SECURITY_REGRESSION` | **FAIL** | Retained Node/React decoder/controller tests pass; mounted profile changes violate source fencing. |
| `L3_ACCEPTANCE` | **PASS** | Local fact-free lifecycle: 20 unit cases, 16 independent checks, 11 React checks, fixture E2E and actual app edit/review/copy/discard. No native finance claim. |
| `DEMO_E2E` | **CHANGES_REQUIRED** | Actual app Search→Select→Open works only after explicit tab remount; scenarios retain stale transport without remount. |
| `DEMO_ISOLATION` | **FAIL** | Synthetic records appear under CORE banner; forged references and cross-provider scope accepted. |
| `CORE_ERP_INDEPENDENCE` | **PASS** | Actual isolated startup: only frappe, lotus_fin; ERPNext module and Company/Sales Invoice schemas absent. All 346 backend/support hashes match. |
| `FULL_PRODUCT_INDEPENDENCE` | **FAIL** | Legacy financial providers and exposed route/catalog families still require ERP schemas or lack qualified native replacements. |
| `FULL_FRONTEND_LINT_BUILD` | **CHANGES_REQUIRED** | Clean npm ci and full TS/Vite build pass; oxlint passes; requested ESLint package/config absent. |
| `SOURCE_REPRODUCIBILITY` | **CHANGES_REQUIRED** | Selected source available/hash-bound and clean frontend build reproduced; no staged/committed clean clone and image UI differs from current P3 source. |
| `SECURITY_PRE_PUSH` | **FAIL** | P1 source-profile crossover and disabled-user admission remain; generic RPC error disclosure and dependency review outstanding. |
| `GITHUB_PUSH_READINESS` | **CHANGES_REQUIRED** | Do not push this candidate until security, serving/UI and source/evidence corrections pass. |
| `G10_JUDGE_READINESS` | **BLOCKED** | N0 authority unavailable; independent P3/security gates also fail. Not blocked solely by N0. |

| Command receipt | Exit | Output SHA256 |
|---|---|---|
| `backend-focused` | 0 | `8253f0d0ca80a753276a175f68dd6b065d7c251963a73949e872dd4b1f1dfbfd` |
| `backend` | 2 | `6407b1a919e1f8a75d8dc3c68ad7755a123161e77065e17577b412f02f8ab5f6` |
| `boundary` | 0 | `c89198195c6863f58363fe47a2a31f8662aa7c95dd417607dcace5c021debf0b` |
| `browser-fixtures` | 0 | `e904d216938c039369fecb01e4667fe322b0a3d8d6a59db6725cce2c36e28c8c` |
| `build-unsandboxed` | 0 | `dcc7c5026ba61032a71a3cffd1efaf9b986ea83d07b18d0283c716630e3802e1` |
| `build` | 1 | `e113152a0b9ce56e602090927a176809656248211209c4a86b1e9755fa33eccb` |
| `clean-build` | 0 | `d23fa0f3c6a170a60467d055c8e2fa8f05854e6451f31aac055e2e3d95c367b8` |
| `clean-lint` | 0 | `103131a9acfb2a584bf756fa8fa37e5a7118ef4cef2b51918758c0fdf1d4fa2b` |
| `clean-npm-ci` | 0 | `1c00fc8b2e2b913fe19ee153fa9cb5652464492ef094c56b346a0f8cd5047325` |
| `core-cleanup` | 0 | `1b0e4d5be10b33b12b81b3fe27d8019371cc1dd82cf9f46287f567435448cca6` |
| `core-extended-final` | 0 | `b20411b2764240cb65ae2fd0e4127918d480a7a2e5549f5fbf220031fa4d9d84` |
| `core-extended-generic` | 0 | `322e59e62082c172551c63f8a65ab850023530ec8d07812146730569d5e8a9eb` |
| `core-extended-r2` | 1 | `12e92b95f9f8ee319f4ff0be4c4970d496b8f5411933787b517e6ec20e81d22e` |
| `core-extended-r3` | 0 | `37f4ad796c41804acda4602ef625a38ff2a16cd6dc791a30e7445edffbb91bb2` |
| `core-extended-r4` | 0 | `98fefc08b616491830c35ffe294a203ad7f6729c49e94c4f56afff30c0f560c4` |
| `core-extended` | 1 | `dde163e6e0c5ab891d754aaf829c5e15e494d5f34949cf36ab50c329e94d759a` |
| `core-http` | 0 | `14f63012a460154a1ddb673055a9bd4a4e6d8f077fcae5912041ac2f0b2ba2c7` |
| `core-runtime-versions` | 0 | `9b18b8dcf2548cf7730dfe23de8d8d77af54bfe94112ae58a2c1519d2284ad0a` |
| `core-smoke` | 0 | `e584b4fbd168c6b489abfe51364da41c93c97562db2e31b4d0868caa907eee23` |
| `core-start` | 0 | `c2c2fb0dc5b9e33eeede72e05f34e3c186ba87bdd5727eb47f045ec9b11a1c95` |
| `core-status` | 0 | `327fa95b12d2dc055381f7958cd41d95b7f90644284919b6e8f04ee09d5cca07` |
| `demo-negative-r2` | 1 | `2deb98eab3e27bd23dc02db72a61b71db3cc47075ad7b5565e772277b3bd20ba` |
| `demo-negative` | 1 | `0820517aec9e306f0b2aa38a4afca98b79f09febce763473e7bd3fe314c4acfe` |
| `diff-check` | 2 | `3c34b80efd7bb5a071be2c8fbd8df89a4f92d7af7bb4d75aa078905ae024f32c` |
| `eslint-requested` | 1 | `bb6e9952eb971f28c484484f1d0f15949324df39c5845283a4b33a07e094f2d9` |
| `features-current` | 0 | `5f00a76b5e35a7833271b1d9c67dd0641a746550a6aaa89c683f1610b9250670` |
| `frontend-unit` | 0 | `6387427b21691e25ddf7395135927bd07d816dd3b206b2bc4b468d537ae546c5` |
| `graph-context` | 0 | `039ed94dd6c205adc494ecef0a35ee0261fdbe6f40684b5778d0ba1e9f4dc4ef` |
| `graph-full` | 0 | `d8fc89038f61b23d4d5aaa9b57919b38006426d2b5850074f91844a32dd9af03` |
| `graph-impact` | 0 | `4d4a5a2409d3ff85b9a04ae5e1138f7ba2a9ad4e8eff1b3c706e7b3144959992` |
| `graph-refresh` | 1 | `b3557832535192f7d8afc004f902ebfd3e174d2eca9f34819c789c5a57c8283e` |
| `graph-status` | 0 | `29edcb97d7b31b2f17b36469de88da2d44658cf9e50cd7b73d256ca726f5f00c` |
| `graph` | 0 | `d8fc89038f61b23d4d5aaa9b57919b38006426d2b5850074f91844a32dd9af03` |
| `image-source-final` | 0 | `43ca11a1e0c54252133c9671a1ad99206f1b9c39b47b986cdb9156e5bc6699c0` |
| `image-source` | 0 | `81061ffa4ddc923a7636e49d743478db6c0ee7283cc8ca8bf9ec25add89fc845` |
| `independent-backend` | 0 | `8a4ca286697d0f1c4b564b393ba778fb49775f5ea3b7de82e3e8e28f9e755b1b` |
| `independent-l3-react` | 0 | `507463f23f15b39d198522316eb785cc61a706fd0dc500fd64ff75eea4224c31` |
| `independent-l3` | 0 | `575cbb7cb14a1788de45eb1f7fd528692f258f8fc28447cb49b192ad24378973` |
| `independent-new` | 0 | `22468a01e48c2d47c795616d8338187d5fdaa25995ed66d12fd9d898e337f5a6` |
| `independent-p2b` | 0 | `6039d11cf7ba504dce4f49a423c451e34b3d7860f51317c86820c68a663ec90a` |
| `independent-react` | 0 | `cf6a254a27c83369f604c24e761d42291cf5d2e02ffe2db13768e463eeaab8c8` |
| `independent-ui23-r2` | 0 | `93852dbe5ca095cd7b9893a606ad36a099ebebb21a55c7cc41882c5592ffc8dc` |
| `independent-ui23` | 1 | `b643710e18ab0094d4a17e384442bf97252e28ff8f3b9f6d3b1da86ce6068f77` |
| `independent-wire` | 0 | `9804491428843402c2246ad3b4863f1f9c81f04b848aad63696fa89220f90981` |
| `lint` | 0 | `483d19ad0338c79659bbe9292ace60eae8b7ea228be26f9be355ab589b7b0057` |
| `npm-audit` | 1 | `d4bb8302f8c3c73095c7f30bbf2e77c789c234a147939c9a890f1b391947fc49` |
| `typecheck` | 1 | `7299b20634141b20c8739b674f5905ac6963a5ecee4e9f187183bbbef3c17950` |

The exact argv/cwd, logs and test counts are available in COMMANDS_AND_EXITS.json and named .txt files. Retained harnesses read current source; only their evidence output directory was relocated. Review narrower adversarial failures and the actual app screenshot before accepting builder PASS reports.

## Graph review and authority

Bound repo/index: `lotus-fin`, `E:/lotus-fin`, indexed 2026-10-12T07:02:27.060Z at the same Git HEAD; working-tree/untracked coverage is incomplete. Concept query returned no definitions with FTS disabled. Explicit UID impact on the actual VercelChatPanel returned **HIGH**, 7 impacted symbols, 3 direct callers (LotusCopilotDrawer, LotusCopilotPage and fixture composition), App/UniversalPageView processes and 4 modules. HIGH is not waived by its LOW shared-axis score. New enforce_request_boundary is absent from the index; text inspection follows that unresolved graph result.

`detect-changes --scope all` reports 23 tracked files, 78 symbols, 12 processes, HIGH risk. Rerun with `--limit 500` still prints only 15 symbols/10 flows. This is not a clean graph gate and cannot cover the 140 unstaged/untracked candidate additions/changes or all unindexed source. No commit was attempted. Refresh the actual source index and obtain complete, non-partial/non-truncated change analysis before a future commit; do not quote the builder's “2 files / no breaking changes” as acceptance.

Final CLI status explicitly reports stale. The mandated `analyze --index-only` refresh was attempted and exited 1 after 375.80 seconds: native parse worker startup failed (5000ms readiness limit; bounded self-heal exhausted). No fresh graph acceptance is claimed. Existing risk receipts and source confirmation remain evidence with this coverage limitation. Global tool reinstall or production source changes were not performed to conceal the failure.

Authorities inspected: AGENTS.md, ADR001, Security Code V3, frozen P1/P2-B references, all seven required platform/runtime/N0/inventory reports and all seven current P3 builder reports. Latest user architecture supersedes legacy ERP assumptions and old transport descriptions. All remaining native source/policy approvals stay BLOCKED. Reports are evidence claims, not source authority or human N0 approval.

# LOTUS FIN — P2-A F01–F03 Correction

12/10/2026 · Asia/Saigon · **P2A_CORRECTION_LOCAL_PASS**.

Đây là builder/direct-fix/self-verification, **không phải independent PASS**. Đã sửa source và freeze [P2-B wire contract](CHATBOT_P2B_WIRE_CONTRACT.md). Live ERP/HTTP integration vẫn **BLOCKED / NOT_RUN**, G10 vẫn BLOCKED độc lập. Không enable actions, deploy, commit hoặc dispatch UI.

## 1. Authority, baseline và containment

Đã đọc P2-A Independent Recheck, Final Work→Chat, Implementation Handoff, Test Oracle, Backend Integration Report, Security Test Evidence, P1 MASTER và Final Independent Recheck; AGENTS, ADR001, Security Code V3. Áp dụng `my-skills/backend-security-coder/SKILL.md`, `my-skills/systematic-debugging/SKILL.md` và GitNexus debugging/impact skills của repository.

Actual branch `develop`, HEAD **`5f805ef34f788245a3ec0e9c2f44e224eb16c305`**, đã checkpoint thêm so với historical independent HEAD07f7251. Backend hiện tracked. Không dùng HEAD thay source artifact; baseline SHA256 khóa4116 file fingerprints. Staged rỗng và nguyên sau task.

Evidence mới riêng: `docs/reviews/evidence/chatbot-p2a-f01-f03-correction-2026-10-12/`. Không overwrite báo cáo/runner/results độc lập cũ. [SOURCE_BEFORE](../evidence/chatbot-p2a-f01-f03-correction-2026-10-12/SOURCE_BEFORE.json), [source patch](../evidence/chatbot-p2a-f01-f03-correction-2026-10-12/SOURCE_PATCH.diff), before/after text snapshots và [final audit](../evidence/chatbot-p2a-f01-f03-correction-2026-10-12/SOURCE_AFTER_AND_SELF_AUDIT.json) định danh byte thực tế.

Baseline oracle chạy lại trên actual source: **84 cases =72 PASS/12 FAIL/0 ERROR**, exit1, đúng12 assertions historical. Python3.13.7 (`C:/Python313/python.exe`), pytest9.0.2, Pydantic2.12.5; no package install. Guards trước application imports chặn socket connect/connect_ex/bind/DNS và real Frappe/ERP/provider/LLM/legacy imports. No conftest/plugin autoload/cache/bytecode. Private synthetic Company seam/read port/logger streams; no real business data/credentials/session.

## 2. Direct fixes theo F01 → F02 → F03

|Finding|Exact RED|Root correction|GREEN|
|---|---|---|---|
|F01|C05 versions khác capability; C06 context_ref fail với fresh search; C08 selection fail fresh open và port0|Authorizer fingerprint dùng canonical read-family scope, bỏ capability khỏi identity; bind actor/session/trusted site/product/company/connection/config/policy/key/contract/projection. Capability allowlist và exact Company/read/current actor vẫn kiểm mỗi resolve. Không bỏ token/version verification hoặc ép context_version bằng model_copy.|C05/C06/C08 PASS; fresh resolver→search signed selection→fresh open đạt DOCUMENT_READY/port1. New replay/scope/capability tests18PASS.|
|F02|C02 thiếu date defaults; C03 body expiry≈5s trong khi token≈300s; new14 calendar/expiry/timezone assertions RED|Timezone lấy từ current site System Settings `time_zone`, validate IANA/fail safely. Controller dùng common filters90-day inclusive normalization sau timezone conversion. ContextDataDTO strict đủ7fields; expiry lấy từ actual claim của token đã verify, không từ deadline/config estimate. Codec P1 v1 nguyên byte.|C02/C03 PASS;14 new assertions PASS: UTC→local day/month/year/leap boundary, timezone phía tây, TTL60/300/600 khác deadline, shorter effective codec expiry, missing/invalid timezone, timezone change revokes old context.|
|F03|Six missing/null schema negatives và explicit-null application query tới port1/OK; new10 failing assertions|Required nonnullable filters; page_size strict integer default20 only when omitted. Date before-validator reject explicit None. Filters/service revalidate với `exclude_unset=True` để omitted default nội bộ không bị biến thành supplied null. Không sửa future/range/NFC/extra-field rules.|Seven historical assertions PASS; invalid decode và unvalidated explicit-null model đều INVALID_REQUEST/null/port0; valid empty/supplied dates/page_size pass.35new tests PASS.|

Policy fingerprint bao gồm current configuration (secret chỉ đưa dạng digest vào internal fingerprint), sorted capability allowlist, contract/projection constants và site timezone. Mọi real scope/config thay đổi làm refs cũ fail; current authorization không dựa fingerprint như permission snapshot. Existing exact Company permission call vẫn `has_permission('Company', ptype='read', doc=candidate_company, user=current_actor)`, chỉ `True` mới grant. B03 denied/outage precedence giữ nguyên vì timezone check đặt sau Company gate.

Resolver và Open usecase không cần sửa: source hashes nguyên. Fresh document/field reauthorization được kiểm bằng private port protocol; chưa có concrete ERP adapter/live permission qualification. Signed token không thành permission grant. Wrong actor/session/site/company/product/connection/policy/key/capability, tamper, replay sau revoke và denial thắng stale/source vẫn được kiểm.

## 3. Exact source/test delta và SHA256

Paths dưới `lotus_fin/lotus_fin/`. **5 production modules edited,5 existing fixtures augmented,3 permanent regression modules new**; không sửa modules khác trong allowed7.

|File|SHA256 hiện tại|Lines|
|---|---|---:|
|`infrastructure/security/frappe_invoice_authorizer.py`|`0f6af5e31a20b8d49a8084e02e9dbcf65b6c0d4b8019e1e9730f8efb10d79a7b`|194|
|`presentation/controller/invoice_actions_controller.py`|`ab218965c93a31dfa467a85350768425ad6e9f4a3e4194be272a9c0e27c808d3`|135|
|`presentation/dto/invoice_action_request.py`|`c0cbecd5eb5a03e419a363e83d051f253f6cb0b9e94b2a820030289ad9a055dd`|83|
|`domain/schema/invoice_read.py`|`a6cdc9d25e9a9e8f41459764bfa956cc9661e1eb04cbc28f3cf53d6e5a8aca3e`|154|
|`application/service/search_invoices.py`|`3d51430d3c0769178e9e3f141ae79a6517e1122b8a635520798cac4a617817ef`|89|
|`tests/test_action_reference_privacy.py`|`a107119ca0f95ca9d52af4e27fc1ffec4bd27fc9617b8ccf56d04b25e6197f4e`|113|
|`tests/test_invoice_auth_delivery.py`|`cf796508ce6cd5aa30baa4b269a8bfabf7dcf801a6ba84ba2947d120152876be`|116|
|`tests/test_invoice_context.py`|`bd06caa647c4bcea49f679a866a91fadc306894547ea8b3a1f9ca534f2d3ba22`|197|
|`tests/test_invoice_permission_seam.py`|`acfd2d4f013183d1dc180ba50f7f7914bf4a64b695b34749eb317d5cadfd37ab`|74|
|`tests/test_invoice_terminal_delivery.py`|`56bb7ecac9d745947bb706a6a41b15a84687b1cd9e1d991841860cbeaf811a52`|145|
|NEW `tests/test_invoice_read_family_correction.py`|`efabedf0ca53ce2b87fb1700122e3c731e49fb7987f38031dd3bc3ac0ee29ed9`|138|
|NEW `tests/test_invoice_context_data_correction.py`|`e3106269c3d240fa769d6a86cfb23d379dfbe2844f22946311b57a83ec0ce38d`|115|
|NEW `tests/test_invoice_request_correction.py`|`d3826d9fe17ddb2046fdd949ca98c62e8e579b66784de1415ff810a4df662dae`|113|

Existing five test files chỉ bổ sung explicit synthetic site timezone vào affirmative fixture; **mọi `assert` và `pytest.raises` AST nguyên**. Không đổi kỳ vọng để khớp lỗi. ContextDataDTO đặt trong existing invoice action DTO module để giữ exact production allowlist; không tạo module/package mới.

Protected source SHA256 nguyên: P1 v1 codec `a9d8ec5bd15838d9034dca1bf7296bf9ae2cac1c52a7df461b35eb3995cc394a`; P2 v2 codec `a951b667f5f5d53d960461bee58c393691fb04d72002d4123272254539d0ec16`; A16 sink `990ee5243e2f50264b5664d2360e60fa0eb422547bd93412f7f1ee3ee045b198`; API `90ea0be717f55100d53f71fc308c166f4b0955c932bc57d68342b76dfdc1f23f`; config `ae56b57f9123fa449a7c07da1a96ceca04a961f7c659404d5f6c61fe4a32ac91`. Resolver/Open hashes và Panel/Drawer hashes trong final audit.

Compile13changed/new Python files PASS, tất cả<200lines, max197. Domain/application không thêm Frappe/infrastructure coupling; required audit implementation nguyên. Không business mutation, SDK/executor, React/Docker/dependency/ERP-permission edits của batch.

## 4. Execution commands, exits và incremental gates

Full commands/pytest args/exits: [COMMANDS_AND_RESULTS](../evidence/chatbot-p2a-f01-f03-correction-2026-10-12/COMMANDS_AND_RESULTS.json). Mỗi phase lưu stdin reproduction, full stdout, case ledger và actual imported module path/hash. Từ `E:/lotus-fin`:

```powershell
$env:PYTHONUTF8='1'
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
Get-Content -Raw docs/reviews/evidence/chatbot-p2a-f01-f03-correction-2026-10-12/FINAL/FOCUSED_REPRODUCTION.txt | C:/Python313/python.exe -B -
Get-Content -Raw docs/reviews/evidence/chatbot-p2a-f01-f03-correction-2026-10-12/FINAL_ORACLE/NEGATIVE_REPRODUCTION.txt | C:/Python313/python.exe -B -
Get-Content -Raw docs/reviews/evidence/chatbot-p2a-f01-f03-correction-2026-10-12/A16_CURRENT/REPRODUCTION.txt | C:/Python313/python.exe -B -
Get-Content -Raw docs/reviews/evidence/chatbot-p2a-f01-f03-correction-2026-10-12/B03_CURRENT/REPRODUCTION.txt | C:/Python313/python.exe -B -
```

Focused uses `pytest.main(['-p','no:cacheprovider','--noconftest','-v', ...22 explicit module paths...])`;12 P1 +7 existing P2 +3 regression modules. No test discovery outside scope.

|Phase|PASS|FAIL|Exit|Observation|
|---|---:|---:|---:|---|
|BASELINE independent oracle replay|72|12|1|Exact current defects,0ERROR|
|F01_RED accumulated focused|292|2|1|Fresh pipeline/replay assertions RED|
|F01_GREEN accumulated focused|294|0|0|Original276+18F01|
|F01_GREEN oracle|75|9|1|3F01 closed; F02/F03 remain|
|F02_RED accumulated focused|294|14|1|Calendar/expiry/missing timezone RED|
|F02_GREEN first focused|307|1|1|One old affirmative fixture omitted timezone; raw result retained|
|F02_GREEN oracle|77|7|1|2F02 closed; F03 remain|
|F02_GREEN2 accumulated focused|308|0|0|Last fixture gets site timezone; assertions unchanged|
|F03_RED accumulated focused|333|10|1|Known schema/date null still RED|
|FINAL focused|343|0|0|**173P1+103existingP2+67new(18+14+35)**;0SKIP|
|FINAL original-bookkeeping oracle adaptation|84|0|1|All assertions GREEN; blocked optional Frappe import still counted as failure by old exit logic|
|FINAL_ORACLE corrected containment bookkeeping|84|0|0|Same assertions/case IDs;0ERROR/0network|
|A16_CURRENT fresh dedicated|14|0|0|Required sink/ack/outage/concurrency/callback preservation|
|B03_CURRENT fresh dedicated|8|0|0|Exact Company/actor denied/outage/Guest/SID/interface controls|

Counts có overlap, **không cộng343+84+14+8 thành unique coverage**. Không lặp regression sau GREEN khi source không đổi; subsequent work chỉ evidence/docs/graph.

Oracle runner chỉ thay: output root mới; thêm approved synthetic timezone; bắt ValidationError quanh null-date DTO construction để assertion hiện có vẫn kiểm INVALID_REQUEST/port0 khi DTO reject sớm; exit bookkeeping chấp nhận duy nhất **blocked** `import:frappe` từ package initialization, vẫn fail mọi unexpected import/network và FAIL/ERROR. [Exact adaptation diff](../evidence/chatbot-p2a-f01-f03-correction-2026-10-12/ORACLE_RUNNER_ADAPTATION.diff). Original historical runner/results nguyên; original-bookkeeping exit1 được giữ ở FINAL, không báo thành exit0.

Final [oracle ledger](../evidence/chatbot-p2a-f01-f03-correction-2026-10-12/FINAL_ORACLE/NEGATIVE_RESULTS.json) đối chiếu đúng84IDs; [final audit](../evidence/chatbot-p2a-f01-f03-correction-2026-10-12/SOURCE_AFTER_AND_SELF_AUDIT.json) ghi riêng12FAIL→PASS và toàn bộ72previous positive vẫn PASS. F03 permanent test thêm model_construct(null) revalidation/port0 để không chỉ dựa harness catch.

## 5. Impact graph và integrity

Repo bound `lotus-fin / E:/lotus-fin`. Cached GitNexus1.6.12, không install. Pre-edit exact authorizer/method/controller impacts UNKNOWN; Context/SearchRequestDTO và Search service LOW. UNKNOWN đã được xác nhận bằng bounded source search: resolver gọi authorizer qua IReadAuthorizerPort; controller dùng resolver; affirmative permission/privacy/terminal tests là private composition. Zero graph processes không chứng minh unused.

Initial index refresh gặp FTS InvalidUTF8 và registry write EPERM; transient impact filters trả **CRITICAL** cùng garbled IDs/unrelated historical/skills relations. Đã cảnh báo trước F03, giữ raw artifact; không dùng riskSharedAxes để waive. Registry registration bằng cached CLI được automatic approval chấp nhận. Retry `analyze --index-only --skip-fts` completed exit0; không đổi AGENTS/skills. Final refreshed filters **MEDIUM**,6direct dependents: read port, Search/Open, controller, request/response DTO. Authorizer/controller UNKNOWN vẫn được ghi cùng source confirmation, không đổi thành LOW.

Final index HEAD khớp current checkout; graph166057nodes/196803edges/547flows. FTS explicit disabled; process enumeration có warning dropped/unexplored paths, nên không claim complete execution coverage. [Refresh log](../evidence/chatbot-p2a-f01-f03-correction-2026-10-12/GRAPH_REFRESH.txt), `GRAPH_FINAL_*` và raw pre-edit evidence giữ nguyên.

Fresh `detect-changes --scope all --repo . --limit2000` exit0: **12tracked files/39symbols/8flows/HIGH**, gồm pre-existing Panel/Drawer và correction tracked source. CLI formatter chỉ hiển thị15symbols; đã rerun qua **cùng GitNexus LocalBackend.callTool('detect_changes',{scope:'all',repo:'E:/lotus-fin'})** để lưu [FULL structured39symbols](../evidence/chatbot-p2a-f01-f03-correction-2026-10-12/GRAPH_CHANGES_FULL.json), không partial/truncated/error. HIGH là risk report, **không clean release/commit authorization**; untracked new tests/docs không nằm trong Git-only delta. Không commit.

Hash integrity:4116initial fingerprints,4105unchanged;10owned existing edits đúng allowlist;1external concurrent change tại `frontend/src/pages/copilot/actions/invoiceActionPresentation.ts` được phát hiện và để nguyên. Không phải edit của batch. Hai Panel/Drawer byte hashes nguyên so đầu phiên; historical evidence/report source nguyên. HEAD/staged nguyên. Không tuyên bố toàn workspace unchanged khi có external edit.

## 6. Live gate và handoff

**P2A_LIVE_INTEGRATION=BLOCKED; execution NOT_RUN.** Không ERP source/HTTP calls hoặc business writes trong correction. Zero calls nhờ containment không phải actual ERP before/after no-write proof. Historical serving-image10missing-source observation không rerun hay biến thành current deployed artifact acceptance.

Prerequisites còn thiếu: approved private target/immutable installed source+imports, ordinary-user permission gold và fixtures/lifecycle, site/map/key/audit composition, concrete authorized read adapter, Company/DocType/document/field/mask/revocation/cache checks, actual HTTP POST/session/CSRF/origin/single wrapper/status/CID/no-store, physical SQL/bytes/hard timeout/admission/required audit/no-business-write+cleanup. Không dùng synthetic PASS để đóng chúng.

P2-B đã có authoritative **minimal DTO/fixture wire contract**, đủ để thiết kế UI riêng khi được giao; live transport/actions vẫn off. Không sửa AI001–AI003, finance, G10, packages hoặc Docker. Không enable/deploy/business mutation.

**Final: `P2A_CORRECTION_LOCAL_PASS` — F01–F03 trực tiếp sửa,12previous failures GREEN; chờ independent offline recheck và live qualification riêng.**

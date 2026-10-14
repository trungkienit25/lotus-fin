# P1 Final Fix — Test Evidence, 2026-10-12

**P1_FINAL_FIX_LOCAL_PASS**, builder self-verification. Runtime Windows11 10.0.26200, `C:\Python313\python.exe`3.13.7, pytest9.0.2, pydantic2.12.5, pluggy1.6.0; không install.

## Reproduction và incremental outcomes

Evidence root: `docs/reviews/evidence/chatbot-p1-final-direct-fix-2026-10-12/`. Mỗi phase có `REPRODUCTION.txt` (Python stdin), `SOURCE.json` current fingerprints, `PYTEST.txt`, `RESULTS.json` actual nodeid/status/assertion/exit. `INCREMENTAL_TEST_LEDGER.json` chứa exact pytest argument lists; source manifest/diff không phụ thuộc HEAD.

Commands: installed `python -B -` từ workspace, chạy reproduction phần sau header. Pytest dùng `pytest.main(["-p","no:cacheprovider","--noconftest","-v", ...explicit focused paths...])`. Exact final12paths nằm trong `FINAL-FOCUSED/RESULTS.json` và reproduction. Env PYTHONUTF8=1, PYTHONDONTWRITEBYTECODE=1, PYTEST_DISABLE_PLUGIN_AUTOLOAD=1. Guard trước app imports từ chối socket connect/connect_ex/bind/getaddrinfo và real ERP/LLM/legacy imports; framework doubles chỉ cài ở fixture. Không chạy executable runtime .py.

| Run | PASS | FAIL | Exit |
|---|---:|---:|---:|
| F04-RED |14|16|1|
| F04-GREEN |71|0|0|
| F04-GREEN-ADR |71|0|0|
| F01-RED |8|6|1|
| F01-GREEN |42|0|0|
| F02-F03-RED |5|21|1|
| F02-F03-RED-valid-CID |6|21|1|
| F02-F03-GREEN |27|0|0|
| F02-F03-REGRESSION |85|1|1|
| F02-F03-REGRESSION-GREEN |102|0|0|
| FINAL-FOCUSED |173|0|0|

Thực hiện F04 RED→GREEN-ADR trước F01, rồi F01 RED→GREEN trước F02/F03. Không coi first F04 GREEN204dòng là ADR acceptance. First C RED có bad-CID fixture trên valid-ID case; đã tách riêng, chạy RED-valid-CID trước edit. Regression failure duy nhất là disabled-test input thiếu ID; chỉ sửa input hợp lệ, không sửa assertion. Raw failures bảo tồn.

Final173distinct pytest call nodeids =86historical +87new (denial30/privacy14/terminal27/delivery16). Không đếm setup/teardown hay runner repetition như unique cases.

## Previously demonstrated counterexamples và controls

| Current execution | Kết quả | Raw evidence dưới root |
|---|---|---|
| N01–N12, A13–A16, C01–C06 |22/22 PASS, exit0|FINAL-INDEPENDENT_PROBES/TRACK_A_PROBES.json|
| B01–B14 |14/14 PASS, exit0|FINAL-TRACK_B/TRACK_B_PROBES.json|
| A16 direct/ancestor/root/default/concurrent/suppression/missing sink |14/14 PASS, exit0|FINAL-A16_CURRENT/A16_CURRENT_QUALIFICATION.json|
| B03 exact Company/absent/exception/DocType/Guest/positive |8/8 PASS, exit0|FINAL-B03_CURRENT/B03_PUBLIC_QUALIFICATION.json|
| Original F01–F04 findings8 +controls3 |11/11 PASS, exit0|FINAL-TARGETED/TARGETED_FINDINGS.json|

Historical script/schema có chữ independent vì giữ nguyên prior assertions; **đợt này builder chạy**, không independent acceptance. Không cộng69probe assertions vào173 như coverage unique. Probe directories giữ exact stdin, stdout/stderr, execution exits/current source hashes.

## Actual logger và privacy artifacts

`ACTUAL_DELIVERY_SNAPSHOTS.json` lưu actual stream text, attempts/acknowledged metadata, safe response metadata, decoded public synthetic claims. Bổ trợ7healthy terminal paths +7actual failing StreamHandler streams, không tăng unique test count.

Healthy:1attempt=1ack=1logline, RESPONSE_DELIVERY, UUID/header/body/event consistency; không raw actor/SID/ref/key/request/provider protected data. Outage: safe ActionEventDeliveryError,1attempt/0ack/empty stream, zero business reads. Missing sink không admission,503/null/0ack; không false delivery. Full required sink regression kiểm tra suppressions, direct/ancestor/root, default path, shared-handler concurrency và callback/global-state preservation.

Public decode có opaque actor/session và required binding/projection; raw synthetic actor/email/SID/key không xuất hiện. Domain/DTO deny đủ5reason với OK/PARTIAL dict/list; final mutated controller deny403/null, malformed source502/null, safe allowlist message. Benign positives giữ đúng hợp đồng.

## Source, scope, warnings, cleanup

`STATIC_SCOPE_AUDIT.json`: compile current source/test PASS, original assert/pytest.raises AST của8test files retained, ADR<200, outside-approved changes=[], historical review changes=[]. `ACTUAL_SOURCE_DIFF.patch.txt` chứa exact working-tree source/new-file diff. `FINAL_INTEGRITY.json` xác minh report append-only và preservation sau xuất tài liệu.

Final pytest không warning/failed assertion. Git inventory có permission-denied warning tại2 `.pytest_cache` có trước; không truy cập/xóa cache, explicit no-cache test unaffected. Metadata aggregation đầu dùng nhầm key outcome thay status bị KeyError sau static checks; recorder đã sửa và chạy lại exit0, không application failure.

Network attempts0, business reads0. Các import frappe bị guard từ chối ở absent-framework negatives là expected, không live call. Không Vite/Node/Docker/ERP process spawned/terminated hoặc shared port/service. Python GREEN processes exit0; logger handlers/threads dọn, framework double gỡ. Evidence giữ nguyên, không private directory cần xóa. Không source edit sau final focused, chỉ factual docs/report append.

## Gates

| Gate | Current local status | Giới hạn |
|---|---|---|
| F01–F04 |LOCAL_PASS|approved source/controller/serializer offline|
| P1-A |P1A_LOCAL_PASS|independent acceptance pending|
| P1-B |P1B_LOCAL_PASS|disabled offline foundation|
| P1B_LIVE_AUTHORIZATION |NOT_RUN|qualified target/auth/CSRF/document rights required|
| G10 |BLOCKED|judge deployment gate riêng|
| B1-S |historical PASS preserved|source unchanged, browser NOT_RUN|

Không ERP financial permission PASS, invoice action enable hoặc P2 dispatch.


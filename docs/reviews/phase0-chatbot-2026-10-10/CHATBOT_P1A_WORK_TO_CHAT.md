# Work → Chat — P1-A focused acceptance

11/10/2026 · Lotus Fin · FinTechathon Shenzhen 2026 · `develop@07f7251d3a0744356bf96fb2fea55ec6df9a0ce2` +current untracked P1-A artifact.

**`P1A_CHANGES_REQUIRED`. Chat chưa thể đóng P1-A; chưa dispatch P1-B.** Không blocker từ kiến trúc ERP cũ: lỗi được tái hiện trong chính foundation mới.

|Actual current execution|Kết quả|
|---|---|
|Focused builder tests|18/18 PASS, pytest0|
|Independent bounded checks|6 PASS /12 FAIL, process1; các safety assertions thất bại thật|
|Closed status/reason oracle|24 allowed +120 rejected,0 mismatches; subchecks, không cộng thành144 tests|
|CID/UUID/header tuple và keyword redaction|PASS; actual HTTP NOT_RUN|
|New import/network isolation|PASS, forbidden imports/network attempts0|
|Preserved B1/legacy|13 R7 +80 prior selected fingerprints unchanged; no broad rerun|

**Bốn root corrections, một scope/evidence correction:**

1. Final serializer chưa revalidate: mutated FORBIDDEN model vẫn trả protected data; raw user_message vẫn ra response. Enforce terminal data/source/message safety ở delivery.
2. Outcome/DTO chưa đủ strict: OK+INCOMPLETE, PARTIAL có selection_ref, nested denial và bogus DTO version/status/capability đều qua. Enforce approved contract, không build invoice use cases.
3. Log regex không bảo vệ metadata: raw sid/email/provider text thực sự ra logger; event IDs/stage/outcome pair không validate. Chỉ approved opaque refs/fixed metadata, actual-output sentinel tests.
4. Sink OSError bị nuốt nhưng event vẫn counted recorded. Port phải báo delivery failure theo SSOT policy; không audit framework mới.
5. Delivery test231 lines vượt ADR; report ghi196 (outcome177 ghi158). SHA match; sửa counts và giữ coherent table-driven tests trong cap/approved allowlist.

**Proposed bounded correction owner:** Antigravity sửa đúng5 production modules +2 tests +factual implementation-report update của P1-A; fresh GitNexus impact, không sửa legacy/frontend/API/session/financial/dependencies. Thêm regression vào intended assertion, không coi exception bất kỳ là PASS. Work recheck current hashes/focused suite và các counterexamples đã ghi; Chat đóng sau khi đạt cả năm gates. Không broad architecture/F07 rerun hoặc speculative refactor.

G1/G2/G3 FAIL; G4 host isolation PASS; G5 PARTIAL. Docker/ERP/live HTTP/performance NOT_RUN và không là bằng chứng permissions. Source độc lập với deployed artifact. P1-A chỉ foundation inert, không enabled action endpoint.

**P1-B sau closure:** canonical private image/site/version/import/apps +reviewed fixture lifecycle; trusted principal/company/site/product/connection mapping; exact permission boundary; signing-key owner/rotation/TTL; disabled-by-default routes/CSRF/admission; ordinary allowed/denied users/fields/revocation fixtures; Chat approve P1-B §9 allowlist và §7 budget/key/log decisions. Các mục này chưa được kiểm chứng runtime ở P1-A.

B1-S prior PASS giữ nguyên. G3/G01–G03 chưa đóng; G10 BLOCKED riêng. Không ERP financial automation, dependency install hoặc implementation dispatch trong lượt này.

[Independent recheck +exact findings/reproduction](E:/lotus-fin/docs/reviews/phase0-chatbot-2026-10-10/CHATBOT_P1A_INDEPENDENT_RECHECK.md) · [Actual pytest output](E:/lotus-fin/docs/reviews/evidence/chatbot-p1a-independent-2026-10-11/FOCUSED_PYTEST.txt) · [Independent probe ledger](E:/lotus-fin/docs/reviews/evidence/chatbot-p1a-independent-2026-10-11/INDEPENDENT_PROBES.json).

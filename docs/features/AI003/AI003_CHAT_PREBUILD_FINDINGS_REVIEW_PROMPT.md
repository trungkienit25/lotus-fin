# Prompt — ChatGPT Chat: AI003 final Work findings → technical decisions/F0

Bạn là architecture/contract owner. Review Work final package ở HEAD `86208f49e05122531c1cbe8b11d066092244dd4c`, branch `feature/risk-signal-agent`, trước khi giao implementation. Không tự coi business values approved; không freeze ở trạng thái này.

## Gửi kèm

1. `AI003_FINAL_PREBUILD_DECISION_PACKAGE.md`.
2. `evidence/AI003_FINAL_FOUNDATION_VERIFICATION_2026-09-30.md`.
3. `AI003_BUSINESS_POLICY_DECISION_SHEET.md` (phần tiếng Việt hiện hành).
4. `AI003_TECHNICAL_SCAFFOLD_IMPLEMENTATION_PLAN.md`.
5. Candidate v0.2, SSOT §35 và Gold Manifest khi cần exact field/case.

Tất cả đường dẫn dưới `docs/features/AI003/`. Work đã tìm trong repo: chưa có v0.3 hoặc technical decisions do Chat phê duyệt. Commit mới documentation/harness-only, production code vẫn c6f4cd1. Nếu bạn có v0.3/decisions ngoài repo, gửi exact authoritative text để Work kiểm; không yêu cầu Work phỏng đoán nội dung.

## Verified facts

- 152 focused unit tests PASS. Current 51 probe checks:39 PASS/12 FAIL/zero harness errors; 12 checks thuộc ba PB defects, không 12 bugs. 25 specification assertions TEST_ONLY, không engine/approval proof; không cộng overlapping totals.
- PB-SEC-01 HIGH: real Frappe Custom Role thu hồi AR, direct report denied, active/trusted explicit-user guard vẫn cho qua; populated cache trả same forecast ID, 10 obligations/opening cash. Fresh uncached trả SOURCE_ERROR thay generic FORBIDDEN, payload fresh rỗng. Regrant works.
- PB-DATA-01: positive row thiếu/bad due/overdue basis → available total565k nhưng overdue−10k/ratio−0.0177. Valid total có thể giữ available, affected overdue cần unavailable; không đổi legacy formula.
- PB-DATA-02: exact/conflicting duplicate rows được cộng tại AI001/AI002 AR/AP. Missing voucher failclosed. Real distinct payment-term/account-split reconciliation chưa verified; simulated split không thay proof.
- Numeric gold/fingerprints giữ nguyên tại20/09 và26/09. Net AR565k/overdue65k; positive575k/75k; credit−10k riêng. AP+1..7=275k,+1..30=975k; overdue600k/today700k riêng. Đây là synthetic verification pair6ngày, không approval baseline7ngày hoặc threshold.
- Company/Account/document controls pass; isolated site only, current probe quyền rollback/User+Role absent, no new voucher writes/frontend mutation. Temporal posting-date/restatement evidence reused unchanged source; no AS_KNOWN_AT.
- Dynamic replay khả thi trong harness, production reuse conditional do report auth chưa fixed. Không checksum/snapshot token access, không atomic multi-report snapshot guarantee.

## Việc bạn cần chốt

1. Issue candidate v0.3 hoặc approved technical decisions có exact fields/status/error/version semantics; review closure table trong final package.
2. Chốt overdue basis/consistency/coverage, observation identity và reconciliation (dedup identical hoặc typed reject; conflict/ambiguous failclosed; valid term/account splits giữ đủ amounts). Tách economic voucher count khỏi row count; Finance approve N_min policy sau.
3. Chốt precedence auth→invalid/inconsistent→not-applicable→policy-pending→evaluable, zero handling, >=/high ordering, Decimal precision/no display-rounding-before-threshold; source success khác coverage completeness.
4. Chốt dynamic authorized replay/hash context/method/schema/scope/version và source/derived distinction; no saved-data fallback on deny/unavailable.
5. Review B1–B9 proposals; Finance/Product ký riêng. Không chọn thresholds từ synthetic data. No approval→POLICY_PENDING/finding null/severity null với valid source. Không dùng trạng thái pending để che source-invalid.
6. Phát hành **một prompt F0 tập trung cho Antigravity/Zcode** theo allowed files/tests/stop/evidence trong plan. Builder sửa production ba PB, không buildAI003/đổi formula/threshold/gold/auto-upgradegate. Work replays real permission tests và affected gold sau newcommit/runtimealignment.
7. Nếu muốn tiến độ song song, authorize S1 mock/schema-only với draft technical semantics rõ; real financial reads/API MUST_WAIT F0 independentPASS. Không gọi overallTECHNICAL_SCAFFOLD_READY khi foundation còn lỗi.
8. Handoff integration member về shared auth/report/identity/DTOownership, additive versioning, agreedmergebase và isolatedpost-rebaseverification. Không tự rebase hay review ngoài AI003sharedboundaries.

## Outputs

- Authoritative v0.3/technical decision artifact, approvals tách pending.
- Focused F0 Antigravity/Zcode implementation prompt; conditional offline S1 prompt nếu được quyết định.
- Exact Work re-verification entry/exit criteria.
- Next owner và declared scaffold scope. Current outcomeCNOT_READY, G1PASSisolated/G2PARTIAL/G3+G4ABLOCKED/G4BNOT_APPLICABLE_YET/CONTRACT_FREEZENOT_READY.
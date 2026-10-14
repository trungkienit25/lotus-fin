# LOTUS FIN — P2-A/P2-B Final Work → Chat

12/10/2026 · Asia/Saigon · targeted acceptance + proposal gap, no implementation edits.

|Outcome|Verdict|
|---|---|
|P2A_OFFLINE_INDEPENDENT|**P2A_OFFLINE_INDEPENDENT_PASS** — technical independent-oracle scope|
|P2B_UI_INDEPENDENT|**CHANGES_REQUIRED**|
|P2AB_LIVE_ACCEPTANCE|**BLOCKED**, tests NOT_RUN|
|CHATBOT_PROPOSAL_COVERAGE|**PARTIAL**|
|G10|**BLOCKED**, separate gate|

**Provenance:** reviewer là cùng agent đã sửa P2-A trước đó. New oracle/fixtures tách builder tests và actual execution GREEN; không claim organizational reviewer independence. Reviewer khác vẫn cần xác nhận nếu release policy yêu cầu. P2-B reviewed from separately built source.

P2-A fresh343/343focused (173P1+103P2existing+67correction),50distinct new oracle checks PASS gồm đủ12previous failures; A16 14/14 và B03 8/8PASS; original5P1codec methods AST nguyên. Không cộng overlap. Normal actual get_context→fresh search→signed selection→fresh open đạt, no model_copy positive workaround; capability/scope/config/key/revoke/null/date/expiry guarantees giữ trong offline protocol.

P2-B existing60unit/3fixtureE2EPASS nhưng independent23checks **12PASS/11FAIL**, ReactDOM9 **6PASS/3FAIL**. Three material findings:

1. **F01/P2:** backend valid empty hoặc PARTIALempty với selection_required=false bị UI INVALID_RESPONSE; actual service serialization và DOM reproduced.
2. **F02/P2:** UI nhận ContextData thiếu required date defaults, sai allowed_filters và outer/inner context_version mismatch.
3. **F03/P1:** cùng currentRID/CID/capability nhưng different context/site/product/connection/company vẫn vào state; actual React reader hiển thị **QA B** dưới QA A context trong synthetic negative. Không claim real ERP leak.

Presentation module343lines vượt ADR001; targeted cohesive split cùng decoder/controller correction, không broad React rewrite. Typecheck/lint/build PASS. B1S fresh separate-process4/4PASS; combined run4fail do cached fixture WS token, retained and explained, not app regression. Controlled browser/server cleanup/port release verified.

Fresh runtime: old image `sha256:ed6e02f587eb450a0882ecb4b6fbb259d1a1f27f549e1cc4bbe21a660b3017b7`, no source bind,17/17selected P1/P2files missing. No approved private target/snapshot/restore/cleanup/ordinary-user gold. Actual auth/doc/field/mask/CSRF/HTTP/audit/revocation/no-write/resource/rollback acceptance NOT_RUN; shared sites not used. No enablement/deployment/business read/write/source edit.

Proposal coverage: generic read-family backend foundation exists offline; fixture intent/clarification/search/select/minimum reader is partial due UI findings. **PastFinalDue/financial overdue, summary/priority/customer-search, L3local prepare/prefill, L4saved ERP Draft/confirmation/idempotency and L5submit/cancel/send/payment/autonomous are not implemented in this assisted-action slice.** Generic read is not overdue; view is not draft; no mock-as-live authority. Judge/demo deployment still G10BLOCKED.

Deliverables:

- [Recheck, exact findings/tests/provenance/live gate](CHATBOT_P2AB_INDEPENDENT_RECHECK.md).
- [Every capability: status/data/rules/blockers/smallest batch/demo boundary](CHATBOT_PROPOSAL_COMPLETION_MATRIX.md).
- [New evidence summary](../evidence/chatbot-p2ab-independent-acceptance-2026-10-12/VERIFICATION_SUMMARY.json), [commands](../evidence/chatbot-p2ab-independent-acceptance-2026-10-12/COMMANDS.json).

Next smallest batch: fix only three UI findings and ADR responsibility split; keep flags off and existing assertions; rerun independent23+DOM9 plus affected existing60/3/B1 4/type/build/lint. Then a separate approved private-target/adapter/HTTP/real no-write qualification batch. Financial V1 and L3/L4/L5 need their own approved rules, not automatic expansion.

Limited trusted fixture positive paths can be shown with explicit simulation labels; **no full P2-B demo-ready/live/proposal-DONE verdict**. Stop after gate decisions and handoff; no automatic dispatch, feature enablement or fix.

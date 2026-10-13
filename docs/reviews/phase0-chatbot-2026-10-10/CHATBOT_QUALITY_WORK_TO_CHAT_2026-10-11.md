# Work → Chat: B1-S và chatbot quality

11/10/2026 · FinTechathon Shenzhen · `develop@07f7251d3a0744356bf96fb2fea55ec6df9a0ce2` + dirty tree. Authority: user audit request; AGENTS/GitNexus, ADR001, Security Code V3, Workflow v3.1 §31–34. Read-only source/tests; no ERP/LLM/shared Docker/Redis, commit/deploy or implementation dispatch. Lotus Fin product khác ERPNext technology; topology chưa được runtime verify.

**Track A verdict: B1S_G4B_CHANGES_REQUIRED.** 12/12 B1source/report fingerprints giữ nguyên Round 4. 52/52 application gold PASS, 32 exact-message assertions PASS trên cùng records. Four supplied native tests PASS và cùng four tests wrapped PASS, không cộng thành 8 unique. Native 20 qualification records:19 PASS/1 FAIL, gồm17 original Q1–Q6 PASS. Five negative pytest invocations:4 fail đúng kỳ vọng; undeclared METHOD GET trả 200/pytest0 sai kỳ vọng. Typecheck/build/target lint exit0; 5 lint warnings, 757.04kB minified JS warning. Private lifecycle/cleanup PASS: owned Node 0/port 5188 free/known Chromium 0, TEMP removed, unrelated kills 0.

**Smallest current blocker:** native guard/mock chỉ match origin/path; GET vào chatbot endpoint mock vẫn HTTP200. Source vẫn chứa four open R4 root causes: strict registry, readiness ownership, post-close final ledger, case-bound synchronization. Seven other extended R4scenarios không rerun ở lượt này; không tự closed vì source unchanged. G2 narrow PASS; G4A FAIL; G4B CHANGES_REQUIRED; G3 PARTIAL và G10 separately BLOCKED/NOT_RUN.

**Actual integration facts:** React Page/Drawer reuse safe Panel/hook/normalizer, qualified=false và không production chatbot transport. CompanyGET là selector, không authorized observation. Desk Page/hooks chọn inline `public/js/lotus_fin.js`; `frappe.call(ai_insights.chat_copilot)` re-export tới public copilot_api → controller → CopilotService/AgentRunner → six-tool invoker → plugin/domain providers; controller dùng global InMemorySessionRepository. Two broad-exception paths route legacy keyword logic. Redis cache alternative không wired và source import/model contracts không đủ để swap. Provider runtime/target/version/site/custom apps/principal delegation/image UNKNOWN. No installed “ERPNext SDK” orchestration proven; defer choice to qualified target/client contract, adapter stays infrastructure.

**Five findings lớn (không B1React blockers):**

1. C01 HIGH: failed tool mất terminal failure; second-denied label mang first-success data, empty model trả “Analysis completed.”
2. C02 HIGH: F001 thiếu period fields; F002 cutoff key lệch/horizon omitted; F003 old keyword signature không bind current service.
3. C03 HIGH: session contract không reject owner/company mismatch; by-reference failed turn mutate state; missing site/product scope/retention.
4. C04 HIGH: configured Desk widget fields unescaped; no equivalent status/provenance/race/scope contract. Prose escape control PASS; full public exploit NOT_VERIFIED.
5. C05 MEDIUM: responseDTO drops status/reason/CID, logs/toolIDs chưa tạo end-to-end trace; raw errors/fallback che original stage.

Eight pure backend/Desk probes:2 controls PASS/6 behavior FAIL; fake dependencies, no HTTP/ERP exploit claim. Three tool-bridge comparisons static, không cộng runtime tests. General AI001–AI007/F102 audit không mở lại.

**Three improvements sau P0:** typed safe outcome/source/CID end-to-end để giữ lỗi đúng; stateless server-owned authorized read boundary để invoice pilot không phụ thuộc session; capability-specific typed adapter/permission/UI tests để schema thực sự khớp execution. Không cần microservice/framework/SDK mới, full Panel/Page split, all-feature refactor, blind Redis replacement hoặc xóa legacy.

| Stage | Eligible scope / acceptance |
|---|---|
| P0 | **B1-S/F07 test-only correction**, approved paths/cap 320: exact method/query/path/assets/WS, post-spawn ownership/readiness, settled-close ledger/finalizer, response-specific sync. Preserve52gold/17 original; eight R4 failing scenarios must qualify. One helper scope proposal if cap/allowlist inadequate; no application change. |
| P1 | Chat-approved public read outcome + authenticated actor/site/product/connection/company/context/source/version + CID/budgets; verify target/delegation and isolated permission/field projection. No capability enable before gates. |
| P2 | Invoice search → bounded authorized results → explicit user selection → document reauthorization → open; existing Lotus Fin application/permission seams, typed InvoiceReadPort. Ambiguity/empty/denied/revoked/stale/scope-switch gold, isolated delivery/DOM evidence. No payment-history inference or mutations. |
| P3 | Selected-path measurements/cohesive refactors only; state/session qualification if actually needed; de-duplicate Desk/legacy only with caller/runtime/impact evidence. |

Designed future writes require separate exact-args/target-version/actor/scope/expiry approval, durable idempotency/evidence, UNKNOWN_OUTCOME reconciliation; none executed/authorized here. p95/throughput/RSS/SQL/real authorization/ERP truth/G10 NOT_MEASURED or NOT_RUN; report/API calls khác SQL count. Numeric budgets/workload cần approved trước benchmark, không guessed PASS.

Decision packet hoàn tất để Chat review, **không freeze/dispatch**. [Track A current appendix](B1S_CORRECTION_R4_INDEPENDENT_RECHECK.md), [AS-IS/TO-BE + backlog](CHATBOT_ARCHITECTURE_SCALE_DEBUG_AUDIT.md), [raw evidence/reproduction](../evidence/chatbot-quality-audit-2026-10-11/REPRODUCTION.md). Historical bytes/hash lineage được giữ qua snapshots và final manifest; source/runtime/image facts tách riêng.

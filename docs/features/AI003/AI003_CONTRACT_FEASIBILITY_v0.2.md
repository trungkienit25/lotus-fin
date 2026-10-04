# AI003 v0.2 — field feasibility (Work, 2026-09-30)

Revision `c6f4cd13c677e167ac645d4d0c48d236383c4fac`; isolated site `ai003-verify.localhost`. `SUPPORTED` means existing primitives/source support the field, not that an AI003 endpoint exists. `SUPPORTED_WITH_CHANGE` means a bounded AI003 adapter/contract change is needed; implementation remains gated. All field names below come from the supplied v0.2 candidate.

| Fields | Status | Evidence / required change |
| --- | --- | --- |
| request.as_of; request_context.as_of | SUPPORTED | AI001 and AR/AP report use accounting date cutoff; future-posted AR/AP excluded. |
| request.baseline_as_of; request_context.baseline_as_of; baseline.as_of | SUPPORTED_WITH_CHANGE | Two independent cutoffs verified; AI003 explicit baseline validation/comparability and approved date policy needed. |
| request.selected_signals; signal_type | SUPPORTED_WITH_CHANGE | New two-signal allowlist needed; no AI003 endpoint yet. Tampered filter tests are G4B. |
| feature_id; contract_version; method_version | SUPPORTED_WITH_CHANGE | Existing versioned AI001/AI002 envelopes reusable; AI003 identifiers/versions need candidate-specific binding. |
| rule_version; rule.rule_version | NOT_SUPPORTED | No approved rule registry/policy yet; do not invent business approval. |
| request_context.verified_company | SUPPORTED | Company session guard passed authorized/unauthorized/nonexistent cases with generic denial. |
| request_context.accounting_timezone | SUPPORTED | Isolated System Settings = Asia/Ho_Chi_Minh; arithmetic is accounting DATE, not arbitrary timestamps. |
| request_context.currency | SUPPORTED | Company VND; USD tampering live returns VALIDATION_ERROR; no FX conversion. |
| request_context.finance_book_scope | SUPPORTED_WITH_CHANGE | AI002 nonempty Finance Book live rejected. AI001 has no explicit Finance Book request field; AI003 must bind verified default scope/reject unsupported book. |
| request_context.data_mode | SUPPORTED_WITH_CHANGE | AI002 LIVE/FIXTURE source mode reusable; gold fixture must remain labelled synthetic. |
| provenance.source_snapshot_refs | SUPPORTED_WITH_CHANGE | AI001/AI002 snapshot IDs and report checksums exist, but no shared atomic snapshot or durable replay by ID. Retain per-source cutoff/hash/method. |
| provenance.generated_at; provenance.correlation_id | SUPPORTED | Existing retrieval timestamps/correlation IDs available; distinguish generation time from accounting cutoff. |
| signal_id | SUPPORTED_WITH_CHANGE | Needs versioned identity/idempotency semantics; existing snapshot IDs are generated per read. |
| source_status | SUPPORTED_WITH_CHANGE | AVAILABLE/UNAVAILABLE and error reasons exist, but SOURCE_INVALID/ZERO_VERIFIED/TIMEOUT mapping needs explicit adapter rules. Current missing due date and duplicate behavior violates safe reuse. |
| coverage_status | SUPPORTED_WITH_CHANGE | Existing TRADE_ONLY/PARTIAL coverage available; add due-date completeness, credit context and source-count/duplicate checks for the chosen signals. |
| evaluation_status; finding; severity | SUPPORTED_WITH_CHANGE | Candidate POLICY_PENDING/null semantics can be specified; business thresholds/severity labels unapproved. Define source-invalid precedence and zero denominator. |
| metric.metric_id; metric.unit | SUPPORTED_WITH_CHANGE | AR ratio/AR delta percentage points and AP ratio IDs require AI003 allowlist; do not accept arbitrary metric ID. |
| metric.value; metric.status | SUPPORTED_WITH_CHANGE | Independent numeric inputs verified; AR source currently accepts missing dates/duplicate; AP positive-obligation dates need completeness/dedup before cluster metric. |
| baseline.value; baseline.status; change.value; change.unit | SUPPORTED_WITH_CHANGE | AR independent current/baseline arithmetic available. Net versus positive credit policy, baseline/count and precision need approval. AP baseline applicability must be defined. |
| rule.threshold_type; rule.threshold | NOT_SUPPORTED | Threshold approval pending; symbolic/Test-only harness cannot supply production values. |
| rule_inputs.denominator; rule_inputs.observation_count | SUPPORTED_WITH_CHANGE | Oracle emits residual denominators; define observation identity (voucher vs installment/account row), legitimate duplicate semantics and zero handling. |
| evidence_refs | SUPPORTED_WITH_CHANGE | AI001 dict ERP_NEXT_REPORT refs with cutoff/filter/checksum; AI002 DOCUMENT_REF-compatible strings. Map to REPORT_SNAPSHOT/DOCUMENT_REF/DERIVED_METRIC explicitly; no automatic durable report replay. |
| missing_inputs; limitations | SUPPORTED | Existing typed failures/limitations available; avoid exposing report/resource existence on denial. |
| explanation.status; explanation.text | SUPPORTED_WITH_CHANGE | Existing AI001 minimized payload/provider/grounding tested for timeout/unavailable/malformed/ungrounded, leaving metrics unchanged. AI003 explanatory schema/tools require bounded binding. |
| next_checks | SUPPORTED_WITH_CHANGE | AI002 NEXT_CHECK_TEMPLATES reusable pattern; approve AI003-specific IDs and permission-aware links. |
| get_risk_signals tool | SUPPORTED_WITH_CHANGE | Expected future build task; no AI003 service/tool exists, which is not itself a pre-build G4A defect. |
| AS_KNOWN_AT reconstruction | NOT_SUPPORTED | Explicitly excluded; current posting-date history restates after backdate/cancel/amend. |
| REPORT_SNAPSHOT/DERIVED_METRIC immutable evidence drilldown | NOT_SUPPORTED | No authorized durable snapshot replay endpoint/storage exists. Dynamic report replay must compare saved hash and explicitly report restatement/unavailability; Chat must choose policy. |
| document evidence access reauthorization | SUPPORTED | Authorized, cross-company, arbitrary DocType, document-specific deny/regrant, role revoked and snapshot-ID-not-token probes passed. |
| report reauthorization on cache hit | NOT_SUPPORTED | Concrete defect: Custom Role revokes actual AR report, direct report fails, guard returns normally and cached financial payload remains accessible. |

Verdict: **NEEDS_CHANGE**. AR/AP window arithmetic is feasible; secure reuse and financial policy are not ready for contract freeze. See pre-build evidence report for concrete defects and acceptance matrix.

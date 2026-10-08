# AI003 — Independent Verification Lead: focused remediation verification (2026-09-30)

Role: Independent Verification Lead (IVL). Basis: current HEAD `c6f4cd1`, branch `feature/risk-signal-agent`; isolated runtime `ai003-verify.localhost`. Authority: SSOT §32–§33 (uncommitted Work sections), Candidate Contract v0.2, pre-build evaluation 2026-09-30. No production code was changed; no AI003 implementation; no business policy approved. Transient probe artifacts were removed; residue is documented in §6.

## 1. Runtime, source and migration sync — VERIFIED

| Check | Result |
| --- | --- |
| Backend/frontend/queue/scheduler/websocket image | `sha256:220e4f5dc54973a3bef476a9ef37ca1ea49a71689cad48526d1da8ddcc383bca` — matches Work's §32 rebuild record; all six services Up, DB healthy |
| Source revision in container | SHA256 of `ai/financial_snapshot.py`, `cashflow/adapters.py`, `api/key_reports.py` identical to workspace HEAD `c6f4cd1` |
| Migration | `Company.ai002_approved_cash_accounts` column present on isolated site |
| Timezone | `System Settings.time_zone = Asia/Ho_Chi_Minh` |
| Gold fixture state | `AI003 Gold 2026` (A3G) approved-scope config present; voucher counts intact (see §5) |

## 2. PB-SEC-01 — INDEPENDENTLY CONFIRMED (HIGH)

Report-specific revoke does not stop the reusable guard or the AI002 cache. Reproduction performed independently of Work's scripts (probe: `evidence/ivl_phase_a_probe.py`):

1. Created transient Accounts User with User Permission `Company → AI003 Gold 2026`. Pre-restriction: AR report read authorized; AI002 request computed real sources (`FORECAST_UNAVAILABLE`, forecast `FC-BD22E79F`, 10 obligations, opening cash 20,000,000); cache populated (repeat request → same forecast ID).
2. Created `Custom Role {report: "Accounts Receivable", roles: [Accounts Manager]}`.
3. Authoritative denial observed: `Report.is_permitted()` falsy; direct `query_report.run` refuses.
4. **Defect:** `check_ai002_report_permission("Accounts Receivable", user=probe)` returns normally; repeating the identical AI002 request returns the **same forecast ID with all 10 obligations and opening cash** — the cached financial payload — instead of `FORBIDDEN` with an empty payload.
5. Regrant (Custom Role removal) restores authorized behavior. Probe user/Custom Role deleted; absence asserted.

Root cause (confirmed by code read): `security/access.py:check_report_permission` calls `frappe.desk.query_report.has_permission`, which is a generic permission check and does not enforce the report's `is_permitted()`/Custom Role restriction. AI002 cache-hit reauthorization (`cashflow/service.py:_reauthorize_cached_resources`) reuses this insufficient primitive.

## 3. PB-DATA-01 — INDEPENDENTLY CONFIRMED

AR overdue metric becomes `AVAILABLE` with a wrong basis when due-date information is missing. Using the real A3G AR report at cutoff 2026-09-26 (baseline: total 565,000 / overdue 65,000 / ratio 0.11504 — matches gold), the first positive-residual row had `due_date`/`overdue`/`overdue_amount` stripped. Result: total unchanged (565,000), overdue became **−10,000** (only the credit row's overdue remains), and `parse_ar_data` still returns the ratio as an available metric: **ratio = −0.0177, AVAILABLE**. Expected per finding: typed unavailable/inconclusive for the overdue metric until the overdue basis is proven; never interpret a missing date as zero overdue.

## 4. PB-DATA-02 — INDEPENDENTLY CONFIRMED (both legs)

- AR: appending an exact copy of a real positive AR row raises the parsed total from 565,000 to **640,000** (75,000 double-counted), still `AVAILABLE`.
- AP (corrected measurement): `_collect_obligations` on the real AP payload yields **7** positive obligations; with an exact duplicate row appended → **8**, with repeated `source_ref=Purchase Invoice:ACC-PINV-2026-00006`. (An initial probe assertion compared a combined AR+AP count against an AP-only count and was re-measured; final evidence is the corrected pair.)

## 5. Regression and numeric-stability checks

- 7 AI001/AI002 suites in Docker: **197/197 OK** (matches §32). Full discovery previously recorded **233/233** at the same revision.
- Independent gold oracle re-run (Work's `prebuild_oracle.py` — verified by inspection to import no Lotus Fin production code; attributes residuals from `Payment Ledger Entry`, not `Invoice.outstanding_amount`):

| Cutoff | AR net | AR overdue | AP +1..+7 | AP +1..+30 |
| --- | ---: | ---: | ---: | ---: |
| 2026-09-20 | 650,000 ✓ | 0 ✓ | 1,400,000 ✓ | 1,950,000 ✓ |
| 2026-09-26 | 565,000 ✓ | 65,000 ✓ | 275,000 ✓ | 975,000 ✓ |

- Impact analysis for not re-running all 70 evaluation cases: container source hashes and image ID are identical to Work's §33 evaluation state (unchanged revision `c6f4cd1`), so the 67 passing cases remain valid; only the three open defects, runtime sync, regression suites and the gold oracle were re-verified.

## 6. Probe hygiene statement

All probe users, User Permissions and Custom Roles were removed and their absence asserted. Four transient Sales Invoice documents created by the replay harness remain on the isolated site in **cancelled** state (docstatus 2: `ACC-SINV-2026-00012/00013/00014/00015`) plus the linked `AI003 IVL Temp Customer` — caused by a harness commit that persisted the transients and a `tabContact` deadlock during user deletion. Cancelled documents contribute nothing to residuals: the gold oracle was re-run after cleanup and returned exactly 650,000/0 and 565,000/65,000 (restored). Recommended: Work purges these four cancelled documents and the temp customer in the next fixture pass if strict zero-residue is required.

## 7. Verification conclusion

```text
FOUNDATION REMEDIATION (WR-01/WR-02 + Buckets A–D, verified scope): CONFIRMED PASS
OPEN DEFECTS REPRODUCED: PB-SEC-01 (HIGH), PB-DATA-01, PB-DATA-02 — all exact, all scoped
GATE IMPACT: G4A remains BLOCKED (PB-SEC-01); G3 remains BLOCKED (PB-DATA-01/02 + policy)
NEXT OWNER: ChatGPT Chat approves focused remediation scope; Antigravity/Zcode implements; Work re-tests
```

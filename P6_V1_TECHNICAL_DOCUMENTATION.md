# P6 V1 PastFinalDue — Technical Documentation

## 1. Executive Summary & Architectural Overview

The **V1 PastFinalDue** capability (`PAST_FINAL_DUE_INVOICES`) implements deterministic overdue candidate evaluation strictly based on **Option B** as specified in `V1_OVERDUE_SOURCE_AND_CONTRACT_CLOSURE.md`.

This implementation is:
1. **Completely ERPNext-Independent:** Operates via Lotus-owned domain models and typed ports (`AuthorizedOutstandingInvoiceObservation` and `IAuthorizedOverdueObservationPort`). Zero reliance on ERPNext invoice tables, stored statuses, or report runs.
2. **Deterministic & Truthful:** Uses high-precision `Decimal` arithmetic for monetary residuals, enforces strict site-local calendar date calculations, and treats "due today" as **not** past-final-due.
3. **Data-Later Isolated:** Separated into three discrete providers (`CORE`, `DEMO`, and `NATIVE`).
4. **Security-Hardened:** Binds HMAC-SHA256 selection references only on complete authorized coverage, stripping selection credentials whenever scans are partial or truncated.

---

## 2. Predicate Engine Specifications (Phase 1 & 2)

The `PastFinalDueEvaluator` enforces the candidate eligibility predicate:
- **Lifecycle:** Must be in approved set (`SUBMITTED`, `APPROVED`, `POSTED`, `1`). Drafts and cancellations are immediately excluded.
- **Returns / Credits / Write-offs:** `is_return`, `is_credit_note`, or `is_write_off` are rejected.
- **Outstanding Residual Balance:** Evaluated as finite `Decimal`. Must be strictly greater than zero (`> Decimal("0")`). Zero residuals (settled invoices) or negative balances (credits/prepayments) are excluded without zero substitution.
- **Site-Local Calendar Evaluation:**
  $$\text{site\_local\_date} = \operatorname{date}(\operatorname{to\_timezone}(\text{observed\_at\_utc}, \text{site\_timezone}))$$
  Eligibility requires:
  $$\text{final\_due\_date} < \text{site\_local\_date}$$
  If $\text{final\_due\_date} \ge \text{site\_local\_date}$, the invoice is not past-final-due.
- **Scope Verification:** Observations with tenant or company IDs mismatched from the caller context are rejected without information leakage.
- **Future-Posted Invoices:** Records with $\text{posting\_date} > \text{site\_local\_date}$ are marked `UNQUALIFIED`, causing the scan to fail-closed into `PARTIAL` coverage.

---

## 3. Typed Port Architecture (Phase 3 & 4)

### Observation Contract
The port [`IAuthorizedOverdueObservationPort`](file:///e:/lotus-fin/lotus_fin/lotus_fin/application/port/i_overdue_observation_port.py) consumes:
- [`AuthorizedReadContext`](file:///e:/lotus-fin/lotus_fin/lotus_fin/domain/model/authorized_read_context.py)
- [`PastFinalDueFilterParams`](file:///e:/lotus-fin/lotus_fin/lotus_fin/domain/schema/overdue_invoice_read.py)

And yields:
- `List[AuthorizedOutstandingInvoiceObservation]`
- `SourceEvidence`
- `is_truncated: bool`
- `ActionStatus`
- `ActionReasonCode`
- `next_cursor: Optional[str]`

### Outcomes & Status Consistency
- `OK`: Delivered only on complete scan coverage (`PAGE_COMPLETE`), complete scope checks, and zero missing data.
- `NO_MATCH` / `EMPTY_RESULT`: Complete coverage with zero candidates. Never inferred from empty pages or network errors.
- `PARTIAL`: Emitted when scan limits are reached (`SCAN_WINDOW_TRUNCATED`) or any candidate observation is `UNQUALIFIED`. Under `PARTIAL`, all `selection_ref` tokens are stripped.
- `NOT_AVAILABLE`: Emitted when native source is unconfigured or blocked by the N0 authority gate.

---

## 4. Three-Tier Provider Architecture (Phase 5)

1. **CORE Provider (`CoreOverdueObservationProvider`)**:
   - Represents production when native adapters are unconfigured.
   - Always returns `NOT_AVAILABLE` (`TARGET_UNQUALIFIED`).
   - Zero hallucinated, synthetic, or fallback rows.
2. **DEMO Provider (`DemoOverdueObservationProvider`)**:
   - Provides fixed, verified fictional records for isolated testing and UI simulation.
   - Distinct from production keys and isolated by session and tenant scope.
   - Explicitly displays `DEMO DATA (FICTIONAL)`.
3. **NATIVE Provider (`NativeOverdueObservationAdapter`)**:
   - Formal interface and config contract (`NativeOverdueAdapterConfig`).
   - Fails closed until explicit N0 authoritative signoff.

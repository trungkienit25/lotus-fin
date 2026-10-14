# P6 V1 PastFinalDue — Frontend Contract & Presentation Specification

## 1. Overview
The frontend contract for `PAST_FINAL_DUE_INVOICES` is designed to be completely decoupled from backend persistence mechanisms and ERP frameworks. It renders candidate items, residual amounts, overdue aging, coverage notices, and isolation badges cleanly in React.

Shared Copilot shell and mount files owned by P6-0 were strictly preserved without modifications.

---

## 2. Component & Model Artifacts

1. **Typed ViewModel Definitions:**
   [`frontend/src/pages/copilot/actions/pastFinalDueTypes.ts`](file:///e:/lotus-fin/frontend/src/pages/copilot/actions/pastFinalDueTypes.ts)
   - `PastFinalDueResponseVm`: High-level view response including provider mode, coverage, limitations, and scope.
   - `PastFinalDueItemVm`: Individual overdue invoice row with `invoiceId`, `finalDueDate`, `overdueDays`, `currentOutstandingDecimal`, `partyAccountCurrency`, and `selectionRef`.
   - `PastFinalDueScanCoverage`: Explicit scan accounting (`scannedRows`, `returnedRows`, `complete`, `missingRequiredData`, `truncated`).

2. **React Presentation Component:**
   [`frontend/src/pages/copilot/actions/PastFinalDueView.tsx`](file:///e:/lotus-fin/frontend/src/pages/copilot/actions/PastFinalDueView.tsx)
   - Labeled with **DEMO DATA (FICTIONAL)** badge when running against DEMO provider.
   - Labeled with **NATIVE SOURCE NOT CONFIGURED** badge when running against unconfigured CORE provider.
   - Highlights **PARTIAL COVERAGE** with warning box listing active limitations.
   - Enforces action button safety: "Xem chi tiết" is only enabled if a cryptographically valid `selectionRef` exists; otherwise displays "Chưa xác thực".
   - Shows site-local date, IANA timezone, and explicit "Làm mới (Fresh Authorization)" control.

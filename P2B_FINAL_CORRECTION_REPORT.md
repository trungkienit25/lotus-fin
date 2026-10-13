# P2-B FINAL TARGETED SECURITY & CONTRACT FIX REPORT

**Date:** 12 October 2026  
**Role:** Senior React/TypeScript Engineer  
**Workspace:** `frontend/src/pages/copilot/actions/`  
**Verdict:** `P2B_BUILDER_READY_FOR_RECHECK`

---

## 1. Executive Summary & Critical Product Constraint

- **ERPNext Independence:** Lotus Fin is independent from ERPNext. No ERPNext SDK, DocTypes, endpoints, permissions, or ERPNext-specific navigation were introduced or depended upon.
- **Contract Boundary:** Fixed all reproduced findings (FIN-F01, FIN-F06, FIN-F07, FIN-F08, FIN-F09) against the currently frozen P2 wire within `frontend/src/pages/copilot/actions/`.
- **Protected State Safety:** All protected handles, context, rows, selections, and readers are fenced and cleared immediately upon expiration, scope changes, or unverifiable responses. Zero ERP mutation or persistence occurred.

---

## 2. Findings Closure Summary

### FIN-F01 — Admission-time expiry [P1]
- **Mechanism:** Checked active context freshness (`now >= expires_at`) immediately upon admission of `invoice.context`, `invoice.search`, and `invoice.open` responses in `InvoiceActionController`.
- **Fencing & Cleanup:** Any response arriving at or after expiration triggers `clearProtected(expiredNotice())`, immediately resetting context, results, selection, and document handles to prevent stale/expired rendering.

### FIN-F06 — Strict envelope and expiry [P2]
- **Mechanism:** Enforced outer `context_version` presence as a non-empty string on all success envelopes (`status === "OK" || status === "PARTIAL"`). Enforced strict equality between outer `context_version` and inner `d.context_version`.
- **Canonical UTC:** Implemented `isCanonicalUtc()` to validate canonical UTC timestamps (`YYYY-MM-DDTHH:mm:ssZ` or `+00:00`), rejecting invalid dates, rollovers (e.g. `2026-02-30`), local datetimes, and date-only strings without falling back to synthetic defaults.

### FIN-F07 — Invalid-response cleanup [P2]
- **Mechanism:** In `openInvoice()`, whenever the received document does not match the selected item's `invoice_id` or `record_version`, or when the response payload is unverifiable/unavailable, all protected handles (`context`, `results`, `document`) are cleared via `clearProtected()`.

### FIN-F08 — Pagination metadata [P2]
- **Mechanism:** Enforced strict wire validation in `parseSearchData`:
  - `has_more` must be an explicit boolean (`true` or `false`).
  - When `has_more === true`, `next_cursor` must be a non-empty string $\le 2048$ chars.
  - When `has_more === false`, `next_cursor` must be strictly `null`.
  - Empty complete results (`items.length === 0`) require `has_more === false` and `next_cursor === null`.
  - For `status === "PARTIAL"`, both `has_more` and `next_cursor` must be `null`.

### FIN-F09 — Source identity pinning [P2]
- **Mechanism:** Added `timezone` to `SourceEvidence`. Pinned all source identity axes (`siteRef`, `productRef`, `connectionRef`, `connectionVersion`, `sourceMode`, and `timezone`) against `expectedContext` in `invoiceActionDecoders.ts`.

---

## 3. Original RED → GREEN Test Matrix

All 18 previously failing Node oracle test cases in `fresh_oracle.mjs` are now passing:

| Case ID | Finding | Pre-Fix Status | Post-Fix Status | Verification Detail |
|---|---|---|---|---|
| `R2_OUTER_VERSION_missing` | FIN-F06 | **FAIL** | **PASS** | Outer `context_version` missing rejected |
| `R2_OUTER_VERSION_null` | FIN-F06 | **FAIL** | **PASS** | Outer `context_version: null` rejected |
| `R2_EXPIRY_FORMAT_2026-02-30T10:00:00Z` | FIN-F06 | **FAIL** | **PASS** | Non-existent calendar date rejected |
| `R2_EXPIRY_FORMAT_October 12, 2026 10:05:00` | FIN-F06 | **FAIL** | **PASS** | Prose date format rejected |
| `R2_EXPIRY_FORMAT_2026-10-12` | FIN-F06 | **FAIL** | **PASS** | Date-only format rejected |
| `R2_EXPIRY_FORMAT_2026-10-12T10:05:00` | FIN-F06 | **FAIL** | **PASS** | Local datetime without UTC offset rejected |
| `R2_PAGE_more_no_cursor` | FIN-F08 | **FAIL** | **PASS** | `has_more: true` with `null` cursor rejected |
| `R2_PAGE_cursor_no_more` | FIN-F08 | **FAIL** | **PASS** | `has_more: false` with non-null cursor rejected |
| `R2_PAGE_missing_more` | FIN-F08 | **FAIL** | **PASS** | Missing `has_more` rejected |
| `R2_ZERO_PAGE_more_cursor` | FIN-F08 | **FAIL** | **PASS** | Zero rows with continuation cursor rejected |
| `R2_ZERO_PAGE_false_cursor` | FIN-F08 | **FAIL** | **PASS** | Zero rows with cursor rejected |
| `R2_ZERO_PAGE_missing_more` | FIN-F08 | **FAIL** | **PASS** | Zero rows without `has_more: false` rejected |
| `R2_F03_search_source_mode` | FIN-F09 | **FAIL** | **PASS** | Changed source mode rejected on search |
| `R2_F03_open_source_mode` | FIN-F09 | **FAIL** | **PASS** | Changed source mode rejected on open |
| `R2_INVALID_OPEN_CLEARS_HANDLES` | FIN-F07 | **FAIL** | **PASS** | Foreign/invalid open clears context & results |
| `R2_EXPIRED_AT_ADMISSION_context` | FIN-F01 | **FAIL** | **PASS** | Expired context envelope rejected at admission |
| `R2_EXPIRED_AT_ADMISSION_search` | FIN-F01 | **FAIL** | **PASS** | Expired context at search admission clears state |
| `R2_EXPIRED_AT_ADMISSION_open` | FIN-F01 | **FAIL** | **PASS** | Expired context at open admission clears state |

**Oracle Summary:** 96 cases total $\to$ **96 PASS / 0 FAIL**.

---

## 4. Source SHA-256 Manifest & Diff

All modified files remain strictly under 200 lines adhering to ADR001:

| File Path | Lines | Pre-Fix SHA-256 | Post-Fix SHA-256 |
|---|---|---|---|
| `frontend/src/pages/copilot/actions/invoiceActionTypes.ts` | 138 | `409A11BAA8B3AB5FCF1676BBEC1DBD769897EF366F2D3F0A812D3DAB4AA1F596` | `6ADC5AEF03FE99C4F70BDFCC0BB9D1BB833C82C29452919A37C5DCD3AA9B9B2E` |
| `frontend/src/pages/copilot/actions/invoiceActionDecoderHelpers.ts` | 95 | `5896BDDD0CEEAB0937167943C4F719D24071334B0F6D2BDAD2E72882B8E5AE8E` | `10FA4FE17430EEDBE787D59C57E85753F027234BC0C8E12D080A5653F3439CF9` |
| `frontend/src/pages/copilot/actions/invoiceActionDecoders.ts` | 126 | `C159593868F879E440691DEA7677D0A82273E103B58BAF60B436465AB625A5CC` | `08649FB91D980AAD9AFC491352276C4EE61096300D006F4BF499E4AE58D6B551` |
| `frontend/src/pages/copilot/actions/invoiceActionPayloadDecoders.ts` | 121 | `C0197824E7506CC9FC8C843E0128D2AF492A92FECDE5FE4CB223D52559007C9F` | `9EF21DFBB8853E1D238E3C8A3D535C0C7D3392019C9E7F40F7EB1909C443AFB0` |
| `frontend/src/pages/copilot/actions/invoiceActionController.ts` | 150 | `EBCD3AFDA6AB3DD3DBA24D7A5F55CC15BFAB4A4095A72E0AEEDE2DBD961BF66B` | `380001AB5C7F781AA3670D44D4493677FA5C83EB0F71BEC918E20B644A64435B` |

---

## 5. Verification Commands and Raw Exit Evidence

1. **Independent Oracle Suite:**
   ```powershell
   node "E:\lotus-fin\docs\reviews\evidence\chatbot-final-integration-2026-10-12-01a1303a\fresh_oracle.mjs"
   ```
   *Exit code:* `0` (`{"counts":{"PASS":96,"FAIL":0},"failed":[]}`)

2. **Frontend Presentation & Decoder Suite:**
   ```powershell
   node --experimental-strip-types --test tests/p2b/presentation.test.ts
   ```
   *Exit code:* `0` (41 tests passed, 0 failed)

3. **Frontend Client & Controller Suite:**
   ```powershell
   node --experimental-strip-types --test tests/p2b/client.test.ts tests/p2b/controller.test.ts
   ```
   *Exit code:* `0` (25 tests passed, 0 failed)

4. **L3 Followup Preview Unit Suite:**
   ```powershell
   node --experimental-strip-types --test tests/followupPreview.test.ts tests/followupPreviewController.test.ts
   ```
   *Exit code:* `0` (20 tests passed, 0 failed)

5. **L3 Followup Preview E2E Suite:**
   ```powershell
   python -B -m pytest -p no:cacheprovider tests_e2e/test_followup_preview_e2e.py -v
   ```
   *Exit code:* `0` (1 passed in 9.26s)

6. **Full Frontend Typecheck & Lint:**
   ```powershell
   npx tsc -b --noEmit
   npx oxlint src/pages/copilot/actions/
   ```
   *Exit code:* `0` (0 errors, 0 warnings in actions)

7. **Production Vite Build:**
   ```powershell
   npx vite build
   ```
   *Exit code:* `0` (built in 5.28s)

---

## 6. Residual Blockers & Next Steps

- **Live HTTP Integration:** Requires approved private target, live Frappe CSRF/session credentials, and deployment environment clearance (owned by Work).
- **Production Transport:** Kept explicitly disabled (`invoiceActionClient.ts` continues to fail closed with `DISABLED` notice).
- **Mount Approval:** L3 preview component and P2-B invoice action panel remain unmounted from main app view pending final UI/product clearance.

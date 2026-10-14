# LOTUS FIN — CHATBOT UI SECURITY AND REGRESSION REPORT

**Document Version:** 1.0.0  
**Verification Target:** Frontend Security Standards (B1-S, P2-B, L3)  
**Execution Environment:** Node.js v22+ Subtest Runner & Playwright Headless Chromium  

---

## 1. Security Invariants and Control Matrix

| Control ID | Description | Threat Mitigated | Status | Evidence |
| :--- | :--- | :--- | :---: | :--- |
| **P2B-F01** | Empty/Partial result selection fencing | Premature / unverified record mutation | **PASS** | `presentation.test.ts` (Subtests 81-82) |
| **P2B-F06** | Read view restricted to exactly 5 fields | Sensitive financial data leakage | **PASS** | `presentation.test.ts` (Subtest 60-61) |
| **P2B-F07** | Strict DocStatus filter verification | Unauthorized invoice status exposure | **PASS** | `presentation.test.ts` (Subtest 74) |
| **P2B-F08** | Date bounds (max 365 days, calendar ISO) | Denial of Service / SQL query exhaustion | **PASS** | `presentation.test.ts` (Subtest 72) |
| **P2B-F09** | Prefix safe-text sanitation (strip control) | Script injection / header pollution | **PASS** | `presentation.test.ts` (Subtest 68, 73) |
| **P2B-F12** | Explicit selection required before Open | Accidental document mutation | **PASS** | `presentation.test.ts` (Subtest 46) |
| **B1-S** | Unqualified context suppresses outbound calls | Unauthorized exfiltration | **PASS** | `test_copilot_failclosed.py` (Subtest 1) |
| **L3-TTL** | Monotonic 10-minute client TTL | Stale / orphaned customer draft leakage | **PASS** | `followupPreview.test.ts` (Subtests 1-12) |
| **L3-GATE** | Checkbox review required before clipboard copy | Accidental unsanitized message send | **PASS** | `followupPreview.test.ts` (Subtest 14) |
| **XSS-01** | Strict text node rendering for payloads | Cross-Site Scripting (XSS) execution | **PASS** | `test_copilot_failclosed.py` (Subtest 4) |

---

## 2. Regression Test Results

### 2.1. Playwright E2E Suite (`tests_e2e/`)
```
============================= test session starts =============================
platform win32 -- Python 3.13.7, pytest-9.0.2, pluggy-1.6.0
collected 8 items

tests_e2e\test_copilot_failclosed.py::test_unqualified_context_makes_zero_post_calls PASSED
tests_e2e\test_copilot_failclosed.py::test_copilot_failclosed_normalization_scenarios PASSED
tests_e2e\test_copilot_failclosed.py::test_scope_presentation_clear_and_unqualified_claims PASSED
tests_e2e\test_copilot_failclosed.py::test_xss_injection_rendered_safely_as_text PASSED
tests_e2e\test_followup_preview_e2e.py::test_followup_preview_e2e_lifecycle PASSED
tests_e2e\test_invoice_actions_e2e.py::test_p2b_invoice_search_select_open_flow PASSED
tests_e2e\test_invoice_actions_e2e.py::test_p2b_invoice_empty_and_partial_results PASSED
tests_e2e\test_invoice_actions_e2e.py::test_p2b_invoice_scope_switch_clears_state PASSED

============================= 8 passed in 47.27s ==============================
```

### 2.2. Unit & Presentation Regression Suite (`frontend/tests/`)
- `frontend/tests/p2b/presentation.test.ts`: 32/32 passed.
- `frontend/tests/p2b/controller.test.ts`: 18/18 passed.
- `frontend/tests/p2b/client.test.ts`: 16/16 passed.
- `frontend/tests/followupPreview.test.ts`: 14/14 passed.
- `frontend/tests/followupPreviewController.test.ts`: 6/6 passed.
- `frontend/tests/p3_transport_and_demo.test.ts`: 9/9 passed.
- **Combined:** 95/95 passed in 778ms.

---

## 3. L3 Followup Preview Controls Verification

The L3 Followup local drafter is mounted in `VercelChatPanel` under the `Followup (L3)` tab:
1. **Unsaved / Unsent Status**: Explicit badge `UNSAVED / UNSENT DRAFT` displayed at all times.
2. **Review Gating**: The "Copy to Clipboard" button remains disabled until the operator checks `[x] I have reviewed this draft`.
3. **Monotonic TTL**: Countdown begins at 600s (10 min). Upon reaching zero, content is wiped and replaced with `EXPIRED` notice.
4. **Scope Isolation**: When the `company` scope or `scopeEpoch` changes, active text and review status are discarded immediately.
5. **Zero Network Transmission**: Tested with Playwright network guard; zero POST/GET requests dispatched during preparation, editing, copying, or discarding.

---

## 4. XSS and Input Sanitization Verification

During `test_xss_injection_rendered_safely_as_text`, the payload:
```html
<script>window.__xss_executed = true;</script><img src='invalid' onerror='window.__xss_executed=true' /><a href='javascript:alert(1)'>click me</a>
```
was supplied to the message renderer.
- **Result:** `window.__xss_executed` was verified `undefined`.
- **DOM Inspection:** Rendered strictly as escaped text content (`CopilotMessageBody`), preventing tag execution or attribute-based scripting.

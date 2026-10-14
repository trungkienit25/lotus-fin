# P2-A Frontend Integration Handoff

**Date:** 12 October 2026  
**Timezone:** Asia/Saigon  
**Branch:** `codex/p2a-invoice-read-backend`  
**HEAD:** `5f805ef34f788245a3ec0e9c2f44e224eb16c305`  
**Status:** Read-only inspection complete; zero frontend lines modified.

---

## 1. Frontend Preservation Policy

In accordance with Section 10 of the Master Implementation Directive:
- **No Frontend Edits:** All files in `frontend/` were inspected strictly read-only.
- **Agent Boundary:** Ownership of frontend source and P2-B tests is retained by the P2-B correction agent.

---

## 2. Identified Integration Seam & Entrypoint

The proposed production integration path connects the Lotus React Copilot UI to the hardened backend:

```
Lotus Copilot Page (frontend/src/pages/copilot/LotusCopilotPage.tsx)
       │
       ▼
InvoiceActionPanel (frontend/src/pages/copilot/actions/InvoiceActionPanel.tsx)
       │
       ▼
useInvoiceActions / invoiceActionController.ts
       │
       ▼
invoiceActionClient.ts (createProductionTransport)
       │
       ▼
Authenticated Lotus API (/api/method/lotus_fin.api.invoice_actions_api.*)
```

### Current Transport Status in `invoiceActionClient.ts`:
The production transport in [invoiceActionClient.ts](file:///e:/lotus-fin/frontend/src/pages/copilot/actions/invoiceActionClient.ts) is disabled by design (`status: 503, reason_code: "CAPABILITY_DISABLED"`).
Even when `VITE_LOTUS_INVOICE_ACTIONS=on`, it suppresses network calls to prevent unauthenticated or non-CSRF traffic until full platform qualification is complete.

---

## 3. Handoff Checklist for Frontend Team (P2-B)

When the N0 Native Authority gate is unblocked and backend endpoints are enabled:

1. **Wire Contract Alignment:**  
   The backend adheres strictly to the frozen `CHATBOT_P2B_WIRE_CONTRACT.md`. All response payloads match `ContextDataDTO`, `SearchResponseDataDTO` (`InvoiceReadPage`), and `OpenResponseDataDTO`.
2. **Date String Round-Trips:**  
   Backend DTOs now accept and emit canonical ISO date strings (`YYYY-MM-DD`). The frontend decoders in `invoiceActionDecoders.ts` will parse these cleanly without type coercion discrepancies.
3. **Transport Enablement:**  
   Replace the disabled stub in `invoiceActionClient.ts` with an authenticated `fetch` transport that includes:
   - `X-Frappe-CSRF-Token: frappe.csrf_token`
   - `credentials: "same-origin"`
   - `Content-Type: application/json`
4. **No Legacy Routing:**  
   Do not introduce Desk routes (`/app/sales-invoice/...`) or ERPNext navigation bars. The read viewer must render purely inside the Lotus React surface (`InvoiceReadView.tsx`).
5. **No Production Fixture Mounts:**  
   Synthetic browser fixtures (`tests_e2e/copilot_fixture/`) must remain confined to test configurations; production builds must never intercept or mock API endpoints.

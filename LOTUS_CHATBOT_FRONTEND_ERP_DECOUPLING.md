# LOTUS FIN — FRONTEND ERP DECOUPLING & ROUTE AUDIT REPORT

**Date:** 2026-10-13  
**Status:** COMPLETE (CORE INDEPENDENT, LEGACY UNQUALIFIED)  
**Security Boundary:** Frappe Core Independent Runtime (Zero ERPNext Coupling)  
**Target Milestone:** P3 Chatbot Product Completion  

---

## 1. Executive Summary & Architectural Principles

Lotus Fin operates under the strict architecture mandate: **Independent from ERPNext ("Build Now, Data Later")**.
- **Frappe Framework** is the underlying application framework.
- **ERPNext application**, its DocTypes (`Sales Invoice`, `Company`, `GL Entry`, `Lead`, `POS Profile`), reports, and RPC endpoints are **NOT** required and **NOT** dependencies of Lotus Fin Core.
- The user interface must never present legacy ERPNext features as functional native Lotus capabilities, nor fabricate synthetic business records when ERPNext data sources are absent.
- Legacy capabilities must be presented as explicitly **UNQUALIFIED** or **OPTIONAL** until native Lotus financial implementations are qualified.

This audit evaluates the entire React route graph, dynamic page loaders, RPC endpoints, and company context selectors across `frontend/src/**` to document decoupling status and surface backend authorization boundaries.

---

## 2. Inventory of ERP-Coupled Touchpoints & Decoupling Actions

### 2.1 Route Graph Audit (`frontend/src/App.tsx`)

| Route Pattern | Target Component | Legacy ERP Dependency | Decoupling Status in Lotus Fin Core |
|---|---|---|---|
| `/` or `/home` | `ModuleSelectorHome` | Desk module grid | Decoupled; displays available Lotus Fin modules. |
| `/ai`, `/copilot`, `/workspace/Lotus Fin AI` | `LotusCopilotPage` | Copilot & AI financial assistant | **100% Decoupled Core**; operates with native Frappe Core transport + isolated demo mode. |
| `/workspace/:workspaceName` | `UniversalWorkspaceView` | ERPNext workspaces (`Invoicing`, `Buying`, `Selling`, `Stock`) | Unqualified observation; loads only schemas present in Frappe site. |
| `/report/:reportName` | `UniversalReportView` | ERPNext reports (`General Ledger`, `Trial Balance`, `Accounts Receivable`) | Unqualified observation; executes via Frappe `query_report.run`. Fails truthfully with server error if DocType/report is absent; no synthetic data fabricated. |
| `/page/:pageName` | `UniversalPageView` | ERPNext pages (`sales_funnel`, `point_of_sale`, `permission-manager`) | **Decoupled & Guarded**; legacy RPC failures intercepted with explicit notice banners. Conditional hooks fixed. |
| `/app/:doctype*` | `UniversalListView` / `UniversalFormView` | Generic Frappe/ERPNext DocTypes | Generic framework renderer; respects Frappe DocType availability. |

---

### 2.2 Dynamic Pages Audit (`frontend/src/pages/dynamic/UniversalPageView.tsx`)

`UniversalPageView.tsx` handles specialized dynamic pages. During P3 audit and remediation, the following touchpoints were decoupled:

1. **Sales Funnel RPC (`sales_funnel`):**
   - **Legacy RPC:** `/api/method/erpnext.selling.page.sales_funnel.sales_funnel.get_funnel_data`
   - **Decoupling Action:** Caught in `fetchFunnelData` catch handler. Added banner:
     ```typescript
     setFunnelNotice(
       "Sales Funnel: Legacy ERPNext module is not connected to Lotus Fin Frappe Core. " +
       "Independent native sales funnel tracking is scheduled for a future milestone."
     );
     ```
   - **Behavior:** Values remain default 0; no fake leads or conversion numbers are fabricated.

2. **Point of Sale RPC & Schema (`point_of_sale`):**
   - **Legacy Schema & RPC:** `/api/resource/POS Profile`, `/api/method/frappe.client.get_count?doctype=POS Invoice`
   - **Decoupling Action:** Intercepted in `fetchPosData` catch handler. Added banner:
     ```typescript
     setPosNotice(
       "Point of Sale: Legacy POS profile RPC is unlinked in Lotus Fin Independent Core."
     );
     ```
   - **Behavior:** POS Profile list remains empty; count displays 0 without crashing.

3. **Company Context Fetching:**
   - **Legacy Schema:** `/api/resource/Company`
   - **Decoupling Action:** Initialized with default state `["Lotus Fin Core"]` and `selectedCompany = "Lotus Fin Core"`. If Frappe returns 404/empty for `Company`, the UI smoothly falls back to `"Lotus Fin Core"`, preventing blank page crashes.

4. **Conditional React Hooks Fix:**
   - Fixed 16 conditional hook violations (previously wrapped inside `if (isAiPage) return <LotusCopilotPage />`). All 18 top-level hooks (`useState`, `useParams`, `useNavigate`, `useTranslation`, `useEffect`) now execute unconditionally, preserving React rendering invariants.

---

### 2.3 Copilot Application Audit (`frontend/src/pages/copilot/**`)

1. **Branding & Claims Decoupling (`LotusCopilotPage.tsx`):**
   - **Legacy Claim:** *"Real-time ERPNext General Ledger reconciliation"*
   - **Decoupled Claim:** *"Lotus Fin Independent Financial Core"*
   - **Company Scope:** Uses `"Lotus Fin Core"` fallback context instead of assuming an ERPNext `Company` entity exists.

2. **Starter Suggestions & Quick Cards (`VercelChatPanel.tsx`):**
   - Quick pills (`Financial Health`, `Cash Forecast 30D`, `Risk Signals`, `What-If Studio`) and starter action cards are maintained under unqualified observation context.
   - In CORE mode without qualified N0 data authority, cards remain disabled with tooltip:
     `title="Unavailable under unqualified observation context"`
   - Asserted and verified by Playwright gate `tests_e2e/test_copilot_failclosed.py`.

3. **HTTP Transport & Invoice Actions (`invoiceActionClient.ts`):**
   - Action transport calls `/api/method/lotus_fin.api.invoice_actions_api.search_invoices` and `/open_invoice`.
   - In Frappe-only CORE runtime without N0, server responds with `503 Service Unavailable` (`CAPABILITY_DISABLED`).
   - Client decodes this truthfully via `InvoiceActionError` (`CAPABILITY_DISABLED`), surfacing:
     `"Native financial data integration (N0) is currently blocked or unavailable."`
   - Zero synthetic rows or fake signed references are minted in CORE mode.

4. **Synthetic Demo Isolation (`demoInvoiceProvider.ts`):**
   - Completely decoupled from both ERPNext and CORE runtime.
   - All records are fictional (`DEMO-SINV-2026-001`, `002`, `003`), labeled `source_identity: "DEMO_ISOLATED"`, and tagged with visible badge `DEMO DATA`.

---

## 3. Server-Side Security & Generic Framework RPC Seam

> [!WARNING]
> **Hiding or decoupling UI routes in React does NOT secure Frappe backend endpoints.**
> Hiding an ERPNext route on the frontend does not prevent an authenticated user or attacker from directly issuing HTTP requests to backend endpoints.

### 3.1 Backend Vulnerability Surface in Frappe Framework

When running Frappe Framework without ERPNext:
1. **Generic Resource Endpoints (`/api/resource/:doctype`):**
   - Frappe provides automatic REST CRUD for any DocType via `/api/resource/:doctype`.
   - If an ERPNext DocType (e.g., `Sales Invoice`) is NOT installed on the site, Frappe correctly returns HTTP `404 Not Found` (`frappe.exceptions.DoesNotExistError`).
   - However, any core Frappe DocTypes (`User`, `Role`, `Custom DocPerm`, `File`, `Version`, `System Settings`, `Activity Log`) remain exposed to users with matching Frappe roles.
2. **Generic Method Endpoints (`/api/method/frappe.client.*`):**
   - `frappe.client.get_list`, `frappe.client.get_value`, `frappe.client.get_count`, and `frappe.client.set_value` are standard whitelisted Frappe framework methods.
   - Any authenticated user session can invoke these methods unless Frappe Permission Manager explicitly restricts Read/Write permissions on the target DocTypes.
3. **Legacy Whitelisted Methods:**
   - Any Python method decorated with `@frappe.whitelist()` is callable via `/api/method/<module>.<method>`.
   - In a Frappe-only setup, legacy `erpnext.*` methods are not present and will return HTTP `404 Method Not Found` or `ImportError`.

### 3.2 Formal Security Recommendations for Backend / Platform Owner (Work)

To ensure true fail-closed security at the transport and API gateway layer:
1. **API Gateway / Nginx Routing Restriction:**
   - Block or deny generic `/api/method/frappe.client.*` calls from untrusted frontend clients, or restrict them to explicit read-only queries with strict DocType whitelists.
2. **Frappe Role-Based Access Control (RBAC):**
   - Audit all roles assigned to Lotus Fin users (`Desk User`, `Lotus User`).
   - Ensure the `Guest` role has zero read/write permissions on `/api/resource/*` and `/api/method/lotus_fin.*`.
3. **Session Fencing & CSRF Enforcement:**
   - All Lotus Fin POST methods (including `invoice_actions_api.py`) must continue enforcing `frappe.session.user != "Guest"` and validate `X-Frappe-CSRF-Token` headers.
4. **Do Not Rely on Client State:**
   - The backend must never accept client-asserted profile parameters (such as `profile="DEMO"` or `mock=true`) to bypass security checks or return fake data in production mode.

---

## 4. Decoupling Status Summary Matrix

| Domain | Prior State | P3 Decoupled State | Verification / Safety |
|---|---|---|---|
| **Sales Funnel Page** | Direct call to `erpnext.selling...`, crashed on failure | Graceful fallback banner `funnelNotice`, 0 metrics | Unconditional hooks, 0 crash |
| **Point of Sale Page** | Direct call to POS Profile and POS Invoice | Graceful fallback banner `posNotice`, 0 metrics | Unconditional hooks, 0 crash |
| **Company Selector** | Hard dependency on ERPNext `Company` DocType | Default `"Lotus Fin Core"`, safe fallback | No missing company crash |
| **Copilot Branding** | Advertised "ERPNext General Ledger reconciliation" | "Lotus Fin Independent Financial Core" | Brand SSOT aligned |
| **Financial Search** | Risk of mock fallback or ERPNext DocType query | Truthful 503 `CAPABILITY_DISABLED` mapping | Zero synthetic records in CORE |
| **Demo Environment** | Mixed or absent | Strict `DEMO_ISOLATED` synthetic provider | Isolated profile, explicit badge |
| **Conditional Hooks** | 16 ESLint conditional hook violations | 0 violations; top-level unconditional order | Oxlint & Vite build pass cleanly |

---

## 5. Conclusion

Frontend decoupling of ERPNext dependencies in Lotus Fin Core is **COMPLETE**. The frontend operates autonomously on Frappe Framework without any functional requirement on ERPNext schemas, DocTypes, or RPCs. Legacy pages are safeguarded with explicit notices, and CORE financial operations fail closed truthfully when N0 data authority is unavailable.

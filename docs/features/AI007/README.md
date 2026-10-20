# AI-F007 — RECEIVABLES RECOVERY & ACTION-ASSISTED COPILOT (AI007)

> **Feature Identifier:** `AI007` / `AI-F007`  
> **Status:** Implemented & Verified  
> **Computation Class:** Deterministic Invoice Matching + Level 4 Two-Phase Commit + Grounded Synthesis  
> **Target Module:** `lotus_fin.modules.f007_copilot` / `lotus_fin.api.invoice_actions`  

---

## 1. Feature Overview
Assists accounting personnel in tracking delinquent customer accounts, searching past-due invoices, drafting payment reminder notices, and dispatching statements via SMTP.

### Capabilities
- **Invoice Search & Aging Inquiry:** Fast-path lookup of outstanding and past-due sales invoices filtered by customer, due-date buckets, and payment status.
- **Statement & Notice Generation:** Generates professional, compliant payment reminder notices populated with real invoice numbers, due dates, outstanding amounts, and payment references.
- **Level 4 Two-Phase Commit (Human-in-the-Loop):** External dispatches (e.g., emailing a customer reminder) generate an interactive preview card in the UI requiring explicit user confirmation before executing.

---

## 2. Architectural Invariants
1. **Human-in-the-Loop Safeguard:** The AI Agent is strictly prohibited from autonomously transmitting external emails or updating invoice records without explicit operator confirmation.
2. **Deterministic Ledger Anchoring:** All amounts and references in reminder notices are anchored to verified database records.
3. **Template Injection Sanitization:** Template strings and email payloads undergo strict HTML and script tag neutralization before presentation or dispatch.


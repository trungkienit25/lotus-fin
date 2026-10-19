# APPLICATION SECURITY & IDENTITY SPECIFICATION REPORT
## Application Security, Zero-Trust Multi-Tenancy & Cryptographic Token Governance

> **Project Name:** Lotus Fin — SME Financial Management Core with AI Key Report Pipeline  
> **Competition:** The 2026 Shenzhen International FinTech Competition — WeBank FinTech University Challenge (Topic E)  
> **Version:** 3.0 (Technical Deep-Dive, Quantitative Metrics & Implementation Aligned)  
> **Methodology:** `Problem` $\to$ `Solution` $\to$ `Implementation Blueprint` $\to$ `Verification Evidence`  
> **Reference Standards:** OWASP Top 10 API Security (2023), NIST SP 800-53 Rev. 5 (AC - Access Control, IA - Identification and Authentication)  

---

## 1. APPLICATION SECURITY ARCHITECTURE OVERVIEW

The application tier of Lotus Fin safeguards enterprise accounting ledgers and analytical calculations across all customer boundaries. Every incoming client request must successfully traverse five strict authorization and validation checkpoints before touching financial persistence layers:

```
[ Incoming Browser / Client Request ]
                 │
                 ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 1. SESSION AUTHENTICATION & ANTI-CSRF GATE                             │
│    - Direct DB verification of user `enabled` status (Cache bypassed)  │
│    - Mandatory `X-Frappe-CSRF-Token` verified in constant time         │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 2. ZERO-TRUST MULTI-TENANT BOUNDARY (IDOR Prevention)                  │
│    - Client-supplied `company` parameter treated as untrusted input    │
│    - Mandatory server-side validation against `tabUser Permission`     │
│    - Immediate fail-closed `CompanyAccessError` on unauthorized scope  │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 3. ROLE-BASED ACCESS CONTROL (RBAC Module Matrix)                      │
│    - Financial modules F001-F007 bound to strict role entitlements     │
│    - High-risk operations (L5) fail-closed with absolute rejection     │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 4. CRYPTOGRAPHIC REFERENCE TOKENIZATION (HMAC Document References)    │
│    - Wire Format: `ref.v2.<Claims>.<HMAC-SHA256>`                      │
│    - Verification: 300s TTL, Actor Hash, Session Hash, Record Version  │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 5. QUERY RESOURCE BOUNDS & EXECUTION BUDGETS                           │
│    - Page Size: Max 50 | Date Range: Max 365 Days | Deadline: 5.0s     │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. APPLICATION SECURITY CONTROLS & IMPLEMENTATION BLUEPRINTS

### 2.1. Session Authentication & Anti-CSRF Protection

#### Problem
Cross-Site Request Forgery (CSRF) vulnerabilities allow malicious third-party websites to exploit an authenticated user's active session, issuing unauthorized financial mutations (such as posting unauthorized journal entries or creating tasks) without the user's consent. Furthermore, relying solely on cached session data allows deactivated user sessions to remain active until cache expiration.

#### Solution
1. **Direct Session Status Verification:** The application request hook queries the persistent database directly to confirm the user account is currently active (`enabled = 1`), bypassing transient in-memory caches.
2. **Mandatory Anti-CSRF Token Matching:** All state-mutating HTTP methods (POST, PUT, DELETE) require a valid `X-Frappe-CSRF-Token` header. Token comparison is performed strictly using constant-time digest comparison to prevent side-channel timing attacks.

#### Implementation Blueprint
* **Request Lifecycle Interceptor:**
  * Intercept incoming HTTP calls prior to RPC dispatch.
  * Extract the session identifier from the secure HTTP-only cookie and resolve the active user identity.
  * Execute a targeted database query checking user status; if disabled, immediately terminate the session and return HTTP 403 Forbidden.
* **Constant-Time Token Validation:**
  * Retrieve the cryptographic CSRF token tied to the current session from Redis.
  * Compare the incoming header token against the session token using constant-time string comparison (`hmac.compare_digest`).
  * If the comparison fails or the token is absent, abort the request with HTTP 400 Bad Request.

---

### 2.2. Role-Based Access Control (RBAC) & Multi-Tenant IDOR Guard

#### Problem
Insecure Direct Object Reference (IDOR / BOLA - Broken Object Level Authorization) occurs when an authenticated user modifies a request payload (e.g., altering `company="Acme Corp"` to `company="Competitor Ltd"`) to view confidential balance sheets, cash projections, or overdue invoice registers belonging to another enterprise.

#### Solution
1. **Zero-Trust Parameter Principle:** Client-supplied enterprise identifiers (`company`) are never trusted. All access is verified server-side against authorized company allocations recorded in the framework's user permission tables.
2. **Fail-Closed Company Boundary Enforcement:** The application gateway executes a mandatory company validation check on every financial endpoint. Any unauthorized company request triggers an unhandled `CompanyAccessError`, terminating execution immediately.
3. **Module-Level RBAC Matrix:** Each analytical module requires explicit role assignments:

| Module Identifier | Capability / Service | Minimum Required Role | Enforcement Mechanism |
| :--- | :--- | :--- | :--- |
| **F001** | Executive Financial Snapshot | `Accounts User`, `Accounts Manager` | Access Gateway company verification |
| **F002** | 30-Day Cash Flow Forecast | `Accounts Manager`, `Auditor` | Strict report allowlist (`check_ai002_report_permission`) |
| **F003** | Risk Signal Monitoring (AR/AP) | `Accounts User`, `Accounts Manager` | Security registry allowlist (`MODULE_SECURITY_REGISTRY["f003"]`) |
| **F004** | Multivariate What-If Stress Studio | `Accounts Manager`, `System Manager` | Scenario engine tenancy & policy validation |
| **F005** | Commercial Banking Loan Matcher | `Accounts User`, `Bank Officer` | Commercial underwriting profile constraints |
| **F006** | Loan Amortization & Rate Shock | `Accounts User`, `Accounts Manager` | Pure mathematical domain calculator validation |
| **F007** | Customer Debt Reminder Drafting | `Accounts User`, `Accounts Manager` | Invoice authorization context verification |
| **L4** | Operational Task Mutation | `Accounts Manager`, `System Manager` | Two-Phase confirmation challenge verification |
| **L5** | Autonomous High-Risk Side Effects | **STRICTLY FORBIDDEN (ALL DENIED)** | Fail-closed policy review (`CAPABILITY_DISABLED`) |

#### Implementation Blueprint
* **Company Access Gateway:**
  * Intercept the target company identifier within the security facade.
  * Query the user permission repository matching the authenticated user ID and the target company string.
  * If no matching permission row exists, raise `CompanyAccessError` and log a security audit event.
* **Role Verification:**
  * Evaluate active role memberships for the current user session against the module's authorized role list.
  * Deny access with descriptive audit logging if the user lacks the required role level.

---

### 2.3. Opaque HMAC Document Tokenization (`InvoiceReferenceV2Codec`)

#### Problem
Exposing sequential database keys or predictable document identifiers (e.g., `ACC-SINV-2026-00001`) allows malicious actors to systematically enumerate and scrape private corporate invoices by altering the identifier string.

#### Solution
Lotus Fin generates **Opaque HMAC Reference Tokens** for all invoice references passed to client browsers. Each reference is cryptographically signed using `HMAC-SHA-256` and bound to the user's specific operational context.

```
Wire Format:
ref.v2.<Base64Url(Payload_Claims)>.<Base64Url(HMAC_Signature)>
```

*Signed Payload Claims Structure:*
* **Binding Version:** Opaque actor protocol version (`opaque-actor.v1`).
* **Purpose:** Specific intended operation (e.g., `invoice.open`, `invoice.cursor`).
* **Cryptographic Identity Hashes:** One-way HMAC hashes of the actor ID and session ID (`aref_...`, `sref_...`).
* **Context Scope:** Exact identifiers for site, company, and schema projection version.
* **Record Integrity:** Specific document ID and optimistic concurrency revision tag (`record_version`).
* **Temporal Window:** Absolute UNIX timestamps for issuance (`issued_at`) and expiration (`expires_at`).

#### Implementation Blueprint
* **Token Issuance:**
  * Serialize the claims into canonical JSON (sorted keys, compact separators).
  * Generate an HMAC-SHA256 signature using the server's master signing secret.
  * Encode claims and signature with URL-safe Base64 without padding, joining them with a `ref.v2.` prefix.
* **Token Verification & Context Binding:**
  * Validate token format and enforce a strict 2,048-character length ceiling.
  * Verify the cryptographic signature using constant-time comparison.
  * Compare the token's claims against the current active context: verify that the token's actor hash and session hash match the current caller. If an attacker copies a token into another session, reject with `Scope mismatch`.
  * Validate token lifetime: enforce a maximum Time-To-Live (TTL) of 300 seconds.
  * Verify optimistic record concurrency: compare `record_version` against the current database state; reject with `Stale read` if the invoice has been modified concurrently.

---

### 2.4. Query Resource Bounds & Denial-of-Service Guardrails

#### Problem
Unconstrained query parameters (such as requesting all invoices across a 10-year span or fetching 50,000 rows in a single request) can exhaust database memory and monopolize thread pools, causing system-wide denial of service.

#### Quantitative Guardrails Blueprint
Lotus Fin enforces hard resource limits at the invoice reading adapter:

| Parameter / Resource | Default Value | Hard Maximum Ceiling | Enforcement Behavior |
| :--- | :--- | :--- | :--- |
| **Page Size** | 20 records | **50 records** | Reject requests exceeding 50 with validation error |
| **Date Query Window** | 90 days | **365 days** | Reject query if `end_date - start_date > 365` |
| **Future Date Policy** | Current Date | Disallowed | Reject any query with `posting_date > Today` |
| **Cursor Pagination Depth** | 1 page | **5 consecutive pages** | Mark `incomplete_coverage = true` and halt scan |
| **Document Scans per Query** | 20 documents | **51 checks** | Abort query loop to protect database CPU |
| **Detail Reads per Selection** | 1 record | **1 record** | Restrict detail resolution strictly to selected ID |
| **Provider Payload Ceiling** | - | **256 KiB** | Terminate upstream connection if data exceeds cap |
| **Response Envelope Ceiling** | - | **64 KiB** | Enforce optimal payload size for frontend delivery |
| **Query Execution Timeout** | 3.0 seconds | **5.0 seconds** | Terminate socket if database fails to return within 5s |

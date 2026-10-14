# Platform to QA

13 October 2026, Asia/Saigon. Evidence: `docs/reviews/evidence/frappe-only-2026-10-13-01a13314`. No commit, push or production deployment.

**CORE_RUNTIME_READY; FULL_PRODUCT_INDEPENDENCE remains blocked by native data/N0.**
Review `VERDICTS.json`, both real HTTP result files, `RUNTIME_COMMANDS.json`,
`IMAGE_SOURCE_INTEGRITY.json`, final source manifest/archive integrity and shared
service preservation evidence. Reproduce from the archive using the runbook.
Framework serving is already qualified; do not hold its acceptance on N0.

| QA track | Evidence/status |
| --- | --- |
| CORE | Frappe-only serving, site/install/import/hash/worker/health/auth/session/CSRF/legacy-denial/cold-start PASS in isolated stack |
| DEMO | Offline typed contracts and preview lifecycle tests PASS; synthetic ports are never native authority |
| NATIVE | No approved business source or membership/document/field policy; disabled HTTP is real, successful financial data is NOT_VERIFIED |

## Data adapter design for later integration

Use the existing frozen `IReadAuthorizerPort` to resolve server-owned principal,
tenant/company, capability and document authority. Use `IAuthorizedInvoiceReadPort`
for bounded search/exact projected read. `AuthorizedReadContext`,
`InvoiceReadFilters`, `InvoiceReadPage`, `InvoiceReadDocument`, `SourceEvidence`,
record version and shared I/O budget are the typed seam. Search/Open services
already accept the port through dependency injection; do not add an arbitrary
DocType/report/SQL parameter to the public API.

When N0 is available, implement a separately reviewed read adapter to that approved
source and compose it explicitly with the authorizer, context/reference services,
framework session storage and required audit sink. Declare source identity/version,
approved field projection, tenant/document/field grants, freshness/version checks,
all read/metadata/permission I/O budgets and fault mapping. Metadata and record
reads must share the same budget and actual principal. No Company/Sales Invoice
schema default, second ledger, ERPNext fallback, synthetic success, Administrator
switch or silent missing-data-to-zero conversion is permitted.

Until then the current API admission remains strict and financial capabilities
return explicit CAPABILITY_DISABLED. Missing source/permission/version/policy
must stay an explicit error/unavailable outcome. The core runtime needs no
business signing secret or source credentials merely to start.

Later NATIVE qualification must prove ordinary-user positive reads, cross-tenant
and field denial, freshness/revocation, audit durability, physical read cancellation,
production frontend mount and business-data backup/restore. These are outstanding
business-integration gates, not blockers to the completed core serving path.
Optional legacy ERP integration stays separately unqualified.

No source commit/push, production deployment or volume deletion is authorized.

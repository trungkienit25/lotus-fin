# P6 security integration

The integrated endpoint reuses P6-0's persisted User.enabled and tabSessions checks plus Frappe and runtime-hook CSRF enforcement. Every request revalidates its principal and role set. No client actor/session/company authorizes a server operation. Server DEMO enablement is independent from the client profile. CORE returns no fictional business result.

The client bootstraps the current cookie session before each integration call. It fences responses on actor, opaque epoch, generation, site and product. Feature components unmount on profile/actor/session changes; pending callbacks are discarded, draft transfer state clears, and L3 includes profile in its scope. Invoice controllers retain their existing reference/context validation. No P6-0 lifecycle source was overwritten.

Simulation storage partitions by server-derived site, actor and session binding. A SQLite immediate transaction serializes workers and commits audit, proposal state, challenge consumption and fictional receipt together. Audit insertion must succeed before operation admission; any error rolls back and returns UNAVAILABLE. This store is exclusively synthetic, and its persistence does not qualify a native ledger. Session identifiers are one-way bound internally and redacted from responses.

L4 native write and all L5 side-effect adapters remain unreachable. Integrated L5 offers policy review with unavailable/denied approval status; it does not mint approvals, review challenges or execution capabilities. No scheduler job, email, payment, submit or cancel is performed. Textual confirmation only opens a review view. L4's expired/cancelled proposal, canonical digest and current role checks remain server-side.

Residual limits: retained module code has architectural debt (including original L4 files over the ADR line limit); full legacy collection mismatch remains unresolved. Current complete graph and dependency advisory qualification are required before push/release. Test evidence is builder evidence, not independent session/security acceptance.

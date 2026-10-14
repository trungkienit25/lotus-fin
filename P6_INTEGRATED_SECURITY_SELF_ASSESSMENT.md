# Integrated security self-assessment

INV-01/02/06/09: execution authority is server-side, tenant/session-bound and allowlisted. LLM is not an execution decision maker; this integration uses a bounded deterministic router. No database/bank credentials reach the assistant UI.

INV-03/04/08: fictional data is explicitly marked DEMO, native missing sources remain unavailable, and presentation uses React text nodes. L3 is user-reviewed text without verified finance claims. V1 monetary predicate uses deterministic decimal arithmetic in the module.

INV-07: real bank writes, L4 writes and L5 side effects remain blocked. Demo receipts are simulation-only. No approval signer, product-policy approval or N0 clearance was created.

Session invalidation and stale response fencing are covered by Node contracts and module tests; runtime browser acceptance is recorded separately. Audit failure, expired proposals, scope swaps, repeat/concurrent confirmation and UNKNOWN_OUTCOME reconciliation are exercised by test_copilot_full_integration.py.

This is a builder self-assessment. Native authority, full product independence, advisory closure, complete graph review and independent G10 qualification cannot be marked PASS from DEMO or mocked tests.

Recovery qualification adds 15 actual HTTP checks before/after cold restart and browser Alice→external logout→Bob protected-state clearing. It does not independently establish a remote revocation timing SLA or refresh correctness of legacy account-header identity caching in another tab. The isolated low-disk profile disables Redis dumps/AOF, caps container logs, and preserves only the approved site's required data. Current image/source match is verified separately; it does not waive the unresolved HIGH/CRITICAL graph/advisory and legacy collection gates.

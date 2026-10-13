# P6 security recheck — P6_SECURITY_BLOCKED

Independent review, 13–14 October 2026, Asia/Saigon. Current dirty/untracked candidate at `E:/lotus-fin`, HEAD `5f805ef34f788245a3ec0e9c2f44e224eb16c305`. Existing isolated site `core-p6-01a1358e.localhost`, loopback 8114. No production-source correction, staging, commit, push or deployment was performed. Only fictional QA sessions and simulation receipts were exercised; accounts and business records were preserved.

**P4-F01 is not closed.** External logout and actor replacement now clear both mounts after cookie/focus revalidation, but remote revocation while the same actor cookie remains is still broken. A stale asynchronous session bootstrap also restores revoked authority state. These are required presentation/session gates; this review did not demonstrate native financial disclosure or a bypass of the server's persisted authentication boundary.

## Blocking session findings and correction batches

**P6-IA01 · P1 · Active-tab remote invalidation is not detected.** `frontend/src/providers/sessionScope.ts:223` (`startPeriodicRevalidation`) checks `user_id`, then performs no server request for a VERIFIED scope when that cookie still equals the actor. HttpOnly SID changes, server revocation, account disable and same-user rotation can leave that cookie unchanged. Independent source probe ran 100 ticks with zero fetches. On the actual Drawer, Bob's three sessions were revoked using Frappe's `delete_session`; remaining sessions were zero. With `document.hidden=false`, three rows and one document remained, and an old selection opened DEMO-SINV-2026-002. The active Page repeated this failure after Alice's three sessions were revoked. New selection request IDs are in `BROWSER_OBSERVATIONS.json`.

Correction batch IA01: change only the session poll/revalidation admission policy and its focused regressions. Periodically verify the authoritative session even when the readable actor cookie is unchanged; use a bounded refresh interval and fail-closed freshness deadline. Invalidate the shared scope before admitting DEMO reads when freshness is lost. Preserve the existing keyed mounts/controllers. Replay server revocation, disable and same-user SID replacement on both visible surfaces without reload. Do not add another identity store or finance adapter.

**P6-IA02 · P1 · A late bootstrap resurrects revoked scope.** `frontend/src/providers/sessionScope.ts:148` (`fetchServerSession`) and `:113` (`markSessionVerified`) do not fence publication by the generation captured before fetch/hash. The independent probe starts a deferred bootstrap, calls `markSessionRevoked`, then delivers the old valid Alice response: the final scope becomes VERIFIED/Alice. `bootstrapSession` checks its own generation only after the shared store has already been mutated. The supplied “delayed response” test calls `assertSessionGeneration` directly and does not deliver a delayed `/copilot/session` response through this path.

Correction batch IA02: add a captured invalidation/request generation to bootstrap publication, check it after each asynchronous boundary including epoch derivation, and ensure coalesced requests cannot be inherited by a newer scope. Old completions must neither publish VERIFIED nor revoke a newer valid scope. Add tests that resolve an actual deferred bootstrap and deferred digest after logout/new actor verification. Keep all existing protected-response tests.

GitNexus impact for `fetchServerSession` is **CRITICAL**, with three direct callers (`bootstrapSession`, `revalidateSessionScope`, `startPeriodicRevalidation`), 12 upstream symbols and eight affected process groups, including integration requests and authentication. This is a warning for the future correction; LOW shared axes do not waive it. No product function was edited. Complete impact evidence is retained.

## HTTP, execution and outcome recheck

| Boundary | Independent result |
| --- | --- |
| Two ordinary actors and two distinct Alice HTTP sessions | Login/bootstrap pass; cross-actor and cross-session L4 confirmation denied |
| Guest and logged-out cookie replay | 401; old bootstrap and operation denied |
| Missing/invalid CSRF | Actual framework 400; no retry or fabricated success |
| GET integration endpoint | 403 POST-only denial |
| SPA/bootstrap/CORE denial and framework errors | Actual no-store headers present; examined responses contain no traceback |
| CORE plus DEMO header/query | Four integration actions remain 503, without fictional rows/receipts |
| Forged actor/session/company/adapter/simulated fields | Strict DTO rejects all five with 400 |
| L4 wrong challenge, duplicates and four concurrent confirmations | Wrong challenge denied; one operation ID and one execution attempt for concurrent/replayed confirmation |
| Durable simulation and process crash | Rollback before atomic commit; new-process UNKNOWN_OUTCOME persists and reconciles without re-execution |
| Audit failure | SQLite trigger rejects admission; no simulation is committed |
| L5 review/send/submit/cancel/payment/scheduler | Catalog decisions deny; arbitrary execution actions reject; four advertised unregistered L5 routes return 403 |
| Native L4/L5 execution | BLOCKED; no qualified production write/approval/external adapter is composed |

The actual private audit table contains `id, scope, event`. Event admission and simulation state commit together. It is not a qualified native operation/outcome audit trail: no timestamp, request/operation ID or outcome is recorded in that table. The adapter's `audit_logged` flag must not be promoted into production audit qualification.

All P6-provided session tests passing does not close IA01/IA02. Independent probes expose behavior outside their assertions. No timing guarantee of ≤200ms is accepted; the foreground server-revocation failures persist until some other revalidation event/request occurs.

## Other remaining defects

The exact V1, dependency, collection/CI, identity-label, documentation and selector findings, each with a separate narrow correction batch, are catalogued in [P6_RELEASE_DECISION.md](P6_RELEASE_DECISION.md). Evidence is under `docs/reviews/evidence/p6-independent-2026-10-13/`: `session-race.txt`, `HTTP_INDEPENDENT.json`, `HTTP_BOUNDARY_EXTRA.json`, `DURABILITY_INDEPENDENT.json`, `BROWSER_OBSERVATIONS.json`, and the two remote-revocation receipts.

N0, actual L4 writes, actual L5 external execution, native V1 and G10 remain **BLOCKED**.

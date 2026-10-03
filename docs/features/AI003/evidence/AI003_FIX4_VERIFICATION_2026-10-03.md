# AI003 — Fix-4 Independent-Findings Verification (2026-10-03, round 2)

Implementation-owner verification record for the four-finding fix round on
branch `feature/ai003-risk-signal`, baseline `27fe96558077d8bbeccf669863881f0a50e80e40`
(independently reviewed). This is BUILDER evidence, not independent approval.
Authorized scope: (1) legacy/corrupt evidence decode failure, (2) security
harness state preservation, (3) TTL harness key isolation, (4) stale-response
UI defect. Frozen items untouched: Contract V2.2, AI003_DEMO_POLICY_V1,
DEMO_ONLY / COMPETITION, production_calibrated=false, thresholds, financial
method, authorization semantics; no evaluation cache added.

## Root causes fixed

1. **Legacy/corrupt evidence decode unhandled (finding 1).** Parent `117d7e5`
   stored evidence with the Frappe convenience wrapper (non-JSON payload
   format); commit `27fe965` reads JSON at the same key prefix. In
   `EvidenceStore.get()` the `raw.decode("utf-8")` and `_deserialize_record()`
   sat OUTSIDE the typed boundary, so parent-format bytes injected into the
   installed Redis client produced an unhandled UnicodeDecodeError through the
   public endpoint. Fix (`lotus_fin/lotus_fin/risk_signal/evidence.py`):
   decode + JSON parse + strict record validation
   (`_deserialize_record` now validates ref prefix/company/as_of/signal_id/
   payload/metadata types and raises on malformed records) all inside the
   typed boundary; each failure logs exactly one structured
   `ai003_evidence_storage_error` diagnostic (operation `evidence_cache_decode`,
   sanitized exception type, correlation id preserved, no raw bytes/record
   content/exception message) and raises typed `EvidenceStorageUnavailable` →
   replay UNAVAILABLE with null payload. No `pickle.loads` anywhere; no local
   fallback; prefix/TTL unchanged; valid JSON records unaffected; missing/
   expired → generic FORBIDDEN and Redis outage → UNAVAILABLE semantics kept.
2. **Security harness deleted pre-existing users (finding 2).**
   `test_security_revoke_regrant.py` previously deleted any user at the test
   email and blanket-deleted AP Custom Roles. Fix: per-run unique user email
   (`ai003_sec_<uuid>@example.com`, created only if absent — reuse aborts);
   preconditions snapshotted BEFORE any mutation (pre-existing AP Custom
   Roles + user absence) and the run ABORTS (exit 2, zero mutation) if a
   pre-existing AP Custom Role or same-email user exists; every created
   artifact (user, User Permission, Custom Role) tracked by name; cleanup runs
   in a finally block, is idempotent, deletes ONLY run-created artifacts,
   issues no blanket clear-cache (targeted per-user cache refresh only), and
   asserts pre-existing state before == after.
3. **TTL probe overwrote existing evidence (finding 3).** The old probe derived
   its ref from the same scope/hash as a normal AP evaluation
   (`AI003-EV-c78691c3fd8d-5117cb50a85a`), then SETEX TTL=4 + DELETE —
   overwriting/truncating/deleting a live record. Fix
   (`tests_e2e/test_ttl_expiry_http.py`): probe uses a UNIQUE reserved ref
   (`AI003-EV-probe-<uuid12>`, distinct from every production ref), asserts
   key absence before writing (collision → abort, nothing overwritten), keeps
   payload/hash/company/cutoff valid so a real replay returns MATCH, deletes
   only its own key, and verifies the existing production record afterwards:
   same value hash, TTL only naturally decayed (3599s → 3587s observed, never
   truncated to the probe TTL), still replays MATCH.
4. **Stale-response UI defect (finding 4, now in scope).** Reproduced live:
   AP/2026-09-26 response rendered after the user had already changed the date
   to 2026-09-27. Root causes: (a) the `frappe.call` callbacks rendered
   unconditionally while input `change` handlers only cleared the DOM;
   (b) caught `frappe.throw("FORBIDDEN")` calls in the typed authorization
   path leaked `_server_messages`, popping a blocking modal on top of the
   typed envelope. Fix (`risk_signal.js`, `api/ai_insights.py`):
   - request-sequence token: every evaluation captures a seq; any
     company/signal/date change calls `invalidate_requests()` which clears the
     outstanding token, drops the dead request's loading panel, restores the
     primary action (never stuck in "Evaluating…"), and clears the result;
     `.then/.fail` callbacks discard anything whose token is no longer current
     (stale success AND stale transport error), so only responses matching the
     current inputs render, and a new evaluation is immediately possible after
     invalidation;
   - `_clear_leaked_server_messages()` in both AI003 endpoints (same cleanup
     pattern the AI002 endpoint already used) — the FORBIDDEN wire is
     unchanged; only the leaked client-side modal disappears;
   - E2E upgraded: `rapid_change_last_wins` now runs with a REAL held request
     (Playwright route holds dispatch; release continues to the real server —
     only delivery ORDER is controlled, financial results are never faked);
     `keyboard_primary_action` asserts a real evaluation result (no
     unconditional `record(..., True)`); new scenarios: delayed success
     discarded after date change, after signal change, delayed transport error
     discarded after input change, evaluate-new-inputs after invalidation.

## Commands and results (actual, final image
sha256:4eeb7dd024de1645099f74940742b4b6c6eccccc51d1438988d2d6e7c6080cc2)

| Check | Command (shell) | Result |
|---|---|---|
| Narrow host suite | `python -m pytest lotus_fin/tests/test_risk_signal_evidence.py lotus_fin/tests/test_risk_signal_service.py -q` | 66 passed + 7 subtests (evidence 34: 8 storage-boundary + 6 decode-boundary tests incl. parent pickle bytes, invalid UTF-8, invalid JSON, wrong structure/type/date, one-sanitized-diagnostic, zero content logging) |
| Full hermetic host suite | `python -m pytest lotus_fin/tests/` (3 frappe-import modules excluded, host-env limitation) | 412 passed + 7 subtests |
| Container targeted suite | docker exec unittest -q over the 9-module list | 298 tests OK (evidence suite also passes in isolation: 34 OK) |
| Installed-Frappe raw Redis fault probe (NEW) | `python tests_e2e/test_raw_redis_fault_probe.py` (site-context process; patches the live `frappe.cache()` RAW get/setex/delete, evidence keys only, restores in finally) | 5/5 PASS: GET ConnectionError → endpoint UNAVAILABLE/null; GET TimeoutError → same; SETEX ConnectionError → typed, no ref; DELETE ConnectionError → typed; healthy MATCH after unpatch |
| Decode boundary public-endpoint probe (NEW) | `python tests_e2e/test_decode_boundary_endpoint.py` (public endpoint called in a separate site-context process; corrupt payloads injected into the installed Redis client under unique collision-checked probe refs) | 5/5 PASS: parent pickle bytes / invalid UTF-8 / invalid JSON / valid-JSON-wrong-structure → typed UNAVAILABLE, payload null, NO unhandled exception; healthy JSON record → MATCH unchanged |
| Frozen AR/AP gold smoke | smoke probe | `"pass": true` 7/7 — artifact `evidence/ai003_smoke_results_2026-10-03.json` |
| Cross-worker HTTP replay | `python tests_e2e/test_cross_worker_evidence.py` | 20/20 MATCH, 0 false FORBIDDEN; cross-company/unknown → FORBIDDEN |
| Hardened revoke/regrant + state preservation | `python tests_e2e/test_security_revoke_regrant.py` | PASS: MATCH → revoke → FORBIDDEN (null payload) → restore → MATCH; pre-state snapshotted; only run-created artifacts removed; pre-existing AP Custom Roles before == after |
| Harness conflict-abort case | seed a foreign AP Custom Role, run harness, inspect, remove seed | exit 2 "HARNESS ABORT (no mutation performed)"; seeded role preserved; NO stray test user created; state restored afterwards |
| Isolated TTL probe | `python tests_e2e/test_ttl_expiry_http.py` | PASS: probe ref `AI003-EV-probe-…` ≠ existing ref; fresh MATCH → post-expiry FORBIDDEN (null); existing record value hash unchanged, TTL 3599→3587 (natural decay only), still MATCH. Expiry MECHANISM with short TTL — NOT a 3600s wall-clock verification |
| Live Playwright E2E | `python tests_e2e/test_risk_signal_workspace.py` | PASS 22/22 — includes rapid_inflight_invalidated_not_stuck, rapid_change_last_wins (A-after-B never overwrites B), stale_success_discarded_after_date_change, evaluate_new_inputs_after_invalidation, stale_success_discarded_after_signal_change, evaluate_after_signal_invalidation, stale_transport_error_discarded_after_change, keyboard_primary_action (real result). Video `tests_e2e/videos/ai003_risk_signal_e2e.webm` |
| Registry durability | rebuild + `up -d --force-recreate configurator backend …` (twice this round) | configurator exit=0; `sites/apps.txt` = erpnext, frappe, lotus_fin each time |
| Runtime code parity | sha256 inside container vs working tree | evidence.py d25c4578…, ai_insights.py 1d2b45b8…, risk_signal.js 16ff6b9a… identical |

## Failure-mode matrix after this round

| Mode | Observed |
|---|---|
| Redis healthy, valid JSON record | resolves; MATCH |
| Missing / expired key | clean miss → generic FORBIDDEN (payload null) |
| Redis outage / timeout (raw commands, installed client) | typed UNAVAILABLE, payload null; no ref emitted on store path |
| Legacy pickle / invalid UTF-8 / invalid JSON / malformed record | typed UNAVAILABLE via public endpoint, payload null; ONE sanitized diagnostic; no unhandled exception; no content logging; no pickle.loads |
| Stale response (success or transport error) after any input change | discarded by token; UI never renders stale result; primary action never stuck; new evaluation immediately possible |

## Remaining findings / limitations

1. Builder evidence only — independent re-verify pending (handoff prompt
   issued separately). G4B closure is NOT declared by this round.
2. 3 host test modules require frappe (container-only) — pre-existing env
   limitation.
3. Full-site `bench run-tests` not run (allow_tests disabled by design).
4. 3600-second TTL wall-clock behavior not waited out (mechanism verified;
   production TTL pinned by unit test).
5. Historical artifacts from earlier rounds are preserved under their own
   dates; they are not current verification.

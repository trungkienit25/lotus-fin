# AI003 Playwright E2E — implementation state and live-run blocker (2026-10-02)

## Status: IMPLEMENTED, live run BLOCKED by a pre-existing site-config issue (NOT AI003 code)

Script: `tests_e2e/test_risk_signal_workspace.py` (bare-script Playwright pattern, target
`http://ai003-verify.localhost:8080` only, read-only, no frontend-site mutation).

## What works (verified live)
- HTTP routing to the isolated site: nginx Host-map conf added
  (`docker/ai003-local/nginx/frappe.conf` + compose override volume mount) —
  `ai003-verify.localhost:8080` serves the verify site; `localhost:8080` keeps serving `frontend`.
- Login works (Administrator; `bench set-admin-password admin` applied on the verify site — documented below).
- The risk-signal **Page record and loader work server-side**
  (`frappe.desk.desk_page.get('risk-signal')` → LOADER OK; sidebar shows the page).

## Blocker (root-caused)
After desk boot on the verify site, the client continuously navigates: desk → setup-wizard
(SPA) → `setup_wizard.js:36` (`window.location.href = frappe.boot.apps_data.default_path || "/desk"`)
→ /desk → … (CDP `Network.requestWillBeSent` initiator stack captured; reload every ~0.5–1 s).

Chain of facts:
- `System Settings.setup_complete` = **1** in the DB; `frappe.is_setup_complete()` → True.
- The embedded `frappe.boot` JSON in the /desk HTML still carries **`"setup_complete": "0"`**
  → client believes setup incomplete → SPA-routes to setup-wizard → wizard sees
  `setup_complete` truthy? no — its on_page_load sees the boot value path → redirects to
  `/desk` → loop (the falsy boot flag drives the router to the wizard; the wizard's redirect
  drives back; ping-pong).
- `frappe.cache.hdel('bootinfo', 'Administrator')` deleted the cached boot entry, but the
  re-fetched boot STILL embeds "0" → a second cache layer (client_cache / system-settings
  document cache) is still serving the stale flag.

## Environment fixes already applied on the way (documented for the owner)
1. `sites/apps.txt` was missing `lotus_fin` (only erpnext+frappe) → caused
   "Module Lotus Fin AI not found" on page load and missing asset linking; fixed by appending
   `lotus_fin` (run.ps1's sync path does the same).
2. Verify-site Administrator password was not the stack standard →
   `bench --site ai003-verify.localhost set-admin-password admin`.
3. `System Settings.setup_complete` set to 1 server-side (DB level) — the remaining stale
   cache layer still needs flushing (owner call).
4. nginx Host-map (config-only) + baked app include assets added to the Dockerfile.

## UI coverage in lieu of the live E2E run
- All result-state rendering logic (status/finding/severity chips, reason copy, evidence
  affordance, explanation-UNAVAILABLE copy, banned words, stale-clear, no-double-submit,
  text-node-only rendering) is pinned by 31 hermetic service tests + contract tests.
- The full backend path is proven live on the verify site by the smoke probe
  (`docs/features/AI003/evidence/ai003_smoke_results_2026-10-02.json`): 7/7 PASS including
  METHOD GOLD number assertions through the real AI001/AP boundaries.

## DoD entry
Playwright E2E: **NOT_RUN (live)** — implemented script + root-caused environment blocker
(verify-site desk boot loop, independent of AI003 code); UI logic covered hermetically; live
API path covered by the smoke probe. Owner may rerun after flushing the verify site's
bootinfo/system-settings cache.

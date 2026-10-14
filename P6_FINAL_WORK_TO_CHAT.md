# P6 final integration handoff

Executable integration runs in the existing `/copilot` page and approved drawer. The existing dirty/untracked work is preserved. No commit, push or production/shared deployment was performed. This is a builder handoff, not independent release qualification.

Builder offline evidence: **507 backend checks and 124 frontend checks passed**, with no frontend skips. Type checking, frontend build, lint and whitespace checks passed. The full legacy collection remains a separate failed gate: 968 collected, four collection errors. Earlier failed attempts are retained; no assertion was removed or weakened.

After Docker storage recovery/reset, a fresh `--no-cache` lean build completed in 11m48s with **zero cached steps**. Serving image: `sha256:5264a4c2d7992fdeaa69f40c041752b8cfdb3849f2a852ab536eb1075737c256`. **331 backend Python/JSON files and both served React JS/CSS assets match current source/build hashes**. The owned site is `core-p6-01a1358e.localhost`, loopback **http://127.0.0.1:8114/copilot**. Installed apps are exactly frappe + lotus_fin; ERPNext is absent. Real HTTP qualification passed 15 checks before and 15 after cold restart; these are repeated checks, not 30 unique tests. Browser login, V1 gold results, external logout clearing, Bob login without restoration of Alice's protected results, and post-restart browser serving were observed.

The disposable builder, its helper image, old anonymous Redis cache volume and completed init container were removed. Build Cache is **0 B**. Only three needed runtime images remain (4.783 GB total) plus the owned runtime/site data. Container stdout/stderr logs are limited to two 1 MB files each; Redis snapshots/AOF are disabled in this demo, with cache on bounded RAM. No verbose recovery build log, database dump or duplicate source archive was created. Docker storage is on E.

| Verdict | Current scope |
|---|---|
| SESSION_SECURITY | PASS_BUILDER for executed session/CSRF/scope checks; independent qualification pending |
| L0_L3_REGRESSION | PASS_BUILDER — contracts and retained mounted flow; no native data qualification |
| L4_SIMULATED | PASS_BUILDER — real HTTP synthetic proposal/confirmation/idempotency; no business write |
| L4_REAL_WRITE | BLOCKED — N0 and target unapproved |
| L5_SIMULATED | PASS_POLICY_REVIEW_ONLY — denial/approval-provider status; integrated execution remains disabled |
| L5_REAL_SIDE_EFFECTS | BLOCKED — no qualified adapter/approval provider |
| V1_DETERMINISTIC | PASS_BUILDER — actual predicate, HTTP and browser gold |
| V1_NATIVE | BLOCKED — no approved native source |
| CORE_ERP_INDEPENDENCE | PASS_BUILDER for Frappe-only auth/serving/disabled-source shell and cold restart |
| FULL_PRODUCT_INDEPENDENCE | BLOCKED — legacy finance remains ERP-derived/unqualified |
| SOURCE_READY | PASS_SCOPED — current backend and React image bytes verified; full release qualification remains separate |
| GITHUB_PUSH_READINESS | BLOCKED — no commit/push, advisory and legacy quality gates unresolved |
| G10_READINESS | BLOCKED — requires independent acceptance and native/policy closure |

Known unresolved issues remain explicit: legacy pytest BaselineSourceError/AI004 contract mismatch; dependency advisory closure (retained evidence chosen by user); original module architectural debt; and any incomplete graph/native/browser qualification. No DEMO verdict qualifies a real write or financial source.

The scoped graph refresh produced 12,450 nodes/368 flows; the complete structured tracked-change report contains 102 changed symbols and 64 affected flows at CRITICAL risk. Shared panel impact remains HIGH (page, drawer, fixture callers). Late UI availability/recipe changes require a refreshed pre-commit graph review; no commit is authorized. Remote account/role revocation timing and the other tab's cached account-header label are not independently qualified by the protected-state clearing tests.

Evidence: `docs/reviews/evidence/p6-full-integration/LOW_DISK_BUILD_RECEIPT.json`, `RECOVERY_SOURCE_PROVENANCE.json`, `HTTP_RECOVERY_CHECKS.json`, `HTTP_POST_COLD_RESTART.json`, `BROWSER_RECOVERY_CHECKS.json`, `FINAL_SOURCE_AND_TEST_HASHES.json`, and `release/COMMANDS_AND_EXITS.json`. All seven requested reports plus integrated technical documentation and security self-assessment are present at repository root. Private demo credentials are in ignored `.runtime/lotus-core-p6-01a1358e/demo-credentials.json`.

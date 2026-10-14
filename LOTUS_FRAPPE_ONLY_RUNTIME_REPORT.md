# Lotus Frappe-only runtime report

13 October 2026, Asia/Saigon. Evidence: `docs/reviews/evidence/frappe-only-2026-10-13-01a13314`. No commit, push or production deployment.

**CORE_RUNTIME_READY. ERPNext is absent from the built image and installed site.**
Runtime, API admission, ordinary-user authentication and infrastructure were qualified
without waiting for N0. Full business independence remains blocked by unavailable
approved native financial data and its authority/policy decision.

| Verdict | Actual result |
| --- | --- |
| ERP_APP_REQUIRED | NO_FOR_CORE; YES_FOR_OPTIONAL_LEGACY_ERP_FEATURES |
| FRAPPE_ONLY_BUILD | PASS |
| FRAPPE_ONLY_STARTUP | PASS_ISOLATED |
| SOURCE_REPRODUCIBILITY | PASS_SELECTED_WORKTREE_SOURCE_AND_TRANSFER |
| HOOKS_INDEPENDENCE | PASS_CORE |
| CORE_RUNTIME_READINESS | CORE_RUNTIME_READY |
| FULL_PRODUCT_INDEPENDENCE | BLOCKED_NATIVE_DATA_AND_N0_APPROVAL |

| Layer | What was actually qualified | Limit |
| --- | --- | --- |
| CORE | Frappe-only image; site; MariaDB/Redis; workers/websocket/scheduler/nginx; authenticated readiness; cookie login/logout; CSRF; disabled native APIs | Isolated localhost environment |
| DEMO | 438 retained backend tests; 21 boundary/CSRF tests; 20 local preview lifecycle tests; clean React build | Doubles/synthetic contracts; no financial authority |
| NATIVE | Contracts, typed interfaces and denied/disabled HTTP endpoints are present | No approved business source/schema/grants; no successful native financial read |

Image: `sha256:de0aa8d8454af7bf0970d39a9610c41d6acf935d9b8918b942b605ab57edca62`. Python 3.14.8; Frappe
`v16.35.0`, upstream commit `012667b9c4e7f66d5e1ff5858d2e922331d4300a`.
Qualification is Linux amd64. Official build/base image digests and Node builder
are pinned in `docker/lotus-core/Dockerfile`; MariaDB/Redis digests in the core Compose file.

Real serving used only `lotus-core-01a13314`, `core-01a13314.localhost`, port 8097.
Site smoke proved installed apps exactly `frappe, lotus_fin`, and absence of
`Company` and `Sales Invoice` DocTypes. The ordinary QA account had a minimal
framework Desk role and no business grants. Administrator was used explicitly
only for isolated account bootstrap, never as a request fallback.

Two complete hardened cold-start/HTTP rounds passed on the isolated site with
retained volumes. `RUNTIME_COMMANDS.json` contains exact argv/exits and log hashes;
`HTTP_1.json` and `HTTP_2.json` contain 15 cases per round.
All owned containers were stopped/removed afterward; all four private volumes retained.
Shared container identities/start times were compared separately.

The offline Python test image was never used as proof of a serving startup.
No native financial schema, mock production ledger, ERPNext substitute, numerical
algorithm rewrite, shared-site migration or shared-service restart occurred.

Read authorities: AGENTS.md, Security Code V3, existing packaging/hooks/helpers,
previous final integration and release-candidate reports. Requested
`LOTUS_FULL_ERP_DEPENDENCY_INVENTORY.md` and `LOTUS_FINAL_N0_APPROVAL_SHEET.md`
were not available; the latest instruction explicitly confirms N0 is blocked.

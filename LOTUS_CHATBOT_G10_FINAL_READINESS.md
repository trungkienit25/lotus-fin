# Lotus Fin — G10 final judge readiness

12 October 2026, Asia/Saigon. **G10_JUDGE_READINESS = BLOCKED / NO-GO.** This is an independent release preflight, not a judge deployment. Original UI/L3 corrections pass reproduced offline cases, but the complete candidate has residual UI failures and cannot deliver an independently authorized native Lotus workflow.

Identity: branch `codex/p2a-invoice-read-backend`, HEAD `5f805ef34f788245a3ec0e9c2f44e224eb16c305`; [549-file manifest](docs/reviews/evidence/lotus-final-acceptance-2026-10-12-01a130c1/SOURCE_MANIFEST.json) SHA256 `a59b5b472d44d3251a92247d281627ce7f3d4cfa93acdf58158bf3c4df1a3d40`. [Actual commands/exits](docs/reviews/evidence/lotus-final-acceptance-2026-10-12-01a130c1/COMMANDS_AND_EXITS.json). Source and selected original evidence remain unchanged.

## Current release gates

| Gate | Fresh evidence / result | Required exit |
| --- | --- | --- |
| Complete independent offline acceptance | CHANGES_REQUIRED: new controller 16 failures, actual React 3; original P2-B/L3 vectors pass | FIN-F07 malformed-search invalidation and FIN-F12 source observation-time validity green; preserve originals. |
| Product independence | FAIL current recipe: ERPNext base and explicit site install; ERP accounting inputs remain | Approved core scope and native source, Frappe-only positive operation with ERPNext absent; measured package/schema/role/credential/egress independence. |
| Native authority/permissions | BLOCKED: no owned tenant/invoice/schema/update authority approval or concrete native read adapter | Product/Data/Security records plus ordinary-user native company/document/field/revocation gold. |
| Actual HTTP and frontend integration | BLOCKED: all public methods disabled; production client does no I/O; panel/preview unmounted | Approved actual transport/route, ordinary-session POST/CSRF/single envelope/status/CID/no-store and actual UI journey. |
| Immutable source and runtime | FAIL: 49 manifest paths absent from HEAD; fresh 17/17 backend paths absent from running image | Complete immutable artifact and clean dependency/image build; identical worker/module/browser bytes; cold-start recheck. |
| Host build | PASS narrowly: tsc/app+node exit0, Vite exit0 | Cannot close image/native/judge gate. Current bundle has no action or preview capability markers. |
| Release lint | Full lint exit1; selected action/L3 exit0, one warning | Resolve or explicitly govern baseline quality gate; do not report universally clean source. |
| Real framework security | Exit2 collection failure: Frappe unavailable in host tests | Actual framework/site/auth policy tests against approved artifact; no fake Frappe PASS substitution. |
| Audit/resources/no business writes | Offline logical tests pass; live NOT_RUN | Durable required sink policy/fault proof, physical I/O/deadline/hydration bounds, before/after business and declared framework side effects. |
| Judge target and rollback | NOT_RUN | Named isolated owned project/site/ordinary accounts/fixtures and approved provisioning, restore/cleanup/rollback rehearsal. |

## Canonical quick-start defects confirmed in current source

1. `README.md` advertises `run.ps1 setup`, `smoke`, and project selection. Current PowerShell ValidateSet has neither setup nor smoke, and no Project parameter. Bash has no corresponding cases. Both target the shared `frappe_docker` stack and `frontend` site; they are not the advertised standalone judge runner. No run/sync/demo/setup mutation command was executed.
2. Judge Compose selects `docker/ai003-local/Dockerfile`. It calls `/home/frappe/judge/init.sh`, but the Dockerfile does not COPY judge support files. The recipe packages Lotus backend and Desk include assets, not React action source/build. Even a host build PASS cannot supply the missing image contents.
3. Init installs ERPNext and runs site migration/smoke. This contradicts independent-product acceptance and lacks native membership/invoice policy. Administrator walkthrough/import-only smoke is not an ordinary-user read authorization test.
4. Production React and Desk routes remain different product paths. No accepted canonical mounted action route/auth/CSRF/hosting artifact is established. Current source import scan and built bundle confirm action/preview absence.
5. The observed running backend is an older October3 image, not this candidate: ID `sha256:ed6e02f587eb450a0882ecb4b6fbb259d1a1f27f549e1cc4bbe21a660b3017b7`; source hash probe finds 17/17 sampled modules missing. No new worker/image was started and no judge site was initialized.

These are current source/runtime observations, not inherited preflight PASS/FAIL. [Provenance](docs/reviews/evidence/lotus-final-acceptance-2026-10-12-01a130c1/PROVENANCE.json), [runtime source](docs/reviews/evidence/lotus-final-acceptance-2026-10-12-01a130c1/RUNTIME_SOURCE.txt), [build hashes](docs/reviews/evidence/lotus-final-acceptance-2026-10-12-01a130c1/BUILD_MANIFEST.json).

## Safe demonstration boundary

The current source supports a technical fixture demonstration with visibly simulated transport and records, explicit selected metadata reader, and separate local fact-free text preview. Disclose the residual negative failures and that native/live/judge release is blocked. The local preview is unsaved and unsent; fake clipboard success is not real browser clipboard qualification. Do not present generic metadata search as overdue, current balance, complete-company analysis, saved Draft, send/submit/cancel/payment, or native ERP-free product operation.

393 offline AI001–003/numeric/plugin regressions pass with seven subtests separately; this preserves deterministic compatibility, not native data equivalence or live calibration. AI002 unavailable future-source behavior and AI003 DEMO_ONLY limits remain. No performance/usability/ROI/competition score is measured by these test durations.

## Ordered G10 exit package

Obtain N0 owned native data/policy and core-scope approval; close residual UI cases; qualify one native adapter and existing typed HTTP family; select/mount the actual product route; create complete immutable ERP-free source/dependency/image artifact; execute ordinary-user positive/negative native HTTP/UI, sink/resource/no-write and AI compatibility tests; rehearse a second cold start and approved restoration/rollback. Record exact source/image/worker/site/fixture identities, command exits, safe traces and boundaries.

Missing V1/L4/L5 capabilities remain proposal gaps and stay disabled. G10 requires its own independent judge acceptance after native/live gates pass; offline or builder success never grants it. No deployment, source fix, ERP mutation, commit or push is authorized or performed by this report. **STOP.**

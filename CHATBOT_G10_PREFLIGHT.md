# Lotus Fin G10 reproducibility preflight

12 October 2026 · Asia/Saigon. **G10 = BLOCKED. Judge build/start/site provisioning/HTTP/UI qualification NOT_RUN.** This is a canonical checklist and defect handoff, not release approval. Private P2 acceptance cannot close G10 automatically.

Authority: [judge reconciliation plan](docs/reviews/phase0-chatbot-2026-10-10/JUDGE_RELEASE_RECONCILIATION_PLAN.md), current README/run scripts/Dockerfile/ignore/Compose/init/smoke, [frozen wire](docs/reviews/phase0-chatbot-2026-10-10/CHATBOT_P2B_WIRE_CONTRACT.md), [P2AB acceptance](docs/reviews/phase0-chatbot-2026-10-10/CHATBOT_P2AB_INDEPENDENT_RECHECK.md), Security Code V3. Fresh commands/fingerprints are in [discovery evidence](docs/reviews/evidence/chatbot-private-erp-discovery-2026-10-12-1655-a12f82/). No judge environment was selected or operated.

## Current blockers proven by source inspection

| ID | Current condition | Required resolution |
|---|---|---|
| J01 | README advertises `run.ps1 setup/smoke`, Project selection and fresh self-contained judge setup; actual script supports none of setup/smoke/Project and targets shared frappe_docker/frontend. Bash also lacks setup/smoke. | Align truthful judge-only runner/README with approved exact project/site and fail-fast behavior. Do not execute current sync/run/demo/test as judge qualification. |
| J02 | Compose init entrypoint expects `/home/frappe/judge/init.sh`; Dockerfile does not COPY judge support files and ignore excludes them. Smoke is also not packaged by this recipe. | Review/package/hash init/smoke/config and verify paths in actual image. |
| J03 | Dockerfile copies Lotus app and Desk include assets; no React source/build artifact. React `/copilot` and `/ai` exist, while hooks/README use Desk `/app/lotus-copilot`. | Product owner chooses canonical entrypoint and capabilities. React is required for the approved P2 UI architecture and needs its own artifact/origin/history/auth delivery. Desk is a separate path. |
| J04 | React `/app/:doctype` namespace overlaps Desk `/app`; Vite dev proxy targets shared localhost8080 with changeOrigin. | Approve separate path/origin routing and trusted site mapping; dev proxy is not canonical production auth/CSRF proof. |
| J05 | Current backend image missing17/17selected P1/P2files; source dirty and some judge inputs untracked. | Frozen full source archive/manifest, pinned base/dependencies and immutable worker lineage; clean-clone instructions must include approved inputs. |
| J06 | Judge init creates site, installs/migrates/clears cache and updates apps.txt; Compose starts scheduler/queues. | Explicit site mutation approval, new owned volumes, safe bootstrap baseline and background/email/provider containment. |
| J07 | README uses Administrator walkthrough; smoke only checks a legacy module set, not P1/P2 read family. | Ordinary judge user/permission oracle and exact P1/P2 modules/HTTP smoke; Admin bootstrap is separate. |
| J08 | No installed-site app/hook/rights, key/map/sink, no-write or restoration evidence for judge. | Qualify all checklist rows below on the separately approved judge target. |
| J09 | CI build-and-test is placeholder and Semgrep continues on error; existing P2 UI findings not closed in inspected acceptance packet. | Real release validation with current fingerprints and corrected UI regression evidence; no green-CI substitution. |

Existing plan proposes a worker-startup lineage config `docker/judge/gunicorn.conf.py`; it is currently absent. No stale historical judge-image result is reused as current build/import/HTTP evidence.

## Canonical checklist and required evidence

| Area | Release requirement | Current status |
|---|---|---|
| Owner/scope | Named release/ERP/security/product/QA owners, approved judge project/site/image/volumes, allowed provisioning/fixtures/rollback operations | BLOCKED |
| Primary frontend | Approved React route/artifact for P2, or separately scoped Desk foundation demo; label disabled/unqualified capabilities honestly | BLOCKED |
| Source lineage | Source SHA/dirty/untracked archive, exact included files and SHA256, excluded caches/secrets/plans, Docker/build manifest | BLOCKED |
| Backend image | Base `frappe/erpnext@sha256:77eedd6d4180452d1c2832c2f762e588e20de85c038ed8c148aa77007329a8f3` is only a local candidate; approve platform and locked dependencies, record resulting immutable image IDs | NOT_RUN |
| Imports/workers | All expected API/controller/services/ports/codecs/config/events/serializer/adapter modules load from approved image in every new serving worker; record origins/hashes and PID lifecycle | NOT_RUN |
| Site provisioning | Reviewed init packaged, explicit new site/DB/Redis, ERPNext/Lotus installed order/versions and effective hooks/customizations/schema/timezone verified | NOT_RUN |
| Permissions | Ordinary judge users with allowed/denied Company/doc/field/mask/custom-hook cases and independently owned expected fixture ledger | NOT_RUN |
| Secrets/map/sink | Secure private signing/auth configuration, retirement/rotation, versioned approved scope map, required sink acknowledgement/retention/access/failure behavior | BLOCKED |
| Health | DB/Redis/service liveness distinguished from app readiness | NOT_RUN |
| Readiness | Module/worker/source identity + installed-site schema/config/key/sink gates; disabled/unqualified states cannot report enabled-read readiness | NOT_RUN |
| HTTP smoke | Three real POST routes, Guest/GET/CSRF/wrong scope, one envelope, exact status/CID/no-store, fresh authorized search/open | NOT_RUN |
| UI walkthrough | Real ordinary user Company candidate→context→filters→bounded search→explicit selection→five-field read view; empty/partial/denied/stale/logout/scope-reset cases | NOT_RUN |
| Security/resources | Revocation, keys/cursors/session races, actual SQL/hydration/bytes/deadlines/collation/outage/sink failures | NOT_RUN |
| No-write | Applicable business/seen/view/queue/lifecycle before/after plus app audit separation; declared unavoidable framework writes | NOT_RUN |
| Fresh start | Clean clone/materialized source and isolated boot, worker/site/HTTP evidence, second cold start and restored-baseline reproduction | NOT_RUN |
| Evidence | Exact commands/exits/time window, image/source/worker/site fixture identity, redacted logs/request results/screens, no credentials/tokens/document dumps | NOT_RUN |
| Cleanup/rollback | Approved snapshot restoration rehearsal and owned-object cleanup, retained evidence, no shared-volume deletion or global prune | NOT_RUN |

Health commands such as Docker ps or DB healthchecks do not prove any readiness row. Smoke's current root imports/list-apps are also insufficient for HTTP, ordinary-user policy or worker code lineage.

## Conditional smoke command skeleton — NOT EXECUTED

These identifiers must come from the separately approved judge packet. The recipe must first package the support files and expand smoke to the accepted module/read family. Current runner commands are unsuitable.

```powershell
$judgeCompose = '<approved-canonical-judge-compose-absolute-path>'
$judgeProject = '<approved-new-judge-project>'
# Before any start: check manifest/image/source and exact owned-resource boundary.
docker compose -p $judgeProject -f $judgeCompose config --quiet
docker compose -p $judgeProject -f $judgeCompose ps
docker compose -p $judgeProject -f $judgeCompose exec -T backend `
    /home/frappe/frappe-bench/env/bin/python -B /home/frappe/judge/smoke.py
# Capture redacted ordinary-user real HTTP test evidence through the approved
# session/CSRF test driver; credentials must not appear in command arguments/logs.
```

Every invocation needs fail-fast exit handling in the repaired runner. Site smoke imports/connects to ERP and is permitted only under the judge target approval. No executable HTTP driver or site/bootstrap command was invented as successful evidence. Tests in [adapter report](CHATBOT_AUTHORIZED_READ_ADAPTER_REPORT.md) define the actual HTTP and oracle requirements; [runtime report](CHATBOT_PRIVATE_RUNTIME_QUALIFICATION.md) defines source/image/fresh-start checks.

## Walkthrough, logs and rollback

Qualification must show the chosen product entrypoint under an ordinary authenticated judge identity, with independently authorized synthetic companies/documents. Display source mode accurately. Exercise valid empty and incomplete pages, selection even for one row, minimum document read, denial and scope/logout reset. No financial overdue/amount/ERP Draft/submit/cancel/payment or legacy LLM claims from generic read success. Synthetic fixture demonstrations must be labeled and cannot substitute for real rights.

Correlate browser RID/CID with actual serving-worker lineage and required audit events. Retain safe build/init/readiness/proxy/backend results and before/after measurements, protecting sessions, keys and document data. Separate required application audit from prohibited ERP business side effects.

Rollback only the approved judge project: disable capability, retire/invalidate references as approved, restore last accepted image/config and the reviewed snapshot where necessary. Verify restored business/permission/file/queue state and disabled routes. Remove only recorded project-owned containers/networks/volumes authorized for deletion, verify residue, preserve evidence. No current shared sync, AI003 cleanup, volume prune or shared Redis flush.

**G10 stays BLOCKED until separately executed independent judge qualification passes against the approved canonical artifact and entrypoint.** No unauthorized deployment, ERP write, feature enablement, commit or push occurred in this task.

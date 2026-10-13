# Round 2 — canonical artifact and target verification

10/10/2026 · FinTechathon Shenzhen · T1 only · **DEVELOPMENT_SOURCE_IDENTIFIED; RELEASE_CANONICAL_BLOCKED; DEPLOYMENT_BLOCKED**. Lotus Fin is the product; ERPNext/Frappe is its observed local technology foundation. Separate product identity does not imply separate deployment. Work has neither approved a release source nor deployed anything.

Authority: [workflow v3.1 §34](../../features/LOTUS_FIN_AI_FEATURE_BUILD_WORKFLOW_3_TOOLS_V3_VI.md), [ADR001](../../adr/001-clean-architecture-core-first-adr.md), [Security Code V3](../../security/LotusFin_Security_SSOT_Code_V3_Codebase_Aligned.md). Earlier Phase 0 remains dated evidence; this packet adds targeted observations. Raw evidence directory: [Round 2](../evidence/phase0-round2-2026-10-10/SELECTED_SOURCE_MANIFEST.json).

## Source authority and classification

`develop`, HEAD `07f7251d3a0744356bf96fb2fea55ec6df9a0ce2`; tracked and staged diffs empty before inspection, many pre-existing untracked files. **333/333 protected host fingerprints match** the previous final snapshot, remeasured this run. [Git before](../evidence/phase0-round2-2026-10-10/git-status-before.txt), [protected hashes](../evidence/phase0-round2-2026-10-10/PROTECTED_HOST_BEFORE.json). This is not a clean/reproducible release checkout.

Configured development/build input is the host tree, not the resident container. The tracked `docker/ai003-local/Dockerfile` SHA256 `9CFA468B3F7CC162F06408F8F9C0F128FB1EF28967EE212830B5492C478F86B5` copies `lotus_fin/`, installs the app editable with `--no-deps`, copies Desk JS/CSS and one AI002 fixture. Its adjacent ignore file SHA256 `427850CD73C5568A63A7BC6F2356D4FC5DE253921CD6A9287F5F8DDEF6921AF6` excludes everything then admits the entire app tree and that fixture. Thus untracked app files/caches/plans may become inputs; Git ignore is not Docker input exclusion. Base `frappe/erpnext:v16.35.0` is a mutable tag. No React build/COPY or judge-script COPY appears in this recipe.

The following table closes the 15-file comparison, without reopening the feature audit. H/R are host/current container; full SHA256 values and tracked flags are in [host/runtime hashes](../evidence/phase0-round2-2026-10-10/HOST_RUNTIME_HASHES.json); full image hashes, missing paths and classification are in [classification ledger](../evidence/phase0-round2-2026-10-10/SOURCE_CLASSIFICATION.json). Prefixes below are identifiers, not truncated integrity checks. Container-only changes are **candidates**, never automatically adopted as canonical fixes.

| Exact path below `lotus_fin/lotus_fin/` | H / R SHA256 prefixes | Classification; observed difference / owner |
|---|---|---|
| presentation/controller/copilot_controller.py | 4CDA41678815 / 330a2d7f91a5 | CONFLICT; runtime requires authenticated server context, cache repository and verified company. Chat arbitrates, Antigravity reconciles after approval. |
| application/service/copilot_service.py | EE4160AE290E / 9324aad14d37 | CONFLICT; runtime session ownership/status checks differ. Same owner. |
| api/copilot_api.py | 511141A47618 / 73fd73f77d0d | CONFLICT; host guest/legacy exception fallback versus runtime session parameter/auth/error handling. Same owner. |
| api/ai_insights.py | CADC25F865DD / 959b2cc8cf75 | CONFLICT; runtime removes guest exposure on aliases. Same owner. |
| api/key_reports.py | A2CA639FD6FF / 98e6b09cf36e | HOST_CANONICAL; line-ending-only difference confirmed by current line comparison and prior normalized fingerprint, no behavioral change established. |
| modules/f004_what_if/api.py | D368824B1AFC / 517ead957d20 | CONFLICT; runtime checked-user guard. Chat owns reconciliation; outside B1-S edits. |
| modules/f004_what_if/adapters/baseline_adapter.py | 28C1B0606AEB / 68f4ee8f1d0c | CONFLICT; runtime guard/typed source error instead of default zero. Same owner, no engine edit. |
| modules/f005_financing/service.py | FE84D6A24A30 / 8ff1c06ab39a | CONFLICT; runtime profile source fails closed instead of defaults. Same owner, no engine edit. |
| infrastructure/tool/impl/f003_risk_tool.py | BAE368C03F07 / fe49024f4983 | CONFLICT; runtime payload/service call and checked-user binding differ. Same owner. |
| infrastructure/tool/invoker/tool_invoker.py | 95C37739EDA1 / e288fee52cec | CONFLICT; runtime schema validation/redacted errors added. No new company-binding guarantee established by this diff. Same owner. |
| application/agent/agent_runner.py | 89C7E5F77427 / 1d4d1f4fae1f | CONFLICT; runtime tool budget/status and limit message replace misleading completion fallback. Same owner. |
| core/domain/calculators/pnl_extractor.py | 90C4B3C93234 / 90c4b3c93234 | HOST_CANONICAL; byte match, no financial acceptance implied. |
| modules/f001_health/financial_health.py | ACCE59CD5E14 / acce59cd5e14 | HOST_CANONICAL; byte match. |
| infrastructure/persistence/frappe_cache_session_repository.py | C0365A5096DA / c0365a5096da | RUNTIME_CANDIDATE; byte match but host file is untracked. Chat must select and manifest it before release. |
| lotus_fin_ai/page/financial_health/financial_health.js | 8FC163E4FAE7 / 8fc163e4fae7 | HOST_CANONICAL; byte match of Desk source, not delivered-browser proof. |

Behavior comparison evidence: [current line differences](../evidence/phase0-round2-2026-10-10/HOST_RUNTIME_LINE_DIFFS.txt). No current symbol declared dead or renamed. Host package initializer activates `core/compat/legacy_module_resolver.py`; the judge initializer is version-only and lacks that resolver. Package layout/import behavior is therefore also **CONFLICT**, not merely differing file dates.

## Artifact and target lineage

Docker connectivity was actually verified first: server **29.1.3**, exit0. Existing backend uses image ID `sha256:ed6e02f587eb450a0882ecb4b6fbb259d1a1f27f549e1cc4bbe21a660b3017b7`; mounts sites/logs, not host application source. Installed package source reports Frappe16.34.0 / ERPNext16.35.0 / Lotus0.0.1. Disk changes do not prove preloaded Gunicorn workers use them.

**New local judge image evidence:** `lotus-fin:judge`, immutable image ID `sha256:130619296d8b53795e4223dc2dd40c893823258c7de6265abd266e3847819d56`, created 2026-10-05T15:08:25.205100745Z; labels identify prior compose project `lotus-readiness-fresh-20261005`. No judge container was running. This image is **STALE_IMAGE** relative to the current selected application tree, not an approved official competition target.

| Lineage step | Actual result / limitation |
|---|---|
| Committed/manifested source | PARTIAL: HEAD and host manifest established; untracked inputs and runtime reconciliation unresolved. |
| Source → build inputs | PARTIAL: current recipe read. **CONFLICT:** untracked `docker/compose.judge.yml` selects that recipe, but it cannot copy `docker/judge/init.sh`/`smoke.py`, which exist inside the old judge image. Original full build provenance UNKNOWN. |
| Inputs → immutable image | BLOCKED: exact local image IDs captured; no reproducible current build manifest/base digest/frontend artifact. No build run. |
| Immutable image → new worker | NOT_RUN: no new Gunicorn worker/site, no resident application inspection. |
| Offline package resolution | **PASS, narrowly:** isolated judge-image Python3.14.7 imports `lotus_fin`; `find_spec` locates `api/copilot_api.py`, but application/presentation specs are `None`. This does not import the API or prove its dependencies load. |
| Selected route dependency files | **FAIL alignment:** judge missing controller, service, runner, invoker, risk tool, health module and cache-session repository. Its Copilot API hash `98189f3b735501c7300c0bf60e09caba0d8b70ef2af733ff0388c0acb78f4c8f` differs from current host and runtime. |
| HTTP/UI/session/permission | NOT_RUN: no reviewed clean target; offline import is not acceptance. |

See [judge metadata](../evidence/phase0-round2-2026-10-10/judge-image-metadata.txt), [hashes](../evidence/phase0-round2-2026-10-10/judge-image-source-hashes.txt), [layout](../evidence/phase0-round2-2026-10-10/JUDGE_PACKAGE_LAYOUT.txt), [offline import](../evidence/phase0-round2-2026-10-10/JUDGE_OFFLINE_IMPORT.txt). Missing-file reads exit1/2 are artifact inspection failures, not failed financial assertions; all temporary readers were removed.

**Configured candidate judge route:** compose binds frontend only to `127.0.0.1:8088`, supplies explicit `${LOTUS_SITE}` to nginx, and declares separate sites/logs/DB/Redis volumes. README claims `run.ps1 setup` and `/app/lotus-copilot`; tracked `run.ps1` actually operates the shared `frappe_docker` stack with copy/build/migrate/restart/seed modes and has no advertised setup/project interface. **CONFLICT** owned by Chat/deployment owner. `/app/lotus-copilot` is the claimed Desk entry; React source route is `/page/lotus-copilot`. Judge image has Desk assets but no React app artifact. Do not treat these entrypoints as equivalent.

Per-site installed apps/customizations/permissions/effective principal/company mapping and official published endpoint are **NOT_VERIFIED**. Package versions and `${LOTUS_SITE}` configuration cannot establish these. Current port5173 belongs to another project, `thesis`; Vite's source proxy targets shared8080. Neither is Lotus acceptance evidence.

## Safe baseline specification and reproduction

**Designed setup; NOT_EXECUTED.** Deployment owner first approves one canonical source manifest and product entry (Desk versus React), reconciles packaging/imports, pins base/image identity and reviews bootstrap line-by-line. Provision a uniquely named compose project with new DB/Redis/sites/logs volumes and explicit new site; no external/shared volumes, host app writes or existing-site snapshot accepted without reviewed provenance. Disable scheduler/queues/outbound email and provider access for the read qualification target. Record empty baseline, installed apps, relevant DocType/custom-field metadata, timezone and two ordinary principals with distinct companies; no Administrator shortcut for acceptance. Seed only approved independent fixture vouchers after lifecycle review; freeze fixture hashes/expected ledger, no ERP test-helper imports. Bootstrap writes (`new-site`, install-app, migrate, cache clearing) are allowed only in that approved isolated project, never here.

After that: launch fresh workers from the exact image, verify module origins/fingerprints on those workers, then direct HTTP and selected UI route with the declared site/principal. For B1-S alone, first use an isolated React server with **all API traffic intercepted and outbound denied**, allowing deterministic DOM tests without ERP or LLM. Explicitly override Vite's shared8080 proxy; select an unused local port. Cleanup must inventory the exact project-labelled containers/networks/volumes, stop/remove only those objects, verify zero remaining objects, and preserve source/image/test logs. Do not issue a generic volume prune or Redis flush. Failed cleanup blocks baseline reuse.

Executed reproduction consists only of Git/hash/config reads, bounded verified cached graph calls, `docker exec … sh -c` source reads, and exact-image readers with `--rm --network none --read-only`, no mounts. The import reader used `PYTHONDONTWRITEBYTECODE=1`, Python `-B`, package initializer and `find_spec` only; initializer side effects were reviewed first. No `frappe.init/connect`, ERP records, worker hot-patch or bootstrap executed. [Execution ledger](../evidence/phase0-round2-2026-10-10/RESULTS.json) records exits, boundaries and invocation errors separately.

GitNexus cached CLI SHA256 `E2C96D62B26A1898E536457377F7B73C539B080C7E8C316869FFC6A790003EB4` verified before bounded direct-node use, without package managers. Context/impact for VercelChatPanel: not found/**UNKNOWN**; receivable query yields historical flows. Index remains 61 commits behind. Static tracing supplements unresolved graph evidence; no refresh/download retried. Before later application edits, new bounded graph impact plus current text callers is mandatory; UNKNOWN cannot waive risk.

## Candidate B0 prerequisites and ownership

Chat is contract/release arbiter; Work verifies; Antigravity implements only a subsequently approved packet. Candidate allowed **existing** paths: `docker/ai003-local/Dockerfile`, adjacent ignore, `docker/compose.judge.yml`, `docker/judge/init.sh`, `docker/judge/smoke.py`, `run.ps1`, `README.md`, package initializer/resolver only if approved; all exact fingerprints in manifest. React packaging path beyond the existing recipe is **UNRESOLVED**, not invented as approved scope. Reconciliation of the ten runtime conflicts needs its own explicit file set and tests; B0 does not authorize wholesale copying.

Minimal future plan: select source/entry → reconcile recipe and runner claims → exclude unintended inputs and manifest untracked dependencies → build once → isolated fresh-worker/HTTP/UI acceptance. Positive tests must prove route imports and selected authorized entry; negative tests must reject wrong site/company and missing inputs; reproduce a build from the same manifest. Rollback is restoring the prior approved source/image in the isolated project only, preserving evidence; do not roll shared data back. Remaining approval: canonical source, entrypoint, isolated lifecycle and exact packaging edits. No broad feature cleanup, financial engine changes, deployment dispatch or F101/F102 work authorized.

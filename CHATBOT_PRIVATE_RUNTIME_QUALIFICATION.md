# Lotus Fin private runtime qualification

12 October 2026 · Asia/Saigon. **Private runtime qualification BLOCKED. Source-to-current-serving-image match FAIL.** No new image, site or deployment was built. All commands below marked proposed remain unexecuted.

Evidence: [commands](docs/reviews/evidence/chatbot-private-erp-discovery-2026-10-12-1655-a12f82/COMMANDS.json), [runtime filesystem metadata](docs/reviews/evidence/chatbot-private-erp-discovery-2026-10-12-1655-a12f82/RUNTIME_SOURCE_FRESH.json), [Python layout](docs/reviews/evidence/chatbot-private-erp-discovery-2026-10-12-1655-a12f82/PYTHON_LAYOUT_FRESH.json), [host comparison](docs/reviews/evidence/chatbot-private-erp-discovery-2026-10-12-1655-a12f82/HOST_RUNTIME_COMPARISON.json), [source manifest](docs/reviews/evidence/chatbot-private-erp-discovery-2026-10-12-1655-a12f82/SOURCE_BEFORE.json). [Target readiness](CHATBOT_ERP_TARGET_READINESS.md) controls authorization; this report supplies the build and runtime handoff.

## Observed serving identity

| Item | Fresh observation |
|---|---|
| Backend | `frappe_docker-backend-1`, container `a857658a101bbe5304d16160d65c5669878e9b5eada9b3d288666236c84f0b55` |
| Image | `lotus-fin:ai003-local`, image ID `sha256:ed6e02f587eb450a0882ecb4b6fbb259d1a1f27f549e1cc4bbe21a660b3017b7` |
| Local RepoDigests | `lotus-fin@sha256:ed6e02f587eb450a0882ecb4b6fbb259d1a1f27f549e1cc4bbe21a660b3017b7`; local metadata observed, registry availability not tested |
| Image/platform | Created `2026-10-03T15:45:15.535651656Z`, Linux/amd64 |
| Container/start | Created October 3; started `2026-10-12T09:33:22.233390437Z` |
| Process settings | User `frappe`, directory `/home/frappe/frappe-bench`, entrypoint `/usr/local/bin/entrypoint.sh`, command `start.sh` |
| Mounts | Only `frappe_docker_sites` and `frappe_docker_logs`; no application source bind mount |
| Compose lineage | Project `frappe_docker`; `E:/frappe_docker/pwd.yml` plus `E:/lotus-fin/docker/ai003-local/compose.override.yml`; working directory `E:/frappe_docker` |
| Frontend | `frappe_docker-frontend-1`, custom tag, host port 8080; routes default to shared `frontend`, ai003 host pattern to `ai003-verify.localhost` |

Other queues/scheduler/websocket are running under the same custom tag; their individual module/import bytes were not certified. A tag match is not an immutable worker-identity check. All inspected targets remain excluded from P2 live testing.

## Why the 17 files are absent

The current Dockerfile uses `COPY lotus_fin/ /home/frappe/frappe-bench/apps/lotus_fin` at build time, then an editable `pip install --no-deps -e`. Adjacent Dockerfile.dockerignore admits the Lotus tree and a specific AI002 synthetic fixture. The Compose override supplies an image tag, no live app-source mount or build stanza. Restarting Docker therefore restarts the October 3 filesystem; it does not copy the October 12 host source.

Image history confirms the app COPY and install layers were created October 3. Fresh filesystem hashing finds all 17 selected P1/P2 files on the host and none at the expected import paths in the serving container. **Additional Docker writable-layer inspection found 1511 existing changes beneath the Lotus app**, including directories/bytecode, changed hooks/package metadata, added older application modules and an extra nested `lotus_fin/lotus_fin/lotus_fin` tree. These are pre-existing runtime changes, not writes performed by this task. The live app is therefore an old image plus runtime modifications; its digest alone does not identify serving source.

There is no automatic current host-source synchronization: the expected P1/P2 modules have not arrived at the import root. Existing run scripts demonstrate an imperative copy/install/migrate/restart path, and the runtime drift is consistent with earlier copy/patch operations, but the exact actor/commands/timing are not established by Docker diff. The original image source manifest and complete hot-patch lineage are unavailable. No inference that `.dockerignore` excludes P1/P2: the current allowlist admits them if present in a future context. See [bounded writable-layer evidence](docs/reviews/evidence/chatbot-private-erp-discovery-2026-10-12-1655-a12f82/CONTAINER_APP_LAYER_DIFF.json). Runtime source/hook/version observations in this report describe the container filesystem, not certified pristine image bytes or imported resident-worker state.

## Versions, Python and installed-site limits

| Layer | Observed | Qualification limit |
|---|---|---|
| Host | Python 3.13.7 at `C:/Python313/python.exe` | Offline host evidence does not qualify container Python. |
| Bench | Python 3.14.7 at `/home/frappe/frappe-bench/env/bin/python`; prefix bench/env, base `/usr/local` | Current interpreter metadata only. |
| Source versions | Frappe 16.34.0, ERPNext 16.35.0, Lotus 0.0.1 | Parsed version literals; no application imports. |
| Distributions | Pydantic 2.12.5, Werkzeug 3.1.6, PyMySQL 1.1.2, Lotus 0.0.1 | Flit-core not installed in running bench environment; build isolation may download it. |
| Python search roots | bench/env site-packages and bench/apps/{erpnext,frappe,lotus_fin} | Root path exists; missing P1/P2 modules remain unimportable from that root. |
| Local base image | `frappe/erpnext:v16.35.0`, ID and RepoDigest `sha256:77eedd6d4180452d1c2832c2f762e588e20de85c038ed8c148aa77007329a8f3`, Linux/amd64 | Candidate pin only; no pull/build/private approval or compatibility execution. |
| Bench apps.txt | erpnext, frappe, lotus_fin | Not installed-site app order, hooks or permissions. |
| Disk sites | frontend, ai003-verify.localhost | No DB connection; neither selected for this task. |

Host package requires Python >=3.10, with no declared runtime dependencies in pyproject; separate requirements use open lower bounds for pandas/numpy/pydantic. Build-system flit_core range is not an exact dependency lock. Thus a successful editable install cannot certify the P1/P2 dependency set or Python 3.14 compatibility. Run accepted tests and import checks inside the new authorized image.

Static hook files were hashed and declared keys inspected. Installed site apps, effective hook order, customizations, schema, current request principal, disabled-user behavior and System Settings timezone are **NOT_RUN**. Candidate invoice/key/map/sink configuration keys were absent in common/site JSON; only key-presence booleans were recorded. This does not rule out an external secret/config store or prove actual site settings absent.

## Reproducibility assessment

**Current source-to-image process is not qualified as reproducible.** A build recipe exists, but the serving artifact has no captured source manifest, uses a mutable base tag, is older than current dirty source and has substantial existing writable-layer app drift. Required untracked inputs are not recoverable from a clean clone plus tracked diff. The broad app COPY can admit cache/agent metadata; Docker ignores and Git ignores differ. External Compose is outside the repository. Dependencies/build frontend artifact are not locked into a canonical P2 release. CI's build-and-test job is a placeholder, not acceptance.

A reproducible private build requires the following explicit manifest fields before execution:

| Manifest field | Required content |
|---|---|
| Source | HEAD, branch, dirty/staged patch identity, every included tracked/dirty/untracked file with relative path, original byte SHA256 and length; archived source bytes retained |
| Exclusions | Reviewed caches, agent plans, secrets, unrelated fixtures; dependency/import confirmation for any code exclusion |
| Build | Exact Dockerfile/ignore/Compose/support hashes, build args without secrets, Linux/amd64, pinned base registry digest |
| Dependencies | Exact build/runtime wheel versions and hashes, approved wheelhouse/index policy; verify installed versions instead of relying on no-deps |
| Frontend | Separate React source/lock/toolchain/build/artifact identity and route ownership if selected; current ERP image does not package React |
| Runtime | New private project/site/network/owned volumes, all service image IDs, worker imports/hashes, installed-site apps/hooks/schema/timezone |
| Lifecycle | Approved bootstrap/fixture mutation, snapshot ID/provenance, restore rehearsal, cleanup/rollback object allowlist |

The evidence SOURCE_BEFORE is a discovery fingerprint inventory, **not an approved build manifest**. Its hash is in IDENTITY.json; approval and retained materialized bytes are still required.

## Proposed build commands — NOT EXECUTED

Use only after A01–A10 approval. The new private Compose/Dockerfile/manifest below are design paths and do not yet exist. No command targets `lotus-fin:ai003-local`, `frontend`, AI003 or judge. The approved private recipe must pin `FROM frappe/erpnext@sha256:77eedd6d4180452d1c2832c2f762e588e20de85c038ed8c148aa77007329a8f3`, copy only manifest-materialized inputs, preserve required assets, and use locked build dependencies. Keep any AI002 fixture explicitly synthetic or omit it in the separately reviewed private recipe.

```powershell
# Supply operator-approved absolute paths and exact new identifiers.
$privateManifest = '<approved-private-manifest.json>'
$privateContext = '<approved-materialized-context>'
$privateRecipe = '<approved-private-Dockerfile>'
$privateTag = '<approved-new-private-tag>'
$privateCompose = '<approved-private-compose.yml>'
$privateProject = '<approved-new-private-project>'
# Before build: validate names, ownership/nonexistence, archive hashes and every input.
$inputs = Get-Content -LiteralPath $privateManifest -Raw | ConvertFrom-Json
foreach ($item in $inputs.files) {
    # Paths must already be validated as relative and inside privateContext.
    $inputPath = Join-Path $privateContext $item.path
    if ((Get-FileHash -LiteralPath $inputPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $item.sha256) {
        throw "Approved source hash mismatch"
    }
}
docker build --platform linux/amd64 --pull=false --no-cache `
    --file $privateRecipe --tag $privateTag $privateContext
if ($LASTEXITCODE -ne 0) { throw 'Private build failed' }
docker image inspect $privateTag --format '{{json .Id}} {{json .RepoDigests}}'
# Record the resulting ID; approve service mapping to that exact ID before start.
docker compose -p $privateProject -f $privateCompose config --quiet
if ($LASTEXITCODE -ne 0) { throw 'Private configuration invalid' }
# Only after approved snapshot/bootstrap lifecycle and object-ownership checks:
docker compose -p $privateProject -f $privateCompose up -d
if ($LASTEXITCODE -ne 0) { throw 'Private startup failed' }
```

This is a conditional command template, not a runnable current deployment recipe or approval. Manifest path validation must reject rooted paths, traversal, links escaping the context and duplicate/colliding paths. Freeze captured source bytes before build; do not reconstruct dirty/untracked code from Git HEAD. Pin DB/Redis/platform too; do not quietly inherit current open service tags. Do not call current `run.ps1 sync/run/test/demo`.

After authorized start, use bench Python for selected module imports and per-file origin/hash checks in a fresh process **and each serving worker**, then actual installed-site list-apps/hooks/schema checks. Verify no app-source hot patch or unexpected mount. A source file/spec or process smoke does not prove a resident worker imported it. Cold start a second instance of the same approved image against a separately approved restored baseline and repeat lineage/readiness/smoke. Full image rebuild must reproduce manifest inputs; byte-identical image IDs are not claimed where timestamps/build tooling vary.

## Snapshot, restore and cleanup qualification — NOT_RUN

Take an approved baseline containing DB, site/files/config and relevant cache/queue/session state; retain image/config hashes and fixture oracle. Rehearse restore into an approved separate private instance and compare business/permission/settings/file fingerprints. After tests, restore changed permission/key/sink/schema settings and remove only explicitly approved fixture objects/resources. Verify owned object IDs and residue; never global prune, shared Redis flush or reuse historical AI003 cleanup.

Rollback: disable private API/UI capability, reject outstanding references by approved key/config policy, redeploy the last accepted private image, restore the approved baseline only when migration/data scope requires it, then prove disabled behavior and restored fingerprints. Provisioning and restoration can write ERP state; classify them separately from the measured read-only request interval. No restoration, cleanup deletion or business read was executed here.

**PRIVATE_TARGET_READY BLOCKED; ADAPTER_IMPLEMENTATION BLOCKED; REAL_HTTP_ACCEPTANCE NOT_RUN; ERP_PERMISSION_ACCEPTANCE NOT_RUN; ERP_NO_WRITE NOT_RUN; P2AB_LIVE_ACCEPTANCE BLOCKED; G10 BLOCKED.**

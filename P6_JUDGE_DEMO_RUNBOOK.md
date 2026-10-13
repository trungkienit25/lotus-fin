# P6 judge demo runbook

This demonstrates one integrated product using fictional DEMO data. It is not a qualified native finance release. N0 remains BLOCKED. No real side-effect adapter is enabled.

## Reproduce an owned Frappe-only stack

### Recovery build with low disk usage

After the Docker reset, the P6 rebuild uses `docker/lotus-core/Dockerfile.lean` and a temporary dedicated builder. The runtime keeps the pinned Frappe build/base environment once, avoiding the full bench copy into a second large stage. It still runs as `frappe` and retains the same Frappe/app pins and disabled native execution boundary. Build tools remain in this demo image; this is not a hardened production image.

```powershell
docker buildx create --name lotus-p6-clean-01a1358e --driver docker-container --driver-opt env.BUILDKIT_STEP_LOG_MAX_SIZE=32768 --driver-opt env.BUILDKIT_STEP_LOG_MAX_SPEED=1024
docker buildx build --builder lotus-p6-clean-01a1358e --no-cache --progress=quiet --provenance=false --load -f docker/lotus-core/Dockerfile.lean -t lotus-fin:core-p6-01a1358e .
docker buildx rm --force lotus-p6-clean-01a1358e
docker compose --project-name lotus-core-p6-01a1358e --env-file .runtime/lotus-core-p6-01a1358e/core.env -f docker/compose.lotus-core.yml -f docker/compose.p6-low-disk.yml up -d --wait --wait-timeout 240
```

The final command reuses only the previously owned P6 identity/secrets after its Docker volumes were removed. A fresh clone must first initialize its own ownership/secrets using the setup helper. Use the low-disk overlay for every later start/restart of this demo. Each container's stdout/stderr log is bounded to two 1 MB files. Do not keep verbose build logs, database dumps, duplicate source copies or unrelated images. Delete only the dedicated temporary builder; do not use global prune against unrelated data. Docker storage is on drive E in this environment.

The recovered instance is running and passed cold restart. Its temporary builder/helper image and completed init container have been removed. Redis snapshot/AOF is disabled for the isolated transient demo queues/cache; business execution remains disabled. Frappe site/MariaDB data and fictional SQLite receipts remain persistent. The retained original full-copy recipe below is historical; use the lean recovery recipe above for this instance.

Use Python 3.13+ and Docker Desktop/Linux containers. Build from the complete dirty working tree, not HEAD alone:

```powershell
python docker/lotus-core/manage.py build --project lotus-core-p6-01a1358e
python docker/lotus-core/manage.py setup --project lotus-core-p6-01a1358e --port 8114 --authorize-isolated lotus-core-p6-01a1358e
python docker/lotus-core/manage.py smoke --project lotus-core-p6-01a1358e --port 8114
```

For a fresh independent copy choose a new `lotus-core-p6-<unique>` project, matching site `core-p6-<unique>.localhost`, and an unused loopback port. Never adopt a shared project. The current builder instance uses port 8114. Runtime secrets are generated in ignored `.runtime/<project>/core.env`. Do not commit them or put them in evidence.

Enable only the isolated simulator through the owned site's server setting `lotus_copilot_demo_enabled = true` (a parsed boolean), and run `docker/lotus-core/provision_demo.py` inside its backend with a private `LOTUS_DEMO_PASSWORD`. The provisioning utility refuses non-P6 sites and existing accounts. It creates fictional Alice/Bob accounts and two permission-free demo roles, without Company/Sales Invoice schema or business records. CORE is unchanged by DEMO enablement. Disable the server switch to verify that L4/L5/V1 simulator requests return DEMO_DISABLED.

## One product demonstration

1. Open http://127.0.0.1:8114/copilot and log in with the owned fictional Alice account. Use the private credentials file under `.runtime/lotus-core-p6-01a1358e/`.
2. Ask “Giải thích Lotus Fin là gì”; inspect L0's local explanation. Ask an ambiguous “Tạo cái đó” and observe clarification.
3. Select DEMO globally, then Invoice Actions. Choose NORMAL, Submitted status and Find invoices. Explicitly select/Open a row. Read the fictional source badge.
4. Click “Soạn lời nhắc cho hóa đơn đã chọn (L3)”. Prepare, edit and review the local unsaved/unsent draft; Copy or Discard are available. No network request occurs for local draft edits.
5. Review the draft and click “Chuẩn bị đề xuất Task (L4)”. Edit title, text and follow-up date, then click “Xem đề xuất Task”. Check field changes, fictional source and expiry.
6. Click the separate Confirm & Execute control. Verify **SIMULATED_SUCCEEDED**, synthetic receipt and one execution attempt. Refresh status; repeated server confirmation returns the same receipt.
7. Open L5; review Submit/Cancel/Email/Payment/Scheduler policy. Observe denied/unavailable approval provider and DISABLED side effects. No actual business action follows.
8. Open V1 and search past-final-due invoices. Verify fixed observation date, VND decimal strings and the two fictional gold rows (12 and 8 days overdue). Drilldown stays disabled without a valid native handle.
9. Switch CORE. Protected fictional results, previews and pending proposals clear. CORE requests return NOT_AVAILABLE/CAPABILITY_DISABLED, not synthetic success.
10. Switch back to DEMO, leave an unconfirmed proposal, log out in another tab and return. Verify state clearance; old confirmation cannot be replayed. Log in as Bob and verify old handles/proposals are unavailable.
11. Repeat the feature controls in the approved drawer, inspect the 390px scenario selector and keyboard focus, and cold-restart only this owned stack. Recheck login, CSRF, source hashes and unavailable CORE.

Use docker/lotus-core/acceptance.py for offline contracts and qualify_copilot.py for loopback HTTP checks. Browser evidence and source provenance are described in P6_BROWSER_E2E.md and P6_BUILD_AND_SOURCE_REPRODUCIBILITY.md. Successful builder tests do not qualify G10.

# P6 source pre-push — CHANGES_REQUIRED / security blocked

Independent review of actual working-tree bytes, 13–14 October 2026, Asia/Saigon. Branch `codex/p2a-invoice-read-backend`, HEAD `5f805ef34f788245a3ec0e9c2f44e224eb16c305`. The Git staging area is empty. This reviewer did not stage, commit, push or deploy; all original tracked modifications and untracked implementation work were retained.

## Executed source and test gates

| Gate | Result |
| --- | --- |
| Backend invoice/action/session/P6 regression list | 507 passed, exit 0; exact selection is the existing release runner's backend argv |
| P6 integration/L4/L5/V1 subset | 67 passed, exit 0; overlaps preceding suite |
| Frontend P1/P2/L3/P4/P6 tests | 124 passed, no skips, exit 0 |
| AI001–AI003 selected foundation/health/cash/risk suites | 376 passed + 7 subtests, exit 0 |
| Broad host collection | 968 collected; four collection errors, exit 2 |
| Independent source probes | Session race/poll fail; V1 18/22 observations pass; probe exit 0 is a collector exit, not acceptance PASS |
| TypeScript + production React build | Pass after sandbox denied TypeScript cache writes; unsandboxed retry exit 0 |
| Frontend lint | Exit 0 with warnings; not warning-free |
| Package/lock consistency | `npm ci --dry-run --ignore-scripts --no-audit --no-fund`, exit 0; not a new clean install/clone |
| Serving Python dependency consistency | `pip check`: no broken requirements |
| Git whitespace | Pass; CRLF conversion notices are not whitespace defects |
| Fresh frontend advisory check | Exit 1; eight HIGH/two MODERATE affected package entries |
| Current Python advisory metadata | 136 installed packages examined; six names flagged; framework/local app not PyPI-qualified |

The source/build identity recheck passes in its measured scope: all 331 packaged Python/JSON files match current backend source, with no extra local product Python/JSON files omitted. The six app containers share one image and have no source bind mounts. An independently rerun local build produces exactly the image's JS/CSS, and actual HTTP downloads match those image bytes:

- JS `assets/index-BkPE-kGj.js`: `d6614f1598dc867d868959b280df5f8691f6152fc1a8e3c7b83cf37f5ea3fd8c`.
- CSS `assets/index-Dzl5mkXx.css`: `c44a7d18afccd01bb5abcd5b01611ce78397d41a2be010e164b2a60e2d1c4716`.

This is source/disk/serving provenance, not a Python in-memory code attestation, reproducible base-image build, independent cold restart or reviewed clean Git clone. No new serving image was built or deployed in this review.

## Dependency security

Fresh npm audit confirms the production `@refinedev/antd → @ant-design/pro-layout → path-to-regexp` chain. Current lock has path-to-regexp 8.2.0; affected range is >=8.0.0 <8.4.0 in [GHSA-j3q9-mxjg-w52f](https://github.com/advisories/GHSA-j3q9-mxjg-w52f) and [GHSA-27v5-c462-wpq7](https://github.com/advisories/GHSA-27v5-c462-wpq7). Development chains additionally flag braces and postcss-selector-parser. Ten affected package entries are not ten independent root vulnerabilities. Static route use alone is insufficient to close reachability; no exploit was attempted.

Actual serving versions flagged by primary PyPI metadata: oauthlib 3.3.1, pdfkit 1.0.0, PyJWT 2.13.0, pypdf 6.15.0, weasyprint 68.0 and Werkzeug 3.1.6. Advisory aliases and affected-range/reachability decisions remain unclosed. `PYTHON_ADVISORIES.json` retains complete metadata, including source links/fix versions; package consistency is not a security clearance. Local frappe 16.35.0 and lotus_fin are outside this metadata check. Follow separate minimal frontend/runtime batches IA06/IA07, without blanket major audit fixes.

## Collection, CI and graph

`test_architecture_remediation.py` imports nonexistent `BaselineSourceError` from the current AI004 baseline adapter. Three other errors (`test_access_and_reports.py`, `test_security_hardening.py`, `test_workspace_ui.py`) require the Frappe test environment. They were neither skipped nor weakened to obtain the scoped PASS.

The old echo build gate and SAST continue-on-error are removed. `copilot-integration.yml` includes codex/** pushes, actual frontend tests/build/lint and five P6 backend files, but it does not enforce the broader P1/P2 backend and AI001–003 gates rerun here. Its Python test dependencies remain partly floating. `ci.yml` still excludes codex/** pushes from its SAST branch trigger. No remote CI run exists for these uncommitted bytes, and no SAST result for this exact candidate was obtained. IA08/IA09 provide narrow corrections.

GitNexus was bound to lotus-fin, indexed at 2026-10-13T14:38:21.413Z on this branch/HEAD. Concept queries report FTS disabled and empty results; named context/impact works, so confirming source inspection followed. The CLI display truncates flow listings even with a large limit; it was not accepted as clean. A direct call to the same LocalBackend produced complete structured `detect_changes(scope=all,limit=10000)`: 29 changed tracked files, 104 symbols and 64 affected flows, CRITICAL risk; array lengths equal summary counts, with no partial/truncated flag. See `GRAPH_STRUCTURED.json`. Untracked implementation additions are not Git diff hunks and must not inherit a zero-change verdict from this report. Named impacts for the actual session and V1 additions are retained.

Before any later reviewed commit, rebind/reindex the selected product candidate and analyze each included untracked addition plus the complete tracked change set. Preserve the CRITICAL warning and explicitly review Page/Drawer/auth/transport callers. This is a scoped graph-review batch, not permission to stage now. There is no UNKNOWN-as-low assumption.

A narrow private-key/token pattern check on product paths found the scanner's own regex in `docker/lotus-core/package_release.py`, not an actual matching secret. This is not comprehensive secret certification of every historical evidence directory. Runtime credentials remain in ignored `.runtime`; generated reviewer evidence contains no passwords, SID cookies or CSRF tokens. Do not blindly stage the repository's large untracked evidence/snapshot/tool inventory.

Developer reviewed-commit readiness is withheld because security and concrete quality/documentation defects remain. Native financial release and G10 are separately BLOCKED even after those corrections.

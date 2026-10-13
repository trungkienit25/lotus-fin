# Lotus recommended commit plan

13 October 2026 · Asia/Saigon · Independent acceptance of `E:/lotus-fin`.

Branch `codex/p2a-invoice-read-backend`; HEAD `5f805ef34f788245a3ec0e9c2f44e224eb16c305`. The candidate is current dirty/untracked working-tree bytes, not HEAD. No production source edit, stage, commit, push, merge or deployment was performed. Tests used only local fixtures and the previously qualified isolated `lotus-core-01a13314` / `core-01a13314.localhost` / loopback 8097. N0 remains BLOCKED.

Evidence directory: [p3-independent-2026-10-13](docs/reviews/evidence/p3-independent-2026-10-13). Exact candidate: [CANDIDATE_SOURCE.json](docs/reviews/evidence/p3-independent-2026-10-13/CANDIDATE_SOURCE.json), 616 files, SHA256 `02da08611f41de6e9ceff876e95bf48e11150cf9cdbe8e06819f816ae3cb8c70`. Every executed test command, inner-command exit code and output hash is in [COMMANDS_AND_EXITS.json](docs/reviews/evidence/p3-independent-2026-10-13/COMMANDS_AND_EXITS.json). Collector shells may exit 0 after recording a failed child; use the recorded child exit. Failed attempts are retained.

**No staging/commit authorization is exercised. This plan is conditional on closing the P1 security defects and rerunning acceptance.**

1. **P2-A typed security/backend boundary:** current modified invoice request/read/controller/auth/delivery tests plus new HTTP DTO, config loader, cache session repository and security tests. Include all imported files and explicit offline test dependency recipe. Preserve HMAC/Pydantic/security assertions. Separate numerical feature work from this change.
2. **Frappe-only default runtime:** hooks, core fixture deletion, hidden workspace, core logo, pyproject, docker/compose.lotus-core.yml, all docker/lotus-core source/locks/examples and run helpers. Stage deletion only with the optional fixture transfer/integration source or a separately reviewed preservation artifact. Keep core installed apps exact. A default startup cannot depend on files left untracked.
3. **P3 UI/transport/DEMO/L3:** page/drawer/dynamic hook fix, all action/components/prepare/demo source and current tests_e2e harness + three scoped regression tests. Apply P1-01/03 and P2-04/07 corrections first; include mounted integration tests and CSRF/session tests. Do not split UI transport from its imported decoder/controller dependencies.
4. **Acceptance/docs and actual CI gate:** updated README/current runbook, corrected seven builder reports if retained, seven independent root reports, minimal sanitized manifests/command receipts/oracles/browser proof. Replace placeholder checks in a separate approved source change; preserve .gitignore and line-ending policy. Do not commit copied source trees, frontend-build/clean-frontend/node_modules/dist, archives, old videos, secrets/private runtime, or the full local skill collection.
5. **Optional historical ERP package, only if intended:** docker/judge and compose.judge additions are not required to prove core startup and must not quietly become the default. Keep any optional integration clearly unqualified. Unrelated data/design/skills/history remains outside this release commit.

Before staging later: rebind source hashes, finish complete GitNexus graph review, scan the exact planned files, check the actual staged diff and whitespace, run required tests/build, rebuild current-source CORE image and verify ordinary-user browser/session/profile negatives. Then verify the proposed commit in a disposable clean checkout with public dependencies and generated local-only QA credentials. Only after that can a disclosed dev/MVP branch be push-ready while N0 remains BLOCKED. No G10 or financial readiness follows from that allowance.

## Exact changed-source path plan

The following list is exhaustive for the selected 140 candidate changes/additions, not a command to stage them. STAGED_FILE_PLAN.json binds each path to its current SHA256. Some paths are deliberately assigned to the optional/history boundary above; decide that scope before committing. Tests/security keys below are explicit offline fixture strings, never production configuration.

- `.gitignore` (M)
- `frontend/src/components/copilot/LotusCopilotDrawer.tsx` (M)
- `frontend/src/pages/copilot/LotusCopilotPage.tsx` (M)
- `frontend/src/pages/copilot/components/VercelChatPanel.tsx` (M)
- `frontend/src/pages/dynamic/UniversalPageView.tsx` (M)
- `lotus_fin/lotus_fin/api/invoice_actions_api.py` (M)
- `lotus_fin/lotus_fin/application/service/search_invoices.py` (M)
- `lotus_fin/lotus_fin/domain/schema/invoice_read.py` (M)
- `lotus_fin/lotus_fin/fixtures/custom_field.json` (D)
- `lotus_fin/lotus_fin/hooks.py` (M)
- `lotus_fin/lotus_fin/infrastructure/config/invoice_actions_config.py` (M)
- `lotus_fin/lotus_fin/infrastructure/security/frappe_invoice_authorizer.py` (M)
- `lotus_fin/lotus_fin/lotus_fin_ai/workspace/lotus_fin_ai/lotus_fin_ai.json` (M)
- `lotus_fin/lotus_fin/presentation/controller/invoice_actions_controller.py` (M)
- `lotus_fin/lotus_fin/presentation/dto/invoice_action_request.py` (M)
- `lotus_fin/lotus_fin/tests/test_action_reference_privacy.py` (M)
- `lotus_fin/lotus_fin/tests/test_invoice_auth_delivery.py` (M)
- `lotus_fin/lotus_fin/tests/test_invoice_context.py` (M)
- `lotus_fin/lotus_fin/tests/test_invoice_permission_seam.py` (M)
- `lotus_fin/lotus_fin/tests/test_invoice_terminal_delivery.py` (M)
- `lotus_fin/pyproject.toml` (M)
- `run.ps1` (M)
- `run.sh` (M)
- `.gitattributes` (??)
- `README.md` (??)
- `docker/compose.judge.yml` (??)
- `docker/compose.lotus-core.yml` (??)
- `docker/judge/init.sh` (??)
- `docker/judge/smoke.py` (??)
- `docker/lotus-core/.env.example` (??)
- `docker/lotus-core/Dockerfile` (??)
- `docker/lotus-core/Dockerfile.dockerignore` (??)
- `docker/lotus-core/framework.lock` (??)
- `docker/lotus-core/http_qualification.py` (??)
- `docker/lotus-core/init.sh` (??)
- `docker/lotus-core/manage.py` (??)
- `docker/lotus-core/package_release.py` (??)
- `docker/lotus-core/provision_qa.py` (??)
- `docker/lotus-core/requirements.lock` (??)
- `docker/lotus-core/smoke.py` (??)
- `docker/lotus-core/upstream/main-entrypoint.sh` (??)
- `docker/lotus-core/upstream/start.sh` (??)
- `docker/offline-acceptance/Dockerfile` (??)
- `docker/offline-acceptance/requirements.lock` (??)
- `frontend/src/pages/copilot/actions/InvoiceActionPanel.tsx` (??)
- `frontend/src/pages/copilot/actions/InvoiceReadView.tsx` (??)
- `frontend/src/pages/copilot/actions/InvoiceSearchResults.tsx` (??)
- `frontend/src/pages/copilot/actions/invoiceActionClient.ts` (??)
- `frontend/src/pages/copilot/actions/invoiceActionController.ts` (??)
- `frontend/src/pages/copilot/actions/invoiceActionControllerOps.ts` (??)
- `frontend/src/pages/copilot/actions/invoiceActionControllerState.ts` (??)
- `frontend/src/pages/copilot/actions/invoiceActionCriteria.ts` (??)
- `frontend/src/pages/copilot/actions/invoiceActionDecoderHelpers.ts` (??)
- `frontend/src/pages/copilot/actions/invoiceActionDecoders.ts` (??)
- `frontend/src/pages/copilot/actions/invoiceActionPayloadDecoders.ts` (??)
- `frontend/src/pages/copilot/actions/invoiceActionPresentation.ts` (??)
- `frontend/src/pages/copilot/actions/invoiceActionTypes.ts` (??)
- `frontend/src/pages/copilot/actions/useInvoiceActions.ts` (??)
- `frontend/src/pages/copilot/components/CopilotMessageBody.tsx` (??)
- `frontend/src/pages/copilot/components/copilotPresentation.ts` (??)
- `frontend/src/pages/copilot/components/useCopilotRequest.ts` (??)
- `frontend/src/pages/copilot/demo/demoInvoiceProvider.ts` (??)
- `frontend/src/pages/copilot/prepare/FollowupPreview.tsx` (??)
- `frontend/src/pages/copilot/prepare/followupPreview.ts` (??)
- `frontend/src/pages/copilot/prepare/followupPreviewController.ts` (??)
- `frontend/tests/followupPreview.test.ts` (??)
- `frontend/tests/followupPreviewController.test.ts` (??)
- `frontend/tests/p2b/client.test.ts` (??)
- `frontend/tests/p2b/controller.test.ts` (??)
- `frontend/tests/p2b/fixtures.ts` (??)
- `frontend/tests/p2b/presentation.test.ts` (??)
- `frontend/tests/p3_transport_and_demo.test.ts` (??)
- `integrations/lotus_erpnext/README.md` (??)
- `integrations/lotus_erpnext/lotus_erpnext/__init__.py` (??)
- `integrations/lotus_erpnext/lotus_erpnext/custom_field.legacy.json` (??)
- `integrations/lotus_erpnext/lotus_erpnext/events.py` (??)
- `integrations/lotus_erpnext/lotus_erpnext/fixtures/custom_field.json` (??)
- `integrations/lotus_erpnext/lotus_erpnext/hooks.py` (??)
- `integrations/lotus_erpnext/lotus_erpnext/install.py` (??)
- `integrations/lotus_erpnext/lotus_erpnext/modules.txt` (??)
- `integrations/lotus_erpnext/lotus_erpnext/workspace.legacy.json` (??)
- `integrations/lotus_erpnext/pyproject.toml` (??)
- `lotus_fin/lotus_fin/infrastructure/config/invoice_actions_config_loader.py` (??)
- `lotus_fin/lotus_fin/infrastructure/persistence/frappe_cache_session_repository.py` (??)
- `lotus_fin/lotus_fin/presentation/dto/invoice_action_http_request.py` (??)
- `lotus_fin/lotus_fin/public/logo.svg` (??)
- `lotus_fin/lotus_fin/runtime/__init__.py` (??)
- `lotus_fin/lotus_fin/runtime/boundary.py` (??)
- `lotus_fin/lotus_fin/runtime/health.py` (??)
- `lotus_fin/lotus_fin/tests/test_architecture_remediation.py` (??)
- `lotus_fin/lotus_fin/tests/test_frappe_only_boundary.py` (??)
- `lotus_fin/lotus_fin/tests/test_invoice_config_loader.py` (??)
- `lotus_fin/lotus_fin/tests/test_invoice_config_rotation_security.py` (??)
- `lotus_fin/lotus_fin/tests/test_invoice_context_data_correction.py` (??)
- `lotus_fin/lotus_fin/tests/test_invoice_controller_context_expiry.py` (??)
- `lotus_fin/lotus_fin/tests/test_invoice_controller_wiring.py` (??)
- `lotus_fin/lotus_fin/tests/test_invoice_http_boundary.py` (??)
- `lotus_fin/lotus_fin/tests/test_invoice_read_family_correction.py` (??)
- `lotus_fin/lotus_fin/tests/test_invoice_request_correction.py` (??)
- `lotus_fin/lotus_fin/tests/test_pydantic_b1_hardening.py` (??)
- `tests_e2e/copilot_fixture/.vite/deps/_metadata.json` (??)
- `tests_e2e/copilot_fixture/.vite/deps/axios.js` (??)
- `tests_e2e/copilot_fixture/.vite/deps/axios.js.map` (??)
- `tests_e2e/copilot_fixture/.vite/deps/package.json` (??)
- `tests_e2e/copilot_fixture/.vite/deps/react-dom.js` (??)
- `tests_e2e/copilot_fixture/.vite/deps/react-dom.js.map` (??)
- `tests_e2e/copilot_fixture/.vite/deps/react-dom_client.js` (??)
- `tests_e2e/copilot_fixture/.vite/deps/react-dom_client.js.map` (??)
- `tests_e2e/copilot_fixture/.vite/deps/react-router-dom.js` (??)
- `tests_e2e/copilot_fixture/.vite/deps/react-router-dom.js.map` (??)
- `tests_e2e/copilot_fixture/.vite/deps/react.js` (??)
- `tests_e2e/copilot_fixture/.vite/deps/react.js.map` (??)
- `tests_e2e/copilot_fixture/.vite/deps/react_jsx-dev-runtime.js` (??)
- `tests_e2e/copilot_fixture/.vite/deps/react_jsx-dev-runtime.js.map` (??)
- `tests_e2e/copilot_fixture/.vite/deps/react_jsx-runtime.js` (??)
- `tests_e2e/copilot_fixture/.vite/deps/react_jsx-runtime.js.map` (??)
- `tests_e2e/copilot_fixture/.vite/deps/rolldown-runtime-DC62tzP2.js` (??)
- `tests_e2e/copilot_fixture/index.html` (??)
- `tests_e2e/copilot_fixture/main.tsx` (??)
- `tests_e2e/copilot_fixture/vite.config.ts` (??)
- `tests_e2e/copilot_test_harness.py` (??)
- `tests_e2e/followup_preview_fixture/.vite/deps/_metadata.json` (??)
- `tests_e2e/followup_preview_fixture/.vite/deps/package.json` (??)
- `tests_e2e/followup_preview_fixture/.vite/deps/react-dom.js` (??)
- `tests_e2e/followup_preview_fixture/.vite/deps/react-dom.js.map` (??)
- `tests_e2e/followup_preview_fixture/.vite/deps/react-dom_client.js` (??)
- `tests_e2e/followup_preview_fixture/.vite/deps/react-dom_client.js.map` (??)
- `tests_e2e/followup_preview_fixture/.vite/deps/react.js` (??)
- `tests_e2e/followup_preview_fixture/.vite/deps/react.js.map` (??)
- `tests_e2e/followup_preview_fixture/.vite/deps/react_jsx-dev-runtime.js` (??)
- `tests_e2e/followup_preview_fixture/.vite/deps/react_jsx-dev-runtime.js.map` (??)
- `tests_e2e/followup_preview_fixture/.vite/deps/react_jsx-runtime.js` (??)
- `tests_e2e/followup_preview_fixture/.vite/deps/react_jsx-runtime.js.map` (??)
- `tests_e2e/followup_preview_fixture/.vite/deps/rolldown-runtime-BvCyGRYZ.js` (??)
- `tests_e2e/followup_preview_fixture/index.html` (??)
- `tests_e2e/followup_preview_fixture/main.tsx` (??)
- `tests_e2e/followup_preview_fixture/vite.config.ts` (??)
- `tests_e2e/test_copilot_failclosed.py` (??)
- `tests_e2e/test_followup_preview_e2e.py` (??)
- `tests_e2e/test_invoice_actions_e2e.py` (??)

## Exact independent report additions

- `LOTUS_P3_INDEPENDENT_ACCEPTANCE.md`
- `LOTUS_P3_SECURITY_RECHECK.md`
- `LOTUS_CORE_DEMO_E2E_MATRIX.md`
- `LOTUS_ERP_INDEPENDENCE_RECHECK.md`
- `LOTUS_GITHUB_PRE_PUSH_AUDIT.md`
- `LOTUS_RECOMMENDED_COMMIT_PLAN.md`
- `LOTUS_P3_WORK_TO_CHAT.md`

Audit evidence must be added file-by-file from the public evidence manifest, after checking hashes/redaction. .log files are ignored; matching .txt copies preserve output hashes. No blanket evidence-directory staging.

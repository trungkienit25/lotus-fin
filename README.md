# Lotus Fin

Current chatbot handoff: [proposal progress, remaining gaps and improvements](CHATBOT_PROPOSAL_PROGRESS_AND_IMPROVEMENTS.md), updated 14 October 2026. The `codex/chatbot` branch is a review candidate with independent verdict **P6_SECURITY_BLOCKED**; it does not approve native financial release, N0, real L4/L5 execution or G10.

Lotus Fin targets an independent financial product using Frappe as a framework and React as its UI. The current AI001–AI003 runtime still relies on ERPNext financial sources. Native chatbot invoice reads are **blocked until Product/Data/Security approve the source and policy**; this checkout is not a qualified judge release.

The integrated chatbot is available at `/copilot` and in the approved drawer. It includes L0 explanation/clarification, L1/L2 explicit invoice search/open, L3 local reminder drafting, L4 proposal/confirmation/status, L5 policy review, and V1 PastFinalDue. CORE invoice sources remain unavailable; DEMO uses visibly fictional data and simulated receipts. No real email, payment, submit, cancel or scheduler adapter is enabled.

P6 integration documentation: [integration](P6_FULL_CHATBOT_INTEGRATION.md), [capability matrix](P6_FULL_CAPABILITY_MATRIX.md), [demo runbook](P6_JUDGE_DEMO_RUNBOOK.md), [security](P6_SECURITY_INTEGRATION.md), and [build/source evidence](P6_BUILD_AND_SOURCE_REPRODUCIBILITY.md). Builder checks are distinct from independent acceptance.

The recovered P6 demo runs at `http://127.0.0.1:8114/copilot`. Its current image was rebuilt with no cache using the lean recipe; temporary builder artifacts were removed, logs are bounded, and Redis dumps are disabled for the demo. Use the recovery commands in the [P6 runbook](P6_JUDGE_DEMO_RUNBOOK.md). See [final handoff](P6_FINAL_WORK_TO_CHAT.md) for tested scopes and unresolved release gates.

Run the current offline integration gates with `python docker/lotus-core/acceptance.py`. On Windows, pass `--node "C:\Program Files\nodejs\node.exe"` when the default runtime predates Node 22. Commands, child exits, logs and source/test SHA256 are recorded under `docs/reviews/evidence/p6-full-integration`. The suite explicitly selects invoice/action/session/L4/L5/V1 contracts; full legacy pytest collection remains a separate gate described in the integration report.

## Review and qualified offline checks

Read the [native source/policy decision packet](docs/reviews/evidence/chatbot-release-candidate-2026-10-13-01a132c2/N0_PRODUCT_DATA_SECURITY_DECISION_PACKET.md) and [execution report](docs/reviews/evidence/chatbot-release-candidate-2026-10-13-01a132c2/LOTUS_CHATBOT_FINAL_INTEGRATION_EXECUTION.md).

With Python 3.13, Node 22 and the test/frontend dependencies installed, the evidence runner records each command, exit, execution layer and output hash:

```powershell
python -B docs/reviews/evidence/chatbot-release-candidate-2026-10-13-01a132c2/run_acceptance.py backend
python -B docs/reviews/evidence/chatbot-release-candidate-2026-10-13-01a132c2/run_acceptance.py frontend
python -B docs/reviews/evidence/chatbot-release-candidate-2026-10-13-01a132c2/run_acceptance.py browser
python -B docs/reviews/evidence/chatbot-release-candidate-2026-10-13-01a132c2/run_acceptance.py build
```

Run `backend` first: browser/original UI oracles consume freshly generated typed wire samples. Browser cases use owned local servers and intercepted synthetic transport, then release their ports. They exercise explicit selection, partial/empty results, expired context, malformed response cleanup, XSS and local preview lifecycle. They do not save/send business records.

For a clean core-only test container, use the candidate packaging and commands in the [reproducibility report](docs/reviews/evidence/chatbot-release-candidate-2026-10-13-01a132c2/LOTUS_CHATBOT_REPRODUCIBLE_RELEASE_CANDIDATE.md). `docker/offline-acceptance/Dockerfile` is a pinned test environment without Frappe/ERPNext; it is not a product-serving image or a native data source.

## Existing runtime helpers

The default `run.ps1` and `run.sh` now use the isolated Frappe-only helper. Build:
`python docker/lotus-core/manage.py build --project lotus-core-<id>`.
Setup requires explicit authorization:
`python docker/lotus-core/manage.py setup --project lotus-core-<id> --authorize-isolated lotus-core-<id>`.
Use the same project for `smoke`, `health`, `status`, and `logs`. `cleanup` requires
the same explicit authorization and retains all volumes. The matching site is
`core-<id>.localhost`; the default loopback port is 8097. Pass the same `--port`
on every command when choosing another port. No default shared site is selected.
See [the judge runbook](LOTUS_JUDGE_INSTALL_RUNBOOK.md) and
[runtime evidence](LOTUS_FRAPPE_ONLY_RUNTIME_REPORT.md) for tested commands and limits.
React is built into the image under `/assets/lotus_fin/core/`; inclusion does not
qualify its legacy financial pages or production native action mounts.

### Legacy runtime history (retained for context)

The previous helpers targeted a `frappe_docker` checkout and the shared-named
`frontend` site. Their exact bytes are preserved in the pre-change evidence.
Shared-site `up`, `sync`, `demo`, and `test` are no longer default commands.

`docker/compose.judge.yml` still selects the ERPNext-based recipe; its init installs ERPNext, and the recipe does not include all advertised judge support/React artifacts. It is not an independent Lotus core startup path. No native site/account/schema provisioning is authorized by this README.

Native release requires an approved source, tenant/document/field policy, versioned native contract, Frappe-only serving artifact, ordinary-user HTTP/browser acceptance and independent G10 review. V1 financial reads, form.prefill, L4 saved drafts/tasks and L5 submit/send/payment remain separate unqualified capabilities.

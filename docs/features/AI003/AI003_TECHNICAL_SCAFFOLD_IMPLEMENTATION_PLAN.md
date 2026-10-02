# AI003 — Technical Scaffold Implementation Plan

Work 30/09/2026, HEAD `86208f4`. **Không implement bucket nào trong phiên này.** Kế hoạch để Chat chốt handoff; không cho builder tự freeze/approve policy. Chỉ AR_OVERDUE_SPIKE và AP_DUE_CLUSTER.

## Readiness

| Thành phần | Classification | Điều kiện |
| --- | --- | --- |
| Draft typed schemas, interfaces, mock policy registry, status tests | SAFE_TO_SCAFFOLD | Chat xác nhận draft semantics; không Frappe DB/read/API publish, versions vẫn candidate. |
| Deterministic interface + POLICY_PENDING + Decimal inputs | SAFE_TO_SCAFFOLD với mocks | Không LIVE/default thresholds, source-invalid/zero trước pending, TEST_ONLY tách mode. |
| Real financial source/service/cache/evidence adapters | MUST_WAIT | F0 và independent Work acceptance PASS cho cả ba PB; identity/coverage contract đã chốt. |
| Production findings/severity | MUST_WAIT | Finance/Product approve basis/baseline/windows/floors/thresholds/labels/version; chosen-policy gold verified. |
| Bounded agent/explanation/observability | CONDITIONAL | Mock-only trước F0; real tools chỉ sau foundation/source trust, allowlist/minimized payload. |

Overall **CONDITIONAL**; outcome C NOT READY cho real-data scaffold. Offline development không tương đương foundation readiness.

## F0 — Foundation remediation tập trung

- **Owner/scope:** Antigravity/Zcode sửa đúng PB-SEC-01/PB-DATA-01/PB-DATA-02, Work verify. Chat chốt identity/basis/error semantics; không đổi legacy formula, threshold hoặc thêm AI003.
- **Allowed files:** `lotus_fin/lotus_fin/security/access.py`, `ai/financial_snapshot.py`, `cashflow/adapters.py`, `cashflow/service.py`, `api/key_reports.py` chỉ khi cần typed permission envelope; focused tests trong `lotus_fin/lotus_fin/tests/`, AI003 docs/harness. New shared identity helper cần owner/API agreement. Không unrelated AI004/AI005/frontend.
- **Dependencies:** Chat handoff; current dirty tree preserved; GitNexus impact trước edits, detect before commit, UNKNOWN/stale ghi unresolved + actual caller inspection.
- **Acceptance:** report-specific active/trusted explicit-user auth; real Custom Role revoke → cached/fresh generic FORBIDDEN, no financial payload, evict, regrant. Missing/bad overdue basis → affected metric unavailable, valid total giữ được. Exact duplicates dedup có provenance hoặc reject; conflicting/ambiguous identity failclosed; verified term/account splits reconcile và giữ đủ tiền. Null AP due-date là coverage decision AI003, không phá AI002 nullable contract để test xanh.
- **Required tests:** focused units + real Frappe report-role revoke/regrant inside TTL cho related allowlist; Admin session vs explicit restricted user, cached/fresh, Company/Account/doc controls; missing/bad/explicit/contradictory overdue/credits; both AR/AP duplicates ở AI001/AI002; real multi-term/account split backed by schedule/ledger oracle; both cutoffs unchanged. Existing 152 suites chạy lại, mở rộng chỉ changed paths.
- **Stop conditions:** unproven identity/source shape, policy/formula change, unsupported explicit-user auth, mutation frontend, unplanned migration/shared API change. Không broaden audit hoặc đoán allocation.
- **Evidence:** commit/diff + graph limitations, test output, container hashes/versions, actual live JSON denial/regrant/cache eviction, oracle fingerprints, cleanup. Builder report không thay Work PASS.

## S1 — Draft contracts và mock interfaces

- **Scope:** typed request/output/source/coverage/evaluation/evidence/policy, two-signal allowlist.
- **Allowed files (proposed new):** `lotus_fin/lotus_fin/risk_signal/{__init__,contracts,interfaces}.py`, `tests/test_risk_signal_contract.py`. Không sửa API/DB/hooks.
- **Dependencies:** Chat v0.3 hoặc approved technical draft decisions; có thể offline song song F0 khi được giao riêng.
- **Acceptance/tests:** strict date/company/currency/book/cutoff; arbitrary signal/metric/report/SQL/URL/user override rejected; separated statuses, no-policy nulls, invalid/zero precedence, Decimal serialization/version contract. Mock tests không chứng minh live auth.
- **Stop:** cần source read/threshold/default severity. **Evidence:** diff/schema examples/contract tests và DRAFT/MOCK label; không G4B/live claim.

## S2 — Versioned source và coverage adapters

- **Scope:** AR/AP raw report adapters, unrounded inputs, identity reconciliation, credit context, due-date coverage, baseline comparability.
- **Allowed:** `risk_signal/{sources,coverage,provenance}.py`, `tests/test_risk_signal_sources.py`; consume shared guard, không duplicate permission framework.
- **Dependencies:** F0 independent PASS + Chat identity/coverage/basis, integration owner agrees shared helper. Real reads trước đó MUST_WAIT.
- **Acceptance/tests:** independent oracle both cutoffs; retain net/positive views; no AI001 rounded ratio as raw input; no missing-date→zero exposure; credit counted once; valid splits reconcile; approved economic observation count; Company/report/Account/doc checks. DATE cutoff; reject unsupported FX/book/AS_KNOWN_AT.
- **Stop:** partial source labelled complete, incompatible AI001 formula change, atomic multi-report snapshot claim chưa proof. **Evidence:** raw source/oracle/coverage/provenance comparisons, live security and tests.

## S3 — Policy registry và deterministic evaluation interface

- **Scope/allowed:** `risk_signal/{policy,evaluation}.py`, `tests/test_risk_signal_policy.py`; immutable versioned scope/approval registry, mock/approved source interface.
- **Dependencies:** S1 + Chat comparator/order/floors/status; S2 before LIVE. Business verdict waits Finance/Product approval; valid source without policy → POLICY_PENDING/nulls.
- **Acceptance/tests:** no default LIVE thresholds; DEMO_ONLY isolated; partial/reversed policy rejected; equality/high precedence/floors/count; source-invalid/zero before pending; near-threshold Decimal without display quantization; method/policy version binding. Explicit signal-specific floor units. Decide internal precision/error bounds or cross-multiplication before exact-edge acceptance.
- **Stop:** client thresholds, fixture-based production values, auto-promote demo, changing AI001 formula. **Evidence:** boundary tests + genuine approval metadata if any; no invented approver.

## S4 — Dynamic evidence và observability

- **Scope/allowed:** `risk_signal/{evidence,observability}.py`, `tests/test_risk_signal_evidence.py`; dynamic authorized replay + saved hash, safe logging, chưa cần production replay endpoint.
- **Dependencies:** F0/S1/S2; Chat approves replay/hash/version semantics.
- **Acceptance/tests:** authorization trước stored payload/hash; same source MATCH, actual historical change RESTATED, typed unavailable, revoked/cross-company FORBIDDEN; bind company/report/filters/cutoff/currency/timezone/schema/method, canonical ordering, source/derived hashes riêng. Logs correlation/version/status/timing/count/hash prefix, không raw parties/invoices/amounts/prompts/tokens. Cutoff giống nhau không chứng minh atomic snapshot.
- **Stop:** snapshot token grants access, mutable scope, hash-only without context, auth guessed from error text, claim AS_KNOWN_AT. **Evidence:** actual revoke/restatement live replay, provenance and redacted logs; harness simulations labelled riêng.

## S5 — Bounded API/service/agent (G4B later)

- **Scope/allowed:** `risk_signal/{service,agent}.py`, additive API in `api/ai_insights.py`, dedicated contract/integration/E2E tests. Không đổi public AI001/AI002 schema chưa approval.
- **Dependencies:** S1–S4 + independent foundation/source security PASS; POLICY_PENDING endpoint may expose authorized metrics only after live guards pass. Production verdict waits approved policy.
- **Acceptance/tests:** session user/server Company binding, two-signal allowlist; endpoint tampering/cross-company/multi-user/cache/evidence revoke; generic denied payload empty; source failure/no-policy nulls; model timeout/malformed/ungrounded leaves deterministic metrics unchanged; no voucher writes/threshold edits.
- **Stop:** arbitrary tools, missing user/scope/version cache isolation, incompatible shared DTO change/unplanned migration. **Evidence:** reproducible G4B E2E/security/eval + versioned API samples; Work verification before closure.

## Integration handoff — không rebase trong phiên Work

Ownership **PROPOSED**: shared auth/report envelope/identity helpers → foundation owner + integration member review; AI003 adapters/contracts/policy → AI003 team. Confirm actual team ownership before merging; AI004/AI005 consumers review shared DTO/API changes.

Shared surfaces: `security/access.py`, `api/key_reports.py`, AI001 snapshot/provenance, AI002 obligation DTO/adapters/cache/service, API `ai_insights.py`. Existing obligation `source_ref` không unique installment key. Prefer additive versioned AI003 DTO; giữ AI001 net/rounded output semantics và AI002 nullable dates. S1–S3 không đề xuất migration; persistent observations sau này cần storage/retention/ACL/migration approval riêng.

Integration owner chốt **agreed merge base**, không đoán main. Before rebase review shared diff + graph; after rebase/rebuild verify source hash/apps/timezone/scope isolated, migrate only actual new migration, preserve gold, replay F0 + changed consumer tests. Không reset untracked hoặc mutate frontend.

```powershell
git diff <agreed-base>..HEAD -- lotus_fin/lotus_fin/security/access.py lotus_fin/lotus_fin/api/key_reports.py lotus_fin/lotus_fin/ai/financial_snapshot.py lotus_fin/lotus_fin/cashflow
node .gitnexus/run.cjs detect-changes --scope compare --base-ref <agreed-base> --repo .
docker exec -w /home/frappe/frappe-bench/sites frappe_docker-backend-1 /home/frappe/frappe-bench/env/bin/python -m unittest -q lotus_fin.tests.test_ai003_foundation_remediation lotus_fin.tests.test_financial_snapshot lotus_fin.tests.test_cashflow_security lotus_fin.tests.test_cashflow_failclosed
docker exec -w /home/frappe/frappe-bench/sites frappe_docker-backend-1 /home/frappe/frappe-bench/env/bin/python /tmp/final_foundation_probe.py
```

Replace `<agreed-base>` bằng team-confirmed ref. Add new AI003/consumer tests when available. Đây là hướng dẫn verification, không phải rebase đã chạy. Graph stale/UNKNOWN/truncated chưa giải quyết không được coi clean check.

# AI003 IVL — independent gold closure (2026-09-30)

Scope: independent re-verification of the numeric source gold and coverage classes in [`AI003_GOLD_MANIFEST.yaml`](../AI003_GOLD_MANIFEST.yaml) at unchanged revision `c6f4cd1`, isolated site `ai003-verify.localhost`. No production signal/rule functions were imported into any oracle. No production verdicts were created; thresholds remain symbolic (`TEST_ONLY_POLICY`) and `production_policy_status: PENDING_APPROVAL`.

## 1. Oracle independence — VERIFIED

`prebuild_oracle.py::voucher_oracle` reads submitted Sales/Purchase Invoices, Payment Entry references and **`Payment Ledger Entry` attribution** (`delinked=0`, posting-date ≤ cutoff) and computes signed residuals per voucher. It imports no Lotus Fin production metric/rule code and does not read `Invoice.outstanding_amount` or the AR/AP reports. `return_against` is not treated as allocation proof (the initial-oracle assumption that Work disproved is retained as superseded evidence in `AI003_PREBUILD_RESULTS_INITIAL_2026-09-30.json`).

## 2. Independent re-run — MATCHES MANIFEST

Run: 2026-09-30, backend container (image `220e4f5d…`), probe `ivl_phase_a_probe.py` §A5 and `ivl_cleanup4.py` (post-cleanup restore proof).

| Cutoff | AR net residual | AR overdue (net) | AR positive residual | AR unallocated credit | AP +1..+7 | AP +1..+30 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2026-09-20 | 650,000 ✓ | 0 ✓ | 650,000 | 0 | 1,400,000 ✓ | 1,950,000 ✓ |
| 2026-09-26 | 565,000 ✓ | 65,000 ✓ | 575,000 | −10,000 | 275,000 ✓ | 975,000 ✓ |

Boundary semantics re-verified live: AR due-before residual 75,000 is overdue; due-exact 200,000 and due-after 300,000 are not. AP D1 75,000 / D7 200,000 in-window; D8/D30 reference-only; D31 excluded; overdue 600,000 and due-today 700,000 are separate context. AP D1 residual = 100,000 − 20,000 payment − 5,000 allocated credit = 75,000; allocated credits counted once; unallocated credits separate (−10,000), not auto-netted.

## 3. Coverage closure per required classes

| Required class | State | Evidence |
| --- | --- | --- |
| Numeric AR inputs | CLOSED (source-level) | Manifest + IVL re-run; netting policy remains open business decision |
| Numeric AP inputs | CLOSED (source-level) | Manifest + IVL re-run |
| AP window boundaries | CLOSED | D1/D7/D8/D30/D31 inclusive-boundary probes (Work) re-confirmed by oracle arithmetic |
| Positive / benign / inconclusive | CLOSED as SOURCE gold; evaluation states stay symbolic | Manifest: zero denominator → AR INCONCLUSIVE / AP NOT_APPLICABLE, finding/severity null; thresholds TEST_ONLY_POLICY |
| Legitimate empty | CLOSED | `AI003 Empty 2026` voucher-free company: empty report, zero denominator, ratio undefined (not benign) |
| Malformed / duplicate source | OPEN (defects) | PB-DATA-01 (missing due date → AVAILABLE wrong ratio) and PB-DATA-02 (duplicate double-count) independently reproduced 2026-09-30 |
| Future posting | CLOSED | Future AR/AP leaves historical input hash unchanged (Work; oracle hash semantics) |
| Backdate/cancel/restatement | CLOSED under posting-date restatement scope | AR 565,000 → 688,000 → 565,000 → 689,000 with new evidence checksum; IVL harness C6 reproduced RESTATED + cancel-restores |
| Company/report/document isolation | CLOSED except report+cache defect | Cross-company denied generically; document-specific denial/regrant passed (IVL C7/C7B); **PB-SEC-01 open on report-specific revoke + cache** |
| Production signal verdict | NOT CREATED (by design) | `production_policy_status: PENDING_APPROVAL`; POLICY_PENDING produces no finding/severity |

## 4. Conclusion

```text
AR SOURCE + GOLD: PARTIAL — numeric oracle independently verified; netting/missing-due-date/duplicate policy and defects open
AP SOURCE + GOLD: PARTIAL — numeric/window oracle independently verified; completeness/dedup/null-due-date policy open
GOLD MANIFEST: valid source/symbolic artifact (70 cases; 67 verified-passing cases remain valid at unchanged revision)
NOT a production signal gold; no threshold values approved
```

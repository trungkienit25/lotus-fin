"""Build a JSON-formatted YAML manifest from recorded independent probe evidence."""
import json
from pathlib import Path

root = Path(__file__).resolve().parent
main = json.loads((root / 'AI003_PREBUILD_RESULTS_2026-09-30.json').read_text(encoding='utf-8'))
extra = json.loads((root / 'AI003_PREBUILD_ADDITIONAL_RESULTS_2026-09-30.json').read_text(encoding='utf-8'))
cases = main['cases'] + extra['cases']
assert len({c['case_id'] for c in cases}) == len(cases)
manifest = {
    'manifest_version': '0.2.0-prebuild', 'format': 'JSON (valid YAML 1.2)',
    'contract': 'AI003_CANDIDATE_CONTRACT_v0.2.md', 'verified_revision': 'c6f4cd13c677e167ac645d4d0c48d236383c4fac',
    'status': 'SOURCE_GOLD_AND_SYMBOLIC_SPECIFICATION_ONLY',
    'production_policy_status': 'PENDING_APPROVAL', 'production_finding': None, 'production_severity': None,
    'environment': main['environment'],
    'oracle': {
        'path': 'evidence/prebuild_oracle.py',
        'method': 'Direct submitted voucher/payment allocation and Payment Ledger Entry attribution; no production metric/rule imports',
        'ar_basis': 'Observed AI001 net residual including separate credit balances; positive-only alternative retained; business netting approval open',
        'ap_basis': 'Positive obligation residual after allocated credits; unallocated credits separate, not silently allocated from return_against',
        'cutoffs': {k: v for k, v in main['gold'].items() if isinstance(v, dict)},
        'ar_delta_pp': main['gold']['delta_pp'], 'empty_source': extra['gold']['empty'],
    },
    'notes': [
        'All source records and amounts are synthetic on ai003-verify.localhost.',
        'Initial results file is superseded: return_against was found not to prove credit allocation. Final oracle uses actual posted attribution.',
        'No production threshold values or finance approvals are inferred from this fixture.',
        'Transient future/backdated/cancelled/amended vouchers and permission probes were rolled back; logged transient IDs are observation refs, not durable replay tokens.',
        'Endpoint-specific tampered signal/metric input tests belong to G4B after an AI003 endpoint exists.',
        'Comparator >= is TEST_ONLY_POLICY specification; equality behavior and invalid-source versus POLICY_PENDING precedence require contract clarification.',
    ], 'cases': []}
for c in cases:
    case_id = c['case_id']
    cutoff = '2026-09-20' if '2026-09-20' in case_id else '2026-09-26'
    gold = main['gold'][cutoff]
    is_spec = case_id.startswith('SYMBOLIC_') or case_id in ('POLICY_PENDING', 'ZERO_DENOMINATOR_SPEC')
    is_invalid = any(x in case_id for x in ('MALFORMED', 'MISSING_', 'DUPLICATE', 'SUMMARY_DICT', 'NULL_DUE')) and not case_id.startswith('MODEL_')
    is_empty = case_id in ('LEGITIMATE_EMPTY_SITE', 'AR_EMPTY', 'ZERO_DENOMINATOR_SPEC')
    denied = ('FORBIDDEN' in str(c['expected'])) or case_id == 'REPORT_DIRECT_RUN_REVOKED'
    empty_company = case_id in ('LEGITIMATE_EMPTY_SITE', 'ZERO_DENOMINATOR_SPEC')
    expected_source = 'FORBIDDEN' if denied else ('SOURCE_INVALID' if is_invalid else ('ZERO_VERIFIED' if is_empty else 'AVAILABLE'))
    expected_evaluation = None if denied else ('INCONCLUSIVE' if is_invalid else 'POLICY_PENDING')
    if case_id == 'ZERO_DENOMINATOR_SPEC':
        expected_evaluation = {'AR': 'INCONCLUSIVE', 'AP': 'NOT_APPLICABLE'}
    manifest['cases'].append({
        'case_id': case_id, 'company': 'AI003 Empty 2026' if empty_company else main['environment']['company'],
        'as_of': cutoff, 'baseline_as_of': '2026-09-20' if case_id.startswith('NUMERIC_') and cutoff == '2026-09-26' else None,
        'timezone': main['environment']['timezone'], 'currency': 'VND',
        'source_refs': [c['source_ref']] if 'source_ref' in c else ([] if is_spec or is_empty else gold['source_refs']),
        'source_hashes': {'voucher_and_subledger_sha256': extra['gold']['empty']['source_hash'] if empty_company else gold['source_hash'], **(main.get('source_hashes', {}) if cutoff == '2026-09-26' and not is_empty else {})},
        'expected': {'source_state': expected_source,
                     'metric_inputs': c['expected'], 'metric_value': gold['ar_ratio'] if case_id.startswith('NUMERIC_') else None,
                     'baseline_value': main['gold']['2026-09-20']['ar_ratio'] if case_id == 'NUMERIC_2026-09-26' else None,
                     'change_value': main['gold']['delta_pp'] if case_id == 'NUMERIC_2026-09-26' else None,
                     'evaluation_state': expected_evaluation, 'finding': None, 'severity': None},
        'policy': {'status': 'TEST_ONLY_POLICY' if is_spec else 'PENDING_APPROVAL', 'symbolic_thresholds': ['T_warning', 'T_high', 'A_min', 'D_min', 'N_min'], 'production_approved': False},
        'verification': {'kind': 'SPECIFICATION_ONLY' if is_spec else 'LIVE_SOURCE_OR_REUSABLE_PRIMITIVE', 'result': c['result'], 'actual': c['actual']},
        'notes': c.get('notes') or c.get('assessment') or 'See recorded probe evidence for exact observation and scope.',
    })
(root.parent / 'AI003_GOLD_MANIFEST.yaml').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('MANIFEST', len(cases), 'distinct cases;', sum(c['verification']['kind'] == 'SPECIFICATION_ONLY' for c in manifest['cases']), 'specification cases; production policy pending')

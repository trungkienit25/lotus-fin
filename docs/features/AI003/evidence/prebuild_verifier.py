"""Independent pre-build probes on isolated synthetic site only. No AI003 implementation."""
import copy
import json
import sys
import traceback
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, '/tmp')
from prebuild_oracle import stable_hash, voucher_oracle
import frappe

SITE = 'ai003-verify.localhost'
C = 'AI003 Gold 2026'
CUTOFF = date(2026, 9, 26)
USER = 'ai003-prebuild-reader@example.invalid'
RESULT = {'revision': 'c6f4cd1', 'site': SITE, 'cases': [], 'gold': {}, 'errors': []}


def record(case_id, expected, actual, passed, **details):
    RESULT['cases'].append({'case_id': case_id, 'expected': expected, 'actual': actual,
                            'result': 'PASS' if passed else 'FAIL', **details})
    print(case_id, 'PASS' if passed else 'FAIL', flush=True)


def attempt(case_id, expected, fn):
    try:
        value = fn()
        record(case_id, expected, {'returned': str(value)}, False)
    except frappe.PermissionError as e:
        record(case_id, expected, {'exception': type(e).__name__, 'message': str(e)}, str(e) == 'FORBIDDEN')
    except Exception as e:
        record(case_id, expected, {'exception': type(e).__name__, 'message': str(e)}, False)


def create_invoice(dt, tag, posting, due, amount, **extra):
    existing = frappe.db.get_value(dt, {'company': C, 'remarks': tag, 'docstatus': 1}, 'name')
    if existing:
        return frappe.get_doc(dt, existing)
    d = {'doctype': dt, 'company': C, 'posting_date': str(posting), 'set_posting_time': 1,
         'due_date': str(due), 'remarks': tag, 'currency': 'VND', 'items': [{'item_code': 'AI002 TEST SERVICE', 'qty': 1, 'rate': amount}]}
    if dt == 'Sales Invoice':
        d.update(customer='AI003 Gold Customer', debit_to='Debtors - A3G')
        d['items'][0]['income_account'] = 'Service - A3G'
    else:
        d.update(supplier='AI003 Gold Supplier', credit_to='Creditors - A3G')
        d['items'][0]['expense_account'] = 'Office Maintenance Expenses - A3G'
    d.update(extra)
    doc = frappe.get_doc(d).insert(ignore_permissions=True)
    doc.submit()
    return doc


def pay(doc, amount, tag):
    from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry
    for ref in frappe.get_all('Payment Entry Reference', filters={'reference_doctype': doc.doctype, 'reference_name': doc.name, 'allocated_amount': amount}, fields=['parent'], limit_page_length=100):
        if frappe.db.get_value('Payment Entry', ref.parent, 'docstatus') == 1:
            return
    pe = get_payment_entry(doc.doctype, doc.name)
    pe.posting_date = '2026-09-22'
    pe.set_posting_time = 1
    pe.remarks = tag
    if doc.doctype == 'Sales Invoice':
        pe.paid_to = 'Cash - A3G'
    else:
        pe.paid_from = 'Cash - A3G'
    pe.paid_amount = pe.received_amount = amount
    for r in pe.references:
        r.allocated_amount = amount if r.reference_name == doc.name else 0
    pe.insert(ignore_permissions=True)
    pe.submit()


def fixture():
    if not frappe.db.exists('Company', C):
        frappe.get_doc({'doctype': 'Company', 'company_name': C, 'abbr': 'A3G', 'country': 'Vietnam',
                        'default_currency': 'VND', 'chart_of_accounts': 'Standard'}).insert(ignore_permissions=True)
    fy = frappe.get_doc('Fiscal Year', '2026')
    if C not in [r.company for r in fy.companies]:
        fy.append('companies', {'company': C}); fy.save(ignore_permissions=True)
    for dt, name, parent_field, root in (
        ('Customer Group', 'AI003 Gold Customers', 'parent_customer_group', 'All Customer Groups'),
        ('Supplier Group', 'AI003 Gold Suppliers', 'parent_supplier_group', 'All Supplier Groups'),
        ('Territory', 'AI003 Gold Territory', 'parent_territory', 'All Territories'),
    ):
        if not frappe.db.exists(dt, name):
            frappe.get_doc({'doctype': dt, dt.lower().replace(' ', '_') + '_name': name,
                            parent_field: root, 'is_group': 0}).insert(ignore_permissions=True)
    for dt, name, fields in (
        ('Customer', 'AI003 Gold Customer', {'customer_name': 'AI003 Gold Customer', 'customer_type': 'Company', 'customer_group': 'AI003 Gold Customers', 'territory': 'AI003 Gold Territory'}),
        ('Supplier', 'AI003 Gold Supplier', {'supplier_name': 'AI003 Gold Supplier', 'supplier_group': 'AI003 Gold Suppliers', 'supplier_type': 'Company'}),
    ):
        if not frappe.db.exists(dt, name):
            frappe.get_doc({'doctype': dt, **fields}).insert(ignore_permissions=True)
    frappe.db.set_value('Company', C, 'ai002_approved_cash_accounts', json.dumps(['Cash - A3G']))
    if not frappe.db.exists('Journal Entry', {'company': C, 'user_remark': 'AI003 GOLD OPENING'}):
        je = frappe.get_doc({'doctype': 'Journal Entry', 'company': C, 'posting_date': '2026-09-01',
                            'user_remark': 'AI003 GOLD OPENING', 'accounts': [
                                {'account': 'Cash - A3G', 'debit_in_account_currency': 20000000},
                                {'account': 'Opening Balance Equity - A3G', 'credit_in_account_currency': 20000000}]}).insert(ignore_permissions=True)
        je.submit()
    ar = {}
    for tag, offset, amount in [('BEFORE', -1, 100000), ('EXACT', 0, 200000), ('AFTER', 1, 300000), ('PAID', -2, 50000)]:
        ar[tag] = create_invoice('Sales Invoice', 'AI003_AR_' + tag, '2026-09-01', CUTOFF + timedelta(days=offset), amount)
    ap = {}
    for tag, offset, amount in [('D1', 1, 100000), ('D7', 7, 200000), ('D8', 8, 300000), ('D30', 30, 400000), ('D31', 31, 500000), ('OVERDUE', -1, 600000), ('TODAY', 0, 700000), ('PAID', 3, 50000)]:
        ap[tag] = create_invoice('Purchase Invoice', 'AI003_AP_' + tag, '2026-09-01', CUTOFF + timedelta(days=offset), amount)
    pay(ar['BEFORE'], 20000, 'AI003 AR PARTIAL'); pay(ar['PAID'], 50000, 'AI003 AR PAID')
    pay(ap['D1'], 20000, 'AI003 AP PARTIAL'); pay(ap['PAID'], 50000, 'AI003 AP PAID')
    for dt, original, tag in [('Sales Invoice', ar['BEFORE'], 'AI003_AR_CREDIT'), ('Purchase Invoice', ap['D1'], 'AI003_AP_CREDIT')]:
        if not frappe.db.exists(dt, {'company': C, 'remarks': tag, 'docstatus': 1}):
            item = {'item_code': 'AI002 TEST SERVICE', 'qty': -1, 'rate': 10000}
            item['income_account' if dt == 'Sales Invoice' else 'expense_account'] = 'Service - A3G' if dt == 'Sales Invoice' else 'Office Maintenance Expenses - A3G'
            create_invoice(dt, tag, '2026-09-23', str(original.due_date), -10000,
                           is_return=1, return_against=original.name, items=[item])
    for dt, original, tag in [('Sales Invoice', ar['BEFORE'], 'AI003_AR_ALLOCATED_CREDIT'), ('Purchase Invoice', ap['D1'], 'AI003_AP_ALLOCATED_CREDIT')]:
        if not frappe.db.exists(dt, {'company': C, 'remarks': tag, 'docstatus': 1}):
            item = {'item_code': 'AI002 TEST SERVICE', 'qty': -1, 'rate': 5000}
            item['income_account' if dt == 'Sales Invoice' else 'expense_account'] = 'Service - A3G' if dt == 'Sales Invoice' else 'Office Maintenance Expenses - A3G'
            create_invoice(dt, tag, '2026-09-24', str(original.due_date), -5000,
                           is_return=1, return_against=original.name, update_outstanding_for_self=0, items=[item])
    frappe.db.commit()
    return ar, ap


def fetch(key, filters, company):
    from lotus_fin.api.key_reports import extract_key_report_data
    return extract_key_report_data(key, filters, company)


def snapshot(cutoff=CUTOFF, fetcher=fetch):
    from lotus_fin.ai.financial_snapshot import build_financial_snapshot
    return build_financial_snapshot(company=C, period_start='2026-01-01', period_end='2026-12-31',
                                    as_of=str(cutoff), currency='VND', source_fetcher=fetcher)


def metric_map(snap):
    return {m['metric_id']: m for m in snap['metrics']}


def source(key, cutoff=CUTOFF):
    return fetch(key, {'company': C, 'report_date': str(cutoff)}, C)


def numeric():
    from lotus_fin.cashflow.adapters import get_trade_obligations
    for cutoff in (date(2026, 9, 20), CUTOFF):
        oracle = voucher_oracle(frappe.db, C, cutoff)
        mm = metric_map(snapshot(cutoff))
        obs = get_trade_obligations(C, cutoff)
        ap_rows = [o for o in obs if o.type == 'AP']
        short = sum((o.remaining_amount for o in ap_rows if o.due_date and cutoff + timedelta(days=1) <= o.due_date <= cutoff + timedelta(days=7)), Decimal(0))
        horizon = sum((o.remaining_amount for o in ap_rows if o.due_date and cutoff + timedelta(days=1) <= o.due_date <= cutoff + timedelta(days=30)), Decimal(0))
        actual = {'ar_total': mm['ar_outstanding']['value'], 'ar_ratio': mm['overdue_ar_ratio']['value'], 'ap_short': str(short), 'ap_horizon': str(horizon)}
        passed = Decimal(str(actual['ar_total'])) == Decimal(oracle['total_ar']) and abs(Decimal(str(actual['ar_ratio'])) - Decimal(oracle['ar_ratio'])) <= Decimal('0.00005') and short == Decimal(oracle['ap_short']) and horizon == Decimal(oracle['ap_horizon'])
        record('NUMERIC_' + str(cutoff), {k: oracle[k] for k in ('total_ar', 'overdue_ar', 'ar_ratio', 'ap_short', 'ap_horizon', 'ap_ratio')}, actual, passed, source_hash=oracle['source_hash'])
        RESULT['gold'][str(cutoff)] = oracle
    RESULT['gold']['delta_pp'] = str((Decimal(RESULT['gold'][str(CUTOFF)]['ar_ratio']) - Decimal(RESULT['gold']['2026-09-20']['ar_ratio'])) * 100)


def quality():
    ar_res = source('accounts_receivable'); ap_res = source('accounts_payable')
    RESULT['source_hashes'] = {'AR': stable_hash(ar_res['data']), 'AP': stable_hash(ap_res['data'])}
    positive_ar = next(r for r in ar_res['data'] if Decimal(str(r.get('outstanding') or r.get('outstanding_amount') or 0)) > 0)
    for label, mode in [('MALFORMED_AMOUNT', 'bad'), ('MISSING_VOUCHER', 'identity'), ('MISSING_DUE_DATE', 'due'), ('DUPLICATE', 'duplicate'), ('SUMMARY_DICT', 'summary'), ('EMPTY', 'empty')]:
        def poisoned(key, filters, company, mode=mode):
            res = copy.deepcopy(fetch(key, filters, company))
            if key == 'accounts_receivable' and res.get('status') == 'success':
                if mode == 'empty': res['data'] = []
                elif mode == 'summary': res['data'].append({'is_total_row': True, 'outstanding': 123})
                elif mode == 'duplicate': res['data'].append(copy.deepcopy(res['data'][0]))
                else:
                    row = res['data'][0]
                    if mode == 'bad': row['outstanding'] = 'invalid'; row['outstanding_amount'] = 'invalid'
                    elif mode == 'identity': row.pop('voucher_no', None); row.pop('name', None)
                    elif mode == 'due':
                        for k in ('due_date', 'overdue', 'overdue_amount'): row.pop(k, None)
            return res
        mm = metric_map(snapshot(fetcher=poisoned))
        key = 'overdue_ar_ratio' if mode == 'due' else 'ar_outstanding'
        actual = {'metric': key, 'status': mm[key]['status'], 'value': mm[key]['value']}
        passed = (actual['status'] == 'AVAILABLE' and actual['value'] == 0) if mode == 'empty' else actual['status'] == 'UNAVAILABLE'
        record('AR_' + label, 'ZERO_VERIFIED' if mode == 'empty' else 'SOURCE_INVALID/INCONCLUSIVE', actual, passed)
    from lotus_fin.cashflow.adapters import _collect_obligations
    for label, mode in [('NULL_DUE', 'due'), ('DUPLICATE', 'dup')]:
        payload = copy.deepcopy(ap_res)
        if mode == 'due': payload['data'][0]['due_date'] = None
        else: payload['data'].append(copy.deepcopy(payload['data'][0]))
        try:
            obs = _collect_obligations(payload, 'AP', ('party', 'supplier'), 'Purchase Invoice', 'VND', 'Accounts Payable', company=C)
            actual = {'count': len(obs), 'null_due_count': sum(o.due_date is None for o in obs), 'source_refs': [o.source_ref for o in obs]}
            record('AP_' + label, 'AI003 must mark incomplete or detect exact duplicate; source adapter may expose typed context', actual, False, assessment='SUPPORTED_WITH_CHANGE; no AI003 evaluator exists')
        except Exception as e:
            record('AP_' + label, 'reject invalid source', {'exception': type(e).__name__, 'message': str(e)}, True)


def temporal():
    before = source('accounts_receivable')
    before_hash = stable_hash(before['data'])
    snap_before = snapshot()
    baseline = metric_map(snap_before)['ar_outstanding']['value']
    def evidence_hash(snap):
        return [e['checksum_or_version'] for e in snap['evidence_refs'] if e['source_name'] == 'Accounts Receivable']
    RESULT['temporal_evidence_before'] = evidence_hash(snap_before)
    create_invoice('Sales Invoice', 'AI003_TRANSIENT_FUTURE', '2026-10-05', '2026-10-10', 111000)
    future = metric_map(snapshot())['ar_outstanding']['value']
    record('FUTURE_POSTING', {'value': baseline, 'source_hash': before_hash}, {'value': future, 'source_hash': stable_hash(source('accounts_receivable')['data'])}, future == baseline and stable_hash(source('accounts_receivable')['data']) == before_hash)
    back = create_invoice('Sales Invoice', 'AI003_TRANSIENT_BACKDATED', '2026-09-02', '2026-09-25', 123000)
    snap_after = snapshot()
    after = metric_map(snap_after)['ar_outstanding']['value']
    after_hash = stable_hash(source('accounts_receivable')['data'])
    record('BACKDATED_RESTATEMENT', baseline + 123000, {'value': after, 'hash_changed': after_hash != before_hash, 'evidence_before': evidence_hash(snap_before), 'evidence_after': evidence_hash(snap_after)}, after == baseline + 123000 and after_hash != before_hash and evidence_hash(snap_before) != evidence_hash(snap_after))
    back.cancel()
    cancelled = metric_map(snapshot())['ar_outstanding']['value']
    record('CANCEL_RESTATEMENT', baseline, {'value': cancelled, 'hash_changed_from_backdated': stable_hash(source('accounts_receivable')['data']) != after_hash}, cancelled == baseline and stable_hash(source('accounts_receivable')['data']) != after_hash)
    corrected = create_invoice('Sales Invoice', 'AI003_TRANSIENT_CORRECTED', '2026-09-02', '2026-09-25', 124000, amended_from=back.name)
    amended = metric_map(snapshot())['ar_outstanding']['value']
    record('CORRECTION_RESTATEMENT', baseline + 124000, {'value': amended}, amended == baseline + 124000)
    RESULT['temporal_refs'] = [back.name, corrected.name]
    frappe.db.rollback()


def permissions(ar):
    from lotus_fin.security.access import get_verified_company, check_ai002_report_permission
    from lotus_fin.api.ai_insights import get_ai002_evidence
    from lotus_fin.cashflow.models import ForecastRequest
    from lotus_fin.cashflow.service import get_cash_forecast
    from lotus_fin.cashflow.cache import _CACHE_STORE
    from lotus_fin.cashflow.source_interface import FailClosedSource
    frappe.set_user('Administrator')
    if frappe.db.exists('User', USER): raise RuntimeError('Probe user already exists; refusing to overwrite')
    u = frappe.get_doc({'doctype': 'User', 'email': USER, 'first_name': 'AI003 Prebuild Probe', 'send_welcome_email': 0, 'user_type': 'System User', 'roles': [{'role': 'Accounts User'}]}).insert(ignore_permissions=True)
    frappe.get_doc({'doctype': 'User Permission', 'user': USER, 'allow': 'Company', 'for_value': C, 'apply_to_all_doctypes': 1}).insert(ignore_permissions=True)
    frappe.clear_cache(user=USER); frappe.set_user(USER)
    record('COMPANY_AUTHORIZED', C, get_verified_company(C), get_verified_company(C) == C)
    attempt('COMPANY_DENIED', 'FORBIDDEN', lambda: get_verified_company('AI002 Fixture 2026'))
    attempt('COMPANY_NONEXISTENT', 'FORBIDDEN', lambda: get_verified_company('AI003 NONEXISTENT COMPANY'))
    ref = 'Sales Invoice:' + ar['BEFORE'].name
    ev = get_ai002_evidence(ref, C)
    record('EVIDENCE_AUTHORIZED', 'success', ev.get('status'), ev.get('status') == 'success')
    wrong = frappe.db.get_value('Sales Invoice', {'company': 'AI002 Fixture 2026', 'docstatus': 1}, 'name')
    attempt('EVIDENCE_CROSS_COMPANY', 'FORBIDDEN', lambda: get_ai002_evidence('Sales Invoice:' + wrong, C))
    attempt('EVIDENCE_ARBITRARY_DOCTYPE', 'FORBIDDEN', lambda: get_ai002_evidence('User:Administrator', C))
    attempt('EVIDENCE_SNAPSHOT_NOT_TOKEN', 'FORBIDDEN', lambda: get_ai002_evidence('SNAP-FAKE', C))
    attempt('ARBITRARY_REPORT', 'FORBIDDEN', lambda: check_ai002_report_permission('Stock Balance'))
    req = ForecastRequest(company=C, financial_as_of=CUTOFF, forecast_start=CUTOFF + timedelta(days=1), forecast_end=CUTOFF + timedelta(days=30), cash_account_scope=['Cash - A3G'])
    _CACHE_STORE.clear()
    first = get_cash_forecast(req, user=USER, future_event_source=FailClosedSource())
    cached = get_cash_forecast(req, user=USER, future_event_source=FailClosedSource())
    record('CACHE_POPULATED', 'same forecast ID on cache hit with real source read', {'first': first.status.value, 'hit_same_id': first.forecast_id == cached.forecast_id, 'cache_entries': len(_CACHE_STORE)}, bool(_CACHE_STORE) and first.forecast_id == cached.forecast_id)
    other_req = ForecastRequest(company='AI002 Fixture 2026', financial_as_of=CUTOFF, forecast_start=CUTOFF + timedelta(days=1), forecast_end=CUTOFF + timedelta(days=30), cash_account_scope=['Cash - A2F'])
    other = get_cash_forecast(other_req, user=USER)
    record('CACHE_CROSS_COMPANY', 'FORBIDDEN without financial payload', {'status': other.status.value, 'obligations': len(other.obligations), 'opening_cash': other.opening_cash is not None}, other.status.value == 'FORBIDDEN' and not other.obligations and other.opening_cash is None)
    # Revoke the report-specific role allowlist while retaining Company/Account role permissions.
    frappe.set_user('Administrator')
    custom = frappe.get_doc({'doctype': 'Custom Role', 'report': 'Accounts Receivable', 'ref_doctype': 'Sales Invoice', 'roles': [{'role': 'Accounts Manager'}]}).insert(ignore_permissions=True)
    frappe.clear_cache(user=USER); frappe.clear_cache(doctype='Report'); frappe.set_user(USER)
    from frappe.core.doctype.report.report import get_custom_allowed_roles
    authoritative = frappe.get_doc('Report', 'Accounts Receivable').is_permitted()
    record('REPORT_ROLE_REVOKED_PREFLIGHT', False, bool(authoritative), not bool(authoritative), custom_roles=get_custom_allowed_roles('report', 'Accounts Receivable'))
    denied_report = fetch('accounts_receivable', {'company': C, 'report_date': str(CUTOFF)}, C)
    record('REPORT_DIRECT_RUN_REVOKED', 'source error without data', {'status': denied_report.get('status'), 'has_data': bool(denied_report.get('data'))}, denied_report.get('status') == 'error' and not denied_report.get('data'))
    attempt('REPORT_GUARD_REVOKED', 'FORBIDDEN', lambda: check_ai002_report_permission('Accounts Receivable', user=USER))
    revoked = get_cash_forecast(req, user=USER, future_event_source=FailClosedSource())
    record('CACHE_REPORT_REVOKE', 'FORBIDDEN without obligations/opening_cash/points', {'status': revoked.status.value, 'same_cached_id': revoked.forecast_id == first.forecast_id, 'obligations': len(revoked.obligations), 'opening_cash_present': revoked.opening_cash is not None}, revoked.status.value == 'FORBIDDEN' and not revoked.obligations and revoked.opening_cash is None)
    frappe.set_user('Administrator'); frappe.delete_doc('Custom Role', custom.name, ignore_permissions=True)
    frappe.clear_cache(user=USER); frappe.clear_cache(doctype='Report'); frappe.set_user(USER)
    granted = get_cash_forecast(req, user=USER, future_event_source=FailClosedSource())
    record('CACHE_REPORT_REGRANT', first.status.value, granted.status.value, granted.status.value == first.status.value)
    frappe.set_user('Administrator')
    document_perm = frappe.get_doc({'doctype': 'User Permission', 'user': USER, 'allow': 'Customer', 'for_value': 'Palmer Productions Ltd.', 'apply_to_all_doctypes': 1}).insert(ignore_permissions=True)
    frappe.clear_cache(user=USER); frappe.set_user(USER)
    record('EVIDENCE_COMPANY_STILL_ALLOWED', C, get_verified_company(C), get_verified_company(C) == C)
    attempt('EVIDENCE_DOCUMENT_DENIED', 'FORBIDDEN', lambda: get_ai002_evidence(ref, C))
    frappe.set_user('Administrator'); frappe.delete_doc('User Permission', document_perm.name, ignore_permissions=True)
    frappe.clear_cache(user=USER); frappe.set_user(USER)
    restored = get_ai002_evidence(ref, C)
    record('EVIDENCE_DOCUMENT_REGRANT', 'success', restored.get('status'), restored.get('status') == 'success')
    frappe.set_user('Administrator'); u.reload(); u.set('roles', []); u.save(ignore_permissions=True); frappe.clear_cache(user=USER); frappe.set_user(USER)
    attempt('EVIDENCE_ROLE_REVOKED', 'FORBIDDEN', lambda: get_ai002_evidence(ref, C))
    frappe.set_user('Administrator'); frappe.db.rollback(); frappe.clear_cache(user=USER); frappe.clear_cache(doctype='Report'); _CACHE_STORE.clear()
    record('PROBE_USER_ROLLBACK', 'absent', bool(frappe.db.exists('User', USER)), not frappe.db.exists('User', USER))


def symbolic():
    # This is a specification harness, never a production rule or approved policy.
    for variable in ('T_warning', 'T_high', 'A_min', 'D_min', 'N_min'):
        for relation, value, expected in [('below', Decimal('9'), False), ('equal', Decimal('10'), True), ('above', Decimal('11'), True)]:
            record('SYMBOLIC_' + variable + '_' + relation, expected, value >= Decimal('10'), (value >= Decimal('10')) == expected,
                   policy_status='TEST_ONLY_POLICY', production_finding=None, production_severity=None,
                   notes='Candidate comparator >= still requires Chat approval; chosen only for specification harness')
    record('POLICY_PENDING', {'evaluation_status': 'POLICY_PENDING', 'finding': None, 'severity': None}, {'evaluation_status': 'POLICY_PENDING', 'finding': None, 'severity': None}, True, assessment='specification-only; no AI003 endpoint exists')


def main():
    frappe.init(site=SITE, sites_path='/home/frappe/frappe-bench/sites'); frappe.connect(); frappe.set_user('Administrator')
    assert frappe.local.site == SITE
    import erpnext
    RESULT['environment'] = {'frappe': frappe.__version__, 'erpnext': erpnext.__version__, 'timezone': frappe.utils.get_system_timezone(), 'company': C, 'currency': 'VND', 'migration_column': frappe.db.has_column('Company', 'ai002_approved_cash_accounts')}
    ar, ap = fixture()
    RESULT['fixture_refs'] = {k: v.name for k, v in {**{'AR_' + k: v for k, v in ar.items()}, **{'AP_' + k: v for k, v in ap.items()}}.items()}
    for name, task in [('numeric', numeric), ('quality', quality), ('temporal', temporal), ('permissions', lambda: permissions(ar)), ('symbolic', symbolic)]:
        try: task()
        except Exception as e:
            RESULT['errors'].append({'stage': name, 'exception': type(e).__name__, 'message': str(e), 'traceback': traceback.format_exc()})
            print('STAGE_ERROR', name, type(e).__name__, str(e), flush=True)
            frappe.set_user('Administrator'); frappe.db.rollback()
    frappe.set_user('Administrator'); frappe.db.rollback(); frappe.destroy()
    Path('/tmp/ai003_prebuild_results.json').write_text(json.dumps(RESULT, indent=2, default=str), encoding='utf-8')
    print('RESULTS', len(RESULT['cases']), 'cases', sum(c['result'] == 'FAIL' for c in RESULT['cases']), 'failed', len(RESULT['errors']), 'stage errors', flush=True)


if __name__ == '__main__':
    main()

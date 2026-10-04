"""Isolated transaction-backed METHOD GOLD; not a production AI003 engine.

The candidate method/ordering adapter exists solely in this evidence runner.
Expected amounts are calculated separately by AI003_METHOD_GOLD_ORACLE.py.
No endpoint, policy configuration, hooks, migration, or production package edit.
"""
import calendar
import copy
from contextlib import contextmanager
from datetime import date, datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP, localcontext
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import socket
import sys
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from AI003_METHOD_GOLD_ORACLE import ar_expected, ap_expected, ledger_facts, fingerprint
import frappe

SITE = 'ai003-verify.localhost'
REVISION = '8941cfb075d91a137686bb6b666bf2bb1f7432c5'
CUTOFF = date(2026, 9, 26)
COMPANIES = {'ar': ('AI003 MG AR', 'MGA'), 'calendar': ('AI003 MG Calendar', 'MGC'),
             'zero': ('AI003 MG Zero', 'MGZ'), 'ap': ('AI003 MG AP', 'MGP'),
             'multi': ('AI003 MG Multi', 'MGM')}
USER = 'ai003-method-gold-reader@example.invalid'
DENIED_USER = 'ai003-method-gold-metadata@example.invalid'
OUT = {'manifest_version': '1.0-method-gold', 'contract_candidate': '0.3.2',
       'verified_revision': REVISION, 'site': SITE, 'cases': [], 'errors': [],
       'policy_status': 'PENDING_APPROVAL', 'production_AI003_implemented': False,
       'candidate_adapter_scope': 'TEST_HARNESS_ONLY_NOT_AN_ENDPOINT',
       'oracle': 'AI003_METHOD_GOLD_ORACLE.py', 'persistent_fixtures': [],
       'method_version': 'V2.2_REVIEWED_METHOD_SPEC', 'domain_version': 'LIVE_SOURCE_2026-10-02'}
TRACE = []
# A stopped run must retain required cases as NOT_RUN rather than omit them.
REQUIRED = {
    'RUNTIME': ['RUNTIME_DB_APPS_TIMEZONE', 'RUNTIME_CURRENT_SOURCE_ALIGNMENT'],
    'PRECISION': ['NUMERIC_DOMAIN', 'LIVE_MINIMUM_MONEY_QUANTUM', 'AP_FIXTURE_FRACTION',
                  'AP_CURRENCY_MISMATCH_BEFORE_IDENTITY', 'AP_CURRENCY_CONTRADICTION_BEFORE_IDENTITY',
                  'AP_EXACT_FRACTION_COMPARISON'],
    'AR': ['AR_SAME_DAY', 'AR_31_TO_30', 'AR_31_TO_28', 'AR_31_TO_29', 'AR_YEAR_BOUNDARY',
           'AR_POSITIVE_DELTA', 'AR_NEGATIVE_DELTA', 'AR_ZERO_DELTA', 'AR_BASELINE_MISSING',
           'AR_BASELINE_ZERO', 'AR_CURRENT_ZERO', 'AR_NET_CREDIT', 'AR_FUTURE_POSTING_ISOLATION',
           'AR_SOURCE_FAILURE_BEFORE_POLICY', 'AR_REPORT_PERMISSION_DENIAL'],
    'AP': ['AP_TRANSACTION_ORACLE', 'AP_D0', 'AP_D30', 'AP_D31', 'AP_LONG', 'AP_PAST', 'AP_CREDIT',
           'AP_DISTINCT_VOUCHER_COUNTS', 'AP_ONE_SCHEDULE', 'AP_ZERO_SCHEDULE', 'AP_REAL_ZERO_SCHEDULE_CREDIT',
           'AP_REAL_TWO_SCHEDULES_FLATTENED', 'AP_EXACT_DUPLICATE', 'AP_DUPLICATE_NO_DOUBLE_COUNT',
           'AP_AMOUNT_CONFLICT', 'AP_DATE_CONFLICT', 'AP_CURRENCY_MISMATCH', 'AP_CURRENCY_CONTRADICTION',
           'AP_UNVERIFIED_ACCOUNT_SCOPE', 'AP_MISSING_DUE_DATE', 'AP_MALFORMED_DUE_DATE'],
    'STAGE': ['STAGE_SOURCE_BEFORE_POLICY', 'STAGE_A_UNAUTH_INVALID_SIGNAL',
              'STAGE_BASELINE_SOURCE_BEFORE_CURRENT_ZERO',
              'STAGE_B_STRUCTURAL_NO_COMPANY_LOOKUP', 'STAGE_C_COMPANY_BEFORE_FUTURE',
              'STAGE_E_HISTORY_BEFORE_POLICY', 'STAGE_F_VALID_WITHOUT_POLICY'],
    'SECURITY': ['AP_AMOUNT_CONFLICT_PAYLOAD_SUPPRESSED', 'AP_DATE_CONFLICT_PAYLOAD_SUPPRESSED',
                 'AP_CURRENCY_MISMATCH_PAYLOAD_SUPPRESSED', 'AP_CURRENCY_CONTRADICTION_PAYLOAD_SUPPRESSED',
                 'AP_MALFORMED_DUE_DATE_PAYLOAD_SUPPRESSED', 'CHECKED_USER_METADATA_PERMISSION_REAL',
                 'CHECKED_USER_LIVE_REPORT_ALLOW', 'CHECKED_USER_SCHEDULE_METADATA_DENIAL',
                 'CROSS_COMPANY_METADATA_DENIAL', 'NONEXISTENT_PARENT_GENERIC_DENIAL',
                 'AR_PUBLIC_PATH_REPORT_DENIAL', 'CHECKED_USER_SESSION_RESTORED'],
    'HYGIENE': ['TEMPORARY_USERS_REMOVED', 'PROTECTED_FIXTURES_UNCHANGED', 'METHOD_FIXTURES_UNCHANGED_AFTER_PROBES']}


def record(case_id, category, expected, actual, passed=None, kind='LIVE_PUBLIC_BOUNDARY', inputs=None):
    if passed is None:
        passed = fingerprint(expected) == fingerprint(actual)
    if inputs is None:
        inputs = {'site': SITE}
        if case_id.startswith(('AP_', 'AR_')):
            inputs.update(company=COMPANIES['ap' if case_id.startswith('AP_') else 'ar'][0],
                          as_of_date=str(CUTOFF), currency='VND')
    OUT['cases'].append({'case_id': case_id, 'category': category,
                         'method_version': OUT['method_version'],
                         'inputs': inputs, 'source_refs_scope': 'COMPLETE_CONTROLLED_SUITE_CONTEXT',
                         'source_fixture_refs': OUT['persistent_fixtures'],
                         'source_fixture_hashes': OUT.get('fixture_hashes', {}),
                         'expected': expected, 'actual': actual,
                         'execution_status': 'PASS' if passed else 'FAIL',
                         'evidence_kind': kind, 'evidence_reference': 'AI003_METHOD_GOLD_MANIFEST.yaml#' + case_id})
    print(case_id, 'PASS' if passed else 'FAIL', flush=True)


class StopMethod(Exception):
    def __init__(self, status, reason):
        self.status, self.reason = status, reason


def halt(status, reason):
    raise StopMethod(status, reason)


def outcome(status, reason, values=None):
    return {'status': status, 'reason_code': reason,
            'result': None if status in ('FORBIDDEN', 'VALIDATION_ERROR', 'SOURCE_ERROR') else
            {'finding': None, 'triggered': None, 'severity': None, 'method_values': values}}


@contextmanager
def checked_user(user):
    original = frappe.session.user
    frappe.set_user(user)
    try:
        yield
    finally:
        frappe.set_user(original)


def previous_month(cutoff):
    year = cutoff.year if cutoff.month > 1 else cutoff.year - 1
    month = cutoff.month - 1 if cutoff.month > 1 else 12
    return date(year, month, min(cutoff.day, calendar.monthrange(year, month)[1]))


def report(company, cutoff, key):
    return extract_key_report_data(key, company=company, filters={
        'company': company, 'report_date': str(cutoff), 'based_on_payment_terms': 0,
        'in_party_currency': 0, 'show_future_payments': 0,
        'ageing_based_on': 'Due Date', 'age_as_on': 'Report Date'})


def snapshot(company, cutoff):
    return get_financial_snapshot(company=company, period_start=f'{cutoff.year}-01-01',
                                  period_end=str(cutoff), as_of=str(cutoff), currency='VND',
                                  comparison=None, include_explanation=False)


def ar_method(company, cutoff, missing_baseline=False):
    current = snapshot(company, cutoff)
    baseline_date = previous_month(cutoff)
    baseline = None if missing_baseline else snapshot(company, baseline_date)
    values = []
    for index, envelope in enumerate((current, baseline)):
        if envelope is None:
            values.append(None)
            continue
        if envelope.get('status') == 'FORBIDDEN':
            halt('FORBIDDEN', 'ACCESS_DENIED')
        if envelope.get('status') == 'SOURCE_ERROR' or envelope.get('errors'):
            halt('SOURCE_ERROR', 'SOURCE_INVALID')
        metrics = {r['metric_id']: r for r in envelope.get('metrics', [])}
        required = [metrics.get(k) for k in ('ar_outstanding', 'overdue_ar_ratio')]
        if not all(m and m['status'] == 'AVAILABLE' and m['value'] is not None for m in required):
            halt('SOURCE_ERROR', 'SOURCE_UNAVAILABLE')
        total, ratio = [Decimal(str(m['value'])) for m in required]
        if not total.is_finite() or not ratio.is_finite():
            halt('SOURCE_ERROR', 'SOURCE_INVALID')
        values.append({'total_ar': str(total), 'ratio_published': str(ratio),
                       'contract_version': envelope['contract_version']})
    # Validate both acquired sources before evaluating either method prerequisite.
    TRACE.append('A8_METHOD')
    if Decimal(values[0]['total_ar']) <= 0:
        halt('INCONCLUSIVE', 'CURRENT_DENOMINATOR_INVALID')
    if values[1] is None:
        halt('INCONCLUSIVE', 'HISTORY_INSUFFICIENT')
    if Decimal(values[1]['total_ar']) <= 0:
        halt('INCONCLUSIVE', 'BASELINE_DENOMINATOR_INVALID')
    return {'current': values[0], 'baseline': values[1], 'baseline_as_of': str(baseline_date),
            'delta_pp': str((Decimal(values[0]['ratio_published']) -
                             Decimal(values[1]['ratio_published'])) * 100)}


def ap_method(company, cutoff, rows):
    # Currency scope precedes identity/deduplication, including repeated rows.
    TRACE.append('A6_CURRENCY')
    if any(r.get('currency') != 'VND' for r in rows):
        halt('VALIDATION_ERROR', 'UNSUPPORTED_COMPANY_CURRENCY')
    if any(r.get('account_currency', 'VND') != 'VND' for r in rows):
        halt('SOURCE_ERROR', 'INCONSISTENT_DATA')
    normalized, parents = [], {}
    for row in rows:
        if row.get('voucher_type') != 'Purchase Invoice' or not row.get('voucher_no'):
            halt('INCONCLUSIVE', 'UNSUPPORTED_ALLOCATION_SCOPE')
        try:
            amount = Decimal(str(row['outstanding']))
            if not amount.is_finite():
                raise ValueError('nonfinite')
            raw_date = row.get('due_date')
            due = (raw_date.date() if isinstance(raw_date, datetime) else raw_date
                   if isinstance(raw_date, date) else date.fromisoformat(str(raw_date)[:10])
                   if raw_date else None)
        except (ValueError, TypeError, KeyError):
            halt('SOURCE_ERROR', 'SOURCE_INVALID')
        voucher = row['voucher_no']
        if voucher not in parents:
            try:
                doc = frappe.get_doc('Purchase Invoice', voucher)
            except frappe.DoesNotExistError:
                halt('FORBIDDEN', 'ACCESS_DENIED')
            if not doc.has_permission('read', user=frappe.session.user) or doc.company != company:
                halt('FORBIDDEN', 'ACCESS_DENIED')
            parents[voucher] = doc
        normalized.append((row, amount, due))
    TRACE.append('A7_IDENTITY')
    unique, voucher_scopes = {}, {}
    for row, amount, due in normalized:
        key = (company, row['voucher_type'], row['voucher_no'], row.get('party_account'))
        signature = (amount, due)
        if key in unique and unique[key][1:] != signature:
            halt('SOURCE_ERROR', 'CONFLICTING_OBSERVATION')
        unique[key] = (row, amount, due)
        voucher_scopes.setdefault(row['voucher_no'], set()).add(row.get('party_account'))
    if any(len(scopes) > 1 for scopes in voucher_scopes.values()):
        halt('INCONCLUSIVE', 'UNSUPPORTED_ALLOCATION_SCOPE')
    TRACE.append('A8_METHOD')
    for voucher, doc in parents.items():
        schedules = doc.get('payment_schedule') or []
        if len(schedules) > 1:
            halt('INCONCLUSIVE', 'UNSUPPORTED_MULTI_SCHEDULE')
        row, amount, due = next(r for r in unique.values() if r[0]['voucher_no'] == voucher)
        if amount > 0 and due is None:
            halt('INCONCLUSIVE', 'INCOMPLETE_DUE_DATE_COVERAGE')
        if due is not None and (doc.due_date != due or
                               schedules and schedules[0].due_date != due):
            halt('SOURCE_ERROR', 'INCONSISTENT_DATA')
    TRACE.append('AGGREGATION')
    eligible = [r for r in unique.values() if r[1] > 0 and r[2] >= cutoff]
    window = [r for r in eligible if r[2] <= cutoff + timedelta(days=30)]
    numerator = sum((r[1] for r in window), Decimal(0))
    denominator = sum((r[1] for r in eligible), Decimal(0))
    if denominator <= 0:
        halt('INCONCLUSIVE', 'ZERO_ELIGIBLE_DENOMINATOR')
    with localcontext() as ctx:
        ctx.prec = 50
        display = (numerator / denominator).quantize(Decimal('.0001'), rounding=ROUND_HALF_UP)
    return {'N': str(numerator), 'D': str(denominator), 'display_4dp': str(display),
            'numerator_count': len({r[0]['voucher_no'] for r in window}),
            'denominator_count': len({r[0]['voucher_no'] for r in eligible}),
            'numerator_refs': sorted(r[0]['voucher_no'] for r in window),
            'denominator_refs': sorted(r[0]['voucher_no'] for r in eligible),
            'schedule_counts': {v: len(d.get('payment_schedule') or []) for v, d in parents.items()}}


def evaluate(request, user='Administrator', rows=None, missing_baseline=False):
    """Test-only application adapter; real auth/providers, no policy configured."""
    TRACE.clear()
    try:
        TRACE.append('A1_AUTH')
        if not user or user == 'Guest':
            halt('FORBIDDEN', 'ACCESS_DENIED')
        TRACE.append('A2_STRUCTURE')
        if not isinstance(request, dict) or request.get('signal_type') not in ('AR_OVERDUE_SPIKE', 'AP_DUE_CLUSTER'):
            halt('VALIDATION_ERROR', 'INVALID_REQUEST')
        if not isinstance(request.get('company'), str) or not request['company'].strip():
            halt('VALIDATION_ERROR', 'INVALID_REQUEST')
        try:
            cutoff = date.fromisoformat(request['as_of_date'])
        except (ValueError, TypeError, KeyError):
            halt('VALIDATION_ERROR', 'INVALID_REQUEST')
        with checked_user(user):
            TRACE.append('A3_COMPANY')
            company = access.get_verified_company(request['company'])
            TRACE.append('A4_SCOPE')
            if cutoff > date.fromisoformat(frappe.utils.nowdate()):
                halt('VALIDATION_ERROR', 'FUTURE_AS_OF')
            if frappe.db.get_value('Company', company, 'default_currency') != 'VND':
                halt('VALIDATION_ERROR', 'UNSUPPORTED_COMPANY_CURRENCY')
            TRACE.append('A5_REPORT_AUTH')
            ar = request['signal_type'] == 'AR_OVERDUE_SPIKE'
            access.check_report_permission('Accounts Receivable' if ar else 'Accounts Payable')
            TRACE.append('A6_SOURCE')
            if ar:
                values = ar_method(company, cutoff, missing_baseline)
            else:
                envelope = report(company, cutoff, 'accounts_payable') if rows is None else {'status': 'success', 'data': rows}
                if envelope['status'] != 'success':
                    halt('SOURCE_ERROR', 'SOURCE_UNAVAILABLE')
                values = ap_method(company, cutoff, envelope['data'])
            TRACE.append('A9_POLICY')
            return outcome('POLICY_PENDING', 'POLICY_NOT_APPROVED', values)
    except StopMethod as error:
        return outcome(error.status, error.reason)
    except frappe.PermissionError:
        return outcome('FORBIDDEN', 'ACCESS_DENIED')


def request(company, signal='AR_OVERDUE_SPIKE', cutoff=CUTOFF):
    return {'company': company, 'signal_type': signal, 'as_of_date': str(cutoff)}


def ensure_fixture():
    for company, abbr in COMPANIES.values():
        if not frappe.db.exists('Company', company):
            frappe.get_doc({'doctype': 'Company', 'company_name': company, 'abbr': abbr,
                            'country': 'Vietnam', 'default_currency': 'VND',
                            'create_chart_of_accounts_based_on': 'Existing Company',
                            'existing_company': 'AI003 Gold 2026'}).insert(ignore_permissions=True)
        for year in (2023, 2024, 2025, 2026):
            name = frappe.db.get_value('Fiscal Year', {'year_start_date': f'{year}-01-01',
                                                      'year_end_date': f'{year}-12-31'}, 'name')
            if not name:
                name = frappe.get_doc({'doctype': 'Fiscal Year', 'year': f'AI003 MG {year}',
                                       'year_start_date': f'{year}-01-01', 'year_end_date': f'{year}-12-31',
                                       'companies': [{'company': company}]}).insert(ignore_permissions=True).name
            fiscal = frappe.get_doc('Fiscal Year', name)
            if fiscal.companies and company not in [r.company for r in fiscal.companies]:
                fiscal.append('companies', {'company': company})
                fiscal.save(ignore_permissions=True)
    for doctype, name, parent_field, root in (
        ('Customer Group', 'AI003 MG Customers', 'parent_customer_group', 'All Customer Groups'),
        ('Supplier Group', 'AI003 MG Suppliers', 'parent_supplier_group', 'All Supplier Groups'),
        ('Territory', 'AI003 MG Territory', 'parent_territory', 'All Territories')):
        if not frappe.db.exists(doctype, name):
            frappe.get_doc({'doctype': doctype, doctype.lower().replace(' ', '_') + '_name': name,
                            parent_field: root, 'is_group': 0}).insert(ignore_permissions=True)
    for doctype, name, details in (
        ('Customer', 'AI003 MG Customer', {'customer_name': 'AI003 MG Customer', 'customer_type': 'Company',
                                         'customer_group': 'AI003 MG Customers', 'territory': 'AI003 MG Territory'}),
        ('Supplier', 'AI003 MG Supplier', {'supplier_name': 'AI003 MG Supplier', 'supplier_type': 'Company',
                                         'supplier_group': 'AI003 MG Suppliers'}),
        ('Supplier', 'AI003 MG Other Supplier', {'supplier_name': 'AI003 MG Other Supplier', 'supplier_type': 'Company',
                                               'supplier_group': 'AI003 MG Suppliers'})):
        if not frappe.db.exists(doctype, name):
            frappe.get_doc({'doctype': doctype, **details}).insert(ignore_permissions=True)


def invoice(scope, doctype, tag, posting, due, amount, **extra):
    company, abbr = COMPANIES[scope]
    existing = frappe.db.get_value(doctype, {'company': company, 'remarks': 'AI003_MG_' + tag,
                                           'docstatus': 1}, 'name')
    if existing:
        return frappe.get_doc(doctype, existing)
    item = {'item_code': 'AI002 TEST SERVICE', 'qty': -1 if amount < 0 else 1, 'rate': abs(amount)}
    sales = doctype == 'Sales Invoice'
    item['income_account' if sales else 'expense_account'] = (
        'Service - ' if sales else 'Office Maintenance Expenses - ') + abbr
    data = {'doctype': doctype, 'company': company, 'posting_date': posting, 'set_posting_time': 1,
            'due_date': due, 'remarks': 'AI003_MG_' + tag, 'currency': 'VND', 'items': [item]}
    if sales:
        data.update(customer='AI003 MG Customer', debit_to='Debtors - ' + abbr)
    else:
        data.update(supplier='AI003 MG Supplier', credit_to='Creditors - ' + abbr)
    data.update(extra)
    doc = frappe.get_doc(data).insert(ignore_permissions=True)
    doc.submit()
    return doc


def build_fixture():
    ensure_fixture()
    old = invoice('ar', 'Sales Invoice', 'AR_OLD', '2026-08-01', '2026-08-10', 100.01)
    invoice('ar', 'Sales Invoice', 'AR_LATER', '2026-08-01', '2026-09-10', 199.99)
    invoice('ar', 'Sales Invoice', 'AR_CREDIT', '2026-08-15', '2026-08-15', -25,
            is_return=1, return_against=old.name, update_outstanding_for_self=1)
    invoice('ar', 'Sales Invoice', 'AR_FUTURE_NOT_DUE', '2026-09-29', '2026-12-01', 925)
    invoice('calendar', 'Sales Invoice', 'AR_CALENDAR', '2023-11-01', '2023-12-01', 300)
    invoice('calendar', 'Sales Invoice', 'AR_MONEY_QUANTUM', '2026-09-01', '2026-12-01', .01,
            disable_rounded_total=1)
    paid = invoice('zero', 'Sales Invoice', 'AR_ZERO', '2026-08-01', '2026-08-10', 100)
    company, abbr = COMPANIES['zero']
    # ERPNext regenerates payment remarks; posted outstanding is the replay guard.
    if Decimal(str(frappe.db.get_value('Sales Invoice', paid.name, 'outstanding_amount'))) > 0:
        from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry
        payment = get_payment_entry('Sales Invoice', paid.name)
        payment.posting_date, payment.set_posting_time = '2026-09-22', 1
        payment.paid_to, payment.remarks = 'Cash - ' + abbr, 'AI003_MG_SETTLE'
        payment.insert(ignore_permissions=True)
        payment.submit()
    ap = {}
    for tag, offset, amount in [('D0', 0, 1.01), ('D30', 30, 1.99), ('D31', 31, 2),
                                ('LONG', 90, 4), ('PAST', -1, 5)]:
        ap[tag] = invoice('ap', 'Purchase Invoice', 'AP_' + tag, '2026-09-01',
                          str(CUTOFF + timedelta(days=offset)), amount)
    ap['CREDIT'] = invoice('ap', 'Purchase Invoice', 'AP_CREDIT', '2026-09-05', str(CUTOFF), -.5,
                           is_return=1, return_against=ap['D0'].name, update_outstanding_for_self=1)
    ap['MONEY_QUANTUM'] = invoice('ap', 'Purchase Invoice', 'AP_MONEY_QUANTUM', '2026-09-01',
                                  str(CUTOFF-timedelta(days=2)), .01, disable_rounded_total=1)
    multi = invoice('multi', 'Purchase Invoice', 'AP_TWO_SCHEDULES', '2026-09-01', '2026-10-06', 7,
                    payment_schedule=[{'due_date': '2026-10-06', 'invoice_portion': 50, 'payment_amount': 3.5},
                                      {'due_date': '2026-10-16', 'invoice_portion': 50, 'payment_amount': 3.5}])
    # One durable commit, exclusively new labelled objects in this isolated site.
    frappe.db.commit()
    OUT['persistent_fixtures'] = [f'Company:{c}' for c, a in COMPANIES.values()]
    for c, a in COMPANIES.values():
        for dt in ('Sales Invoice', 'Purchase Invoice', 'Payment Entry'):
            OUT['persistent_fixtures'].extend(f'{dt}:{n}' for n in frappe.get_all(dt, filters={'company': c}, pluck='name'))
    OUT['fixture_hashes'] = {c: ledger_facts(frappe.db, c, date(2026, 12, 31))[1] for c, a in COMPANIES.values()}
    return ap, multi


def ar_gold():
    vectors = [('SAME_DAY', 'ar', date(2026, 9, 26), date(2026, 8, 26)),
               ('31_TO_30', 'calendar', date(2026, 5, 31), date(2026, 4, 30)),
               ('31_TO_28', 'calendar', date(2025, 3, 31), date(2025, 2, 28)),
               ('31_TO_29', 'calendar', date(2024, 3, 31), date(2024, 2, 29)),
               ('YEAR_BOUNDARY', 'calendar', date(2026, 1, 15), date(2025, 12, 15)),
               ('POSITIVE_DELTA', 'ar', CUTOFF, date(2026, 8, 26)),
               ('NEGATIVE_DELTA', 'ar', date(2026, 9, 30), date(2026, 8, 30)),
               ('ZERO_DELTA', 'calendar', CUTOFF, date(2026, 8, 26))]
    for tag, scope, cutoff, baseline_date in vectors:
        company = COMPANIES[scope][0]
        current = ar_expected(frappe.db, company, cutoff)
        baseline = ar_expected(frappe.db, company, baseline_date)
        delta = (Decimal(current['ratio_published']) - Decimal(baseline['ratio_published'])) * 100
        actual = evaluate(request(company, cutoff=cutoff))
        values = actual.get('result', {}).get('method_values') or {}
        ok = actual['status'] == 'POLICY_PENDING' and values.get('baseline_as_of') == str(baseline_date)
        for side, expected in [('current', current), ('baseline', baseline)]:
            observed = values.get(side, {})
            ok = ok and all(Decimal(observed.get(k, '-999999')) == Decimal(expected[k])
                            for k in ('total_ar', 'ratio_published'))
            selected_cutoff = cutoff if side == 'current' else baseline_date
            source_rows = report(company, selected_cutoff, 'accounts_receivable')['data']
            report_overdue = sum((Decimal(str(r['outstanding'])) for r in source_rows
                                  if r['due_date'] < selected_cutoff), Decimal(0))
            observed['overdue_ar_from_public_report'] = str(report_overdue)
            ok = ok and report_overdue == Decimal(expected['overdue_ar'])
        ok = ok and Decimal(values.get('delta_pp', '-999999')) == delta
        record('AR_' + tag, 'AR', {'current': current, 'baseline': baseline,
                                    'baseline_as_of': str(baseline_date), 'delta_pp': str(delta)}, actual, ok,
               inputs={**request(company, cutoff=cutoff), 'baseline_as_of': str(baseline_date),
                       'public_period_start': f'{cutoff.year}-01-01'})
    for tag, scope, cutoff, missing, reason in (
        ('BASELINE_MISSING', 'ar', CUTOFF, True, 'HISTORY_INSUFFICIENT'),
        ('BASELINE_ZERO', 'ar', date(2026, 8, 26), False, 'BASELINE_DENOMINATOR_INVALID'),
        ('CURRENT_ZERO', 'zero', CUTOFF, False, 'CURRENT_DENOMINATOR_INVALID')):
        actual = evaluate(request(COMPANIES[scope][0], cutoff=cutoff), missing_baseline=missing)
        record('AR_' + tag, 'AR', ['INCONCLUSIVE', reason], [actual['status'], actual['reason_code']],
               kind='LIVE_SOURCE_PLUS_LABELLED_MISSING_OBSERVATION' if missing else 'LIVE_PUBLIC_BOUNDARY',
               inputs={**request(COMPANIES[scope][0], cutoff=cutoff), 'missing_baseline_observation': missing})
    company = COMPANIES['ar'][0]
    expected = ar_expected(frappe.db, company, CUTOFF)
    ar_rows = report(company, CUTOFF, 'accounts_receivable')['data']
    overdue_from_authorized_report = sum((Decimal(str(r['outstanding'])) for r in ar_rows
                                         if r['due_date'] < CUTOFF), Decimal(0))
    record('AR_NET_CREDIT', 'AR', {'total': '275', 'overdue': '275'},
           {'total': expected['total_ar'], 'overdue': str(overdue_from_authorized_report)},
           Decimal(expected['total_ar']) == 275 and overdue_from_authorized_report == 275)
    future_name = frappe.db.get_value('Sales Invoice', {'company': company, 'remarks': 'AI003_MG_AR_FUTURE_NOT_DUE'}, 'name')
    record('AR_FUTURE_POSTING_ISOLATION', 'AR', True,
           future_name not in expected['voucher_refs'] and future_name not in [r['voucher_no'] for r in ar_rows])
    original = ai_api.extract_key_report_data
    def malformed(*args, **kwargs):
        key = kwargs.get('report_key', args[0] if args else None)
        if key == 'accounts_receivable':
            return {'status': 'success', 'company': company, 'data': [{'outstanding': 'bad-source'}]}
        return original(*args, **kwargs)
    with patch.object(ai_api, 'extract_key_report_data', malformed):
        result = evaluate(request(company))
        record('AR_SOURCE_FAILURE_BEFORE_POLICY', 'AR', 'SOURCE_ERROR', result['status'],
               kind='PUBLIC_SNAPSHOT_CONTROLLED_SOURCE_PERTURBATION')
        record('STAGE_SOURCE_BEFORE_POLICY', 'STAGE', ['SOURCE_ERROR', True],
               [result['status'], 'A9_POLICY' not in TRACE], kind='HARNESS_WITH_PUBLIC_SNAPSHOT',
               inputs={**request(company), 'source': 'CONTROLLED_MALFORMED', 'policy': 'ABSENT'})
    def malformed_baseline(*args, **kwargs):
        key = kwargs.get('report_key', args[0] if args else None)
        filters = kwargs.get('filters', args[1] if len(args) > 1 else {})
        if key == 'accounts_receivable' and str(filters.get('report_date')) == '2026-08-26':
            return {'status': 'success', 'company': COMPANIES['zero'][0],
                    'data': [{'outstanding': 'bad-baseline-source'}]}
        return original(*args, **kwargs)
    with patch.object(ai_api, 'extract_key_report_data', malformed_baseline):
        result = evaluate(request(COMPANIES['zero'][0]))
        record('STAGE_BASELINE_SOURCE_BEFORE_CURRENT_ZERO', 'STAGE', ['SOURCE_ERROR', False],
               [result['status'], 'A8_METHOD' in TRACE], kind='PUBLIC_SNAPSHOT_CONTROLLED_BASELINE_PERTURBATION',
               inputs={**request(COMPANIES['zero'][0]), 'current_total_ar': '0',
                       'baseline_source': 'CONTROLLED_MALFORMED', 'policy': 'ABSENT'})


def ap_gold(ap, multi):
    company = COMPANIES['ap'][0]
    rows = report(company, CUTOFF, 'accounts_payable')['data']
    expected = ap_expected(frappe.db, company, CUTOFF)
    result = evaluate(request(company, 'AP_DUE_CLUSTER'), rows=rows)
    values = (result.get('result') or {}).get('method_values') or {}
    keys = ('N', 'D', 'display_4dp', 'numerator_count', 'denominator_count')
    ok = result['status'] == 'POLICY_PENDING' and all(
        Decimal(str(values.get(k, '-999999'))) == Decimal(str(expected[k])) for k in keys)
    record('AP_TRANSACTION_ORACLE', 'AP', {k: expected[k] for k in keys}, result, ok,
           kind='LIVE_REPORT_AND_PARENT_AUTH_TEST_ADAPTER')
    record('AP_FIXTURE_FRACTION', 'PRECISION', ['3', '9', '1/3', '0.3333'],
           [expected['N'], expected['D'], expected['fraction'], expected['display_4dp']])
    for tag, n, d in [('D0', True, True), ('D30', True, True), ('D31', False, True),
                      ('LONG', False, True), ('PAST', False, False), ('CREDIT', False, False)]:
        record('AP_' + tag, 'AP', [n, d],
               [ap[tag].name in values.get('numerator_refs', []), ap[tag].name in values.get('denominator_refs', [])])
    record('AP_DISTINCT_VOUCHER_COUNTS', 'AP', [2, 4],
           [values.get('numerator_count'), values.get('denominator_count')])
    record('AP_ONE_SCHEDULE', 'AP', True, all(values.get('schedule_counts', {}).get(ap[t].name) == 1
                                            for t in ('D0', 'D30', 'D31', 'LONG')))
    record('AP_REAL_ZERO_SCHEDULE_CREDIT', 'AP', [0, 'POLICY_PENDING'],
           [len(frappe.get_doc('Purchase Invoice', ap['CREDIT'].name).payment_schedule), result['status']],
           kind='REAL_SUBMITTED_CREDIT_PI_WITH_ZERO_CHILD_ROWS')
    frappe.db.savepoint('zero_schedule')
    before = ledger_facts(frappe.db, company, CUTOFF)[1]
    frappe.db.delete('Payment Schedule', {'parent': ap['D0'].name, 'parenttype': 'Purchase Invoice'})
    zero = evaluate(request(company, 'AP_DUE_CLUSTER'), rows=rows)
    zero_values = (zero.get('result') or {}).get('method_values') or {}
    record('AP_ZERO_SCHEDULE', 'AP', ['POLICY_PENDING', 0, True],
           [zero['status'], zero_values.get('schedule_counts', {}).get(ap['D0'].name),
            before == ledger_facts(frappe.db, company, CUTOFF)[1]],
           kind='REAL_PARENT_METADATA_PERTURBATION_ROLLED_BACK',
           inputs={**request(company, 'AP_DUE_CLUSTER'), 'metadata_perturbation': 'delete Payment Schedule under savepoint',
                   'parent_ref': ap['D0'].name})
    frappe.db.rollback(save_point='zero_schedule')
    multi_company = COMPANIES['multi'][0]
    multi_rows = report(multi_company, CUTOFF, 'accounts_payable')['data']
    observed = evaluate(request(multi_company, 'AP_DUE_CLUSTER'), rows=multi_rows)
    doc = frappe.get_doc('Purchase Invoice', multi.name)
    record('AP_REAL_TWO_SCHEDULES_FLATTENED', 'AP', [2, 1, 'INCONCLUSIVE', 'UNSUPPORTED_MULTI_SCHEDULE'],
           [len(doc.payment_schedule), len([r for r in multi_rows if r['voucher_no'] == multi.name]),
            observed['status'], observed['reason_code']], kind='REAL_SUBMITTED_PI_AND_PARENT_AUTH',
           inputs={**request(multi_company, 'AP_DUE_CLUSTER'), 'parent_ref': multi.name, 'based_on_payment_terms': 0})
    base = next(r for r in rows if r['voucher_no'] == ap['D0'].name)
    perturbations = []
    perturbations.append(('EXACT_DUPLICATE', rows + [copy.deepcopy(base)], 'POLICY_PENDING', 'POLICY_NOT_APPROVED'))
    for label, updates, status, reason in (
        ('AMOUNT_CONFLICT', {'outstanding': str(Decimal(str(base['outstanding'])) + Decimal('.01'))}, 'SOURCE_ERROR', 'CONFLICTING_OBSERVATION'),
        ('DATE_CONFLICT', {'due_date': CUTOFF + timedelta(days=1)}, 'SOURCE_ERROR', 'CONFLICTING_OBSERVATION'),
        ('CURRENCY_MISMATCH', {'currency': 'USD'}, 'VALIDATION_ERROR', 'UNSUPPORTED_COMPANY_CURRENCY'),
        ('CURRENCY_CONTRADICTION', {'account_currency': 'USD'}, 'SOURCE_ERROR', 'INCONSISTENT_DATA'),
        ('UNVERIFIED_ACCOUNT_SCOPE', {'party_account': 'CONTROLLED_UNVERIFIED_ACCOUNT'}, 'INCONCLUSIVE', 'UNSUPPORTED_ALLOCATION_SCOPE')):
        perturbations.append((label, rows + [{**base, **updates}], status, reason))
    for label, due, status, reason in [('MISSING_DUE_DATE', None, 'INCONCLUSIVE', 'INCOMPLETE_DUE_DATE_COVERAGE'),
                                     ('MALFORMED_DUE_DATE', 'bad-date', 'SOURCE_ERROR', 'SOURCE_INVALID')]:
        altered = [{**r, 'due_date': due} if r['voucher_no'] == ap['D0'].name else r for r in rows]
        perturbations.append((label, altered, status, reason))
    for label, altered, status, reason in perturbations:
        observed = evaluate(request(company, 'AP_DUE_CLUSTER'), rows=altered)
        record('AP_' + label, 'AP', [status, reason], [observed['status'], observed['reason_code']],
               kind='LABELLED_REPORT_ROW_PERTURBATION')
        if label == 'EXACT_DUPLICATE':
            v = (observed.get('result') or {}).get('method_values') or {}
            record('AP_DUPLICATE_NO_DOUBLE_COUNT', 'AP', [expected['N'], expected['D'], 2, 4],
                   [v.get('N'), v.get('D'), v.get('numerator_count'), v.get('denominator_count')],
                   Decimal(v['N']) == Decimal(expected['N']) and Decimal(v['D']) == Decimal(expected['D'])
                   and v['numerator_count'] == 2 and v['denominator_count'] == 4)
        if label.startswith('CURRENCY_'):
            record('AP_' + label + '_BEFORE_IDENTITY', 'PRECISION', False,
                   any(stage in TRACE for stage in ('A7_IDENTITY', 'A8_METHOD', 'AGGREGATION')),
                   kind='INSTRUMENTED_TEST_ADAPTER')
        if status in ('SOURCE_ERROR', 'FORBIDDEN', 'VALIDATION_ERROR'):
            record('AP_' + label + '_PAYLOAD_SUPPRESSED', 'SECURITY', None, observed['result'])
    # Exact finite comparison against a TEST_ONLY arithmetic operand, never policy.
    n, d, t = Decimal(values['N']), Decimal(values['D']), Decimal('0.33332')
    with localcontext() as context:
        context.prec = 50
        exact = n >= t * d
        rounded = Decimal(values['display_4dp']) >= t
    proof = {'label': 'TEST_ONLY_NOT_APPROVED_POLICY', 'N': str(n), 'D': str(d),
             'fraction': expected['fraction'], 'display_4dp_HALF_UP': values['display_4dp'],
             'T': str(t), 'T_times_D': str(t*d), 'exact_comparison': exact,
             'rounded_display_comparison': rounded,
             'independent_fraction_comparison': Fraction(n) >= Fraction(t) * Fraction(d)}
    OUT['exact_fraction_proof'] = proof
    record('AP_EXACT_FRACTION_COMPARISON', 'PRECISION', [True, False, True],
           [proof['exact_comparison'], rounded, proof['independent_fraction_comparison']],
           kind='TRANSACTION_AMOUNTS_TEST_ONLY_OPERAND')
    return rows


def security_gold(rows, multi):
    company = COMPANIES['ap'][0]
    for user in (USER, DENIED_USER):
        assert not frappe.db.exists('User', user), 'Temporary probe user unexpectedly exists'
        frappe.get_doc({'doctype': 'User', 'email': user, 'first_name': 'AI003 Method Gold',
                        'send_welcome_email': 0, 'user_type': 'System User',
                        'roles': [{'role': 'Accounts User'}]}).insert(ignore_permissions=True)
        frappe.get_doc({'doctype': 'User Permission', 'user': user, 'allow': 'Company',
                        'for_value': company, 'apply_to_all_doctypes': 1}).insert(ignore_permissions=True)
    frappe.get_doc({'doctype': 'User Permission', 'user': DENIED_USER, 'allow': 'Supplier',
                    'for_value': 'AI003 MG Other Supplier', 'apply_to_all_doctypes': 1}).insert(ignore_permissions=True)
    base = next(r for r in rows if Decimal(str(r['outstanding'])) > 0)
    permitted_doc = frappe.get_doc('Purchase Invoice', base['voucher_no'])
    record('CHECKED_USER_METADATA_PERMISSION_REAL', 'SECURITY', [True, False],
           [permitted_doc.has_permission('read', user=USER), permitted_doc.has_permission('read', user=DENIED_USER)],
           inputs={'parent_ref': base['voucher_no'], 'checked_users': [USER, DENIED_USER], 'ambient_user': 'Administrator'})
    allow = evaluate(request(company, 'AP_DUE_CLUSTER'), user=USER)
    record('CHECKED_USER_LIVE_REPORT_ALLOW', 'SECURITY', 'POLICY_PENDING', allow['status'],
           inputs={**request(company, 'AP_DUE_CLUSTER'), 'checked_user': USER})
    deny = evaluate(request(company, 'AP_DUE_CLUSTER'), user=DENIED_USER, rows=rows)
    record('CHECKED_USER_SCHEDULE_METADATA_DENIAL', 'SECURITY', ['FORBIDDEN', 'ACCESS_DENIED', None],
           [deny['status'], deny['reason_code'], deny['result']], kind='REAL_PARENT_PERMISSION_ADMIN_SOURCE_PROBE',
           inputs={**request(company, 'AP_DUE_CLUSTER'), 'checked_user': DENIED_USER,
                   'report_rows_provenance': 'CONTROLLED_ADMIN_REPORT', 'rows_hash': fingerprint(rows)})
    crossed = [{**base, 'voucher_no': multi.name}]
    deny = evaluate(request(company, 'AP_DUE_CLUSTER'), rows=crossed)
    record('CROSS_COMPANY_METADATA_DENIAL', 'SECURITY', ['FORBIDDEN', 'ACCESS_DENIED', None],
           [deny['status'], deny['reason_code'], deny['result']],
           inputs={**request(company, 'AP_DUE_CLUSTER'), 'foreign_parent_ref': multi.name,
                   'foreign_company': COMPANIES['multi'][0], 'checked_user': 'Administrator'})
    nonexistent = [{**base, 'voucher_no': 'AI003-MG-NONEXISTENT'}]
    # Parent nonexistence must map to the same generic denial as no authorization.
    absent = evaluate(request(company, 'AP_DUE_CLUSTER'), rows=nonexistent)
    record('NONEXISTENT_PARENT_GENERIC_DENIAL', 'SECURITY', deny, absent,
           inputs={**request(company, 'AP_DUE_CLUSTER'), 'parent_ref': 'AI003-MG-NONEXISTENT'})
    a = evaluate({'signal_type': 'bad', 'company': 'NONEXISTENT'}, user='Guest')
    record('STAGE_A_UNAUTH_INVALID_SIGNAL', 'STAGE', ['FORBIDDEN', ['A1_AUTH']], [a['status'], list(TRACE)],
           inputs={'company': 'NONEXISTENT', 'signal_type': 'bad', 'checked_user': 'Guest'})
    b = evaluate({'signal_type': 'bad', 'company': 'NONEXISTENT'}, user=USER)
    record('STAGE_B_STRUCTURAL_NO_COMPANY_LOOKUP', 'STAGE', ['VALIDATION_ERROR', ['A1_AUTH', 'A2_STRUCTURE']],
           [b['status'], list(TRACE)], inputs={'company': 'NONEXISTENT', 'signal_type': 'bad', 'checked_user': USER})
    future = date.fromisoformat(frappe.utils.nowdate()) + timedelta(days=1)
    c = evaluate(request(COMPANIES['ar'][0], cutoff=future), user=USER)
    record('STAGE_C_COMPANY_BEFORE_FUTURE', 'STAGE', ['FORBIDDEN', False],
           [c['status'], 'A4_SCOPE' in TRACE], inputs={**request(COMPANIES['ar'][0], cutoff=future), 'checked_user': USER})
    e = evaluate(request(COMPANIES['ar'][0]), missing_baseline=True)
    record('STAGE_E_HISTORY_BEFORE_POLICY', 'STAGE', ['INCONCLUSIVE', False],
           [e['status'], 'A9_POLICY' in TRACE], inputs={**request(COMPANIES['ar'][0]), 'missing_baseline_observation': True})
    f = evaluate(request(COMPANIES['ar'][0]))
    record('STAGE_F_VALID_WITHOUT_POLICY', 'STAGE', ['POLICY_PENDING', 'POLICY_NOT_APPROVED', None],
           [f['status'], f['reason_code'], f['result']['finding']],
           inputs={**request(COMPANIES['ar'][0]), 'policy': 'ABSENT'})
    # Real authoritative report restrictions, transient and isolated.
    frappe.db.savepoint('report_deny')
    frappe.db.delete('Custom Role', {'report': 'Accounts Receivable'})
    frappe.get_doc({'doctype': 'Custom Role', 'report': 'Accounts Receivable',
                    'roles': [{'role': 'System Manager'}]}).insert(ignore_permissions=True)
    with checked_user(USER):
        try:
            access.check_report_permission('Accounts Receivable')
            denied = False
        except frappe.PermissionError:
            denied = True
    record('AR_REPORT_PERMISSION_DENIAL', 'AR', True, denied,
           inputs={'report': 'Accounts Receivable', 'checked_user': USER, 'allowed_role': 'System Manager'})
    # Assign an additional allowed company temporarily so report denial, not company denial, wins.
    frappe.get_doc({'doctype': 'User Permission', 'user': USER, 'allow': 'Company',
                    'for_value': COMPANIES['ar'][0], 'apply_to_all_doctypes': 1}).insert(ignore_permissions=True)
    frappe.clear_cache(user=USER)
    denied = evaluate(request(COMPANIES['ar'][0]), user=USER)
    record('AR_PUBLIC_PATH_REPORT_DENIAL', 'SECURITY', ['FORBIDDEN', 'ACCESS_DENIED', None],
           [denied['status'], denied['reason_code'], denied['result']],
           inputs={**request(COMPANIES['ar'][0]), 'checked_user': USER, 'report_restricted': 'Accounts Receivable'})
    frappe.db.rollback(save_point='report_deny')
    record('CHECKED_USER_SESSION_RESTORED', 'SECURITY', 'Administrator', frappe.session.user)


def run_method_gold():
    frappe.init(site=SITE, sites_path='/home/frappe/frappe-bench/sites')
    frappe.connect()
    frappe.set_user('Administrator')
    assert frappe.local.site == SITE
    global access, ai_api, extract_key_report_data, get_financial_snapshot
    from lotus_fin.security import access
    from lotus_fin.api import ai_insights as ai_api
    from lotus_fin.api.key_reports import extract_key_report_data
    from lotus_fin.api.ai_insights import get_financial_snapshot
    from erpnext.accounts.utils import get_currency_precision
    protected = {c: ledger_facts(frappe.db, c, date(2026, 12, 31))[1]
                 for c in frappe.get_all('Company', pluck='name') if not c.startswith('AI003 MG ')}
    try:
        precision = get_currency_precision() or 2
        OUT['runtime'] = {'site': SITE, 'db_host': frappe.conf.db_host,
                          'db_resolved': socket.gethostbyname(frappe.conf.db_host),
                          'db_connection': frappe.db.sql('select 1')[0][0],
                          'apps': frappe.get_installed_apps(),
                          'timezone': frappe.db.get_single_value('System Settings', 'time_zone'),
                          'app_path': str(Path(__import__('lotus_fin').__file__).resolve()),
                          'date': frappe.utils.nowdate()}
        OUT['runtime']['source_hashes'] = {
            path: hashlib.sha256(Path('/review/lotus_fin/lotus_fin').joinpath(path).read_bytes()).hexdigest()
            for path in ['api/ai_insights.py', 'api/key_reports.py', 'security/access.py',
                         'core/domain/calculators/ar_extractor.py']}
        record('RUNTIME_DB_APPS_TIMEZONE', 'RUNTIME', True,
               OUT['runtime']['db_connection'] == 1 and OUT['runtime']['timezone'] == 'Asia/Ho_Chi_Minh'
               and all(a in OUT['runtime']['apps'] for a in ('frappe', 'erpnext', 'lotus_fin')))
        production_path = Path('/review/lotus_fin/lotus_fin')
        aligned = all(hashlib.sha256(p.read_bytes()).hexdigest() ==
                      hashlib.sha256((Path(__import__('lotus_fin').__file__).parent / p.relative_to(production_path)).read_bytes()).hexdigest()
                      for p in production_path.rglob('*.py') if '.zcode' not in p.parts)
        record('RUNTIME_CURRENT_SOURCE_ALIGNMENT', 'RUNTIME', True, aligned)
        OUT['numeric_domain'] = {'currency': 'VND', 'report_money_scale': precision,
                                 'report_Q_MONEY': str(Decimal(10) ** -precision),
                                 'AI001_money_scale': 2, 'AI001_Q_MONEY': '0.01',
                                 'AI001_ratio_scale': 4, 'AR_delta_quantum_pp': '0.01'}
        if precision != 2:
            record('NUMERIC_DOMAIN', 'PRECISION', 2, precision)
            raise RuntimeError('Numeric domain differs; stop before fixture creation')
        ap, multi = build_fixture()
        # All following metadata/user changes roll back; durable fixture stays.
        frappe.db.savepoint('temporary_probes')
        a = snapshot(COMPANIES['ar'][0], date(2026, 8, 26))
        mm = {m['metric_id']: m for m in a['metrics']}
        ratio = Decimal(str(mm['overdue_ar_ratio']['value']))
        expected_ratio = ar_expected(frappe.db, COMPANIES['ar'][0], date(2026, 8, 26))['ratio_published']
        record('NUMERIC_DOMAIN', 'PRECISION', [expected_ratio, '275', 2],
               [str(ratio), str(Decimal(str(mm['ar_outstanding']['value']))), precision],
               ratio == Decimal(expected_ratio) == Decimal('.2727') and
               Decimal(str(mm['ar_outstanding']['value'])) == 275 and precision == 2,
               inputs={**request(COMPANIES['ar'][0], cutoff=date(2026,8,26)), 'ratio_quantization': '.0001'})
        money_observations = []
        for scope, key, tag in [('calendar', 'accounts_receivable', 'AR_MONEY_QUANTUM'),
                                ('ap', 'accounts_payable', 'AP_MONEY_QUANTUM')]:
            company = COMPANIES[scope][0]
            doctype = 'Sales Invoice' if key == 'accounts_receivable' else 'Purchase Invoice'
            voucher = frappe.db.get_value(doctype, {'company': company, 'remarks': 'AI003_MG_' + tag}, 'name')
            observed = next(r for r in report(company, CUTOFF, key)['data'] if r['voucher_no'] == voucher)
            money_observations.append(Decimal(str(observed['outstanding'])))
        record('LIVE_MINIMUM_MONEY_QUANTUM', 'PRECISION', ['0.01', '0.01'],
               [str(v) for v in money_observations], all(v == Decimal('.01') for v in money_observations),
               inputs={'source_keys': ['accounts_receivable', 'accounts_payable'],
                       'new_fixture_amount': '0.01', 'disable_rounded_total': 1, 'policy_values': 'NONE'})
        if OUT['cases'][-1]['execution_status'] != 'PASS' or OUT['cases'][-2]['execution_status'] != 'PASS':
            raise RuntimeError('Numeric-domain contradiction: stop METHOD GOLD')
        ar_gold()
        rows = ap_gold(ap, multi)
        security_gold(rows, multi)
    except Exception as error:
        import traceback
        OUT['errors'].append({'type': type(error).__name__, 'message': str(error),
                              'traceback': traceback.format_exc()})
        print('RUN_ERROR', type(error).__name__, str(error), flush=True)
    finally:
        frappe.set_user('Administrator')
        frappe.db.rollback()
        for user in (USER, DENIED_USER):
            frappe.clear_cache(user=user)
        record('TEMPORARY_USERS_REMOVED', 'HYGIENE', True,
               all(not frappe.db.exists('User', user) for user in (USER, DENIED_USER)))
        record('PROTECTED_FIXTURES_UNCHANGED', 'HYGIENE', True,
               all(ledger_facts(frappe.db, c, date(2026, 12, 31))[1] == h for c, h in protected.items()))
        if OUT.get('fixture_hashes'):
            record('METHOD_FIXTURES_UNCHANGED_AFTER_PROBES', 'HYGIENE', True,
                   all(ledger_facts(frappe.db, c, date(2026, 12, 31))[1] == h
                       for c, h in OUT['fixture_hashes'].items()))
        recorded = {c['case_id'] for c in OUT['cases']}
        for category, case_ids in REQUIRED.items():
            for case_id in case_ids:
                if case_id not in recorded:
                    OUT['cases'].append({'case_id': case_id, 'category': category,
                                         'method_version': OUT['method_version'], 'inputs': {'site': SITE},
                                         'expected': 'REQUIRED_CASE', 'actual': None,
                                         'source_fixture_refs': OUT['persistent_fixtures'],
                                         'source_fixture_hashes': OUT.get('fixture_hashes', {}),
                                         'execution_status': 'NOT_RUN',
                                         'evidence_reference': 'AI003_METHOD_GOLD_MANIFEST.yaml#' + case_id})
        OUT['counts'] = {'passed': sum(c['execution_status'] == 'PASS' for c in OUT['cases']),
                         'failed': sum(c['execution_status'] == 'FAIL' for c in OUT['cases']),
                         'not_run': sum(c['execution_status'] == 'NOT_RUN' for c in OUT['cases']),
                         'errors': len(OUT['errors'])}
        OUT['oracle_sha256'] = hashlib.sha256(Path(__file__).resolve().parents[1].joinpath('AI003_METHOD_GOLD_ORACLE.py').read_bytes()).hexdigest()
        OUT['runner_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        print('RESULT_JSON:' + json.dumps(OUT, default=str), flush=True)
        frappe.db.rollback()
        frappe.destroy()


if __name__ == '__main__':
    run_method_gold()

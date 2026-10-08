"""Independent transaction oracle for controlled AI003 METHOD GOLD.

Only stdlib imports. No Lotus Fin, AI003, provider, or candidate-harness import.
Balances come from posted Payment Ledger Entry attribution, not report output.
"""
from datetime import date, timedelta
from decimal import Decimal
from fractions import Fraction
import hashlib
import json


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()


def rounded_fraction(value, places=4):
    """ROUND_HALF_UP with integer arithmetic, independent of Decimal context."""
    sign = -1 if value < 0 else 1
    value = abs(value)
    scaled = (2 * value.numerator * 10**places + value.denominator) // (2 * value.denominator)
    return f'{Decimal(sign * scaled) / Decimal(10**places):.{places}f}'


def ledger_facts(db, company, cutoff):
    cutoff = date.fromisoformat(str(cutoff))
    vouchers = []
    for doctype in ('Sales Invoice', 'Purchase Invoice'):
        for row in db.get_all(doctype, filters={'company': company, 'docstatus': 1,
                                               'posting_date': ['<=', cutoff]},
                              fields=['name', 'posting_date', 'due_date', 'grand_total',
                                      'is_return', 'currency'], order_by='name', limit_page_length=1000):
            vouchers.append({'doctype': doctype, **dict(row)})
    entries = db.get_all('Payment Ledger Entry', filters={'company': company, 'delinked': 0,
                                                         'posting_date': ['<=', cutoff]},
                         fields=['voucher_type', 'voucher_no', 'against_voucher_type',
                                 'against_voucher_no', 'amount', 'posting_date', 'account'],
                         order_by='posting_date,name', limit_page_length=2000)
    balances = {}
    for row in entries:
        key = (row.against_voucher_type, row.against_voucher_no)
        balances[key] = balances.get(key, Fraction(0)) + Fraction(str(row.amount))
    facts = []
    for voucher in vouchers:
        key = (voucher['doctype'], voucher['name'])
        if key in balances:
            facts.append({**voucher, 'residual': str(Decimal(balances[key].numerator) /
                                                   Decimal(balances[key].denominator))})
    return facts, fingerprint({'vouchers': vouchers, 'ledger': entries})


def ar_expected(db, company, cutoff):
    facts, source_hash = ledger_facts(db, company, cutoff)
    rows = [r for r in facts if r['doctype'] == 'Sales Invoice']
    total = sum((Fraction(r['residual']) for r in rows), Fraction(0))
    overdue = sum((Fraction(r['residual']) for r in rows
                   if r['due_date'] < cutoff), Fraction(0))
    return {'total_ar': str(Decimal(total.numerator) / Decimal(total.denominator)),
            'overdue_ar': str(Decimal(overdue.numerator) / Decimal(overdue.denominator)),
            'ratio_published': rounded_fraction(overdue / total) if total else '0.0000',
            'source_hash': source_hash, 'voucher_refs': [r['name'] for r in rows]}


def ap_expected(db, company, cutoff):
    facts, source_hash = ledger_facts(db, company, cutoff)
    ap = [r for r in facts if r['doctype'] == 'Purchase Invoice']
    eligible = [r for r in ap if Fraction(r['residual']) > 0 and r['due_date'] >= cutoff]
    window = [r for r in eligible if r['due_date'] <= cutoff + timedelta(days=30)]
    numerator = sum((Fraction(r['residual']) for r in window), Fraction(0))
    denominator = sum((Fraction(r['residual']) for r in eligible), Fraction(0))
    share = numerator / denominator if denominator else None
    return {'N': str(Decimal(numerator.numerator) / Decimal(numerator.denominator)),
            'D': str(Decimal(denominator.numerator) / Decimal(denominator.denominator)),
            'fraction': str(share) if share is not None else None,
            'display_4dp': rounded_fraction(share) if share is not None else None,
            'numerator_count': len({r['name'] for r in window}),
            'denominator_count': len({r['name'] for r in eligible}),
            'numerator_refs': [r['name'] for r in window],
            'denominator_refs': [r['name'] for r in eligible],
            'source_hash': source_hash}

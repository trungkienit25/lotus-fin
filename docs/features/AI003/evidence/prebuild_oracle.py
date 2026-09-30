"""Independent synthetic voucher oracle. No Lotus Fin production imports."""
from datetime import date, timedelta
from decimal import Decimal
import hashlib
import json


def stable_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()


def voucher_oracle(db, company, cutoff):
    cutoff = date.fromisoformat(str(cutoff))
    invoices, payments, credits, records = {}, [], [], []
    for dt in ('Sales Invoice', 'Purchase Invoice'):
        rows = db.get_all(dt, filters={'company': company, 'docstatus': 1, 'posting_date': ['<=', cutoff]},
                          fields=['name', 'posting_date', 'due_date', 'grand_total', 'is_return', 'return_against', 'currency'],
                          order_by='name', limit_page_length=1000)
        for row in rows:
            records.append({'doctype': dt, **dict(row)})
            if row.is_return:
                credits.append(row)
            else:
                invoices[(dt, row.name)] = dict(row)
    entries = db.get_all('Payment Entry', filters={'company': company, 'docstatus': 1, 'posting_date': ['<=', cutoff]},
                         fields=['name', 'posting_date'], order_by='name', limit_page_length=1000)
    for pe in entries:
        for ref in db.get_all('Payment Entry Reference', filters={'parent': pe.name},
                             fields=['reference_doctype', 'reference_name', 'allocated_amount'], order_by='idx', limit_page_length=1000):
            payments.append({'payment': pe.name, 'posting_date': pe.posting_date, **dict(ref)})
    # return_against alone is not proof of credit allocation. Attribute signed
    # residuals from the posted subledger, independent of report calculations.
    ledger = db.get_all('Payment Ledger Entry', filters={'company': company, 'delinked': 0, 'posting_date': ['<=', cutoff]},
                        fields=['voucher_type', 'voucher_no', 'against_voucher_type', 'against_voucher_no', 'amount', 'posting_date', 'account'],
                        order_by='posting_date,name', limit_page_length=1000)
    balances = {}
    for row in ledger:
        key = (row.against_voucher_type, row.against_voucher_no)
        balances[key] = balances.get(key, Decimal(0)) + Decimal(str(row.amount))
    residuals = []
    for inv in records:
        dt, name = inv['doctype'], inv['name']
        if (dt, name) not in balances:
            continue  # allocated credit appears only in its invoice residual
        residuals.append({'doctype': dt, 'voucher': name, 'due_date': str(inv['due_date']), 'gross': str(inv['grand_total']),
                          'is_return': inv['is_return'], 'return_against': inv['return_against'], 'residual': str(balances[(dt, name)])})
    positive = [r for r in residuals if Decimal(r['residual']) > 0]
    ar = [r for r in positive if r['doctype'] == 'Sales Invoice']
    ap = [r for r in positive if r['doctype'] == 'Purchase Invoice']
    net_ar = [r for r in residuals if r['doctype'] == 'Sales Invoice']
    total_ar = sum((Decimal(r['residual']) for r in net_ar), Decimal(0))
    overdue = sum((Decimal(r['residual']) for r in net_ar if date.fromisoformat(r['due_date']) < cutoff), Decimal(0))
    short = sum((Decimal(r['residual']) for r in ap if cutoff + timedelta(days=1) <= date.fromisoformat(r['due_date']) <= cutoff + timedelta(days=7)), Decimal(0))
    horizon = sum((Decimal(r['residual']) for r in ap if cutoff + timedelta(days=1) <= date.fromisoformat(r['due_date']) <= cutoff + timedelta(days=30)), Decimal(0))
    return {'company': company, 'as_of': str(cutoff), 'total_ar': str(total_ar), 'overdue_ar': str(overdue),
            'ar_ratio': str(overdue / total_ar) if total_ar else None,
            'ap_short': str(short), 'ap_horizon': str(horizon), 'ap_ratio': str(short / horizon) if horizon else None,
            'ar_positive_residual': str(sum((Decimal(r['residual']) for r in ar), Decimal(0))),
            'ar_unallocated_credit': str(sum((Decimal(r['residual']) for r in net_ar if Decimal(r['residual']) < 0), Decimal(0))),
            'ap_unallocated_credit': str(sum((Decimal(r['residual']) for r in residuals if r['doctype'] == 'Purchase Invoice' and Decimal(r['residual']) < 0), Decimal(0))),
            'ap_total_positive': str(sum((Decimal(r['residual']) for r in ap), Decimal(0))),
            'ap_overdue': str(sum((Decimal(r['residual']) for r in ap if date.fromisoformat(r['due_date']) < cutoff), Decimal(0))),
            'ap_due_today': str(sum((Decimal(r['residual']) for r in ap if date.fromisoformat(r['due_date']) == cutoff), Decimal(0))),
            'residuals': residuals, 'source_refs': [f'{r["doctype"]}:{r["voucher"]}' for r in residuals],
            'source_hash': stable_hash({'invoices': records, 'payment_allocations': payments, 'payment_ledger': ledger}),
            'source_records': records, 'payment_allocations': payments, 'payment_ledger': ledger,
            'ar_netting_policy': 'Observed AI001 net residual; positive-only/credit policy requires approval',
            'ap_netting_policy': 'positive obligation residual; posted allocated credits reduce invoice once; unallocated credits separate'}

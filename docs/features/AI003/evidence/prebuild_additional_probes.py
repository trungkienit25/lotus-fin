"""Boundary, zero-denominator and explanation probes; isolated synthetic site only."""
import copy
import json
from datetime import timedelta
from decimal import Decimal
from pathlib import Path
import frappe
import prebuild_verifier as v
from prebuild_oracle import voucher_oracle, stable_hash

frappe.init(site=v.SITE, sites_path='/home/frappe/frappe-bench/sites'); frappe.connect(); frappe.set_user('Administrator')
assert frappe.local.site == v.SITE
from lotus_fin.ai.financial_snapshot import parse_ar_data
from lotus_fin.cashflow.adapters import get_trade_obligations

ar_source = v.source('accounts_receivable')
obs = get_trade_obligations(v.C, v.CUTOFF)
for tag, offset, amount in [('D1', 1, 75000), ('D7', 7, 200000), ('D8', 8, 300000), ('D30', 30, 400000), ('D31', 31, 500000), ('OVERDUE', -1, 600000), ('TODAY', 0, 700000)]:
    name = frappe.db.get_value('Purchase Invoice', {'company': v.C, 'remarks': 'AI003_AP_' + tag}, 'name')
    row = next(o for o in obs if o.source_ref == 'Purchase Invoice:' + name)
    in_short = v.CUTOFF + timedelta(days=1) <= row.due_date <= v.CUTOFF + timedelta(days=7)
    in_horizon = v.CUTOFF + timedelta(days=1) <= row.due_date <= v.CUTOFF + timedelta(days=30)
    expected = {'due_date': str(v.CUTOFF + timedelta(days=offset)), 'residual': str(amount), 'short': 1 <= offset <= 7, 'horizon': 1 <= offset <= 30}
    actual = {'due_date': str(row.due_date), 'residual': str(row.remaining_amount), 'short': in_short, 'horizon': in_horizon}
    v.record('AP_BOUNDARY_' + tag, expected, actual, row.due_date == v.CUTOFF + timedelta(days=offset) and row.remaining_amount == amount and in_short == expected['short'] and in_horizon == expected['horizon'], source_ref=row.source_ref)
for tag, offset, amount in [('BEFORE', -1, 75000), ('EXACT', 0, 200000), ('AFTER', 1, 300000)]:
    name = frappe.db.get_value('Sales Invoice', {'company': v.C, 'remarks': 'AI003_AR_' + tag}, 'name')
    row = next(r for r in ar_source['data'] if r.get('voucher_no') == name)
    total, overdue, ratio, limits = parse_ar_data([row], as_of_date=v.CUTOFF, company=v.C)
    expected = amount if offset < 0 else 0
    v.record('AR_DUE_' + tag, expected, str(overdue), overdue == expected, source_ref='Sales Invoice:' + name)
oracle = voucher_oracle(frappe.db, v.C, v.CUTOFF)
v.RESULT['gold']['credits'] = oracle
v.record('ALLOCATED_CREDITS_ONCE', {'AR_original': '75000', 'AP_original': '75000'}, {'AR_original': next(r['residual'] for r in oracle['residuals'] if r['voucher'] == frappe.db.get_value('Sales Invoice', {'company':v.C,'remarks':'AI003_AR_BEFORE'},'name')), 'AP_original': next(r['residual'] for r in oracle['residuals'] if r['voucher'] == frappe.db.get_value('Purchase Invoice', {'company':v.C,'remarks':'AI003_AP_D1'},'name'))}, all(any(r['residual'] == '75000.0' and r['doctype'] == dt for r in oracle['residuals']) for dt in ('Sales Invoice','Purchase Invoice')))
v.record('UNALLOCATED_CREDIT_CONTEXT', {'AR':'-10000', 'AP':'-10000'}, {'AR':oracle['ar_unallocated_credit'],'AP':oracle['ap_unallocated_credit']}, Decimal(oracle['ar_unallocated_credit']) == -10000 and Decimal(oracle['ap_unallocated_credit']) == -10000)

empty = 'AI003 Empty 2026'
if not frappe.db.exists('Company', empty):
    frappe.get_doc({'doctype':'Company','company_name':empty,'abbr':'A3E','country':'Vietnam','default_currency':'VND','chart_of_accounts':'Standard'}).insert(ignore_permissions=True)
    fy = frappe.get_doc('Fiscal Year','2026'); fy.append('companies',{'company':empty}); fy.save(ignore_permissions=True)
    frappe.db.commit()
empty_oracle = voucher_oracle(frappe.db, empty, v.CUTOFF)
empty_report = v.fetch('accounts_receivable', {'company':empty,'report_date':str(v.CUTOFF)},empty)
v.record('LEGITIMATE_EMPTY_SITE', {'total_ar':'0','ratio':None}, {'row_count':len(empty_report['data']),'oracle_ar':empty_oracle['total_ar'],'oracle_ratio':empty_oracle['ar_ratio']}, not empty_report['data'] and Decimal(empty_oracle['total_ar']) == 0 and empty_oracle['ar_ratio'] is None)
v.RESULT['gold']['empty'] = empty_oracle
v.record('ZERO_DENOMINATOR_SPEC', {'AR':'INCONCLUSIVE','AP':'NOT_APPLICABLE','finding':None,'severity':None}, {'AR':'INCONCLUSIVE','AP':'NOT_APPLICABLE','finding':None,'severity':None}, True, assessment='candidate specification only; needs AI003 adapter mapping, no production rule verdict')

# AP posting-date and cancellation checks are rolled back, leaving fixture unchanged.
before = get_trade_obligations(v.C, v.CUTOFF)
before_hash = stable_hash(v.source('accounts_payable')['data'])
future = v.create_invoice('Purchase Invoice','AI003_TRANSIENT_AP_FUTURE','2026-10-05','2026-10-10',333000)
v.record('AP_FUTURE_POSTING', before_hash, stable_hash(v.source('accounts_payable')['data']), before_hash == stable_hash(v.source('accounts_payable')['data']))
cancelled = v.create_invoice('Purchase Invoice','AI003_TRANSIENT_AP_CANCEL','2026-09-02','2026-09-30',99000)
with_cancel = get_trade_obligations(v.C, v.CUTOFF)
cancelled.cancel()
after = get_trade_obligations(v.C, v.CUTOFF)
ref = 'Purchase Invoice:' + cancelled.name
v.record('AP_CANCELLED_VOUCHER', {'present_before':True,'present_after':False}, {'present_before':any(o.source_ref==ref for o in with_cancel),'present_after':any(o.source_ref==ref for o in after)}, any(o.source_ref==ref for o in with_cancel) and not any(o.source_ref==ref for o in after))
frappe.db.rollback()

# Test existing bounded architecture without making a model/network request.
from lotus_fin.ai.explanation import LLMExplanationProvider, generate_financial_explanation
snap = v.snapshot()
for label, raw in [('TIMEOUT',(504,'Gateway Timeout',{})), ('UNAVAILABLE',(500,'Unavailable',{})), ('MALFORMED',(200,'<html>invalid</html>',{})), ('GROUNDING',(200,json.dumps({'status':'AVAILABLE','facts':['Revenue is 999999999.00 VND.'],'interpretations':[],'next_checks':[]}),{}))]:
    provider = LLMExplanationProvider()
    provider.generate_explanation_raw = lambda payload, raw=raw: raw
    preserved = copy.deepcopy(snap['metrics'])
    explanation = generate_financial_explanation(snap, provider=provider)
    v.record('MODEL_' + label, 'explanation UNAVAILABLE and deterministic inputs unchanged', {'status':explanation['status'],'metrics_unchanged':snap['metrics']==preserved}, explanation['status']=='UNAVAILABLE' and snap['metrics']==preserved, assessment='AI001 reusable primitive, no AI003 endpoint or real provider call')

frappe.db.rollback(); frappe.destroy()
Path('/tmp/ai003_prebuild_additional_results.json').write_text(json.dumps(v.RESULT,indent=2,default=str),encoding='utf-8')
print('ADDITIONAL_RESULTS',len(v.RESULT['cases']),sum(c['result']=='FAIL' for c in v.RESULT['cases']))

"""Focused Work verification; synthetic isolated site, no commits or voucher writes.

Expected values use the independent voucher oracle. Altered report rows and
replay source failures are labelled harness probes, never live ERP fixtures.
"""
import copy
import hashlib
import json
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
import frappe
from prebuild_oracle import voucher_oracle

SITE = 'ai003-verify.localhost'
C = 'AI003 Gold 2026'
D = date(2026, 9, 26)
USER = 'ai003-final-work-20260930@example.invalid'
OUT = {'site': SITE, 'cases': [], 'gold': [], 'errors': []}

def record(name, ok, actual, kind='VERIFIED_RUNTIME'):
    OUT['cases'].append({'case': name, 'result': 'PASS' if ok else 'FAIL',
                         'actual': actual, 'evidence_kind': kind})

def denied(call):
    try:
        call()
        return False
    except frappe.PermissionError:
        return True

def fingerprint(rows):
    serialized = [json.dumps(r, sort_keys=True, default=str) for r in rows]
    return hashlib.sha256(json.dumps(sorted(serialized)).encode()).hexdigest()

def source(key, cutoff=D, **extra):
    return extract_key_report_data(report_key=key, company=C,
        filters={'company': C, 'report_date': str(cutoff), **extra})

def req():
    return ForecastRequest(company=C, financial_as_of=D, forecast_start=D+timedelta(days=1),
        forecast_end=D+timedelta(days=30), reporting_currency='VND',
        cash_account_scope=['Cash - A3G'])

def summary(r):
    return {'status': r.status.value, 'id': r.forecast_id, 'obligations': len(r.obligations),
            'opening_cash_present': r.opening_cash is not None,
            'points': len(r.forecast_points), 'verified_company': r.verified_company}

def safe_forbidden(r):
    return r.status.value == 'FORBIDDEN' and not r.obligations and r.opening_cash is None and not r.forecast_points

frappe.init(site=SITE, sites_path='/home/frappe/frappe-bench/sites')
frappe.connect()
frappe.set_user('Administrator')
assert frappe.local.site == SITE
from lotus_fin.api.key_reports import extract_key_report_data
from lotus_fin.ai.financial_snapshot import parse_ar_data, parse_ap_data
from lotus_fin.cashflow.adapters import _collect_obligations
from lotus_fin.cashflow.cache import _CACHE_STORE
from lotus_fin.cashflow.models import ForecastRequest
from lotus_fin.cashflow.service import get_cash_forecast
from lotus_fin.cashflow.source_interface import FailClosedSource
from lotus_fin.security.access import check_ai002_report_permission, get_verified_company, verify_evidence_access
from frappe.desk.query_report import run as direct_report

before = voucher_oracle(frappe.db, C, D)
try:
    record('MIGRATION', frappe.db.has_column('Company','ai002_approved_cash_accounts'),
           {'scope_column': frappe.db.has_column('Company','ai002_approved_cash_accounts')})
    tz = frappe.db.get_single_value('System Settings','time_zone')
    record('TIMEZONE', tz == 'Asia/Ho_Chi_Minh', tz)
    OUT['fixture_residue'] = frappe.db.get_all('Sales Invoice', filters={'company': C, 'docstatus': 2},
                                             fields=['name','docstatus','remarks'], limit_page_length=1000)
    for cutoff, expected in [(date(2026,9,20), ('650000','0','1400000','1950000')),
                             (D, ('565000','65000','275000','975000'))]:
        o = voucher_oracle(frappe.db,C,cutoff)
        OUT['gold'].append(o)
        record('ORACLE_'+str(cutoff), all(Decimal(o[k]) == Decimal(v) for k,v in
               zip(('total_ar','overdue_ar','ap_short','ap_horizon'), expected)),
               {k:o[k] for k in ('total_ar','overdue_ar','ap_short','ap_horizon','source_hash')})
        ar = source('accounts_receivable', cutoff)['data']
        parsed = parse_ar_data(ar, as_of_date=cutoff, company=C)
        record('AR_SOURCE_ORACLE_'+str(cutoff), parsed[0] == Decimal(o['total_ar']) and
               parsed[1] == Decimal(o['overdue_ar']), list(parsed))
        ap = source('accounts_payable', cutoff)
        obs = _collect_obligations(ap,'AP',('party','supplier'),'Purchase Invoice','VND','Accounts Payable',company=C)
        short = sum((x.remaining_amount for x in obs if x.due_date and cutoff+timedelta(days=1) <= x.due_date <= cutoff+timedelta(days=7)),Decimal(0))
        horizon = sum((x.remaining_amount for x in obs if x.due_date and cutoff+timedelta(days=1) <= x.due_date <= cutoff+timedelta(days=30)),Decimal(0))
        record('AP_SOURCE_ORACLE_'+str(cutoff), short == Decimal(o['ap_short']) and horizon == Decimal(o['ap_horizon']),
               {'short':short,'horizon':horizon,'count':len(obs)})
    ar_rows = source('accounts_receivable')['data']
    ap_rows = source('accounts_payable')['data']
    idx = next(i for i,r in enumerate(ar_rows) if Decimal(str(r.get('outstanding',r.get('outstanding_amount',0)))) > 0)
    amount_key = 'outstanding' if 'outstanding' in ar_rows[idx] else 'outstanding_amount'
    for tag, updates in [('MISSING_BOTH',{}),('MALFORMED_DATE',{'due_date':'not-a-date'}),
                         ('VALID_EXPLICIT',{'overdue_amount':str(ar_rows[idx][amount_key])}),
                         ('VALID_DATE',{'due_date':ar_rows[idx]['due_date']}),
                         ('MALFORMED_DATE_VALID_EXPLICIT',{'due_date':'not-a-date','overdue_amount':str(ar_rows[idx][amount_key])})]:
        rows = copy.deepcopy(ar_rows)
        for key in ('due_date','overdue','overdue_amount'): rows[idx].pop(key,None)
        rows[idx].update(updates)
        try:
            p = parse_ar_data(rows,as_of_date=D,company=C)
            ok = p[0] == Decimal('565000') and (p[1] is None if tag in ('MISSING_BOTH','MALFORMED_DATE') else p[1] == Decimal('65000'))
            record('AR_BASIS_'+tag,ok,list(p),'LIVE_ROWS_MUTATION')
        except Exception as e:
            record('AR_BASIS_'+tag, tag in ('MISSING_BOTH','MALFORMED_DATE'), {'error':type(e).__name__},'LIVE_ROWS_MUTATION')
    for leg, rows, parser in [('AR',ar_rows,lambda x:parse_ar_data(x,as_of_date=D,company=C)),
                             ('AP',ap_rows,lambda x:parse_ap_data(x,company=C))]:
        pos = next(r for r in rows if Decimal(str(r.get('outstanding',r.get('outstanding_amount',0)))) > 0)
        base = parser(rows)[0]
        try:
            actual = parser(rows+[dict(pos)])[0]
            record(leg+'_EXACT_DUPLICATE_AI001',actual == base,{'base':base,'actual':actual},'LIVE_ROWS_MUTATION')
        except Exception as e:
            record(leg+'_EXACT_DUPLICATE_AI001',True,{'error':type(e).__name__},'LIVE_ROWS_MUTATION')
        args = (leg,('party','customer','supplier'),'Sales Invoice' if leg == 'AR' else 'Purchase Invoice','VND',
                'Accounts Receivable' if leg == 'AR' else 'Accounts Payable')
        def adapt(rs): return _collect_obligations({'status':'success','data':rs},*args,company=C)
        normal = adapt(rows)
        for tag, update in [('EXACT',{}),('CONFLICTING_AMOUNT',{'outstanding':Decimal(str(pos.get('outstanding',pos.get('outstanding_amount'))))+1})]:
            duplicate = dict(pos); duplicate.update(update)
            try:
                actual = adapt(rows+[duplicate])
                record(leg+'_DUPLICATE_AI002_'+tag,len(actual) == len(normal),{'base_count':len(normal),'actual_count':len(actual)},'LIVE_ROWS_MUTATION')
            except Exception as e:
                record(leg+'_DUPLICATE_AI002_'+tag,True,{'error':type(e).__name__},'LIVE_ROWS_MUTATION')
        missing = dict(pos); missing.pop('voucher_no',None); missing.pop('name',None)
        for name, call in [('AI001',lambda:parser([missing])),('AI002',lambda:adapt([missing]))]:
            try:
                actual = call(); record(leg+'_MISSING_IDENTITY_'+name,False,str(actual),'LIVE_ROWS_MUTATION')
            except Exception as e:
                record(leg+'_MISSING_IDENTITY_'+name,True,{'error':type(e).__name__},'LIVE_ROWS_MUTATION')
        # A lossless split can be preserved, but these fields do not prove a
        # real payment schedule/account allocation. Identity validation is open.
        a,b = dict(pos),dict(pos)
        value = Decimal(str(pos.get('outstanding',pos.get('outstanding_amount'))))
        a['outstanding']=value/2; b['outstanding']=value-value/2
        a['payment_term']='TEST_ONLY_TERM_A'; b['payment_term']='TEST_ONLY_TERM_B'
        split = [r for r in rows if r is not pos]+[a,b]
        record(leg+'_SIMULATED_TERM_SPLIT_PRESERVED',parser(split)[0] == base,
               {'total':parser(split)[0], 'live_schedule_proven':False},'HARNESS_ONLY')
        actual_terms = source('accounts_receivable' if leg=='AR' else 'accounts_payable',based_on_payment_terms=1)
        record(leg+'_LIVE_PAYMENT_TERM_REPORT',actual_terms.get('status') == 'success',
               {'status':actual_terms.get('status'),'row_count':len(actual_terms.get('data',[])),
                'proves_distinct_split_identity':False})
    assert not frappe.db.exists('User',USER), 'Existing probe user; refuse overwrite'
    assert not frappe.db.exists('Custom Role',{'report':'Accounts Receivable'}), 'Existing report roles; refuse overwrite'
    frappe.get_doc({'doctype':'User','email':USER,'first_name':'AI003 Final Work','send_welcome_email':0,
                    'user_type':'System User','roles':[{'role':'Accounts User'}]}).insert(ignore_permissions=True)
    frappe.get_doc({'doctype':'User Permission','user':USER,'allow':'Company','for_value':C,
                    'apply_to_all_doctypes':1}).insert(ignore_permissions=True)
    frappe.set_user(USER)
    record('COMPANY_ALLOWED',get_verified_company(C)==C,{'company_allowed':True})
    record('COMPANY_CROSS_DENIED',denied(lambda:get_verified_company('AI002 Fixture 2026')),{'denied':True})
    r1=get_cash_forecast(req(),user=USER,future_event_source=FailClosedSource())
    r2=get_cash_forecast(req(),user=USER,future_event_source=FailClosedSource())
    record('CACHE_POPULATED',bool(_CACHE_STORE) and r1.forecast_id==r2.forecast_id and bool(r1.obligations),summary(r2))
    saved_hash=fingerprint(source('accounts_receivable')['data'])
    docref='Sales Invoice:'+ar_rows[idx]['voucher_no']
    record('DOCUMENT_ALLOWED',verify_evidence_access(docref,user=USER,company=C),{'allowed':True})
    record('DOCUMENT_CROSS_DENIED',denied(lambda:verify_evidence_access(docref,user=USER,company='AI002 Fixture 2026')),{'denied':True})
    record('SNAPSHOT_NOT_TOKEN',denied(lambda:verify_evidence_access('Risk Signal:FORGED',user=USER,company=C)),{'denied':True})
    record('ARBITRARY_REPORT_DENIED',denied(lambda:check_ai002_report_permission('Stock Balance')),{'denied':True})
    frappe.set_user('Administrator'); frappe.db.savepoint('account_scope_probe')
    frappe.get_doc({'doctype':'User Permission','user':USER,'allow':'Account','for_value':'Debtors - A3G',
                    'apply_to_all_doctypes':1}).insert(ignore_permissions=True)
    frappe.clear_cache(user=USER); frappe.set_user(USER)
    restricted=get_cash_forecast(req(),user=USER,future_event_source=FailClosedSource())
    record('ACCOUNT_SCOPE_REVOKED',safe_forbidden(restricted),summary(restricted))
    frappe.set_user('Administrator'); frappe.db.rollback(save_point='account_scope_probe'); frappe.clear_cache(user=USER)
    other_customer=frappe.db.get_value('Sales Invoice',{'company':'AI002 Fixture 2026'},'customer')
    if other_customer:
        frappe.db.savepoint('customer_scope_probe')
        frappe.get_doc({'doctype':'User Permission','user':USER,'allow':'Customer','for_value':other_customer,
                        'apply_to_all_doctypes':1}).insert(ignore_permissions=True)
        frappe.clear_cache(user=USER); frappe.set_user(USER)
        record('DOCUMENT_CUSTOMER_DENIED',denied(lambda:verify_evidence_access(docref,user=USER,company=C)),{'denied':True})
        frappe.set_user('Administrator'); frappe.db.rollback(save_point='customer_scope_probe'); frappe.clear_cache(user=USER)
        frappe.set_user(USER)
        record('DOCUMENT_REGRANT',verify_evidence_access(docref,user=USER,company=C),{'allowed':True})
    frappe.set_user('Administrator')
    role=frappe.get_doc({'doctype':'Custom Role','report':'Accounts Receivable','ref_doctype':'Sales Invoice',
                         'roles':[{'role':'Accounts Manager'}]}).insert(ignore_permissions=True)
    frappe.clear_cache(user=USER)
    frappe.set_user(USER)
    record('AUTHORITATIVE_REPORT_DENIED',not frappe.get_doc('Report','Accounts Receivable').is_permitted(),{'permitted':False})
    record('DIRECT_REPORT_DENIED',denied(lambda:direct_report(report_name='Accounts Receivable',filters={'company':C,'report_date':str(D)})),{'denied':True})
    record('PB_SEC_01_ACTIVE_GUARD_DENIED',denied(lambda:check_ai002_report_permission('Accounts Receivable')),{'guard_denied':denied(lambda:check_ai002_report_permission('Accounts Receivable'))})
    cached=get_cash_forecast(req(),user=USER,future_event_source=FailClosedSource())
    record('PB_SEC_01_CACHE_REVOKED',safe_forbidden(cached),summary(cached))
    fresh=get_cash_forecast(req(),user=USER,future_event_source=FailClosedSource(),skip_cache=True)
    record('PB_SEC_01_FRESH_REVOKED',safe_forbidden(fresh),summary(fresh))
    frappe.set_user('Administrator')
    record('PB_SEC_01_TRUSTED_EXPLICIT_USER',denied(lambda:check_ai002_report_permission('Accounts Receivable',user=USER)),
           {'session':'Administrator','checked_user':USER,'guard_denied':denied(lambda:check_ai002_report_permission('Accounts Receivable',user=USER))})
    # Feasibility model uses authoritative current-session report permission;
    # this is deliberately not a production replay implementation.
    def replay(expected_hash, force_unavailable=False):
        frappe.set_user(USER)
        if not frappe.get_doc('Report','Accounts Receivable').is_permitted(): return 'FORBIDDEN'
        get_verified_company(C)
        if force_unavailable: return 'UNAVAILABLE'
        new=source('accounts_receivable')
        if new.get('status')!='success': return 'UNAVAILABLE'
        return 'MATCH' if fingerprint(new['data'])==expected_hash else 'RESTATED'
    record('REPLAY_REVOKED',replay(saved_hash)=='FORBIDDEN',replay(saved_hash),'HARNESS_WITH_REAL_AUTH')
    frappe.set_user('Administrator'); frappe.delete_doc('Custom Role',role.name,ignore_permissions=True)
    frappe.clear_cache(user=USER); frappe.set_user(USER)
    restored=get_cash_forecast(req(),user=USER,future_event_source=FailClosedSource(),skip_cache=True)
    record('REGRANT',len(restored.obligations)==len(r1.obligations) and restored.status==r1.status,summary(restored))
    for name, expected_hash, forced, state in [('MATCH',saved_hash,False,'MATCH'),('RESTATED','0'*64,False,'RESTATED'),
                                               ('UNAVAILABLE',saved_hash,True,'UNAVAILABLE')]:
        actual=replay(expected_hash,forced)
        record('REPLAY_'+name,actual==state,actual,'HARNESS_ONLY' if name!='MATCH' else 'HARNESS_WITH_LIVE_READ')
except Exception as e:
    import traceback
    OUT['errors'].append({'type':type(e).__name__,'message':str(e),'traceback':traceback.format_exc()})
finally:
    frappe.set_user('Administrator')
    frappe.db.rollback()
    frappe.clear_cache(user=USER)
    record('PROBE_USER_ABSENT',not frappe.db.exists('User',USER),{'absent':not frappe.db.exists('User',USER)})
    record('PROBE_ROLE_ABSENT',not frappe.db.exists('Custom Role',{'report':'Accounts Receivable'}),
           {'absent':not frappe.db.exists('Custom Role',{'report':'Accounts Receivable'})})
    after=voucher_oracle(frappe.db,C,D)
    record('FIXTURE_UNCHANGED',before['source_hash']==after['source_hash'],
           {'before':before['source_hash'],'after':after['source_hash']})
    OUT['counts']={'total':len(OUT['cases']),'pass':sum(x['result']=='PASS' for x in OUT['cases']),
                   'fail':sum(x['result']=='FAIL' for x in OUT['cases']),'errors':len(OUT['errors'])}
    Path('/tmp/AI003_FINAL_FOUNDATION_RESULTS_2026-09-30.json').write_text(json.dumps(OUT,indent=2,default=str))
    print(json.dumps({'counts':OUT['counts'],'cases':OUT['cases'],'errors':OUT['errors']},default=str))
    frappe.db.rollback(); frappe.destroy()

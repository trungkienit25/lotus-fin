import json, pathlib, uuid
from datetime import date
from lotus_fin.domain.model.overdue_invoice_observation import AuthorizedOutstandingInvoiceObservation as O
from lotus_fin.domain.policy.past_final_due_evaluator import PastFinalDueEvaluator as E
base=dict(invoice_id='GOLD',tenant_id='T',company_id='C',source_system='Independent',document_version='1',lifecycle_status='SUBMITTED',is_return=False,is_credit_note=False,is_write_off=False,posting_date=date(2026,9,1),final_due_date=date(2026,10,12),party_account_currency='VND',invoice_currency='VND',outstanding_balance='0.000001',currency_precision=6,observed_at_utc='2026-10-12T18:00:00Z',site_timezone='Asia/Ho_Chi_Minh',source_completeness='COMPLETE',authorized_scope='T:C')
cases=[('strict-positive-small-decimal',{},'ELIGIBLE'),('due-today',{'final_due_date':date(2026,10,13)},'NOT_ELIGIBLE'),('due-future',{'final_due_date':date(2026,10,14)},'NOT_ELIGIBLE'),('zero',{'outstanding_balance':'0'},'NOT_ELIGIBLE'),('negative',{'outstanding_balance':'-0.000001'},'NOT_ELIGIBLE'),('draft',{'lifecycle_status':'DRAFT'},'NOT_ELIGIBLE'),('cancelled',{'lifecycle_status':'CANCELLED'},'NOT_ELIGIBLE'),('return',{'is_return':True},'NOT_ELIGIBLE'),('credit',{'is_credit_note':True},'NOT_ELIGIBLE'),('writeoff',{'is_write_off':True},'NOT_ELIGIBLE'),('future-posting',{'posting_date':date(2026,10,14)},'UNQUALIFIED'),('partial',{'source_completeness':'PARTIAL'},'UNQUALIFIED'),('tenant',{'tenant_id':'OTHER'},'NOT_ELIGIBLE'),('company',{'company_id':'OTHER'},'NOT_ELIGIBLE'),('nan',{'outstanding_balance':'NaN'},'INVALID'),('infinity',{'outstanding_balance':'Infinity'},'INVALID'),('float',{'outstanding_balance':0.1},'INVALID'),('naive-observation-time',{'observed_at_utc':'2026-10-12T18:00:00'},'INVALID'),('invalid-currency',{'party_account_currency':'???'},'INVALID'),('missing-source-completeness',{'source_completeness':None},'INVALID')]
results=[]
for name,changes,expected in cases:
    row=base|changes
    if name=='missing-source-completeness':del row['source_completeness']
    try: o=O(**row); actual=E.evaluate(o,'T','C').decision.value
    except Exception:actual='INVALID'
    results.append(dict(case=name,expected=expected,actual=actual,result='PASS' if actual==expected else 'FAIL'))
o=O(**(base|{'party_account_currency':'USD'}))
results.append(dict(case='currency-filter',expected='NOT_ELIGIBLE',actual=E.evaluate(o,'T','C',expected_currency='VND').decision.value))
results[-1]['result']='PASS' if results[-1]['actual']==results[-1]['expected'] else 'FAIL'
from lotus_fin.application.service.search_overdue_invoices import SearchOverdueInvoicesService
from lotus_fin.domain.model.authorized_read_context import AuthorizedReadContext
from lotus_fin.domain.schema.action_outcome import ActionStatus,ActionReasonCode
from datetime import datetime,timedelta,timezone
context=AuthorizedReadContext(actor_id='alice',auth_session_binding='S',site_id='T',product_id='lotus-fin',connection_id='qa',connection_version='1',company_id='C',capability='invoice.search',context_version='1',observed_at_utc=base['observed_at_utc'],timezone=base['site_timezone'],deadline_at_utc=(datetime.now(timezone.utc)+timedelta(minutes=5)).isoformat(),correlation_id=str(uuid.uuid4()),request_id=str(uuid.uuid4()),adapter_mode='DEMO_ISOLATED')
class MissingEvidencePort:
    def scan_invoice_observations(self,**kw):return [O(**base)],None,False,ActionStatus.OK,ActionReasonCode.RESULTS_FOUND,None
data,source,status,reason=SearchOverdueInvoicesService(MissingEvidencePort(),provider_mode='DEMO').execute(context)
results.append(dict(case='missing-source-evidence',expected='fail-closed',actual=status.value,returned_rows=len(data.items) if data else 0,coverage_complete=data.coverage.complete if data else None,result='FAIL' if data and data.items and data.coverage.complete else 'PASS'))
pathlib.Path(__file__).with_name('V1_INDEPENDENT.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
print(json.dumps({'checks':len(results),'failures':[r for r in results if r.get('result')=='FAIL']}))

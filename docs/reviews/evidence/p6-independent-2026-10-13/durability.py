import json,os,pathlib,sqlite3,subprocess,sys,tempfile
from lotus_fin.application.service.copilot_integration import CopilotIntegrationService
from lotus_fin.infrastructure.persistence.copilot_demo_store import CopilotDemoStore
from lotus_fin.application.service.l4_mutation_service import L4MutationService
from lotus_fin.domain.model.user_context import UserPrincipal
out=pathlib.Path(__file__).parent
def call(path,action,payload):
    return CopilotIntegrationService(CopilotDemoStore(path)).dispatch('alice',['Accounts User'],'S','site',True,{'profile':'DEMO','action':action,'payload':payload})[1]
def propose(path):return call(path,'l4_propose',{'request_id':'qa','action_id':'lotus.task.create','arguments':{'title':'Fictional','description':'QA only','due_date':'2026-10-20'}})['proposal']
def confirm(p):return {'request_id':'qa','proposal_id':p['proposal_id'],'confirmation_challenge':p['confirmation_challenge']}
if len(sys.argv)>1:
    path,mode,p=sys.argv[1],sys.argv[2],json.loads(sys.argv[3])
    if mode=='crash':
        with CopilotDemoStore(path).transaction('site:alice:S:DEMO','crash') as (ledger,adapter):
            L4MutationService(ledger,adapter).confirm_action(UserPrincipal(user_id='alice',roles=['Accounts User'],company='Lotus Demo Corp'),'S',p['proposal_id'],p['confirmation_challenge'])
            os._exit(79)
    if mode=='unknown':
        with CopilotDemoStore(path).transaction('site:alice:S:DEMO','timeout') as (ledger,adapter):
            adapter.set_simulate_timeout(True)
            state,op,_=L4MutationService(ledger,adapter).confirm_action(UserPrincipal(user_id='alice',roles=['Accounts User'],company='Lotus Demo Corp'),'S',p['proposal_id'],p['confirmation_challenge'])
        print(op.operation_id)
    sys.exit()
rows=[]
with tempfile.TemporaryDirectory(prefix='lotus-p6-independent-') as tmp:
    path=str(pathlib.Path(tmp)/'simulation.sqlite3');p=propose(path)
    proc=subprocess.run([sys.executable,__file__,path,'crash',json.dumps(p)],capture_output=True,text=True)
    with sqlite3.connect(path) as db:
        data=json.loads(db.execute('select body from state').fetchone()[0]); audit=db.execute('select count(*) from audit').fetchone()[0]
    db.close()
    r=call(path,'l4_confirm',confirm(p));op=r['operation']
    rows.append({'case':'process-crash-before-atomic-commit','result':'PASS' if proc.returncode==79 and not data['operations'] and not data['records'] and audit==1 and op['execution_attempts']==1 else 'FAIL','crash_exit':proc.returncode,'surviving_operations':len(data['operations']),'surviving_records':len(data['records'])})
    p=propose(path);proc=subprocess.run([sys.executable,__file__,path,'unknown',json.dumps(p)],capture_output=True,text=True,check=True);oid=proc.stdout.strip()
    before=call(path,'l4_status',{'request_id':'qa','operation_id':oid});replay=call(path,'l4_confirm',confirm(p));after=call(path,'l4_reconcile',{'request_id':'qa','operation_id':oid})
    rows.append({'case':'unknown-outcome-survives-process-exit-and-reconciles','result':'PASS' if before['operation']['state']=='UNKNOWN_OUTCOME' and replay['state']=='UNKNOWN_OUTCOME' and after['state']=='SUCCEEDED' and after['operation']['execution_attempts']==1 else 'FAIL','before':before['operation']['state'],'replay':replay['state'],'after':after['state'],'attempts':after['operation']['execution_attempts']})
    with sqlite3.connect(path) as db:
        db.execute("CREATE TRIGGER reject_audit BEFORE INSERT ON audit BEGIN SELECT RAISE(ABORT,'audit unavailable'); END")
    db.close()
    try:propose(path);ok=False
    except sqlite3.IntegrityError:ok=True
    rows.append({'case':'audit-failure-pre-admission','result':'PASS' if ok else 'FAIL'})
(out/'DURABILITY_INDEPENDENT.json').write_text(json.dumps(rows,indent=2),encoding='utf-8');print(json.dumps(rows))

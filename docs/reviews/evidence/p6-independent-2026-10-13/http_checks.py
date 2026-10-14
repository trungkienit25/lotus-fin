import concurrent.futures, json, pathlib, requests, uuid
BASE='http://127.0.0.1:8114'
EP='/api/method/lotus_fin.api.copilot_integration_api.dispatch'
ROOT=pathlib.Path(__file__).resolve().parents[4]
cred=json.loads((ROOT/'.runtime/lotus-core-p6-01a1358e/demo-credentials.json').read_text())
checks=[]
def check(name,ok,**data):
    checks.append(dict(case=name,result='PASS' if ok else 'FAIL',**data))
def login(user):
    s=requests.Session();r=s.post(BASE+'/api/method/login',json={'usr':user,'pwd':cred['pwd']},timeout=20)
    check('login:'+user,r.status_code==200,http=r.status_code)
    r=s.get(BASE+'/copilot/session',timeout=20);check('bootstrap:'+user,r.status_code==200 and 'no-store' in r.headers.get('Cache-Control',''),http=r.status_code)
    return s,r.json()['csrf_token']
def post(s,csrf,action,payload=None,profile='DEMO',**kw):
    return s.post(BASE+EP,json={'profile':profile,'action':action,'payload':payload or {}},headers={'X-Frappe-CSRF-Token':csrf},timeout=20,**kw)
a,csrf=login(cred['usr']);b,bc=login('p6-bob@example.invalid')
guest=requests.post(BASE+EP,json={'profile':'DEMO','action':'past_final_due'},timeout=20)
check('guest',guest.status_code in (401,403),http=guest.status_code)
r=post(a,'invalid','past_final_due');check('csrf-invalid',r.status_code==400 and 'CSRF' in r.text,http=r.status_code)
r=a.post(BASE+EP,json={'profile':'DEMO','action':'past_final_due'},timeout=20);check('csrf-missing',r.status_code==400,http=r.status_code)
r=post(a,csrf,'past_final_due');d=r.json()['message']['data']
check('V1-http-independent-gold',r.status_code==200 and [(x['invoice_id'],x['overdue_days'],x['current_outstanding_decimal'],x['party_account_currency']) for x in d['items']]==[('DEMO-INV-001',12,'15000000.00','VND'),('DEMO-INV-002',8,'2850000.50','VND')],http=r.status_code,rows=d['items'])
check('integration-no-store','no-store' in r.headers.get('Cache-Control',''),cache=r.headers.get('Cache-Control'))
for action in ['past_final_due','l4_propose','l4_confirm','l5_review']:
    r=a.post(BASE+EP+'?profile=DEMO',json={'profile':'CORE','action':action},headers={'X-Frappe-CSRF-Token':csrf,'X-Lotus-Profile':'DEMO'},timeout=20)
    check('CORE-forged-header-query:'+action,r.status_code==503 and 'DEMO-INV' not in r.text,http=r.status_code)
r=post(a,csrf,'l4_propose',{'request_id':str(uuid.uuid4()),'action_id':'lotus.task.create','arguments':{'title':'Independent acceptance fictional task','description':'SIMULATION ONLY','due_date':'2026-10-20'}})
p=r.json()['message'].get('proposal');check('L4-propose',r.status_code==200 and p and p['simulated'],http=r.status_code)
payload={'request_id':str(uuid.uuid4()),'proposal_id':p['proposal_id'],'confirmation_challenge':p['confirmation_challenge']}
r=post(b,bc,'l4_confirm',payload);check('L4-cross-actor-denied',not r.json()['message']['success'],http=r.status_code)
a2,c2=login(cred['usr']);r=post(a2,c2,'l4_confirm',payload);check('L4-cross-session-denied',not r.json()['message']['success'],http=r.status_code)
r=post(a,csrf,'l4_confirm',dict(payload,confirmation_challenge='forged'));check('L4-forged-challenge',not r.json()['message']['success'],http=r.status_code)
def confirm(_):
    s=requests.Session();s.cookies.update(a.cookies);return post(s,csrf,'l4_confirm',payload).json()['message']
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex: results=list(ex.map(confirm,range(4)))
ops=[x.get('operation') for x in results]
check('L4-concurrent-confirm-single-receipt',all(x and x['execution_attempts']==1 for x in ops) and len({x['operation_id'] for x in ops if x})==1,states=[x.get('state') for x in results])
op=ops[0]['operation_id'];r=post(a,csrf,'l4_status',{'request_id':str(uuid.uuid4()),'operation_id':op});check('L4-durable-new-request-status',r.json()['message']['operation']['operation_id']==op,http=r.status_code)
for name in ['l5.doc.submit_sales_invoice.v1','l5.doc.cancel_sales_invoice.v1','l5.comm.send_statement_email.v1','l5.pay.execute_wire_transfer.v1','l5.sched.autonomous_reconciliation.v1']:
    r=a.post(BASE+EP,json={'profile':'DEMO','action':'l5_review','action_name':name},headers={'X-Frappe-CSRF-Token':csrf},timeout=20);m=r.json()['message'];check('L5-review:'+name,m['status']=='DENIED' and 'review_challenge' not in m,reason=m.get('reason_code'))
for action in ['l5_execute','send','submit','cancel','payment','scheduler']:
    r=post(a,csrf,action);check('unapproved-execute:'+action,r.status_code==400,http=r.status_code)
for field in ['actor','session','company','adapter','simulated']:
    r=a.post(BASE+EP,json={'profile':'DEMO','action':'l4_propose',field:'forged'},headers={'X-Frappe-CSRF-Token':csrf},timeout=20);check('forged-authority:'+field,r.status_code==400,http=r.status_code)
old=requests.Session();old.cookies.update(a.cookies)
r=a.post(BASE+'/api/method/logout',headers={'X-Frappe-CSRF-Token':csrf},timeout=20)
r=old.get(BASE+'/copilot/session',timeout=20);check('logged-out-cookie-bootstrap',r.status_code in (401,403),http=r.status_code)
r=post(old,csrf,'l4_confirm',payload);check('logged-out-cookie-operation',r.status_code in (401,403),http=r.status_code)
(pathlib.Path(__file__).parent/'HTTP_INDEPENDENT.json').write_text(json.dumps(checks,indent=2),encoding='utf-8')
print(json.dumps({'checks':len(checks),'failures':[x for x in checks if x['result']=='FAIL']}))

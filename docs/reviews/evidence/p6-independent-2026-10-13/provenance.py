import hashlib,json,pathlib,subprocess,requests
ROOT=pathlib.Path(__file__).resolve().parents[4];OUT=pathlib.Path(__file__).parent
DOCKER='C:/Users/longm/AppData/Local/Programs/DockerDesktop/resources/bin/docker.exe'
names=['lotus-core-p6-01a1358e-'+x+'-1' for x in ['backend','frontend','queue-long','queue-short','scheduler','websocket']]
info=json.loads(subprocess.check_output([DOCKER,'inspect',*names],text=True))
code="""import pathlib,hashlib,json,importlib.util
p=pathlib.Path('/home/frappe/frappe-bench/apps/lotus_fin/lotus_fin')
data={str(f.relative_to(p)):hashlib.sha256(f.read_bytes()).hexdigest() for f in p.rglob('*') if f.is_file() and f.suffix in ('.py','.json') and '__pycache__' not in str(f)}
assets=pathlib.Path('/home/frappe/frappe-bench/apps/lotus_fin/lotus_fin/public/core')
ui={str(f.relative_to(assets)):hashlib.sha256(f.read_bytes()).hexdigest() for f in assets.rglob('*') if f.is_file()}
print(json.dumps({'backend':data,'ui':ui,'erpnext_importable':importlib.util.find_spec('erpnext') is not None}))
"""
actual=json.loads(subprocess.check_output([DOCKER,'exec',names[0],'env/bin/python','-c',code],text=True))
local=ROOT/'lotus_fin/lotus_fin'
diff=[]
for path,h in actual['backend'].items():
    f=local/path
    if not f.is_file() or hashlib.sha256(f.read_bytes()).hexdigest()!=h:diff.append(path)
missing=[f.relative_to(local).as_posix() for f in local.rglob('*') if f.is_file() and f.suffix in ('.py','.json') and '__pycache__' not in str(f) and f.relative_to(local).as_posix() not in actual['backend']]
ui_diff=[]
for path,h in actual['ui'].items():
    if path.endswith(('.js','.css')):
        f=ROOT/'frontend/dist'/path
        if not f.is_file() or hashlib.sha256(f.read_bytes()).hexdigest()!=h:ui_diff.append(path)
result={'containers':[{'name':x['Name'],'image':x['Image'],'source_bind_mounts':[m['Destination'] for m in x['Mounts'] if m['Type']=='bind']} for x in info], 'backend_count':len(actual['backend']),'backend_drift':diff,'local_not_packaged':missing,'ui_drift':ui_diff,'ui':actual['ui'],'erpnext_importable':actual['erpnext_importable']}
result['http_assets']=[]
for path,h in actual['ui'].items():
    if path.endswith(('.js','.css')):
        r=requests.get('http://127.0.0.1:8114/assets/lotus_fin/core/'+path,timeout=20)
        result['http_assets'].append({'path':path,'http':r.status_code,'sha256':hashlib.sha256(r.content).hexdigest(),'matches_image':r.status_code==200 and hashlib.sha256(r.content).hexdigest()==h})
(OUT/'PROVENANCE.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k not in ('ui','containers')}))

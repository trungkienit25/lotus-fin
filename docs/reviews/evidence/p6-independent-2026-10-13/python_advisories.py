import concurrent.futures,json,pathlib,requests
out=pathlib.Path(__file__).parent
packages=json.loads((out/'runtime-packages.json').read_text())
def get(p):
    if p['name'] in ['frappe','lotus_fin']:return {'name':p['name'],'version':p['version'],'qualification':'local/framework source excluded from PyPI'}
    try:
        r=requests.get('https://pypi.org/pypi/'+p['name']+'/'+p['version']+'/json',timeout=15)
        if r.status_code!=200:return {'name':p['name'],'version':p['version'],'http':r.status_code}
        d=r.json();return {'name':p['name'],'version':p['version'],'vulnerabilities':d.get('vulnerabilities',[])}
    except Exception as e:return {'name':p['name'],'version':p['version'],'error':type(e).__name__}
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex: rows=list(ex.map(get,packages))
(out/'PYTHON_ADVISORIES.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
print(json.dumps({'queried':len(rows),'flagged':[{'name':p['name'],'version':p['version'],'ids':[v['id'] for v in p.get('vulnerabilities',[])]} for p in rows if p.get('vulnerabilities')],'unverified':[p for p in rows if p.get('http') or p.get('error') or p.get('qualification')]}))

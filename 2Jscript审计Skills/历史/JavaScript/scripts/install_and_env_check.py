#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, os, shutil, subprocess, sys
from pathlib import Path

PY = sys.executable
def run(cmd, timeout=20):
    try:
        p=subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
        return {'cmd':cmd,'ok':p.returncode==0,'returncode':p.returncode,'stdout':p.stdout[-2000:],'stderr':p.stderr[-2000:]}
    except Exception as e:
        return {'cmd':cmd,'ok':False,'error':str(e)}

def node_module_status(root: Path, mod: str):
    node=shutil.which('node')
    if not node: return {'name':mod,'ok':False,'reason':'node not found'}
    code=f"try{{require.resolve('{mod}'); console.log('ok')}}catch(e){{console.error(e.message); process.exit(2)}}"
    # Use CommonJS evaluation even though package type is module.
    r=run([node,'-e',code])
    return {'name':mod,'ok':r['ok'],'detail':r}

def main():
    ap=argparse.ArgumentParser(description='One-click environment readiness check for JS audit skills. It installs nothing; installers call this before/after npm install.')
    ap.add_argument('--root', default='.')
    ap.add_argument('--out', default='reports/env-check')
    args=ap.parse_args(); root=Path(args.root).resolve(); out=Path(args.out).resolve(); out.mkdir(parents=True, exist_ok=True)
    checks=[]
    executable_checks=[('python-current', PY),('python', 'python'),('node','node'),('npm','npm'),('npx','npx'),('git','git')]
    for name, exe in executable_checks:
        path=exe if Path(exe).exists() else shutil.which(exe)
        checks.append({'kind':'binary','name':name,'ok':bool(path),'path':str(path) if path else None})
    node=shutil.which('node')
    if node:
        checks.append({'kind':'version','name':'node','result':run([node,'--version'])})
    py=sys.executable
    checks.append({'kind':'version','name':'python','result':run([py,'--version'])})
    for mod in ['@babel/parser','@babel/traverse','typescript','playwright','source-map']:
        checks.append({'kind':'node_module', **node_module_status(root, mod)})
    npx=shutil.which('npx')
    if npx:
        checks.append({'kind':'playwright','name':'playwright-version','result':run([npx,'playwright','--version'])})
    dirs=['reports','reports/js-top-tier','reports/env-check']
    for d in dirs:
        p=root/d; p.mkdir(parents=True, exist_ok=True)
        ok=os.access(p, os.W_OK)
        checks.append({'kind':'writable_dir','name':d,'ok':ok,'path':str(p)})
    # script backend smoke tests use existing fixture if present
    fixture=root/'fixtures/js-hidden-param-samples/frontend/app.js'
    backend_smoke=[]
    if fixture.exists() and node:
        for b in ['scripts/backends/js/babel_extract.mjs','scripts/backends/js/typescript_extract.mjs']:
            bp=root/b
            r=run([node,str(bp),str(fixture)]) if bp.exists() else {'ok':False,'error':'missing'}
            backend_smoke.append({'backend':b,'ok':r.get('ok'), 'stdout_tail':r.get('stdout','')[-500:], 'stderr_tail':r.get('stderr','')[-500:], 'error':r.get('error')})
    checks.append({'kind':'ast_backend_smoke','name':'babel/typescript fixture parse','ok':all(x.get('ok') for x in backend_smoke) if backend_smoke else False,'items':backend_smoke})
    must=['node','npm','npx']
    binary_ok={c['name']:c['ok'] for c in checks if c.get('kind')=='binary'}
    modules_ok=all(c.get('ok') for c in checks if c.get('kind')=='node_module')
    ast_ok=all(x.get('ok') for x in backend_smoke) if backend_smoke else False
    ready=all(binary_ok.get(x) for x in must) and modules_ok and ast_ok
    result={'schema_version':'js-env-check/v1','status':'ready' if ready else 'not-ready','ready':ready,'root':str(root),'checks':checks,'blocking':[c for c in checks if c.get('ok') is False and c.get('kind') in {'binary','node_module','ast_backend_smoke'}],'note':'not-ready is expected before npm install/playwright install; package must not claim AST/browser runtime ready until this passes.'}
    (out/'js_env_check.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'ok':True,'ready':ready,'out':str(out/'js_env_check.json')}, ensure_ascii=False, indent=2))
    raise SystemExit(0 if ready else 2)
if __name__=='__main__': main()

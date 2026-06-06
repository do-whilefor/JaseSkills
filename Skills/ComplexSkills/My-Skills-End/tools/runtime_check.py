#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, os, shutil, socket, subprocess
from datetime import datetime, timezone
from importlib.util import find_spec

def cmd_status(cmd):
    exe = shutil.which(cmd)
    if not exe: return {'name': cmd, 'status': 'missing', 'path': None, 'detail': f'{cmd} not found'}
    try:
        cp = subprocess.run([exe, '--version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=5)
        detail = (cp.stdout or cp.stderr).splitlines()[0] if (cp.stdout or cp.stderr) else 'version command returned no output'
    except Exception as exc: detail = str(exc)
    return {'name': cmd, 'status': 'ready', 'path': exe, 'detail': detail}

def node_pkg(pkg):
    node = shutil.which('node')
    if not node: return {'name': pkg, 'status': 'missing', 'detail': 'node missing'}
    code = f"try{{require.resolve('{pkg}'); console.log('ready')}}catch(e){{console.log('missing')}}"
    cp = subprocess.run([node, '-e', code], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=5)
    return {'name': pkg, 'status': 'ready' if cp.stdout.strip() == 'ready' else 'missing', 'detail': (cp.stderr or '').strip()}

def port(host, p):
    s = socket.socket(); s.settimeout(0.4)
    try: s.connect((host,p)); return True
    except Exception: return False
    finally: s.close()

def playwright_status():
    pkg = find_spec('playwright') is not None
    out = {'name':'playwright','python_package':pkg,'browser_runtime_ready':False,'browser_launch_verified':False,'status':'missing' if not pkg else 'degraded','errors':[]}
    if not pkg: return out
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            b = p.chromium.launch(headless=True); b.close()
        out.update({'browser_runtime_ready':True,'browser_launch_verified':True,'status':'ready'})
    except Exception as exc: out['errors'].append(str(exc)[:1000])
    return out

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--out'); args = ap.parse_args()
    checks = [cmd_status(c) for c in ['python3','node','java','php','go','ruby','cargo','tree-sitter']]
    checks += [node_pkg(p) for p in ['typescript','@babel/parser']]
    checks.append({'name':'jsonschema_python_package','status':'ready' if find_spec('jsonschema') else 'missing','detail':''})
    checks.append({'name':'burp_proxy_127.0.0.1_8080','status':'degraded' if port('127.0.0.1',8080) else 'missing','detail':'port open is not proof of Burp project/API readiness'})
    checks.append(playwright_status())
    result={'schema_version':'runtime_readiness_v1','generated_at':datetime.now(timezone.utc).isoformat(),'read_only':True,'ready_count':sum(1 for c in checks if c.get('status')=='ready'),'total_checks':len(checks),'checks':checks,'policy':'Missing/degraded parser or browser runtime blocks promoted/full-dynamic claims.'}
    text=json.dumps(result,ensure_ascii=False,indent=2)
    if args.out:
        os.makedirs(os.path.dirname(args.out) or '.', exist_ok=True); open(args.out,'w',encoding='utf-8').write(text+'\n')
    print(text); return 0
if __name__=='__main__': raise SystemExit(main())

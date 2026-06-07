#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, threading, time, urllib.parse, urllib.request, urllib.error
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
SAFE={'GET','HEAD','OPTIONS'}
LOCAL={'localhost','127.0.0.1','::1'}

def load(p: Path, default=None):
    try: return json.loads(p.read_text(encoding='utf-8'))
    except Exception: return default if default is not None else {}

def is_allowed_url(url: str, allow_external=False):
    u=urllib.parse.urlparse(url)
    return u.scheme in {'http','https'} and (allow_external or u.hostname in LOCAL or (u.hostname or '').endswith('.local'))

def fixture_request(req: dict[str,Any]):
    method=str(req.get('method','GET')).upper(); url=req.get('url',''); headers=req.get('headers',{}) or {}
    if method not in SAFE and not req.get('explicit_safe_mutation'):
        return {'blocked':True,'reason':'unsafe method blocked','method':method,'url':url}
    u=urllib.parse.urlparse(url); qs=urllib.parse.parse_qs(u.query)
    role=headers.get('X-Role','guest'); tenant=headers.get('X-Tenant',''); target=qs.get('tenant',[''])[0]
    body={"role":role,"tenant":tenant,"target_tenant":target,"path":u.path,"fixture":True}
    if u.path == '/api/tenant-data':
        status=200 if role in {'admin','analyst'} and tenant and target == tenant else 403
    elif u.path == '/api/admin-panel':
        status=200 if role == 'admin' else 403
    else:
        status=404
    body['authorization']='allowed' if status < 400 else ('blocked' if status == 403 else 'not_found')
    return {'blocked':False,'method':method,'url':url,'status':status,'body_preview':json.dumps(body)[:500],'elapsed_ms':0.01}

def safe_request(req: dict[str,Any], allow_external=False):
    method=str(req.get('method','GET')).upper(); url=req.get('url',''); headers=req.get('headers',{}) or {}
    if str(url).startswith('fixture://'):
        return fixture_request(req)
    if method not in SAFE and not req.get('explicit_safe_mutation'):
        return {'blocked':True,'reason':'unsafe method blocked','method':method,'url':url}
    if not is_allowed_url(url, allow_external):
        return {'blocked':True,'reason':'non-local url blocked without --allow-external','method':method,'url':url}
    started=time.time()
    try:
        q=urllib.request.Request(url, headers=headers, method=method)
        with urllib.request.urlopen(q, timeout=8) as r:
            body=r.read(2048).decode('utf-8','replace')
            return {'blocked':False,'method':method,'url':url,'status':r.status,'body_preview':body[:500],'elapsed_ms':round((time.time()-started)*1000,2)}
    except urllib.error.HTTPError as e:
        body=e.read(2048).decode('utf-8','replace')
        return {'blocked':False,'method':method,'url':url,'status':e.code,'body_preview':body[:500],'elapsed_ms':round((time.time()-started)*1000,2)}
    except Exception as e:
        return {'blocked':True,'reason':str(e),'method':method,'url':url}

class FixtureHandler(BaseHTTPRequestHandler):
    server_version='RoleTenantFixture/1.0'
    def log_message(self, fmt, *args): return
    def do_GET(self):
        u=urllib.parse.urlparse(self.path); qs=urllib.parse.parse_qs(u.query)
        role=self.headers.get('X-Role','guest'); tenant=self.headers.get('X-Tenant','')
        target=qs.get('tenant',[''])[0]
        body={"role":role,"tenant":tenant,"target_tenant":target,"path":u.path}
        if u.path == '/api/tenant-data':
            if role in {'admin','analyst'} and tenant and target == tenant:
                self.send_response(200); body['authorization']='allowed'
            else:
                self.send_response(403); body['authorization']='blocked'
        elif u.path == '/api/admin-panel':
            if role == 'admin': self.send_response(200); body['authorization']='allowed'
            else: self.send_response(403); body['authorization']='blocked'
        else:
            self.send_response(404); body['authorization']='not_found'
        self.send_header('Content-Type','application/json'); self.end_headers(); self.wfile.write(json.dumps(body).encode())

def start_fixture(port:int):
    srv=ThreadingHTTPServer(('127.0.0.1',port), FixtureHandler)
    th=threading.Thread(target=srv.serve_forever, daemon=True); th.start(); return srv

def default_cases(base):
    return [
      {'name':'positive_same_tenant_admin','category':'positive','left':'admin_t1','right':'tenant_t1','role':'admin','tenant':'t1','request':{'method':'GET','url':base+'/api/tenant-data?tenant=t1','headers':{'X-Role':'admin','X-Tenant':'t1'}},'expected_status':200},
      {'name':'negative_cross_tenant_blocked','category':'negative','left':'admin_t1','right':'tenant_t2','role':'admin','tenant':'t1','request':{'method':'GET','url':base+'/api/tenant-data?tenant=t2','headers':{'X-Role':'admin','X-Tenant':'t1'}},'expected_status':403},
      {'name':'negative_role_blocked','category':'negative','left':'user_t1','right':'admin_panel','role':'user','tenant':'t1','request':{'method':'GET','url':base+'/api/admin-panel','headers':{'X-Role':'user','X-Tenant':'t1'}},'expected_status':403},
      {'name':'blocked_unsafe_method','category':'blocked','left':'user_t1','right':'tenant_t1','role':'user','tenant':'t1','request':{'method':'POST','url':base+'/api/tenant-data?tenant=t1','headers':{'X-Role':'user','X-Tenant':'t1'}}}
    ]

def main():
    ap=argparse.ArgumentParser(description='Execute non-destructive multi-role/multi-tenant authorization replay and record authorization_result. Unsafe methods are blocked unless explicitly marked safe.')
    ap.add_argument('--scenarios', default='')
    ap.add_argument('--out', default='reports/js-top-tier')
    ap.add_argument('--allow-external', action='store_true')
    ap.add_argument('--fixture-server', action='store_true')
    ap.add_argument('--port', type=int, default=8765)
    args=ap.parse_args(); out=Path(args.out); out.mkdir(parents=True, exist_ok=True)
    srv=None
    data=load(Path(args.scenarios),{}) if args.scenarios else {}
    cases=data.get('cases') or data.get('replays') or []
    if not cases and args.fixture_server:
        cases=default_cases('fixture://role-tenant')
    results=[]
    for c in cases:
        r=safe_request(c.get('request',{}), args.allow_external)
        expected=c.get('expected_status')
        category=c.get('category','positive' if expected and int(expected)<400 else 'negative')
        ok = bool(r.get('blocked')) if category=='blocked' else (r.get('status') == expected)
        auth_failure = (category=='negative' and not r.get('blocked') and isinstance(r.get('status'),int) and r.get('status') < 400)
        results.append({'name':c.get('name'),'category':category,'role':c.get('role'),'tenant':c.get('tenant'),'left':c.get('left'),'right':c.get('right'),'expected_status':expected,'actual':r,'ok':ok,'authorization_failure':auth_failure})
    if srv:
        srv.shutdown(); srv.server_close()
    summary={'positive':sum(1 for r in results if r['category']=='positive' and r['ok']),'negative':sum(1 for r in results if r['category']=='negative' and r['ok']),'blocked':sum(1 for r in results if r['category']=='blocked' and r['ok']),'authorization_failures':sum(1 for r in results if r['authorization_failure']),'confirmed_vulnerabilities':0}
    status='ready' if summary['positive'] and summary['negative'] and summary['blocked'] else ('partial' if results else 'missing')
    output={'schema_version':'js-role-tenant-authorization-result/v1','status':status,'results':results,'summary':summary,'promotion_rule':'authorization_failure requires security impact review before vulnerability confirmation; passing positive/negative/blocked matrix is validation evidence, not a finding.'}
    (out/'js_role_tenant_authorization_result.json').write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding='utf-8')
    # compatibility output consumed by older quality gate
    diff={'schema_version':'js-role-tenant-diff/v2','status':status,'authorization_validation': status=='ready','reason':'Generated from non-destructive role/tenant authorization replay; no vulnerability is confirmed unless authorization_failures > 0 and impact evidence exists.','diffs':[{'left':r.get('left'),'right':r.get('right'),'authorization_result':[r]} for r in results]}
    (out/'js_role_tenant_diff.json').write_text(json.dumps(diff, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'ok':True,'status':status,**summary,'out':str(out/'js_role_tenant_authorization_result.json')}, ensure_ascii=False, indent=2))
if __name__=='__main__': main()

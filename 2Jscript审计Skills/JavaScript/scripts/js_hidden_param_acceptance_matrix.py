#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, threading, time, urllib.parse, urllib.request, urllib.error
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
SAFE={'GET','HEAD','OPTIONS'}; LOCAL={'localhost','127.0.0.1','::1'}

def load(p: Path, default=None):
    try: return json.loads(p.read_text(encoding='utf-8'))
    except Exception: return default if default is not None else {}

def allowed(url, allow_external=False):
    u=urllib.parse.urlparse(url); return u.scheme in {'http','https'} and (allow_external or u.hostname in LOCAL or (u.hostname or '').endswith('.local'))

def fixture_req_once(req):
    method=str(req.get('method','GET')).upper(); url=req.get('url','')
    if method not in SAFE and not req.get('explicit_safe_mutation'):
        return {'blocked':True,'reason':'unsafe method blocked','method':method,'url':url}
    u=urllib.parse.urlparse(url); qs=urllib.parse.parse_qs(u.query)
    if u.path == '/api/profile-preview':
        body={'accepted':{'displayName':qs.get('displayName',[''])[0]},'ignored':[k for k in qs if k not in {'displayName'}],'role':'user','fixture':True}
        return {'blocked':False,'status':200,'body_preview':json.dumps(body)[:800],'method':method,'url':url,'elapsed_ms':0.01}
    if u.path == '/api/admin-preview':
        if qs.get('admin',['false'])[0].lower() == 'true':
            body={'accepted':{},'rejected':['admin'],'authorization':'blocked','fixture':True}; status=403
        else:
            body={'accepted':{},'authorization':'allowed','fixture':True}; status=200
        return {'blocked':False,'status':status,'body_preview':json.dumps(body)[:800],'method':method,'url':url,'elapsed_ms':0.01}
    return {'blocked':False,'status':404,'body_preview':'','method':method,'url':url,'elapsed_ms':0.01}

def req_once(req, allow_external=False):
    method=str(req.get('method','GET')).upper(); url=req.get('url',''); headers=req.get('headers',{}) or {}
    if str(url).startswith('fixture://'):
        return fixture_req_once(req)
    if method not in SAFE and not req.get('explicit_safe_mutation'):
        return {'blocked':True,'reason':'unsafe method blocked','method':method,'url':url}
    if not allowed(url, allow_external): return {'blocked':True,'reason':'non-local url blocked','method':method,'url':url}
    start=time.time()
    try:
        q=urllib.request.Request(url, headers=headers, method=method)
        with urllib.request.urlopen(q, timeout=8) as r:
            body=r.read(4096).decode('utf-8','replace')
            return {'blocked':False,'status':r.status,'body_preview':body[:800],'method':method,'url':url,'elapsed_ms':round((time.time()-start)*1000,2)}
    except urllib.error.HTTPError as e:
        body=e.read(4096).decode('utf-8','replace')
        return {'blocked':False,'status':e.code,'body_preview':body[:800],'method':method,'url':url,'elapsed_ms':round((time.time()-start)*1000,2)}
    except Exception as e:
        return {'blocked':True,'reason':str(e),'method':method,'url':url}

class HiddenParamFixture(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args): return
    def do_GET(self):
        u=urllib.parse.urlparse(self.path); qs=urllib.parse.parse_qs(u.query)
        if u.path == '/api/profile-preview':
            accepted={'displayName':qs.get('displayName',[''])[0]}
            ignored=[k for k in qs if k not in {'displayName'}]
            self.send_response(200); self.send_header('Content-Type','application/json'); self.end_headers(); self.wfile.write(json.dumps({'accepted':accepted,'ignored':ignored,'role':'user'}).encode()); return
        if u.path == '/api/admin-preview':
            if qs.get('admin',['false'])[0].lower() == 'true':
                self.send_response(403); body={'accepted':{},'rejected':['admin'],'authorization':'blocked'}
            else:
                self.send_response(200); body={'accepted':{},'authorization':'allowed'}
            self.send_header('Content-Type','application/json'); self.end_headers(); self.wfile.write(json.dumps(body).encode()); return
        self.send_response(404); self.end_headers()

def start_fixture(port):
    srv=ThreadingHTTPServer(('127.0.0.1',port), HiddenParamFixture); threading.Thread(target=srv.serve_forever, daemon=True).start(); return srv

def default_probes(base):
    return [
      {'name':'positive_visible_param_accepted','category':'positive','expected_field':'displayName','baseline_request':{'method':'GET','url':base+'/api/profile-preview?displayName=alice'},'mutated_request':{'method':'GET','url':base+'/api/profile-preview?displayName=bob'},'expected_status':200},
      {'name':'negative_hidden_admin_rejected','category':'negative','expected_field':'admin','baseline_request':{'method':'GET','url':base+'/api/admin-preview'},'mutated_request':{'method':'GET','url':base+'/api/admin-preview?admin=true'},'expected_status':403},
      {'name':'blocked_unsafe_mutation','category':'blocked','expected_field':'role','baseline_request':{'method':'GET','url':base+'/api/profile-preview?displayName=alice'},'mutated_request':{'method':'POST','url':base+'/api/profile-preview?role=admin'}}
    ]

def verdict(category, base, mut, expected_status=None, impact=False):
    if category=='blocked': return 'blocked' if mut.get('blocked') else 'unsafe-not-blocked'
    if mut.get('blocked'): return 'not-tested'
    if expected_status is not None and mut.get('status') == expected_status:
        if category=='negative' and int(expected_status) >= 400: return 'rejected-as-expected'
        return 'accepted-as-expected'
    if base.get('body_preview') != mut.get('body_preview') or base.get('status') != mut.get('status'):
        return 'accepted-and-impactful' if impact else 'accepted-with-observable-difference'
    return 'no-observable-difference'

def main():
    ap=argparse.ArgumentParser(description='Execute backend positive/negative/blocked hidden parameter acceptance probes. Non-destructive by default.')
    ap.add_argument('--scenarios', default='')
    ap.add_argument('--out', default='reports/js-top-tier')
    ap.add_argument('--allow-external', action='store_true')
    ap.add_argument('--fixture-server', action='store_true')
    ap.add_argument('--port', type=int, default=8766)
    args=ap.parse_args(); out=Path(args.out); out.mkdir(parents=True, exist_ok=True)
    srv=None
    data=load(Path(args.scenarios),{}) if args.scenarios else {}; probes=data.get('probes') or []
    if not probes and args.fixture_server: probes=default_probes('fixture://hidden-param')
    results=[]
    for p in probes:
        base=req_once(p.get('baseline_request',{}), args.allow_external)
        mut=req_once(p.get('mutated_request',{}), args.allow_external)
        v=verdict(p.get('category','positive'), base, mut, p.get('expected_status'), bool(p.get('security_impact_proven')))
        results.append({'name':p.get('name'),'category':p.get('category'),'field':p.get('expected_field'),'baseline':base,'mutated':mut,'verdict':v,'security_impact_proven':bool(p.get('security_impact_proven')),'confirmed_vulnerability':False})
    if srv:
        srv.shutdown(); srv.server_close()
    summary={'positive':sum(1 for r in results if r['category']=='positive' and r['verdict'] in {'accepted-as-expected','accepted-with-observable-difference'}),'negative':sum(1 for r in results if r['category']=='negative' and r['verdict']=='rejected-as-expected'),'blocked':sum(1 for r in results if r['category']=='blocked' and r['verdict']=='blocked'),'accepted_and_impactful':sum(1 for r in results if r['verdict']=='accepted-and-impactful')}
    status='ready' if summary['positive'] and summary['negative'] and summary['blocked'] else ('partial' if results else 'missing')
    output={'schema_version':'js-hidden-param-acceptance-matrix/v1','status':status,'probes':results,'summary':summary,'promotion_rule':'accepted hidden parameter becomes a vulnerability only with explicit security impact evidence; rejected/blocked cases are evidence against false positives.'}
    (out/'js_hidden_param_acceptance_matrix.json').write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding='utf-8')
    compat={'schema_version':'js-backend-acceptance-evidence/v1','status':status,'probes':[{'name':r['name'],'field':r['field'],'verdict':r['verdict'],'baseline':r['baseline'],'mutated':r['mutated'],'security_impact_proven':r['security_impact_proven']} for r in results],'downgrade':'No accepted-and-impactful verdict may be claimed until response difference and security impact are both proven.'}
    (out/'js_backend_acceptance_evidence.json').write_text(json.dumps(compat, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'ok':True,'status':status,**summary,'out':str(out/'js_hidden_param_acceptance_matrix.json')}, ensure_ascii=False, indent=2))
if __name__=='__main__': main()

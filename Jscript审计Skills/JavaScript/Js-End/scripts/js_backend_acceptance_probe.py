#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, time, urllib.parse, urllib.request, urllib.error
from pathlib import Path
from typing import Any
SAFE_METHODS={'GET','HEAD','OPTIONS'}
LOCAL_HOSTS={'localhost','127.0.0.1','::1'}

def load(p: Path, default):
    try: return json.loads(p.read_text(encoding='utf-8'))
    except Exception: return default

def safe_url(url: str, allow_external: bool) -> bool:
    u=urllib.parse.urlparse(url)
    if u.scheme not in {'http','https'}: return False
    if allow_external: return True
    return u.hostname in LOCAL_HOSTS or (u.hostname or '').endswith('.local')

def request_once(req: dict[str,Any], allow_external: bool):
    method=req.get('method','GET').upper()
    url=req.get('url','')
    headers=req.get('headers',{}) or {}
    if method not in SAFE_METHODS and not req.get('explicit_safe_mutation'):
        return {'blocked':True,'reason':'method not safe without explicit_safe_mutation','method':method,'url':url}
    if not safe_url(url, allow_external):
        return {'blocked':True,'reason':'url not local/allowed','method':method,'url':url}
    data=None
    if req.get('body') is not None:
        body=req['body']
        if isinstance(body,(dict,list)): body=json.dumps(body).encode('utf-8'); headers.setdefault('Content-Type','application/json')
        elif isinstance(body,str): body=body.encode('utf-8')
        data=body
    q=urllib.request.Request(url, data=data, headers=headers, method=method)
    started=time.time()
    try:
        with urllib.request.urlopen(q, timeout=10) as r:
            body=r.read(4096)
            return {'blocked':False,'method':method,'url':url,'status':r.status,'headers':dict(r.headers),'body_sha256_len':len(body),'body_preview':body[:400].decode('utf-8','replace'),'elapsed_ms':round((time.time()-started)*1000,2)}
    except urllib.error.HTTPError as e:
        body=e.read(4096)
        return {'blocked':False,'method':method,'url':url,'status':e.code,'headers':dict(e.headers),'body_sha256_len':len(body),'body_preview':body[:400].decode('utf-8','replace'),'elapsed_ms':round((time.time()-started)*1000,2)}
    except Exception as e:
        return {'blocked':True,'reason':str(e),'method':method,'url':url}

def verdict(base, mutated):
    if base.get('blocked') or mutated.get('blocked'): return 'not-tested'
    if base.get('status') != mutated.get('status'): return 'accepted-with-response-difference'
    if base.get('body_preview') != mutated.get('body_preview'): return 'accepted-with-body-difference'
    return 'no-observable-difference'

def main():
    ap=argparse.ArgumentParser(description='Non-destructive backend acceptance probe for hidden/extra params. Local/allowlisted targets only.')
    ap.add_argument('--scenarios', required=True, help='JSON with probes: [{name,baseline_request,mutated_request,expected_field,role,tenant}]')
    ap.add_argument('--out', default='reports/js-top-tier')
    ap.add_argument('--allow-external', action='store_true', help='allow non-local authorized targets')
    args=ap.parse_args(); out=Path(args.out); out.mkdir(parents=True, exist_ok=True)
    data=load(Path(args.scenarios), {})
    probes=data.get('probes', data if isinstance(data,list) else [])
    results=[]
    for p in probes:
        b=request_once(p.get('baseline_request',{}), args.allow_external)
        m=request_once(p.get('mutated_request',{}), args.allow_external)
        v=verdict(b,m)
        if v in {'accepted-with-response-difference','accepted-with-body-difference'} and p.get('security_impact_proven'):
            v='accepted-and-impactful'
        results.append({'name':p.get('name'), 'field':p.get('expected_field'), 'role':p.get('role'), 'tenant':p.get('tenant'), 'baseline':b, 'mutated':m, 'verdict':v, 'security_impact_proven': bool(p.get('security_impact_proven')), 'impact_required':'response difference alone is not a vulnerability; accepted-and-impactful requires explicit security impact evidence'})
    status='ready' if any(r['verdict'] in {'accepted-with-response-difference','accepted-with-body-difference'} for r in results) else ('partial' if results else 'missing')
    ev={'schema_version':'js-backend-acceptance-evidence/v1','status':status,'probes':results,'downgrade':'No accepted-and-impactful verdict may be claimed until response difference and security impact are both proven.'}
    (out/'js_backend_acceptance_evidence.json').write_text(json.dumps(ev, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'ok':True,'status':status,'probes':len(results),'out':str(out/'js_backend_acceptance_evidence.json')}, ensure_ascii=False, indent=2))
if __name__=='__main__': main()

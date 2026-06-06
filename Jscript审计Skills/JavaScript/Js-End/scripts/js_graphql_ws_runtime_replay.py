#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, time, urllib.parse, urllib.request, urllib.error
from pathlib import Path
LOCAL={'localhost','127.0.0.1','::1'}

def load(p: Path, default=None):
    try: return json.loads(p.read_text(encoding='utf-8'))
    except Exception: return default if default is not None else {}

def local_url(url: str, allow_external=False):
    u=urllib.parse.urlparse(url)
    return u.scheme in {'http','https','ws','wss'} and (allow_external or u.hostname in LOCAL or (u.hostname or '').endswith('.local'))

def http_json(url, payload, headers, allow_external=False):
    if not local_url(url, allow_external): return {'blocked':True,'reason':'non-local url without --allow-external','url':url}
    data=json.dumps(payload).encode(); h={'Content-Type':'application/json', **(headers or {})}
    req=urllib.request.Request(url, data=data, headers=h, method='POST')
    st=time.time()
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            body=r.read(4096).decode('utf-8','replace')
            return {'blocked':False,'status':r.status,'body_preview':body[:500],'elapsed_ms':round((time.time()-st)*1000,2)}
    except urllib.error.HTTPError as e:
        body=e.read(4096).decode('utf-8','replace')
        return {'blocked':False,'status':e.code,'body_preview':body[:500],'elapsed_ms':round((time.time()-st)*1000,2)}
    except Exception as e:
        return {'blocked':True,'reason':str(e)}

def safe_graphql_probe(p):
    q=p.get('query','')
    if any(x in q.lower() for x in ['mutation','delete','remove','refund','pay','approve','transfer']):
        if not p.get('explicit_safe_mutation'):
            return {'blocked':True,'reason':'mutation/dangerous operation blocked without explicit_safe_mutation'}
    return http_json(p.get('url'), {'query':q,'variables':p.get('variables',{}),'operationName':p.get('operationName')}, p.get('headers',{}), p.get('allow_external',False))

def ws_probe(p):
    # Standard library has no WebSocket client; generate executable Playwright fragment instead of faking replay.
    if not local_url(p.get('url',''), p.get('allow_external',False)):
        return {'blocked':True,'reason':'non-local ws url without allow_external','url':p.get('url')}
    return {'blocked':False,'status':'playwright-fragment-required','url':p.get('url'),'message':p.get('message',{}),'note':'Use generated Playwright spec to execute WebSocket replay and capture HAR/trace; this JSON is not proof of execution.'}

def main():
    ap=argparse.ArgumentParser(description='Safe GraphQL/WebSocket runtime replay. GraphQL queries can execute against local/allowed targets; WebSocket emits replay fragments unless an external Playwright run supplies evidence.')
    ap.add_argument('--scenarios', required=True)
    ap.add_argument('--out', default='reports/js-top-tier')
    ap.add_argument('--allow-external', action='store_true')
    args=ap.parse_args(); out=Path(args.out); out.mkdir(parents=True, exist_ok=True)
    data=load(Path(args.scenarios),{}); scenarios=data.get('scenarios', data if isinstance(data,list) else [])
    results=[]
    for s in scenarios:
        s=dict(s); s['allow_external']=args.allow_external or s.get('allow_external',False)
        proto=s.get('protocol','').lower()
        if proto=='graphql': r=safe_graphql_probe(s)
        elif proto in {'websocket','ws'}: r=ws_probe(s)
        else: r={'blocked':True,'reason':'unknown protocol'}
        results.append({'name':s.get('name'),'protocol':proto,'role':s.get('role'),'tenant':s.get('tenant'),'result':r,'promotable':False,'promotion_rule':'Only request/response evidence with role/tenant diff and security impact may be promoted.'})
    status='partial' if results else 'missing'
    if any(not x['result'].get('blocked') and isinstance(x['result'].get('status'),int) for x in results): status='evidence-present'
    ev={'schema_version':'js-graphql-ws-runtime-replay/v1','status':status,'results':results,'downgrade':'WebSocket fragments and GraphQL response differences are candidates until linked to runtime evidence manifest and role/tenant authorization result.'}
    (out/'js_graphql_ws_runtime_replay.json').write_text(json.dumps(ev, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'ok':True,'status':status,'results':len(results),'out':str(out/'js_graphql_ws_runtime_replay.json')}, ensure_ascii=False, indent=2))
if __name__=='__main__': main()

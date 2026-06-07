#!/usr/bin/env python3
"""GraphQL resolver-level authz and complexity replay planner/executor."""
from __future__ import annotations
import argparse, json, re, subprocess, sys, hashlib, urllib.request
from pathlib import Path
LOCAL=re.compile(r'^https?://(localhost|127\.0\.0\.1|\[::1\])(:\d+)?/', re.I)
FIELD=re.compile(r'\b([A-Za-z_][A-Za-z0-9_]*)\b')
def load(p): return json.loads(Path(p).read_text(encoding='utf-8', errors='ignore')) if p and Path(p).exists() else {}
def resp_hash(s: str) -> str:
    return hashlib.sha256(s.encode('utf-8','ignore')).hexdigest()

def post_graphql(endpoint: str, query: str) -> dict:
    body=json.dumps({'query': query}).encode('utf-8')
    req=urllib.request.Request(endpoint, data=body, headers={'content-type':'application/json'}, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            data=r.read(1000000).decode('utf-8','ignore')
            return {'ok': True, 'status': r.status, 'response_sha256': resp_hash(data), 'response_bytes': len(data)}
    except Exception as exc:
        return {'ok': False, 'error': f'{exc.__class__.__name__}: {str(exc)[:160]}'}

def complexity(q):
    depth=0; maxd=0; fields=0
    for ch in q:
        if ch=='{': depth+=1; maxd=max(maxd, depth)
        elif ch=='}': depth=max(0, depth-1)
    fields=len([x for x in FIELD.findall(q) if x not in {'query','mutation','subscription','fragment','on'}])
    return {'field_count':fields,'max_depth':maxd,'estimated_cost':fields*max(1,maxd)}
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--code-graph'); ap.add_argument('--queries'); ap.add_argument('--endpoint'); ap.add_argument('--execute', action='store_true'); ap.add_argument('--out')
    a=ap.parse_args(); cg=load(a.code_graph); qs=[]
    if a.queries and Path(a.queries).exists():
        obj=load(a.queries); qs=obj.get('queries') if isinstance(obj,dict) else obj
    if not qs:
        for x in (cg.get('api_clients') or []) + (cg.get('routes') or []):
            blob=json.dumps(x, ensure_ascii=False)
            if 'graphql' in blob.lower(): qs.append({'name':'discovered_graphql_surface','query':'query __SafeTypename { __typename }','source':x})
    rows=[]; blockers=[]; executed=False; attempted_execute=bool(a.execute)
    if a.execute:
        if not a.endpoint or not LOCAL.search(a.endpoint): blockers.append('endpoint_must_be_localhost_for_execute')
        if not blockers:
            executed=True
            for i,q in enumerate(qs[:30]):
                query=q.get('query') if isinstance(q,dict) else str(q); comp=complexity(query)
                attempt=post_graphql(a.endpoint, query)
                ok=bool(attempt.get('ok'))
                rows.append({'case_id':'GQL-'+str(i+1),'query_name':q.get('name','anonymous') if isinstance(q,dict) else 'anonymous','complexity':comp,'executed':ok,'attempted':True,'non_destructive':True,'redacted':True, **attempt})
            executed=any(r.get('executed') for r in rows)
            if not executed:
                blockers.append('all_graphql_execute_attempts_failed')
    if not executed and not attempted_execute:
        for i,q in enumerate(qs[:50]):
            query=q.get('query') if isinstance(q,dict) else str(q)
            rows.append({'case_id':'GQL-'+str(i+1),'query_name':q.get('name','anonymous') if isinstance(q,dict) else 'anonymous','complexity':complexity(query),'executed':False,'planned':True,'non_destructive':True})
    res={'schema_version':'graphql_resolver_replay_v1','executor':'graphql_resolver_replay.py','executed':executed,'blockers':blockers,'rows':rows,'promotion_policy':'Resolver authz/complexity findings require executed per-role queries, negative controls and response summaries; planned rows cannot confirm.'}
    text=json.dumps(res, ensure_ascii=False, indent=2)
    if a.out: Path(a.out).parent.mkdir(parents=True, exist_ok=True); Path(a.out).write_text(text+'\n', encoding='utf-8')
    else: print(text)
    return 0 if not blockers else 1
if __name__=='__main__': raise SystemExit(main())

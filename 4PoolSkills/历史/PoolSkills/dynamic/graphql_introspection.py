#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, sys, urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from common.scope_guard import load_scope, assert_url_allowed, assert_payload_safe

def parse_schema_file(path: str | Path) -> dict:
    p=Path(path)
    data=json.loads(p.read_text(encoding='utf-8'))
    types=data.get('__schema',{}).get('types') or data.get('data',{}).get('__schema',{}).get('types') or []
    return {'schema_version':'graphql-introspection-v2','status':'parsed','mode':'local_schema_file','types':[t.get('name') for t in types if isinstance(t,dict)],'counts':{'types':len(types)},'policy':'Local schema import only unless --endpoint is explicitly authorized by scope.'}

def run_query(endpoint: str, root: str | Path, query: str, variables: dict | None = None, scope_file: str | None = None, out_dir: str | Path | None = None) -> dict:
    root=Path(root).resolve(); scope=load_scope(root, scope_file)
    assert_url_allowed(endpoint, scope); assert_payload_safe(query, scope)
    out_dir=Path(out_dir or root/'evidence'/'graphql').resolve(); out_dir.mkdir(parents=True,exist_ok=True)
    payload=json.dumps({'query':query,'variables':variables or {}}).encode('utf-8')
    req=urllib.request.Request(endpoint, data=payload, method='POST', headers={'content-type':'application/json'})
    req_file=out_dir/'graphql.request.json'; res_file=out_dir/'graphql.response.json'
    req_file.write_text(json.dumps({'endpoint':endpoint,'query':query,'variables':variables or {}},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            body=resp.read(2_000_000).decode('utf-8','replace')
            status=resp.status
            headers=dict(resp.headers.items())
    except Exception as e:
        res_file.write_text(json.dumps({'status':'failed','error':str(e)},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        return {'schema_version':'graphql-introspection-v2','status':'failed','mode':'authorized_endpoint','error':str(e),'request_ref':str(req_file.relative_to(root)),'response_ref':str(res_file.relative_to(root))}
    res_file.write_text(json.dumps({'status':status,'headers':headers,'body_prefix':body[:20000]},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    parsed={}
    try: parsed=json.loads(body)
    except Exception: parsed={}
    return {'schema_version':'graphql-introspection-v2','status':'passed' if status < 500 else 'needs_review','mode':'authorized_endpoint','request_ref':str(req_file.relative_to(root)),'response_ref':str(res_file.relative_to(root)),'http_status':status,'errors_present':bool(parsed.get('errors')),'policy':'Endpoint calls are allowed only after scope network authorization; evidence still requires manifest stitching and quality gate.'}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--schema-file'); ap.add_argument('--endpoint'); ap.add_argument('--root',default='.'); ap.add_argument('--scope-file'); ap.add_argument('--query'); ap.add_argument('--variables'); ap.add_argument('--out-dir'); ap.add_argument('--out',required=True); ns=ap.parse_args()
    try:
        if ns.endpoint:
            query=ns.query or '{ __typename }'
            variables=json.loads(ns.variables) if ns.variables else {}
            data=run_query(ns.endpoint, ns.root, query, variables, ns.scope_file, ns.out_dir); code=0 if data.get('status') in {'passed','needs_review'} else 1
        elif ns.schema_file:
            data=parse_schema_file(ns.schema_file); code=0
        else:
            data={'schema_version':'graphql-introspection-v2','status':'blocked','error':'schema_file_or_authorized_endpoint_required'}; code=2
    except Exception as e:
        data={'schema_version':'graphql-introspection-v2','status':'failed','error':str(e)}; code=1
    Path(ns.out).parent.mkdir(parents=True,exist_ok=True); Path(ns.out).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':data['status']},ensure_ascii=False)); sys.exit(code)
if __name__=='__main__': main()

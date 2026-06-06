#!/usr/bin/env python3
"""Inventory API specification artifacts in an authorized local repository.

Supports OpenAPI/Swagger JSON, best-effort YAML, Postman collections, GraphQL
schema/operation files, and protobuf/gRPC service files. Static candidates only.
"""
from __future__ import annotations
import argparse, hashlib, json, re, sys
from pathlib import Path

SKIP={'.git','node_modules','vendor','__pycache__','.venv','venv','target','coverage','.pytest_cache'}
SPEC_NAMES=('openapi','swagger','postman','collection','graphql','schema','proto')
SUFFIXES={'.json','.yaml','.yml','.graphql','.gql','.proto'}
HTTP_METHODS={'get','post','put','delete','patch','options','head','trace'}

def sha(s:str)->str: return hashlib.sha256(s.encode()).hexdigest()[:16]
def emit(rows, root, path, line, typ, value, method=None, endpoint=None, note='static candidate only'):
    rel=str(path.relative_to(root)).replace('\\','/')
    rows.append({'asset_id':'API-'+sha(f'{rel}:{line}:{typ}:{method}:{endpoint}:{value}'),'type':typ,'source_file':rel,'line':line,'method':method,'endpoint':endpoint,'value':value,'evidence_status':'static_candidate_needs_dynamic_validation','dynamic_status':'not_validated','review_status':'needs_review','redaction_status':'metadata_only','note':note})
def walk(root:Path):
    for p in root.rglob('*'):
        if any(part in SKIP for part in p.parts): continue
        if p.is_file() and (p.suffix.lower() in SUFFIXES or any(n in p.name.lower() for n in SPEC_NAMES)):
            yield p
def read(p:Path)->str:
    try:
        if p.stat().st_size>3_000_000: return ''
        return p.read_text(encoding='utf-8', errors='ignore')
    except Exception: return ''
def line_no(text, needle):
    i=text.find(needle)
    return 1 if i<0 else text[:i].count('\n')+1

def scan_openapi_json(rows,root,path,text):
    try: data=json.loads(text)
    except Exception: return False
    if not isinstance(data,dict): return False
    if 'openapi' in data or 'swagger' in data:
        servers=data.get('servers') or []
        for s in servers:
            if isinstance(s,dict) and s.get('url'):
                emit(rows,root,path,1,'openapi_server_url',s.get('url'),endpoint=s.get('url'),note='server URL from local OpenAPI spec; do not contact unless authorized')
        for route, methods in (data.get('paths') or {}).items():
            if isinstance(methods,dict):
                for m,meta in methods.items():
                    if str(m).lower() in HTTP_METHODS:
                        params=[]
                        for p in (meta or {}).get('parameters',[]) if isinstance(meta,dict) else []:
                            if isinstance(p,dict): params.append({'name':p.get('name'),'in':p.get('in')})
                        emit(rows,root,path,1,'openapi_path_operation',{'parameters':params,'operationId':(meta or {}).get('operationId') if isinstance(meta,dict) else None},method=str(m).upper(),endpoint=route,note='OpenAPI operation candidate')
        return True
    if 'item' in data and 'info' in data:
        def rec(items):
            for it in items or []:
                if not isinstance(it,dict): continue
                if 'item' in it:
                    rec(it.get('item'))
                    continue
                req=it.get('request') or {}
                url=req.get('url') if isinstance(req,dict) else None
                method=req.get('method') if isinstance(req,dict) else None
                raw=url.get('raw') if isinstance(url,dict) else url
                if raw:
                    emit(rows,root,path,1,'postman_request',{'name':it.get('name')},method=method,endpoint=str(raw),note='Postman request candidate')
        rec(data.get('item'))
        return True
    return False

def scan_yaml_best_effort(rows,root,path,text):
    if not re.search(r'(?m)^\s*(openapi|swagger)\s*:', text): return
    for m in re.finditer(r'(?m)^\s{0,4}(/[^:\s]+)\s*:\s*$', text):
        route=m.group(1)
        start=m.end(); window=text[start:start+1200]
        for mm in re.finditer(r'(?m)^\s{2,8}(get|post|put|delete|patch|options|head)\s*:', window, re.I):
            emit(rows,root,path,line_no(text,route),'openapi_yaml_path_operation',{},method=mm.group(1).upper(),endpoint=route,note='best-effort YAML OpenAPI operation candidate')
    for m in re.finditer(r'(?m)^\s*-\s*url\s*:\s*([^\n]+)', text):
        emit(rows,root,path,line_no(text,m.group(0)),'openapi_yaml_server_url',m.group(1).strip().strip('"\''),endpoint=m.group(1).strip().strip('"\''),note='server URL from local YAML spec; do not contact unless authorized')

def scan_graphql(rows,root,path,text):
    for m in re.finditer(r'\b(type|input|interface|enum)\s+([A-Za-z_][A-Za-z0-9_]*)', text):
        emit(rows,root,path,line_no(text,m.group(0)),'graphql_schema_type',{'kind':m.group(1),'name':m.group(2)},endpoint='/graphql',note='GraphQL schema type candidate')
    for m in re.finditer(r'\b(query|mutation|subscription)\s+([A-Za-z_][A-Za-z0-9_]*)', text, re.I):
        emit(rows,root,path,line_no(text,m.group(0)),'graphql_operation',{'operation_type':m.group(1),'operation_name':m.group(2)},endpoint='/graphql',note='GraphQL operation candidate')
    for m in re.finditer(r'(?m)^\s*([A-Za-z_][A-Za-z0-9_]*)\s*\([^\n)]*\)\s*:', text):
        # resolver-like field with args in Query/Mutation blocks
        emit(rows,root,path,line_no(text,m.group(0)),'graphql_field_with_args',m.group(1),endpoint='/graphql',note='GraphQL field-with-arguments candidate')

def scan_proto(rows,root,path,text):
    for svc in re.finditer(r'\bservice\s+([A-Za-z_][A-Za-z0-9_]*)\s*\{', text):
        emit(rows,root,path,line_no(text,svc.group(0)),'grpc_service',svc.group(1),endpoint=svc.group(1),note='gRPC/protobuf service candidate')
    for rpc in re.finditer(r'\brpc\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(([^)]*)\)\s*returns\s*\(([^)]*)\)', text):
        emit(rows,root,path,line_no(text,rpc.group(0)),'grpc_rpc_method',{'request':rpc.group(2),'response':rpc.group(3)},method='RPC',endpoint=rpc.group(1),note='gRPC method candidate')

def main():
    ap=argparse.ArgumentParser(description='Inventory local API specs. No network and no validation.')
    ap.add_argument('root')
    ap.add_argument('-o','--out',default='-')
    ap.add_argument('--dry-run',action='store_true')
    args=ap.parse_args()
    root=Path(args.root).resolve()
    if not root.is_dir():
        print(f'root not directory: {root}',file=sys.stderr); return 2
    files=list(walk(root))
    if args.dry_run:
        print(json.dumps({'schema_version':'api-spec-inventory.dry-run.v1','root':str(root),'files_to_scan':len(files),'network':'disabled'})); return 0
    rows=[]
    for p in files:
        text=read(p)
        if not text: continue
        if p.suffix.lower()=='.json' or p.name.lower().endswith('.json'):
            scan_openapi_json(rows,root,p,text)
        if p.suffix.lower() in {'.yaml','.yml'}:
            scan_yaml_best_effort(rows,root,p,text)
        if p.suffix.lower() in {'.graphql','.gql'} or 'graphql' in p.name.lower():
            scan_graphql(rows,root,p,text)
        if p.suffix.lower()=='.proto':
            scan_proto(rows,root,p,text)
    seen=set(); unique=[]
    for r in rows:
        if r['asset_id'] not in seen:
            seen.add(r['asset_id']); unique.append(r)
    fh=sys.stdout if args.out=='-' else open(args.out,'w',encoding='utf-8')
    try:
        for r in unique: fh.write(json.dumps(r,ensure_ascii=False,sort_keys=True)+'\n')
    finally:
        if fh is not sys.stdout: fh.close()
    print(f'wrote {len(unique)} api spec candidates', file=sys.stderr)
    return 0
if __name__=='__main__':
    raise SystemExit(main())

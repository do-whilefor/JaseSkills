#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import json, re
from _info_collect_lib import common_parser, parse_scope, enforce_scope, iter_scoped_files, output_report, evidence, dry_run_report, read_text, ROUTE_RE, PATH_RE, line_no
WS_RE=re.compile(r"(?i)(?:emit|on|send|subscribe|publish|channel|event)\s*\(\s*[`\"']([A-Za-z0-9_.:\-/]+)[`\"']")
GQL_OP=re.compile(r'\b(query|mutation|subscription)\s+([A-Za-z_][A-Za-z0-9_]*)')

def scan_openapi(data,path,root,items,scope_id):
    for route, methods in (data.get('paths') or {}).items():
        if isinstance(methods,dict):
            for method in methods:
                if method.lower() in {'get','post','put','delete','patch','options','head'}:
                    items.append(evidence('route_api_extractor',path,root,'openapi_path_operation',{'method':method.upper(),'path':route},1,confidence=.9,endpoint_relevance='high',scope_id=scope_id,linked_report_section='route-api-inventory'))

def scan_postman(data,path,root,items,scope_id):
    def rec(arr):
        for it in arr or []:
            if isinstance(it,dict) and 'item' in it: rec(it.get('item'))
            elif isinstance(it,dict):
                req=it.get('request') or {}; method=req.get('method','GET'); url=req.get('url')
                raw=url.get('raw') if isinstance(url,dict) else url
                if raw: items.append(evidence('route_api_extractor',path,root,'postman_request',{'method':method,'url':raw},1,confidence=.85,endpoint_relevance='high',scope_id=scope_id,needs_review=True,linked_report_section='route-api-inventory'))
    rec(data.get('item',[]) if isinstance(data,dict) else [])

def main():
    ap=common_parser('Extract backend routes, frontend routes, API specs, GraphQL, WebSocket, RPC and gRPC entry candidates.')
    args=ap.parse_args(); root=Path(args.input).resolve(); scope=parse_scope(args.scope, root); ok,reason=enforce_scope(root, scope)
    if args.dry_run: return dry_run_report(args,'route_api_extractor',root,scope)
    if not ok: return output_report(args,'route_api_extractor',[evidence('route_api_extractor',root,root.parent,'out_of_scope_blocked',reason,1,confidence=1,severity_hint='blocker',needs_review=True)], {'scope_check':'FAIL'}) or 2
    items=[]; files=list(iter_scoped_files(root, scope, args.max_files, args.timeout, args.scan_profile, args.follow_symlinks)) if root.is_dir() else [root]
    for p in files:
        text=read_text(p); low=p.name.lower()
        if low.endswith('.json'):
            try:
                data=json.loads(text)
                if isinstance(data,dict) and ('openapi' in data or 'swagger' in data): scan_openapi(data,p,root,items,scope['scope_id'])
                if isinstance(data,dict) and ('postman' in low or ('item' in data and 'info' in data)): scan_postman(data,p,root,items,scope['scope_id'])
            except Exception: pass
        if low.endswith(('.graphql','.gql')):
            for m in re.finditer(r'\b(type|interface|input|enum|scalar)\s+([A-Za-z_][A-Za-z0-9_]*)',text):
                items.append(evidence('route_api_extractor',p,root,'graphql_schema_type',{'kind':m.group(1),'name':m.group(2)},line_no(text,m.group(0)),confidence=.85,endpoint_relevance='medium',scope_id=scope['scope_id'],linked_report_section='route-api-inventory'))
        if low.endswith('.proto'):
            for m in re.finditer(r'\brpc\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(',text):
                items.append(evidence('route_api_extractor',p,root,'grpc_rpc_method',m.group(1),line_no(text,m.group(0)),confidence=.85,endpoint_relevance='high',scope_id=scope['scope_id'],linked_report_section='route-api-inventory'))
        for m in ROUTE_RE.finditer(text):
            method=(m.group(1) or m.group(3) or 'ROUTE').upper(); route=m.group(2) or m.group(4) or m.group(5)
            items.append(evidence('route_api_extractor',p,root,'backend_or_frontend_route',{'method':method,'path':route},line_no(text,m.group(0)),confidence=.7,endpoint_relevance='high',scope_id=scope['scope_id'],linked_report_section='route-api-inventory'))
        for m in PATH_RE.finditer(text):
            items.append(evidence('route_api_extractor',p,root,'literal_api_path_candidate',m.group(0),line_no(text,m.group(0)),confidence=.55,endpoint_relevance='medium',scope_id=scope['scope_id'],needs_review=True,linked_report_section='route-api-inventory'))
        for m in GQL_OP.finditer(text):
            items.append(evidence('route_api_extractor',p,root,'graphql_operation',{'type':m.group(1),'name':m.group(2)},line_no(text,m.group(0)),confidence=.75,endpoint_relevance='medium',scope_id=scope['scope_id'],linked_report_section='route-api-inventory'))
        for m in WS_RE.finditer(text):
            items.append(evidence('route_api_extractor',p,root,'websocket_or_event_entry',m.group(1),line_no(text,m.group(0)),confidence=.6,endpoint_relevance='medium',scope_id=scope['scope_id'],needs_review=True,linked_report_section='route-api-inventory'))
    return output_report(args,'route_api_extractor',items)
if __name__=='__main__': raise SystemExit(main())

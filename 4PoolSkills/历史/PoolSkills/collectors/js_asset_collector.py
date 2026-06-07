#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.scope_guard import iter_scoped_files, load_scope, read_text_scoped
JS_EXTS={'.js','.jsx','.ts','.tsx','.mjs','.cjs','.vue','.html','.map','.json'}
ENDPOINT_RX=[re.compile(r"(?:fetch|axios(?:\.[a-z]+)?|request|apiClient|apiService|rpcClient)\s*\(\s*['\"](?P<url>/(?:api|v[0-9]|graphql|admin|internal)[^'\"]*)['\"]",re.I), re.compile(r"(?:url|endpoint|path)\s*[:=]\s*['\"](?P<url>/(?:api|v[0-9]|graphql|admin|internal)[^'\"]*)['\"]",re.I)]
DYN_IMPORT_RX=re.compile(r"import\s*\(\s*['\"](?P<chunk>[^'\"]+)['\"]\s*\)")
GRAPHQL_RX=re.compile(r"\b(?P<op>query|mutation|subscription|fragment)\s+(?P<name>[A-Za-z0-9_]+)",re.I)
WS_RX=re.compile(r"(?:socket\.emit|send|onmessage|addEventListener)\s*\(\s*['\"](?P<event>[A-Za-z0-9_:\-.]+)['\"]",re.I)
PARAM_RX=re.compile(r"(?P<name>[A-Za-z_][A-Za-z0-9_]*(?:Id|_id|role|permission|tenant|org|workspace|admin|debug|feature|flag))\s*[:=]",re.I)
STORAGE_RX=re.compile(r"(?:localStorage|sessionStorage)\.(?:getItem|setItem|removeItem)\s*\(\s*['\"](?P<key>[^'\"]+)['\"]",re.I)
ROLE_RX=re.compile(r"['\"](?P<role>admin|owner|superuser|root|support|internal|beta|staff)['\"]",re.I)

def eid(*parts): return 'js-' + hashlib.sha256(':'.join(map(str,parts)).encode()).hexdigest()[:14]
def line_no(t,pos): return t[:pos].count('\n')+1

def collect(root, scope_file=None):
    root=Path(root).resolve(); scope=load_scope(root, scope_file)
    endpoints=[]; chunks=[]; sourcemaps=[]; graphql=[]; ws=[]; params=[]; storage=[]; roles=[]; service_workers=[]; wrappers=[]
    for p in iter_scoped_files(root, scope, JS_EXTS):
        text,_=read_text_scoped(p, root, scope, limit=4_000_000)
        rel=str(p.relative_to(root))
        if rel.endswith('.map') or 'sourceMappingURL=' in text:
            sourcemaps.append({'id':eid('map',rel),'file':rel,'type':'source_map_or_reference'})
        if 'serviceWorker' in text or rel.endswith('service-worker.js') or rel.endswith('sw.js'):
            service_workers.append({'id':eid('sw',rel),'file':rel})
        if re.search(r'(axios\.create|interceptors\.|apiService|rpcClient|graphqlClient|requestClient)',text):
            wrappers.append({'id':eid('wrapper',rel),'file':rel,'kind':'request_wrapper_or_interceptor'})
        for rx in ENDPOINT_RX:
            for m in rx.finditer(text): endpoints.append({'id':eid('ep',rel,m.start()),'url':m.group('url'),'file':rel,'line':line_no(text,m.start()),'source':'js_ast_regex_hybrid'})
        for m in DYN_IMPORT_RX.finditer(text): chunks.append({'id':eid('chunk',rel,m.start()),'chunk':m.group('chunk'),'file':rel,'line':line_no(text,m.start())})
        for m in GRAPHQL_RX.finditer(text): graphql.append({'id':eid('gql',rel,m.start()),'operation_type':m.group('op').lower(),'name':m.group('name'),'file':rel,'line':line_no(text,m.start())})
        for m in WS_RX.finditer(text): ws.append({'id':eid('ws',rel,m.start()),'event':m.group('event'),'file':rel,'line':line_no(text,m.start())})
        for m in PARAM_RX.finditer(text): params.append({'id':eid('param',rel,m.start()),'name':m.group('name'),'file':rel,'line':line_no(text,m.start()),'source':'hidden_param_signal'})
        for m in STORAGE_RX.finditer(text): storage.append({'id':eid('storage',rel,m.start()),'key':m.group('key'),'file':rel,'line':line_no(text,m.start())})
        for m in ROLE_RX.finditer(text): roles.append({'id':eid('role',rel,m.start()),'constant':m.group('role'),'file':rel,'line':line_no(text,m.start())})
    return {'schema_version':'js-assets-v2','root':str(root),'endpoints':endpoints,'dynamic_imports':chunks,'sourcemaps':sourcemaps,'graphql_operations':graphql,'websocket_events':ws,'hidden_parameters':params,'storage_keys':storage,'role_permission_constants':roles,'service_workers':service_workers,'request_wrappers':wrappers,'counts':{'endpoints':len(endpoints),'hidden_parameters':len(params),'graphql':len(graphql),'websocket':len(ws)}}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('root'); ap.add_argument('--scope-file'); ap.add_argument('--out',required=True); ns=ap.parse_args()
    data=collect(ns.root,ns.scope_file); Path(ns.out).parent.mkdir(parents=True,exist_ok=True); Path(ns.out).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); print(json.dumps(data['counts'],ensure_ascii=False))
if __name__=='__main__': main()

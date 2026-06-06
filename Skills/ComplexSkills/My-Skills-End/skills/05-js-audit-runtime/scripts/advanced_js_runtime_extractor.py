#!/usr/bin/env python3
"""JS/TS audit graph extractor v3.

Read-only local extractor. It re-enters sourcemap sourcesContent into the same
API/wrapper/GraphQL detector, resolves common axios/request wrappers and records
interceptors, persisted GraphQL queries, chunk lineage and frontend-backend mapping
obligations. It never confirms vulnerabilities.
"""
from __future__ import annotations
import argparse, base64, json, re, hashlib, subprocess, shutil
from pathlib import Path
from typing import Any

JS_EXT={'.js','.jsx','.ts','.tsx','.mjs','.cjs','.vue','.svelte'}; HTML_EXT={'.html','.htm'}; SKIP={'.git','node_modules','vendor','__pycache__','.venv','target'}
IMPORT_RE=re.compile(r"(?:import\s+(?:[^'\"]+\s+from\s+)?|export\s+[^'\"]*from\s+)[`'\"]([^`'\"]+)[`'\"]")
DYN_IMPORT_RE=re.compile(r"import\s*\(\s*[`'\"]([^`'\"]+)[`'\"]\s*\)")
BASEURL_RE=re.compile(r"(?:baseURL|baseUrl)\s*:\s*[`'\"]([^`'\"]+)[`'\"]|(?:const|let|var)\s+([A-Za-z0-9_]*BASE[A-Za-z0-9_]*|apiBase|baseUrl)\s*=\s*[`'\"]([^`'\"]+)[`'\"]",re.I)
AXIOS_INSTANCE_RE=re.compile(r"(?:const|let|var)\s+([A-Za-z0-9_$]+)\s*=\s*axios\.create\s*\(\s*\{([^}]*)\}",re.S)
INTERCEPTOR_RE=re.compile(r"([A-Za-z0-9_$.]+)\.interceptors\.(request|response)\.use\s*\(",re.I)
FETCH_RE=re.compile(r"\b(fetch|axios\.(?:get|post|put|patch|delete)|request|http\.(?:get|post|put)|client\.(?:get|post|put|patch|delete)|api\.(?:get|post|put|patch|delete)|[A-Za-z0-9_$]+\.(?:get|post|put|patch|delete))\s*\(\s*([`'\"])([^`'\"]+)\2",re.I)
WRAPPER_DEF_RE=re.compile(r"(?:function|const|export\s+function|export\s+const)\s+([A-Za-z0-9_]*(?:request|api|fetch|client|graphql)[A-Za-z0-9_]*)",re.I)
WRAPPER_CALL_RE=re.compile(r"\b([A-Za-z0-9_]*(?:request|api|fetch|client|graphql)[A-Za-z0-9_]*|[A-Za-z0-9_$]+)\.(get|post|put|patch|delete)\s*\(\s*([`'\"])([^`'\"]+)\3",re.I)
GQL_RE=re.compile(r"(?:gql`|\b(query|mutation|subscription)\s+([A-Za-z0-9_]+)|\bfragment\s+([A-Za-z0-9_]+)|operationName\s*[:=]\s*['\"]?([A-Za-z0-9_]+)|persistedQuery|sha256Hash\s*[:=]\s*['\"]([a-fA-F0-9]{16,64}))")
WS_RE=re.compile(r"\b(new\s+WebSocket|EventSource)\s*\(")
POSTMSG_RE=re.compile(r"\bpostMessage\s*\(|addEventListener\s*\(\s*['\"]message['\"]")
OAUTH_CB_RE=re.compile(r"(redirect_uri|oauth|oidc|saml|callback|state|nonce)",re.I)
PERM_RE=re.compile(r"(can\(|hasPermission|permission|role|isAdmin|tenant|orgId|workspaceId|guard|routeGuard|beforeEach)",re.I)
FLAG_RE=re.compile(r"\b(?:featureFlags?|flags?|experiments?|abTest|growthbook|launchdarkly|unleash|variant)\b[^\n]{0,160}",re.I)
I18N_RE=re.compile(r"[`'\"]([a-zA-Z0-9_.-]*(?:admin|role|permission|tenant|org|user|invoice|order|file|webhook|upload)[a-zA-Z0-9_.-]*)[`'\"]")
ANALYTICS_RE=re.compile(r"(track\(|analytics\.|amplitude|mixpanel|posthog|gtag|dataLayer|eventName)",re.I)
SCHEMA_RE=re.compile(r"(z\.object|yup\.object|Joi\.object|ajv|new\s+Ajv|superstruct|valibot)")
SENSITIVE_RE=re.compile(r"(api[_-]?key|secret|token|private[_-]?key|dsn|sentry|firebase|supabase|bucket|AKIA[0-9A-Z]{16})",re.I)
API_PATH_RE=re.compile(r"[`'\"](/(?:api|graphql|rpc|admin|v\d+|internal)/[^`'\"]*)[`'\"]")
SOURCE_MAP_RE=re.compile(r"//#\s*sourceMappingURL=(.+)$",re.M)
HTML_SCRIPT_RE=re.compile(r"<script[^>]+src=[\"']([^\"']+)[\"']",re.I); HTML_LINK_RE=re.compile(r"<link[^>]+rel=[\"'](?:preload|prefetch|modulepreload)[\"'][^>]+href=[\"']([^\"']+)[\"']",re.I)
SERVICE_WORKER_CACHE_RE=re.compile(r"(?:caches\.open|cache\.addAll|workbox|precacheAndRoute|__WB_MANIFEST)",re.I)

def sha16(s:str)->str: return hashlib.sha256(s.encode('utf-8','ignore')).hexdigest()[:16]
def sha_file(p:Path)->str:
    h=hashlib.sha256()
    try:
        with p.open('rb') as f:
            for b in iter(lambda:f.read(65536),b''): h.update(b)
        return h.hexdigest()
    except Exception: return ''
def line_of(text,pos): return text[:pos].count('\n')+1
def safe_read(p:Path)->str:
    try: return p.read_text(encoding='utf-8',errors='ignore')
    except Exception: return ''
def skip(p:Path)->bool: return any(part in SKIP for part in p.parts)

def run_optional_ts_ast(root:Path)->dict[str,Any]:
    node=shutil.which('node'); script=Path(__file__).with_name('js_ts_ast_extractor.js')
    if not node or not script.exists(): return {'ready':False,'backend':'typescript_compiler_api','reason':'node or js_ts_ast_extractor.js missing'}
    try:
        cp=subprocess.run([node,str(script),str(root)],text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=45,env={'PYTHONDONTWRITEBYTECODE':'1',**dict()})
        data=json.loads(cp.stdout or '{}')
        if cp.returncode!=0 and data.get('ready') is not False: data={'ready':False,'backend':'typescript_compiler_api','reason':cp.stderr[:400]}
        return data
    except Exception as exc: return {'ready':False,'backend':'typescript_compiler_api','reason':str(exc)}

def discover_backend_routes(root:Path)->set[str]:
    routes=set()
    for p in root.rglob('*'):
        if not p.is_file() or skip(p) or p.suffix.lower() not in {'.py','.js','.ts','.tsx','.java','.go','.php','.rb','.rs'}: continue
        t=safe_read(p)
        for rx in [r"\.(?:get|post|put|patch|delete|options|head)\(\s*['\"]([^'\"]+)", r"@(?:Get|Post|Put|Patch|Delete|Request)Mapping\s*\(\s*(?:value\s*=\s*)?['\"]([^'\"]+)"]:
            for m in re.finditer(rx,t,re.I): routes.add(m.group(1))
    return routes

def add_link(out,source,item,template_hint,reason):
    out['candidate_to_manifest_links'].append({'link_id':'JSLINK-'+sha16(json.dumps(item,ensure_ascii=False)+template_hint+reason),'source':source,'template_hint':template_hint,'reason':reason,'manifest_fields':['source_file','source_line','route','method','code_evidence','specialized_evidence.fields'],'item':item,'confirmation_policy':'candidate_only_requires_backend_and_dynamic_evidence'})

def target_with_base(base,path):
    if re.match(r'https?://|//|/',path): return path
    return (base or '').rstrip('/') + '/' + path.lstrip('/')

def load_build_manifest(path:Path,rel:str):
    rows=[]; text=safe_read(path)
    try:
        obj=json.loads(text)
        def walk(o,prefix=''):
            if isinstance(o,dict):
                for k,v in o.items(): walk(v,f'{prefix}/{k}' if prefix else k)
            elif isinstance(o,list):
                for v in o: walk(v,prefix)
            elif isinstance(o,str) and (o.endswith('.js') or '.js?' in o): rows.append({'file':rel,'manifest_key':prefix,'chunk':o,'source':'build_manifest'})
        walk(obj)
    except Exception: pass
    return rows

def analyze_js_text(text:str, rel:str, out:dict[str,Any], backend_routes:set[str], origin:str='file', map_file:str|None=None, source_index:int|None=None):
    bases=[next(x for x in m.groups() if x) for m in BASEURL_RE.finditer(text)]
    instances={}
    for m in AXIOS_INSTANCE_RE.finditer(text):
        name=m.group(1); body=m.group(2); bm=re.search(r"baseURL\s*:\s*[`'\"]([^`'\"]+)",body,re.I); base=bm.group(1) if bm else ''
        instances[name]=base; out['api_wrappers'].append({'file':rel,'name':name,'line':line_of(text,m.start()),'base_urls':[base] if base else [],'wrapper_kind':'axios_instance','origin':origin,'map_file':map_file})
    for m in WRAPPER_DEF_RE.finditer(text):
        out['api_wrappers'].append({'file':rel,'name':m.group(1),'line':line_of(text,m.start()),'base_urls':bases,'wrapper_kind':'function_or_const','origin':origin,'map_file':map_file})
    for m in INTERCEPTOR_RE.finditer(text): out['interceptors'].append({'file':rel,'line':line_of(text,m.start()),'client':m.group(1),'kind':m.group(2),'origin':origin,'map_file':map_file})
    for m in IMPORT_RE.finditer(text): out['imports'].append({'file':rel,'module':m.group(1),'line':line_of(text,m.start()),'origin':origin,'map_file':map_file})
    for m in DYN_IMPORT_RE.finditer(text): out['dynamic_imports'].append({'file':rel,'module':m.group(1),'line':line_of(text,m.start()),'origin':origin,'map_file':map_file}); out['chunk_lineage'].append({'from':rel,'to':m.group(1),'type':'dynamic_import','origin':origin})
    for m in FETCH_RE.finditer(text):
        client=m.group(1); path=m.group(3); method=client.split('.')[-1].upper() if '.' in client and not client.lower().startswith('fetch') else 'UNKNOWN'; base=''
        if '.' in client: base=instances.get(client.split('.')[0], '')
        target=target_with_base(base,path) if base else path
        rec={'file':rel,'line':line_of(text,m.start()),'client':client,'target':target,'method':method,'backend_route_known':path in backend_routes or target in backend_routes,'source':'direct_call','origin':origin,'map_file':map_file,'source_index':source_index}
        out['api_clients'].append(rec); add_link(out,'api_client',rec,'C03-idor-bola','frontend API must map to backend route and object authorization')
    for m in WRAPPER_CALL_RE.finditer(text):
        wrapper,method,_,path=m.groups(); bases2=[]
        if wrapper in instances: bases2=[instances[wrapper]]
        bases2+=bases
        if not bases2: bases2=['']
        for b in bases2:
            rec={'file':rel,'line':line_of(text,m.start()),'wrapper':wrapper,'method':method.upper(),'target':target_with_base(b,path),'source':'wrapper_resolution','backend_route_known':path in backend_routes,'origin':origin,'map_file':map_file,'source_index':source_index}
            out['api_clients'].append(rec); out['wrapper_resolutions'].append(rec); add_link(out,'wrapper_resolution',rec,'C03-idor-bola','wrapper-resolved frontend API requires backend route/guard comparison')
    for m in API_PATH_RE.finditer(text): out['endpoints'].append({'file':rel,'endpoint':m.group(1),'line':line_of(text,m.start()),'origin':origin,'map_file':map_file})
    for m in GQL_RE.finditer(text):
        groups=[g for g in m.groups() if g]; rec={'file':rel,'line':line_of(text,m.start()),'operation_or_fragment':groups[0] if groups else 'graphql_signal','persisted_hash':groups[-1] if groups and re.fullmatch(r'[a-fA-F0-9]{16,64}',groups[-1]) else None,'origin':origin,'map_file':map_file}
        out['graphql'].append(rec); add_link(out,'graphql',rec,'C17-graphql-access-control','GraphQL operation/fragment/persisted query requires resolver auth review')
    regex_map=[(WS_RE,'realtime'),(POSTMSG_RE,'post_message'),(OAUTH_CB_RE,'oauth_callbacks'),(PERM_RE,'frontend_permissions'),(FLAG_RE,'feature_flags'),(ANALYTICS_RE,'analytics_events'),(SCHEMA_RE,'schema_validators'),(SERVICE_WORKER_CACHE_RE,'service_workers')]
    for rgx,key in regex_map:
        for m in rgx.finditer(text): out[key].append({'file':rel,'line':line_of(text,m.start()),'snippet_hash':sha16(text[m.start():m.start()+160]),'origin':origin,'map_file':map_file})
    for m in I18N_RE.finditer(text): out['i18n_keys'].append({'file':rel,'line':line_of(text,m.start()),'key':m.group(1),'origin':origin,'map_file':map_file})
    for m in SENSITIVE_RE.finditer(text):
        rec={'file':rel,'line':line_of(text,m.start()),'kind':m.group(1),'snippet_hash':sha16(text[m.start():m.start()+120]),'redacted':True,'origin':origin,'map_file':map_file}
        out['sensitive_signals'].append(rec); add_link(out,'sensitive_signal',rec,'C22-sensitive-info-disclosure','secret-like value requires real-secret false-positive filter')
    if re.search(r'(ipcRenderer|contextBridge|preload|nativeBridge)',text,re.I): out['electron'].append({'file':rel,'signal':'electron_preload_or_ipc','origin':origin,'map_file':map_file})
    if re.search(r'(chrome\.runtime|browser\.runtime|content_scripts|background)',text,re.I): out['browser_extensions'].append({'file':rel,'signal':'extension_runtime_or_content_script','origin':origin,'map_file':map_file})
    if re.search(r'(wx\.request|my\.request|swan\.request|uni\.request|app\.json|page\.json)',text,re.I): out['miniprogram'].append({'file':rel,'signal':'miniprogram_api','origin':origin,'map_file':map_file})
    if re.search(r'(msw|mock|storybook|cypress|playwright|fixture|e2e)',rel,re.I): out['mock_e2e_sources'].append({'file':rel,'signal':'mock_storybook_e2e_flow','origin':origin,'map_file':map_file})

def parse_sourcemap_content(smobj:dict[str,Any], rel_map:str, out:dict[str,Any], backend_routes:set[str]):
    sources=smobj.get('sources') or []; contents=smobj.get('sourcesContent') or []
    for i,src in enumerate(sources[:500]):
        content=contents[i] if i < len(contents) else None
        rec={'map_file':rel_map,'source':src,'source_index':i,'has_sourcesContent':bool(content),'content_hash':sha16(content or '') if content else None}
        out['source_map_originals'].append(rec)
        if content:
            synthetic=f'{rel_map}::{src}'
            analyze_js_text(content, synthetic, out, backend_routes, origin='sourcemap_sourcesContent', map_file=rel_map, source_index=i)
            out['source_map_reentry'].append({'map_file':rel_map,'source':src,'source_index':i,'reentered_extractors':['api_clients','wrapper_resolutions','graphql','sensitive_signals','feature_flags','i18n_keys'],'content_hash':sha16(content)})

def analyze_file(root:Path,p:Path,backend_routes:set[str],out:dict[str,Any]):
    rel=str(p.relative_to(root)); text=safe_read(p); suf=p.suffix.lower(); out['assets'].append({'file':rel,'suffix':suf,'sha256':sha_file(p),'size':len(text)})
    if suf in HTML_EXT:
        for m in HTML_SCRIPT_RE.finditer(text):
            src=m.group(1); rec={'file':rel,'src':src,'line':line_of(text,m.start())}; (out['cdn_js_references'] if src.startswith(('http://','https://','//')) else out['html_js_references']).append(rec)
        for m in HTML_LINK_RE.finditer(text): out['preload_prefetch'].append({'file':rel,'href':m.group(1),'line':line_of(text,m.start())})
        return
    if p.name in {'build-manifest.json','manifest.json','asset-manifest.json','vite.manifest.json'} or rel.endswith('.next/build-manifest.json'): out['chunks'].extend(load_build_manifest(p,rel))
    if suf not in JS_EXT: return
    analyze_js_text(text,rel,out,backend_routes,origin='file')
    for m in SOURCE_MAP_RE.finditer(text):
        sm=m.group(1).strip(); sm_path=None; smobj=None
        if sm.startswith('data:'):
            try:
                b64=sm.split(',',1)[1]; smobj=json.loads(base64.b64decode(b64).decode('utf-8','ignore')); sm_path=rel+'#inline-source-map'
            except Exception as exc: smobj={'_parse_error':str(exc)}; sm_path=rel+'#inline-source-map'
        elif not sm.startswith(('http://','https://')):
            path=(p.parent/sm).resolve(); sm_path=str(path.relative_to(root)) if path.exists() else str(path)
            if path.exists():
                try: smobj=json.loads(safe_read(path))
                except Exception as exc: smobj={'_parse_error':str(exc)}
        rec={'file':rel,'sourceMappingURL':sm,'line':line_of(text,m.start()),'map_exists':bool(smobj and not smobj.get('_parse_error')),'map_file':sm_path}
        if smobj and not smobj.get('_parse_error'):
            rec['sources']=(smobj.get('sources') or [])[:200]; rec['sourcesContent_count']=len(smobj.get('sourcesContent') or []); rec['original_mapping_policy']='sourcesContent is re-entered into extractor; generated line/column maps remain advisory unless external decoder is installed'
            parse_sourcemap_content(smobj, sm_path or sm, out, backend_routes)
        elif smobj and smobj.get('_parse_error'): rec['parse_error']=smobj['_parse_error']
        out['source_maps'].append(rec); out['chunk_lineage'].append({'from':rel,'to':sm,'type':'source_map'})

def extract(root:Path)->dict[str,Any]:
    root=root.resolve(); backend_routes=discover_backend_routes(root)
    keys=['assets','html_js_references','cdn_js_references','preload_prefetch','chunks','source_maps','source_map_originals','source_map_reentry','imports','dynamic_imports','chunk_lineage','api_wrappers','interceptors','wrapper_resolutions','api_clients','endpoints','graphql','realtime','post_message','oauth_callbacks','frontend_permissions','feature_flags','i18n_keys','analytics_events','schema_validators','service_workers','electron','browser_extensions','miniprogram','mock_e2e_sources','sensitive_signals','candidate_to_manifest_links']
    out={k:[] for k in keys}; out.update({'schema_version':'js_audit_graph_v4.1','legacy_schema_compatibility':'js_audit_graph_v4.1','root':str(root),'non_destructive':True,'does_not_confirm':True,'capabilities':{'typescript_ast_optional':True,'axios_instance_resolution':True,'interceptor_detection':True,'graphql_persisted_query_detection':True,'wrapper_resolution':True,'chunk_lineage':True,'source_map_sourcesContent_reentry':True,'frontend_backend_mapping_inputs':True},'backend_routes_seen':sorted(backend_routes)})
    for p in sorted(root.rglob('*')):
        if p.is_file() and not skip(p) and (p.suffix.lower() in JS_EXT|HTML_EXT or p.name in {'build-manifest.json','manifest.json','asset-manifest.json','vite.manifest.json'}): analyze_file(root,p,backend_routes,out)
    ts=run_optional_ts_ast(root); out['typescript_ast_backend']=ts
    if ts.get('ready'):
        for src,dst in [('imports','imports'),('exports','exports'),('dynamic_imports','dynamic_imports'),('api_clients','api_clients'),('graphql','graphql'),('post_message','post_message'),('realtime','realtime')]: out.setdefault(dst,[]).extend(ts.get(src) or [])
    for k in keys:
        seen=set(); new=[]
        for x in out.get(k,[]):
            s=json.dumps(x,sort_keys=True,ensure_ascii=False)
            if s not in seen: seen.add(s); new.append(x)
        out[k]=new

    # v4.1 semantic post-processing: symbol graph, sourcemap spans, wrapper/interceptor/persisted query dataflow.
    symbol_nodes=[]; symbol_edges=[]
    for imp in out.get('imports',[]):
        symbol_nodes.append({'id':'import:'+sha16(json.dumps(imp,ensure_ascii=False)),'type':'import','file':imp.get('file'),'label':imp.get('module'),'origin':imp.get('origin'),'source_line':imp.get('line')})
    for api in out.get('api_clients',[]):
        nid='api:'+sha16(json.dumps(api,ensure_ascii=False)); symbol_nodes.append({'id':nid,'type':'api_client','file':api.get('file'),'label':api.get('target'),'source_line':api.get('line'),'origin':api.get('origin')})
        if api.get('wrapper'):
            wid='wrapper:'+sha16(api.get('wrapper','')+api.get('file','')); symbol_nodes.append({'id':wid,'type':'wrapper','file':api.get('file'),'label':api.get('wrapper'),'source_line':api.get('line')}); symbol_edges.append({'from':wid,'to':nid,'type':'resolves_to','dataflow':'wrapper_to_request','requires_backend_guard_check':True})
    for intr in out.get('interceptors',[]):
        iid='interceptor:'+sha16(json.dumps(intr,ensure_ascii=False)); symbol_nodes.append({'id':iid,'type':'interceptor','file':intr.get('file'),'label':intr.get('client'),'source_line':intr.get('line')})
        for api in out.get('api_clients',[]):
            if api.get('file')==intr.get('file'):
                symbol_edges.append({'from':iid,'to':'api:'+sha16(json.dumps(api,ensure_ascii=False)),'type':'influences','dataflow':'interceptor_to_request','requires_header_token_review':True})
    out['ast_symbol_graph']={'schema_version':'js_ast_symbol_graph_v4.1','nodes':symbol_nodes,'edges':symbol_edges,'claim_policy':'AST-lite graph unless TypeScript compiler API backend is runtime-ready'}
    spans=[]
    for sm in out.get('source_map_originals',[]):
        spans.append({'map_file':sm.get('map_file'),'original_source':sm.get('source'),'source_index':sm.get('source_index'),'generated_line':None,'generated_column':None,'original_line':1 if sm.get('has_sourcesContent') else None,'original_column':0 if sm.get('has_sourcesContent') else None,'mapping_precision':'sourcesContent_reentry_without_mappings_decoder' if sm.get('has_sourcesContent') else 'metadata_only','content_hash':sm.get('content_hash')})
    out['sourcemap_original_spans']=spans
    pq=[]
    for g in out.get('graphql',[]):
        if g.get('persisted_hash'):
            pq.append({'hash':g.get('persisted_hash'),'operation_or_fragment':g.get('operation_or_fragment'),'file':g.get('file'),'line':g.get('line'),'resolver_mapping_required':True,'authz_template_hint':'C17-graphql-access-control'})
    out['persisted_query_dataflow']=pq
    out['wrapper_interceptor_dataflow']={'schema_version':'wrapper_interceptor_dataflow_v4.1','wrapper_resolutions':out.get('wrapper_resolutions',[]),'interceptors':out.get('interceptors',[]),'edges':symbol_edges}

    out['summary']={'asset_count':len(out['assets']),'api_client_count':len(out['api_clients']),'wrapper_resolution_count':len(out['wrapper_resolutions']),'source_map_count':len(out['source_maps']),'source_map_reentry_count':len(out['source_map_reentry']),'ast_symbol_nodes':len(out.get('ast_symbol_graph',{}).get('nodes',[])),'sourcemap_original_spans':len(out.get('sourcemap_original_spans',[])),'candidate_link_count':len(out['candidate_to_manifest_links']),'interceptor_count':len(out['interceptors'])}
    return out

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('root'); ap.add_argument('-o','--output')
    args=ap.parse_args(); data=extract(Path(args.root)); text=json.dumps(data,ensure_ascii=False,indent=2)
    if args.output: Path(args.output).parent.mkdir(parents=True,exist_ok=True); Path(args.output).write_text(text+'\n',encoding='utf-8')
    else: print(text)
if __name__=='__main__': main()

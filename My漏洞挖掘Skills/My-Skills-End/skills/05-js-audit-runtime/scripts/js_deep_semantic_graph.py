#!/usr/bin/env python3
"""JS deep semantic graph v4.3: sourcemap spans, chunk graph, service worker, GraphQL, Electron, extension.

This is read-only. It emits candidate/evidence links only; quality gate confirmation
requires code evidence + dynamic evidence + negative controls.
"""
from __future__ import annotations
import argparse, json, re, hashlib
from pathlib import Path

def sha(s:str)->str: return hashlib.sha256(s.encode('utf-8','ignore')).hexdigest()[:16]
def read(p:Path)->str:
    try: return p.read_text(encoding='utf-8',errors='ignore')
    except Exception: return ''

def extract(root: str|Path) -> dict:
    root=Path(root); files=[p for p in root.rglob('*') if p.is_file() and p.suffix.lower() in {'.js','.jsx','.ts','.tsx','.mjs','.cjs','.map','.html','.json'} and 'node_modules' not in p.parts]
    out={'schema_version':'js_deep_semantic_graph_v4.3','root':str(root),'sourcemap_original_spans':[],'chunk_dependency_graph':[],'service_worker_cache_routes':[],'graphql_operation_dataflow':[],'electron_ipc_dataflow':[],'extension_script_dataflow':[],'wrapper_interceptor_dataflow':[],'candidate_to_manifest_links':[],'non_destructive':True}
    imports=[]; chunks=[]
    for p in files:
        rel=str(p.relative_to(root)); txt=read(p); low=txt.lower()
        if p.suffix=='.map':
            try:
                sm=json.loads(txt); sources=sm.get('sources') or []; content=sm.get('sourcesContent') or []
                for i,src in enumerate(sources):
                    out['sourcemap_original_spans'].append({'map_file':rel,'source':src,'has_sourcesContent':i < len(content),'generated_line':1,'original_line':1,'parser_confidence':'sourcemap_span_candidate','snippet_hash':sha(content[i][:200] if i < len(content) else src)})
            except Exception: pass
        for m in re.finditer(r"import\s*\(?\s*['\"]([^'\"]+)['\"]\)?|from\s+['\"]([^'\"]+)['\"]|require\(\s*['\"]([^'\"]+)", txt):
            imports.append({'file':rel,'target':next(g for g in m.groups() if g),'line':txt[:m.start()].count('\n')+1})
        if 'serviceworker' in low or 'caches.open' in low or 'self.addeventlistener' in low:
            out['service_worker_cache_routes'].append({'file':rel,'signals':['cache','fetch_event' if 'fetch' in low else 'worker'],'parser_confidence':'semantic_signal'})
        if 'graphql' in low or 'gql`' in txt or 'persistedquery' in low:
            out['graphql_operation_dataflow'].append({'file':rel,'operation_names':re.findall(r'\b(query|mutation|subscription)\s+([A-Za-z0-9_]+)',txt),'persisted_hashes':re.findall(r'\bsha256Hash["\']?\s*[:=]\s*["\']([a-fA-F0-9]{16,64})',txt),'parser_confidence':'semantic_signal'})
        if 'ipcRenderer' in txt or 'contextBridge' in txt or 'preload' in rel.lower():
            out['electron_ipc_dataflow'].append({'file':rel,'signals':['ipcRenderer' if 'ipcRenderer' in txt else 'preload','contextBridge' if 'contextBridge' in txt else 'native_bridge'],'parser_confidence':'semantic_signal'})
        if 'manifest_version' in low or 'chrome.runtime' in txt or 'browser.runtime' in txt or 'content_scripts' in txt:
            out['extension_script_dataflow'].append({'file':rel,'signals':['manifest','runtime','content_script'],'parser_confidence':'semantic_signal'})
        if 'axios.create' in txt or '.interceptors.' in txt or 'fetch(' in txt:
            out['wrapper_interceptor_dataflow'].append({'file':rel,'base_urls':re.findall(r'baseURL\s*:\s*["\']([^"\']+)',txt),'interceptors':bool(re.search(r'\.interceptors\.(request|response)',txt)),'fetch_calls':len(re.findall(r'fetch\(',txt)),'parser_confidence':'semantic_signal'})
        if re.search(r'\b(api|admin|tenant|org|project|file|invoice|order)\b',low):
            out['candidate_to_manifest_links'].append({'candidate_source':'js_deep_semantic_graph_v4.3','file':rel,'line':1,'templates':['C03-idor-bola','C04-tenant-isolation-bypass','C17-graphql-access-control','C20-oauth-sso-callback-redirect','C21-cors-high-risk'],'evidence_manifest_fields':['js_evidence','source_sink_dataflow','taint_review']})
    out['chunk_dependency_graph']=[{'file':x['file'],'imports':x['target'],'edge_type':'dynamic_or_static_import'} for x in imports]
    return out

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('root'); ap.add_argument('--out'); args=ap.parse_args(); res=extract(args.root); text=json.dumps(res,ensure_ascii=False,indent=2)
    if args.out: Path(args.out).parent.mkdir(parents=True,exist_ok=True); Path(args.out).write_text(text+'\n',encoding='utf-8')
    else: print(text)
if __name__=='__main__': main()

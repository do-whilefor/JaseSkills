#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, re, shutil, subprocess, hashlib
from pathlib import Path
from typing import Any
JS_SUFFIX={'.js','.mjs','.cjs','.jsx','.ts','.tsx'}
ROUTE_RE=re.compile(r"(?:path|route|href|to)\s*[:=]\s*[`'\"](/[^`'\"]{0,240})[`'\"]|[`'\"](/(?:admin|internal|debug|tenant|org|payment|refund|api|graphql|vnc|app)[^`'\"]{0,240})[`'\"]")
FETCH_RE=re.compile(r"(?P<callee>fetch|axios\.(?:get|post|put|patch|delete)|[A-Za-z0-9_$.]*(?:request|get|post|put|patch|delete))\s*\((?P<args>[^;]{0,1200})", re.S)
STR_RE=re.compile(r"[`'\"]([^`'\"]{1,500})[`'\"]")
PARAM_KEY_RE=re.compile(r"\b([A-Za-z_$][\w$]*)\s*:")

def line_no(text:str, idx:int)->int: return text.count('\n',0,idx)+1

def rel(p:Path, root:Path)->str:
    try: return p.resolve().relative_to(root.resolve()).as_posix()
    except Exception: return p.as_posix()

def sha(p:Path)->str:
    h=hashlib.sha256(); h.update(p.read_bytes()); return h.hexdigest()

def read(p:Path)->str:
    for enc in ('utf-8','utf-8-sig','latin-1'):
        try: return p.read_text(encoding=enc, errors='replace')
        except Exception: pass
    return p.read_text(errors='replace')

def node_backend(file:Path)->dict[str,Any]:
    node=shutil.which('node')
    script=Path(__file__).resolve().parent/'backends/js/typescript_extract.mjs'
    if not node: return {'backend':'typescript','status':'missing','error':'node not found','file':str(file)}
    if not script.exists(): return {'backend':'typescript','status':'missing','error':'typescript_extract.mjs not found','file':str(file)}
    try:
        proc=subprocess.run([node, str(script), str(file)], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
    except subprocess.TimeoutExpired as e:
        out=(e.stdout or '') if isinstance(e.stdout, str) else ((e.stdout or b'').decode(errors='replace') if e.stdout else '')
        err=(e.stderr or '') if isinstance(e.stderr, str) else ((e.stderr or b'').decode(errors='replace') if e.stderr else '')
        return {'backend':'typescript','status':'error','file':str(file),'returncode':124,'stderr':(err+'\nTIMEOUT').strip()[:2000],'stdout':out[:500]}
    except Exception as e:
        return {'backend':'typescript','status':'error','file':str(file),'returncode':127,'stderr':str(e)[:2000]}
    if proc.returncode!=0:
        return {'backend':'typescript','status':'error','file':str(file),'returncode':proc.returncode,'stderr':proc.stderr[:2000]}
    try:
        data=json.loads(proc.stdout); data['status']=data.get('status','ready'); return data
    except Exception as e:
        return {'backend':'typescript','status':'error','file':str(file),'stderr':f'bad json: {e}','stdout':proc.stdout[:500]}

def method_from_callee(callee:str,args:str)->str:
    m=re.search(r'\.(get|post|put|patch|delete)$', callee, re.I)
    if m: return m.group(1).upper()
    m=re.search(r"method\s*:\s*[`'\"]([A-Z]+)[`'\"]", args, re.I)
    if m: return m.group(1).upper()
    return 'GET' if callee.endswith('.get') or callee=='fetch' else 'UNKNOWN'

def add_node(nodes, kind, file, line, label, **kw):
    nid=f"{kind}:{file}:{line}:{len(nodes)+1}"
    obj={'id':nid,'kind':kind,'file':file,'line':line,'label':label, **kw}
    nodes.append(obj); return nid

def regex_supplement(p:Path, root:Path):
    text=read(p); file=rel(p,root); nodes=[]; edges=[]; evidence=[]
    for m in ROUTE_RE.finditer(text):
        val=(m.group(1) or m.group(2) or '').strip()
        if val:
            evidence.append({'kind':'route','value':val,'file':file,'line':line_no(text,m.start()),'ast_node':'regex_supplement_literal','provenance':'regex_supplement_not_ast'})
            add_node(nodes,'route',file,line_no(text,m.start()),val, provenance='regex_supplement')
    for m in FETCH_RE.finditer(text):
        args=m.group('args'); ss=STR_RE.search(args); endpoint=ss.group(1) if ss else ''
        if endpoint and (endpoint.startswith('/') or endpoint.startswith('http')):
            params=sorted(set(PARAM_KEY_RE.findall(args)))[:80]
            method=method_from_callee(m.group('callee'), args)
            evidence.append({'kind':'api_call','endpoint':endpoint,'method':method,'params':params,'file':file,'line':line_no(text,m.start()),'callee':m.group('callee'),'ast_node':'regex_supplement_call','provenance':'regex_supplement_not_ast'})
            add_node(nodes,'api',file,line_no(text,m.start()),endpoint, method=method, params=params, callee=m.group('callee'), provenance='regex_supplement')
    return nodes,edges,evidence

def extract_file(p:Path, root:Path):
    file=rel(p,root); nodes=[]; edges=[]; evidence=[]; call_graph=[]; dataflow=[]; source_sink=[]
    backend=node_backend(p)
    if backend.get('status')=='ready':
        for r in backend.get('routes',[]):
            evidence.append({'kind':'route','value':r.get('value'),'file':file,'line':r.get('line'),'ast_node':'StringLiteral','provenance':'typescript_ast'})
            add_node(nodes,'route',file,r.get('line'),r.get('value'), provenance='typescript_ast')
        for e in backend.get('endpoints',[]):
            evidence.append({'kind':'api_call','endpoint':e.get('value'),'method':e.get('method'),'file':file,'line':e.get('line'),'callee':e.get('callee'),'ast_node':'CallExpression_or_StringLiteral','provenance':'typescript_ast'})
            api_id=add_node(nodes,'api',file,e.get('line'),e.get('value'), method=e.get('method'), callee=e.get('callee'), provenance='typescript_ast')
            for rnode in [n for n in nodes if n['kind']=='route' and n['file']==file]:
                edges.append({'from':rnode['id'],'to':api_id,'kind':'same_file_route_api_candidate','status':'candidate','provenance':'typescript_ast'})
        for g in backend.get('graphql',[]):
            evidence.append({'kind':'graphql','value':g.get('text'),'file':file,'line':g.get('line'),'ast_node':'TaggedTemplate_or_Template','provenance':'typescript_ast'})
            add_node(nodes,'graphql',file,g.get('line'),'graphql operation', provenance='typescript_ast')
        for w in backend.get('websocket',[]):
            evidence.append({'kind':'websocket','url':w.get('url'),'file':file,'line':w.get('line'),'ast_node':'NewExpression','provenance':'typescript_ast'})
            add_node(nodes,'websocket',file,w.get('line'),w.get('url'), provenance='typescript_ast')
        for pm in backend.get('postmessage',[]):
            evidence.append({'kind':'postmessage','value':pm.get('target'),'file':file,'line':pm.get('line'),'ast_node':'CallExpression','provenance':'typescript_ast'})
            add_node(nodes,'postmessage',file,pm.get('line'),pm.get('kind'), provenance='typescript_ast')
        for sig in backend.get('authzTenantSignals',[]):
            evidence.append({'kind':'authz_or_tenant_signal','value':sig.get('value'),'file':file,'line':sig.get('line'),'ast_node':sig.get('ast_kind'),'provenance':'typescript_ast'})
        for s in backend.get('sources',[]): evidence.append({'kind':'taint_source','value':s.get('value'),'file':file,'line':s.get('line'),'ast_node':s.get('ast_kind'),'provenance':'typescript_ast'})
        for s in backend.get('sinks',[]): evidence.append({'kind':'sink','value':s.get('value'),'file':file,'line':s.get('line'),'ast_node':s.get('ast_kind'),'provenance':'typescript_ast'})
        call_graph=[{'file':file, **x} for x in backend.get('callGraphEdges',[])]
        dataflow=[{'file':file, **x} for x in backend.get('dataflowCandidates',[])]
        source_sink=[{'file':file, **x} for x in backend.get('sourceSinkPaths',[])]
        for x in call_graph: edges.append({'from':x.get('from'),'to':x.get('to'),'kind':'ast_call_graph_edge','line':x.get('line'),'status':x.get('status')})
        for x in source_sink: edges.append({'from':f"source:{file}:{x.get('source_line')}",'to':f"sink:{file}:{x.get('sink_line')}",'kind':'ast_source_sink_candidate','status':'candidate','reason':x.get('reason')})
    # Supplemental regex is separate and named; it cannot become AST evidence.
    rn,re_,rv=regex_supplement(p,root); nodes+=rn; edges+=re_; evidence+=rv
    return {'file':file,'sha256':sha(p),'nodes':nodes,'edges':edges,'evidence':evidence,'backend':backend,'call_graph':call_graph,'dataflow_candidates':dataflow,'source_sink_paths':source_sink}

def main():
    ap=argparse.ArgumentParser(description='Build AST-default JS semantic graph: Route→Component→Action→API→Params→AuthZ/Tenant→Sink. Static-only output never confirms vulnerabilities.')
    ap.add_argument('--root', required=True)
    ap.add_argument('--ledger')
    ap.add_argument('--out', default='reports/js-top-tier')
    args=ap.parse_args(); root=Path(args.root).resolve(); out=Path(args.out); out.mkdir(parents=True, exist_ok=True)
    files=[]
    if args.ledger and Path(args.ledger).exists():
        led=json.loads(Path(args.ledger).read_text(encoding='utf-8'))
        ledger_root=Path(led.get('root', root)).resolve()
        root=ledger_root if ledger_root.exists() else root
        for a in led.get('assets',[]):
            if a.get('kind') in {'javascript','service_worker'}:
                asset_path=str(a.get('path') or '')
                if not asset_path:
                    continue
                p=root/asset_path
                if p.exists(): files.append(p)
    if not files:
        files=[p for p in root.rglob('*') if p.suffix.lower() in JS_SUFFIX and 'node_modules' not in p.parts]
    all_nodes=[]; all_edges=[]; all_ev=[]; backend=[]; by_file=[]; all_calls=[]; all_dfs=[]; all_ss=[]
    for p in sorted(set(files)):
        r=extract_file(p,root); by_file.append(r); all_nodes+=r['nodes']; all_edges+=r['edges']; all_ev+=r['evidence']; backend.append(r.get('backend')); all_calls+=r.get('call_graph',[]); all_dfs+=r.get('dataflow_candidates',[]); all_ss+=r.get('source_sink_paths',[])
    ready=[b for b in backend if isinstance(b,dict) and b.get('status')=='ready']
    errors=[b for b in backend if isinstance(b,dict) and b.get('status')!='ready']
    graph={'schema_version':'js-semantic-graph/v1','semantic_status':'ready' if ready and not errors else ('partial' if ready else 'candidate-only'),'ast_backend_policy':{'default_backend':'typescript_compiler_api','regex_supplemental_is_not_ast':True,'fallback_promotion_allowed':False},'static_only':True,'no_confirmed_without_runtime':True,'coverage':{'files':len(files),'nodes':len(all_nodes),'edges':len(all_edges),'evidence_items':len(all_ev),'typescript_backend_ready_files':len(ready),'typescript_backend_error_files':len(errors),'call_graph_edges':len(all_calls),'dataflow_candidates':len(all_dfs),'source_sink_paths':len(all_ss)},'nodes':all_nodes,'edges':all_edges,'evidence':all_ev,'call_graph':all_calls,'dataflow_candidates':all_dfs,'source_sink_paths':all_ss,'backend_results':backend,'files':by_file,'required_promotion_evidence':['scope','request','response','HAR','trace','screenshot_or_dom_snapshot','role_tenant_mapping for authz/tenant findings','backend positive/negative/blocked tests','runtime detector binding for GraphQL/WebSocket/postMessage']}
    (out/'js_semantic_graph.json').write_text(json.dumps(graph, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'ok':True,'out':str(out/'js_semantic_graph.json'),'semantic_status':graph['semantic_status'],'nodes':len(all_nodes),'edges':len(all_edges),'evidence':len(all_ev),'call_graph_edges':len(all_calls),'source_sink_paths':len(all_ss)}, ensure_ascii=False, indent=2))
if __name__=='__main__': main()

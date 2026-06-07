#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from collectors.route_collector import collect as collect_routes
from collectors.hidden_parameter_collector import collect as collect_params
from common.scope_guard import load_scope, iter_scoped_files, read_text_scoped
from analyzers.lang import parse_source

SINKS={
 'command_execution':r'\b(exec|spawn|system|shell_exec|ProcessBuilder|Runtime\.getRuntime\(\)\.exec)\b',
 'sql_or_nosql_query':r'\b(raw|queryRaw|executeRaw|whereRaw|createNativeQuery|\$where)\b',
 'file_read_write':r'\b(readFile|writeFile|sendFile|open\(|File\.read|Files\.read|move_uploaded_file)\b',
 'ssrf_http_client':r'\b(fetch|axios|requests\.get|http\.Get|RestTemplate|open-uri)\b',
 'template_render':r'\b(render_template_string|from_string|Template\(|Twig|Velocity|Freemarker)\b',
 'redirect':r'\bredirect\(|res\.redirect|RedirectResponse\b',
 'deserialization':r'\b(pickle\.loads|yaml\.load|ObjectInputStream|unserialize|Marshal\.load)\b',
 'eval_vm':r'\b(eval\(|new Function|vm\.runIn)\b'
}
SOURCE_PATTERNS={
 'http_parameter': r'\b(req\.body|req\.query|request\.args|request\.form|params\.|PathVariable|RequestParam|$_GET|$_POST|c\.Param|r\.URL\.Query)\b',
 'tenant_input': r'\b(tenantId|orgId|workspaceId|x-tenant|X-Tenant)\b',
 'role_input': r'\b(role|isAdmin|permission|permissions)\b',
}
CALL_NAME_CLEAN=re.compile(r'[^A-Za-z0-9_.$:#]')

def gid(prefix,*parts): return prefix+'-'+hashlib.sha256(':'.join(map(str,parts)).encode()).hexdigest()[:14]
def line(t,p): return t[:p].count('\n')+1

def _node(nodes, nid, typ, label, data):
    if nid not in nodes:
        nodes[nid]={'id':nid,'type':typ,'label':label,'data':data}
    return nodes[nid]

def _edge(edges, src, dst, typ, data=None):
    edges.append({'from':src,'to':dst,'type':typ,'data':data or {}})

def _norm_call(name: str) -> str:
    name=(name or '').split('.')[-1].split('::')[-1]
    return CALL_NAME_CLEAN.sub('', name)

def _function_for_line(functions, file, ln):
    candidates=[f for f in functions if f.get('file')==file and int(f.get('line') or 0) <= ln and (not f.get('end_line') or ln <= int(f.get('end_line') or ln))]
    if not candidates:
        return None
    candidates.sort(key=lambda f: int(f.get('line') or 0), reverse=True)
    return candidates[0]

def build(root, routes_file=None, params_file=None, scope_file=None):
    root=Path(root).resolve(); scope=load_scope(root,scope_file)
    routes=json.loads(Path(routes_file).read_text()) if routes_file else collect_routes(root,scope_file)
    params=json.loads(Path(params_file).read_text()) if params_file else collect_params(root,scope_file)
    nodes={}; edges=[]; parser_status=[]; functions=[]; calls=[]

    # Route/handler/auth/param source layer
    for r in routes.get('routes',[]):
        nid=r['route_id']; _node(nodes,nid,'route',f"{r.get('method')} {r.get('path')}",r)
        hid=gid('handler',r.get('file'),r.get('handler'),r.get('line'))
        _node(nodes,hid,'handler',r.get('handler') or 'unknown',{'file':r.get('file'),'line':r.get('line'),'handler':r.get('handler')})
        _edge(edges,nid,hid,'ROUTE_TO_HANDLER')
        if r.get('authn')!='unknown':
            aid=gid('authn',nid); _node(nodes,aid,'authn',r.get('authn'),{}); _edge(edges,hid,aid,'HANDLER_TO_AUTHN')
        if r.get('authz')!='unknown':
            zid=gid('authz',nid); _node(nodes,zid,'authz',r.get('authz'),{}); _edge(edges,hid,zid,'HANDLER_TO_AUTHZ')
    for prm in params.get('parameters',[]):
        pid=prm['parameter_id']; _node(nodes,pid,'source',prm['name'],{**prm,'source_kind':'declared_parameter'})
        for r in routes.get('routes',[]):
            if r.get('file') == prm.get('file'):
                _edge(edges,r['route_id'],pid,'ROUTE_TO_PARAMETER')
                _edge(edges,pid,gid('handler',r.get('file'),r.get('handler'),r.get('line')),'PARAMETER_TO_HANDLER')

    # Parse each source file with language adapters.
    source_files=[]
    for p in iter_scoped_files(root,scope):
        if p.suffix.lower() not in {'.py','.js','.jsx','.ts','.tsx','.java','.php','.rb','.go','.rs'}: continue
        text,_=read_text_scoped(p,root,scope,limit=1_000_000); rel=str(p.relative_to(root)); source_files.append(rel)
        fid=gid('file',rel); _node(nodes,fid,'file',rel,{'file':rel})
        ast=parse_source(p,text); parser_status.append({'file':rel,'status':ast.get('status'),'parser':ast.get('parser'),'errors':ast.get('errors',[])})
        for cls in ast.get('classes',[]) or []:
            cid=gid('class',rel,cls.get('name'),cls.get('line')); _node(nodes,cid,'class',cls.get('name') or '<class>',{'file':rel,**cls}); _edge(edges,fid,cid,'FILE_TO_CLASS')
        for fn in ast.get('functions',[]) or []:
            name=fn.get('name') or '<anonymous>'; fnid=gid('function',rel,name,fn.get('line'))
            rec={'id':fnid,'name':name,'file':rel,'line':fn.get('line'),'end_line':fn.get('end_line'),'parser':ast.get('parser')}
            functions.append(rec); _node(nodes,fnid,'function',name,rec); _edge(edges,fid,fnid,'FILE_TO_FUNCTION')
            for r in routes.get('routes',[]):
                if r.get('file')==rel and (r.get('handler')==name or str(r.get('handler') or '').endswith('.'+name)):
                    _edge(edges,gid('handler',r.get('file'),r.get('handler'),r.get('line')),fnid,'HANDLER_TO_FUNCTION')
        for call in ast.get('calls',[]) or []:
            cname=call.get('name') or '<call>'; cid=gid('call',rel,cname,call.get('line'),len(calls))
            rec={'id':cid,'name':cname,'normalized_name':_norm_call(cname),'file':rel,'line':call.get('line'),'parser':ast.get('parser')}
            calls.append(rec); _node(nodes,cid,'call',cname,rec); _edge(edges,fid,cid,'FILE_TO_CALL')
        for imp in ast.get('imports',[]) or []:
            iid=gid('import',rel,imp.get('name'),imp.get('line')); _node(nodes,iid,'import',imp.get('name') or '<import>',{'file':rel,**imp}); _edge(edges,fid,iid,'FILE_TO_IMPORT')
        for skind,rx in SOURCE_PATTERNS.items():
            for m in re.finditer(rx,text,re.I):
                sid=gid('source',skind,rel,m.start()); _node(nodes,sid,'source',skind,{'file':rel,'line':line(text,m.start()),'match':m.group(0),'source_kind':skind})
                fn=_function_for_line(functions,rel,line(text,m.start()))
                if fn: _edge(edges,sid,fn['id'],'SOURCE_TO_FUNCTION')
        for kind,rx in SINKS.items():
            for m in re.finditer(rx,text,re.I):
                ln=line(text,m.start()); sid=gid('sink',kind,rel,m.start()); _node(nodes,sid,'sink',kind,{'file':rel,'line':ln,'match':m.group(0)})
                fn=_function_for_line(functions,rel,ln)
                if fn: _edge(edges,fn['id'],sid,'FUNCTION_TO_SINK')
                _edge(edges,fid,sid,'FILE_TO_SINK')
                for r in routes.get('routes',[]):
                    if r.get('file')==rel:
                        _edge(edges,gid('handler',r.get('file'),r.get('handler'),r.get('line')),sid,'HANDLER_TO_SINK')

    # Resolve calls to functions across files by simple name, creating cross-file dataflow edges.
    by_name={}
    for fn in functions:
        by_name.setdefault(_norm_call(fn.get('name','')),[]).append(fn)
    for c in calls:
        cid=c['id']; caller=_function_for_line(functions,c['file'],int(c.get('line') or 0))
        if caller:
            _edge(edges,caller['id'],cid,'FUNCTION_TO_CALL')
        for target in by_name.get(c.get('normalized_name'),[]):
            if target['id'] != (caller or {}).get('id'):
                _edge(edges,cid,target['id'],'CALL_TO_FUNCTION',{'cross_file': target.get('file') != c.get('file')})

    # Backward compatibility: explicit handler to sink edge remains, but function/call graph enables cross-file paths.
    out_nodes=list(nodes.values())
    return {'schema_version':'security-graph-v3','root':str(root),'nodes':out_nodes,'edges':edges,'parser_status':parser_status,'counts':{'nodes':len(out_nodes),'edges':len(edges),'routes':len(routes.get('routes',[])),'functions':len(functions),'calls':len(calls),'files':len(source_files)},'policy':'AST adapters must report parser status; regex fallback is not accepted as AST. Cross-file CALL_TO_FUNCTION edges are marked.'}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('root'); ap.add_argument('--routes'); ap.add_argument('--params'); ap.add_argument('--scope-file'); ap.add_argument('--out',required=True)
    ns=ap.parse_args(); data=build(ns.root,ns.routes,ns.params,ns.scope_file)
    Path(ns.out).parent.mkdir(parents=True,exist_ok=True); Path(ns.out).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(data['counts'],ensure_ascii=False))
if __name__=='__main__': main()

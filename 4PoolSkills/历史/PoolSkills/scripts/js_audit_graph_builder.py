#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, hashlib, re
from pathlib import Path

def h(s): return hashlib.sha256(s.encode()).hexdigest()[:16]
def normalize(p):
    if not p: return ''
    return re.sub(r'https?://[^/]+','',p).split('?')[0].rstrip('/') or '/'

def build(js_file, routes_file, out_file):
    js=json.loads(Path(js_file).read_text(encoding='utf-8'))
    routes=json.loads(Path(routes_file).read_text(encoding='utf-8')) if routes_file and Path(routes_file).exists() else {'routes':[]}
    nodes=[]; edges=[]; route_index=[]
    for r in routes.get('routes',[]):
        rn='route-'+h(r.get('method','')+r.get('path','')+r.get('file',''))
        nodes.append({'id':rn,'type':'backend_route','method':r.get('method'),'url':r.get('path'),'file':r.get('file'),'line':r.get('line'),'authn_hint':r.get('authn_hint'),'authz_hint':r.get('authz_hint')})
        route_index.append((rn, normalize(r.get('path')), r))
    for ep in js.get('endpoints',[]):
        eid=ep.get('id') or 'api-'+h(ep.get('file','')+ep.get('path',''))
        url=normalize(ep.get('path'))
        nodes.append({'id':eid,'type':'frontend_api','url':ep.get('path'),'file':ep.get('file'),'line':ep.get('line'),'evidence':ep.get('evidence'),'requires_backend_correlation':True})
        for rn,rpath,r in route_index:
            if url and (url==rpath or url.startswith(rpath.split('{')[0].rstrip('/')) or rpath.startswith(url.split('{')[0].rstrip('/'))):
                edges.append({'from':eid,'to':rn,'type':'POSSIBLE_BACKEND_HANDLER','confidence':'candidate'})
    for p in js.get('hidden_parameter_candidates',[]):
        pid=p.get('id') or 'param-'+h(p.get('file','')+p.get('name',''))
        nodes.append({'id':pid,'type':'hidden_parameter_candidate','name':p.get('name'),'file':p.get('file'),'line':p.get('line'),'reason':p.get('reason')})
    for g in js.get('frontend_guards',[]):
        gid=g.get('id') or 'guard-'+h(g.get('file','')+g.get('signal',''))
        nodes.append({'id':gid,'type':'frontend_guard','signal':g.get('signal'),'file':g.get('file'),'line':g.get('line'),'cannot_prove_backend_authz':True})
    for sm in js.get('sourcemaps',[]):
        sid=sm.get('id') or 'sm-'+h(sm.get('file','')+sm.get('path',''))
        nodes.append({'id':sid,'type':'sourcemap','path':sm.get('path'),'file':sm.get('file'),'line':sm.get('line'),'must_resolve_for_promotion':True})
    graph={'schema_version':'js-audit-graph-v1','source_js':js_file,'source_routes':routes_file,'nodes':nodes,'edges':edges,'quality':{'frontend_api_count':len(js.get('endpoints',[])),'backend_correlations':sum(1 for e in edges if e.get('type')=='POSSIBLE_BACKEND_HANDLER'),'sourcemap_count':len(js.get('sourcemaps',[])),'hidden_parameter_candidates':len(js.get('hidden_parameter_candidates',[])),'policy':'API graph is candidate-only; needs backend handler, auth matrix and replay evidence before confirmed report'}}
    Path(out_file).parent.mkdir(parents=True,exist_ok=True); Path(out_file).write_text(json.dumps(graph,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'ok':True,'nodes':len(nodes),'edges':len(edges),'backend_correlations':graph['quality']['backend_correlations']},ensure_ascii=False))

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--js',required=True); ap.add_argument('--routes'); ap.add_argument('--out',required=True); ns=ap.parse_args(); build(ns.js,ns.routes,ns.out)
if __name__=='__main__': main()

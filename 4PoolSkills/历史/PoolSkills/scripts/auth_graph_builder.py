#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, hashlib, re
from pathlib import Path

def h(s): return hashlib.sha256(s.encode()).hexdigest()[:16]
ROLE_RX=re.compile(r'(?i)\b(admin|owner|member|user|manager|viewer|editor|tenant|org|workspace|permission|role)\b')

def build(routes_file: str, out_file: str):
    data=json.loads(Path(routes_file).read_text(encoding='utf-8'))
    nodes=[]; edges=[]
    for r in data.get('routes',[]):
        rid=r.get('id') or 'route-'+h(json.dumps(r,sort_keys=True))
        nodes.append({'id':rid,'type':'route','method':r.get('method'),'path':r.get('path'),'file':r.get('file'),'line':r.get('line')})
        for mw in r.get('middlewares',[]) or []:
            mid='mw-'+h(rid+mw); nodes.append({'id':mid,'type':'middleware','name':mw,'file':r.get('file')}); edges.append({'from':rid,'to':mid,'type':'PROTECTED_BY'})
        authn='authn-'+h(rid+(r.get('authn_hint') or ''))
        authz='authz-'+h(rid+(r.get('authz_hint') or ''))
        nodes.append({'id':authn,'type':'authn','status':r.get('authn_hint','missing_or_unknown')})
        nodes.append({'id':authz,'type':'authz','status':r.get('authz_hint','missing_or_unknown')})
        edges.append({'from':rid,'to':authn,'type':'AUTHN_STATUS'})
        edges.append({'from':rid,'to':authz,'type':'AUTHZ_STATUS'})
        for p in r.get('parameters',[]) or []:
            pid='param-'+h(rid+p); nodes.append({'id':pid,'type':'parameter','name':p}); edges.append({'from':rid,'to':pid,'type':'ACCEPTS_PARAMETER'})
            if ROLE_RX.search(p): edges.append({'from':pid,'to':authz,'type':'AUTHZ_RELEVANT_PARAMETER'})
    graph={'schema_version':'auth-graph-v1','source_routes':routes_file,'nodes':nodes,'edges':edges,'quality':{'missing_authn_routes':sum(1 for r in data.get('routes',[]) if r.get('authn_hint')!='present'),'missing_authz_routes':sum(1 for r in data.get('routes',[]) if r.get('authz_hint')!='present'),'policy':'missing auth hints are candidates only; not vulnerability proof'}}
    Path(out_file).parent.mkdir(parents=True,exist_ok=True); Path(out_file).write_text(json.dumps(graph,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'ok':True,'nodes':len(nodes),'edges':len(edges),'missing_authz_routes':graph['quality']['missing_authz_routes']},ensure_ascii=False))

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--routes',required=True); ap.add_argument('--out',required=True); ns=ap.parse_args(); build(ns.routes,ns.out)
if __name__=='__main__': main()

#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, re
from pathlib import Path

def normalize(p):
    p=re.sub(r'<[^>]+>|:[A-Za-z_][A-Za-z0-9_]*|\{[^}]+\}', '{param}', p or '')
    p=re.sub(r'/+','/',p).rstrip('/') or '/'
    return p

def correlate(js_file, routes_file):
    js=json.loads(Path(js_file).read_text(encoding='utf-8')); routes=json.loads(Path(routes_file).read_text(encoding='utf-8'))
    rmap={normalize(r.get('path')):r for r in routes.get('routes',[])}; links=[]; orphan_frontend=[]
    for ep in js.get('endpoints',[]):
        n=normalize(ep.get('url'))
        match=rmap.get(n)
        if not match and n.startswith('/api'):
            match=rmap.get(n[4:] or '/')
        if match: links.append({'frontend_endpoint':ep,'backend_route':match,'confidence':'high' if normalize(match.get('path'))==n else 'medium'})
        else: orphan_frontend.append(ep)
    backend_without_frontend=[r for r in routes.get('routes',[]) if all(normalize(r.get('path'))!=normalize(l['backend_route'].get('path')) for l in links)]
    return {'schema_version':'frontend-backend-correlation-v1','links':links,'orphan_frontend_endpoints':orphan_frontend,'backend_routes_without_frontend':backend_without_frontend,'counts':{'links':len(links),'orphan_frontend':len(orphan_frontend),'backend_only':len(backend_without_frontend)}}
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--js',required=True); ap.add_argument('--routes',required=True); ap.add_argument('--out',required=True); ns=ap.parse_args(); data=correlate(ns.js,ns.routes); Path(ns.out).parent.mkdir(parents=True,exist_ok=True); Path(ns.out).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); print(json.dumps(data['counts'],ensure_ascii=False))
if __name__=='__main__': main()

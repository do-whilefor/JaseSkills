#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, re, sys
from pathlib import Path
DYNAMIC_IMPORT_RX=re.compile(r"import\s*\(\s*['\"](?P<chunk>[^'\"]+)['\"]\s*\)")
STATIC_IMPORT_RX=re.compile(r"(?:import\s+[^'\"]*from\s+|import\s*)['\"](?P<chunk>[^'\"]+)['\"]")
ROUTE_RX=re.compile(r"(?:path|route)\s*[:=]\s*['\"](?P<route>/[^'\"]+)['\"]")

def _id(*parts): return hashlib.sha256(':'.join(map(str,parts)).encode()).hexdigest()[:14]
def _resolve(base: Path, spec: str) -> str:
    if spec.startswith('.'):
        p=(base.parent/spec).resolve()
        return str(p)
    return spec

def build(root: str | Path, out: str | Path | None = None) -> dict:
    root=Path(root).resolve()
    files=[p for p in root.rglob('*') if p.is_file() and p.suffix.lower() in {'.js','.jsx','.ts','.tsx','.mjs','.cjs','.vue'}]
    nodes=[]; edges=[]; routes=[]
    node_ids={}
    def node_for(p: Path):
        rel=str(p.relative_to(root)).replace('\\','/') if p.exists() and root in p.resolve().parents else str(p)
        nid=node_ids.setdefault(rel,'chunk-'+_id(rel))
        if not any(n['id']==nid for n in nodes): nodes.append({'id':nid,'file':rel,'type':'chunk'})
        return nid, rel
    for p in files:
        nid, rel=node_for(p)
        text=p.read_text(encoding='utf-8',errors='ignore')
        for m in STATIC_IMPORT_RX.finditer(text):
            spec=m.group('chunk'); edges.append({'from':nid,'to_spec':spec,'to_resolved':_resolve(p,spec),'type':'static_import','line':text[:m.start()].count('\n')+1})
        for m in DYNAMIC_IMPORT_RX.finditer(text):
            spec=m.group('chunk'); edges.append({'from':nid,'to_spec':spec,'to_resolved':_resolve(p,spec),'type':'dynamic_import','line':text[:m.start()].count('\n')+1})
        for m in ROUTE_RX.finditer(text):
            routes.append({'route':m.group('route'),'chunk':rel,'line':text[:m.start()].count('\n')+1})
    by_rel={n['file']:n['id'] for n in nodes}
    for e in edges:
        rp=Path(e['to_resolved'])
        candidates=[]
        if rp.is_absolute():
            candidates=[rp, rp.with_suffix('.js'), rp.with_suffix('.ts'), rp/'index.js', rp/'index.ts']
        for c in candidates:
            try:
                rel=str(c.resolve().relative_to(root)).replace('\\','/')
                if rel in by_rel: e['to']=by_rel[rel]; break
            except Exception: pass
    data={'schema_version':'chunk-lineage-v1','root':str(root),'nodes':nodes,'edges':edges,'routes':routes,'counts':{'chunks':len(nodes),'edges':len(edges),'dynamic_imports':sum(1 for e in edges if e['type']=='dynamic_import')}}
    if out:
        Path(out).parent.mkdir(parents=True,exist_ok=True); Path(out).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return data

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('root'); ap.add_argument('--out',required=True); ns=ap.parse_args(); data=build(ns.root,ns.out); print(json.dumps(data['counts'],ensure_ascii=False))
if __name__=='__main__': main()

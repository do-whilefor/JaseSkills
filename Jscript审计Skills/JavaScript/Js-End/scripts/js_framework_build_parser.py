#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, re
from pathlib import Path

def load(p):
    try: return json.loads(p.read_text(encoding='utf-8'))
    except Exception: return None

def rel(p,r):
    try: return str(p.resolve().relative_to(r.resolve())).replace('\\','/')
    except Exception: return str(p)

def walk_json(obj, prefix=''):
    out=[]
    if isinstance(obj,dict):
        for k,v in obj.items():
            key=f'{prefix}.{k}' if prefix else str(k)
            if isinstance(v,str) and (v.endswith(('.js','.mjs','.css','.map','.wasm')) or '/_next/' in v or '/_nuxt/' in v or 'chunk' in v.lower()): out.append({'key':key,'value':v})
            else: out += walk_json(v,key)
    elif isinstance(obj,list):
        for i,v in enumerate(obj): out += walk_json(v,f'{prefix}[{i}]')
    return out

def main():
    ap=argparse.ArgumentParser(description='Parse Next/Nuxt/Vite/Webpack/Rollup build artifacts for route->chunk candidates.')
    ap.add_argument('--root', default='.')
    ap.add_argument('--out', default='reports/js-top-tier')
    args=ap.parse_args(); root=Path(args.root).resolve(); out=Path(args.out); out.mkdir(parents=True, exist_ok=True)
    records=[]
    patterns={
      'next-build-manifest':['build-manifest.json','app-build-manifest.json','routes-manifest.json','middleware-manifest.json','prerender-manifest.json'],
      'vite-manifest':['manifest.json','.vite/manifest.json','vite-manifest.json'],
      'asset-manifest':['asset-manifest.json'],
      'nuxt':['payload.js','nuxt.config.js','nitro.json'],
      'webpack-stats':['stats.json','webpack-stats.json']
    }
    for kind,names in patterns.items():
        for p in root.rglob('*'):
            if not p.is_file(): continue
            if p.name not in names and str(p.relative_to(root)).replace('\\','/') not in names: continue
            obj=load(p)
            if obj is None:
                text=p.read_text(encoding='utf-8', errors='replace')
                assets=re.findall(r'''[`"']([^`"']+\.(?:js|mjs|css|map|wasm))(?:\?[^`"']*)?[`"']''', text)
                records.append({'kind':kind,'file':rel(p,root),'parse':'text','assets':assets[:500],'status':'candidate-only'})
            else:
                records.append({'kind':kind,'file':rel(p,root),'parse':'json','assets':walk_json(obj)[:1000],'raw_keys':list(obj.keys())[:100] if isinstance(obj,dict) else [],'status':'candidate-only'})
    res={'schema_version':'js-framework-build-parser/v1','status':'partial' if records else 'empty','records':records,'downgrade':'route/chunk mapping is candidate-only until browser replay confirms chunk loading by action/role/tenant.'}
    (out/'js_framework_build_artifacts.json').write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'ok':True,'records':len(records),'out':str(out/'js_framework_build_artifacts.json')}, ensure_ascii=False, indent=2))
if __name__=='__main__': main()

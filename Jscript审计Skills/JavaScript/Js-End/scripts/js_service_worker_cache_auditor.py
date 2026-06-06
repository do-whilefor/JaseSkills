#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, re
from pathlib import Path
PRECACHE=re.compile(r'''(?:url|revision)\s*[:=]\s*[`"']([^`"']+)[`"']|[`"']([^`"']+\.(?:js|mjs|map|html|json|wasm|css))[`"']''', re.I)

def rel(p,r):
    try: return str(p.resolve().relative_to(r.resolve())).replace('\\','/')
    except Exception: return str(p)

def main():
    ap=argparse.ArgumentParser(description='Service worker static precache auditor and browser cache dump plan generator.')
    ap.add_argument('--root', default='.')
    ap.add_argument('--out', default='reports/js-top-tier')
    args=ap.parse_args(); root=Path(args.root).resolve(); out=Path(args.out); out.mkdir(parents=True, exist_ok=True)
    items=[]; scripts=[]
    for p in root.rglob('*'):
        if not p.is_file(): continue
        if 'service-worker' not in p.name.lower() and 'sw.' not in p.name.lower() and 'precache' not in p.name.lower(): continue
        text=p.read_text(encoding='utf-8', errors='replace')
        for m in PRECACHE.finditer(text):
            val=next((g for g in m.groups() if g), m.group(0))
            items.append({'file':rel(p,root),'line':text.count('\n',0,m.start())+1,'asset':val,'status':'candidate-only'})
    dump_js="""
// Paste into an authorized browser context or execute with Playwright page.evaluate.
async function dumpCaches(){
 const keys = await caches.keys(); const out=[];
 for (const k of keys){ const c=await caches.open(k); const reqs=await c.keys(); out.push({cache:k, urls:reqs.map(r=>r.url)}); }
 return out;
}
""".strip()
    (out/'service_worker_cache_dump_snippet.js').write_text(dump_js, encoding='utf-8')
    res={'schema_version':'js-service-worker-cache-audit/v1','status':'partial' if items else 'empty','precache_candidates':items,'runtime_dump_snippet':str(out/'service_worker_cache_dump_snippet.js'),'downgrade':'static precache candidates are not browser cache evidence until a runtime cache dump is imported into evidence manifest.'}
    (out/'js_service_worker_cache_audit.json').write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'ok':True,'precache_candidates':len(items),'out':str(out/'js_service_worker_cache_audit.json')}, ensure_ascii=False, indent=2))
if __name__=='__main__': main()

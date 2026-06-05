#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, re, zipfile
from pathlib import Path
from typing import Any

def read_json(p: Path):
    try: return json.loads(p.read_text(encoding='utf-8'))
    except Exception: return None

def scan_har(p: Path):
    obj=read_json(p) or {}
    entries=obj.get('log',{}).get('entries',[]) if isinstance(obj,dict) else []
    out=[]
    for i,e in enumerate(entries):
        req=e.get('request',{}) if isinstance(e,dict) else {}
        res=e.get('response',{}) if isinstance(e,dict) else {}
        url=req.get('url','')
        headers={h.get('name','').lower():h.get('value','') for h in res.get('headers',[])}
        if url.endswith(('.js','.mjs','.map','.wasm')) or 'javascript' in headers.get('content-type','') or url.startswith(('ws://','wss://')) or '/graphql' in url:
            out.append({'kind':'har_runtime_asset','file':str(p),'entry_index':i,'url':url,'status':res.get('status'),'content_type':headers.get('content-type',''),'evidence_status':'partial'})
    return out

def scan_trace_zip(p: Path):
    out=[]
    try:
        with zipfile.ZipFile(p) as z:
            names=z.namelist()
            out.append({'kind':'playwright_trace_zip','file':str(p),'entries':len(names),'has_trace_network':any('network' in n.lower() or n.endswith('.network') for n in names),'evidence_status':'partial'})
    except Exception as e:
        out.append({'kind':'trace_parse_error','file':str(p),'error':str(e),'evidence_status':'partial'})
    return out

def main():
    ap=argparse.ArgumentParser(description='Bridge HAR/Playwright trace/Burp exports into JS evidence status. Does not perform browser automation by itself.')
    ap.add_argument('--evidence-root', required=True)
    ap.add_argument('--out', default='reports/js-top-tier')
    args=ap.parse_args()
    root=Path(args.evidence_root).resolve(); out=Path(args.out).resolve(); out.mkdir(parents=True, exist_ok=True)
    items=[]
    for p in root.rglob('*'):
        if not p.is_file(): continue
        low=p.name.lower()
        if low.endswith('.har'): items += scan_har(p)
        elif low.endswith('.zip') and ('trace' in low or 'playwright' in low): items += scan_trace_zip(p)
        elif low.endswith(('.png','.jpg','.jpeg','.webp')):
            items.append({'kind':'screenshot','file':str(p),'evidence_status':'partial'})
    status='ready' if any(i['kind']=='har_runtime_asset' for i in items) and any(i['kind']=='screenshot' for i in items) else ('partial' if items else 'missing')
    result={'schema_version':'js-runtime-evidence/v1','status':status,'reason':'ready requires HAR runtime assets plus screenshots and role/tenant mapping; partial evidence is not dynamic validation proof by itself','items':items}
    (out/'js_runtime_evidence.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'ok':True,'status':status,'items':len(items),'out':str(out/'js_runtime_evidence.json')}, ensure_ascii=False, indent=2))
if __name__=='__main__': main()

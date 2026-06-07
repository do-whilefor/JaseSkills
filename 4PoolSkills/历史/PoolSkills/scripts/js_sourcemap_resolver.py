#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,re,base64
from pathlib import Path
SKIP={'.git','node_modules','vendor','target','coverage'}
API_RX=re.compile(r"(?:(?:https?:)?//[^'\"\s]+|/(?:api|graphql|v\d|admin|internal|webhook)[A-Za-z0-9_./:{}?=&%-]*)")
FLAG_RX=re.compile(r"(?i)(feature[_-]?flag|ab[_-]?test|experiment|launchdarkly|split\.io|growthbook|flags?\.)")
I18N_RX=re.compile(r"(?i)(i18n|intl|translate|t\(['\"]([A-Za-z0-9_.:-]{3,})['\"])")
TELEMETRY_RX=re.compile(r"(?i)(analytics|track\(|eventName|mixpanel|amplitude|segment|gtag|dataLayer)")

def read_json(p):
    try: return json.loads(Path(p).read_text(encoding='utf-8', errors='ignore'))
    except Exception: return None

def scan_text(txt, rel, source='file'):
    out=[]
    for rx,kind in [(API_RX,'endpoint'),(FLAG_RX,'feature_flag'),(I18N_RX,'i18n_key_or_module'),(TELEMETRY_RX,'telemetry_event')]:
        for m in rx.finditer(txt):
            out.append({'file':rel,'kind':kind,'source':source,'line':txt[:m.start()].count('\n')+1,'value':m.group(0)[:180],'candidate_only':True})
    return out

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('project'); ap.add_argument('--out',default='outputs/js_sourcemap_inventory.json'); a=ap.parse_args(); root=Path(a.project).resolve(); items=[]; extracted=[]
    for p in root.rglob('*'):
        if any(x in p.parts for x in SKIP) or not p.is_file(): continue
        rel=str(p.relative_to(root)); suf=p.suffix.lower()
        if suf=='.map':
            sm=read_json(p) or {}; sources=sm.get('sources',[]) or []; contents=sm.get('sourcesContent') or []
            items.append({'file':rel,'kind':'map_file','sources':sources[:300],'has_sourcesContent':bool(contents),'sourcesContent_count':len(contents),'names_count':len(sm.get('names') or [])})
            for idx,content in enumerate(contents[:300]):
                if isinstance(content,str):
                    sname=sources[idx] if idx < len(sources) else f'sourcesContent[{idx}]'
                    extracted.extend(scan_text(content, rel+'::'+sname, 'sourcemap_sourcesContent'))
        elif suf in ['.js','.mjs','.cjs','.ts','.tsx','.jsx','.vue','.html','.htm'] and p.stat().st_size<2000000:
            txt=p.read_text(encoding='utf-8', errors='ignore')
            for m in re.finditer(r'//# sourceMappingURL=(.+)', txt):
                url=m.group(1).strip(); items.append({'file':rel,'kind':'sourceMappingURL','url':url,'line':txt[:m.start()].count('\n')+1,'inline_data_uri':url.startswith('data:')})
            if 'serviceWorker' in txt or 'precache' in txt or '__WB_MANIFEST' in txt or 'caches.open' in txt:
                items.append({'file':rel,'kind':'service_worker_or_precache','signals':['serviceWorker','precache','cache']})
            for m in re.finditer(r'<link[^>]+rel=["\'](?:preload|prefetch)["\'][^>]+href=["\']([^"\']+)', txt, re.I):
                items.append({'file':rel,'kind':'preload_prefetch','url':m.group(1)})
            extracted.extend(scan_text(txt, rel, 'bundle_or_source'))
    out={'schema_version':'js-sourcemap-inventory-v3','project':str(root),'items':items,'extracted_candidate_signals':extracted,'policy':'sourcemap, feature flag, i18n and telemetry evidence is candidate-only; verify backend reachability and authorization before reporting'}
    Path(a.out).parent.mkdir(parents=True,exist_ok=True); Path(a.out).write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8'); print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=='__main__': main()

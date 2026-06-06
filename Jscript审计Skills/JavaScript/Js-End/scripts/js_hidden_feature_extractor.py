#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, re
from pathlib import Path
JS={'.js','.mjs','.cjs','.jsx','.ts','.tsx','.json'}
FEATURE=re.compile(r'''(?:feature|flag|experiment|abTest|remoteConfig|enabled|disabled)[A-Za-z0-9_$.-]{0,80}\s*[:=]\s*['"]?([A-Za-z0-9_.:-]{2,120})''', re.I)
I18N=re.compile(r'''['"]([A-Za-z0-9_.:-]*(?:admin|billing|member|permission|audit|export|download|refund|approve|tenant|org|debug)[A-Za-z0-9_.:-]*)['"]''', re.I)
ANALYTICS=re.compile(r'''(?:track|analytics|amplitude|mixpanel|gtag|dataLayer\.push)\s*\([\s\S]{0,300}?['"]([A-Za-z0-9_.:-]{3,160})['"]''', re.I)
ROUTE_META=re.compile(r'''(?:path|name|meta|permission|roles?)\s*:\s*['"]([^'"]{1,240})['"]''', re.I)

def rel(p,r):
    try: return str(p.resolve().relative_to(r.resolve())).replace('\\','/')
    except Exception: return str(p)

def main():
    ap=argparse.ArgumentParser(description='Extract hidden feature signals from i18n keys, feature flags, analytics events, route meta and UI gating code.')
    ap.add_argument('--root', default='.')
    ap.add_argument('--out', default='reports/js-top-tier')
    args=ap.parse_args(); root=Path(args.root).resolve(); out=Path(args.out); out.mkdir(parents=True, exist_ok=True)
    signals=[]
    for p in root.rglob('*'):
        if not p.is_file() or p.suffix.lower() not in JS: continue
        text=p.read_text(encoding='utf-8', errors='replace'); rp=rel(p,root)
        for rgx,kind in [(FEATURE,'feature-flag'),(I18N,'i18n-hidden-key'),(ANALYTICS,'analytics-event'),(ROUTE_META,'route-meta')]:
            for m in rgx.finditer(text): signals.append({'kind':kind,'file':rp,'line':text.count('\n',0,m.start())+1,'value':m.group(1),'status':'candidate-only'})
    res={'schema_version':'js-hidden-feature-extraction/v1','status':'partial' if signals else 'empty','signals':signals[:5000],'downgrade':'signals indicate possible hidden functionality only; browser replay and role/tenant comparison must confirm reachability.'}
    (out/'js_hidden_feature_signals.json').write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'ok':True,'signals':len(signals),'out':str(out/'js_hidden_feature_signals.json')}, ensure_ascii=False, indent=2))
if __name__=='__main__': main()

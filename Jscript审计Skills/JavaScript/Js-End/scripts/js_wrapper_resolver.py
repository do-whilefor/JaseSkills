#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, re
from pathlib import Path
JS={'.js','.mjs','.cjs','.jsx','.ts','.tsx'}
CREATE=re.compile(r'''(?:axios|ky|got|superagent)\s*\.\s*create\s*\(\s*\{(?P<body>[\s\S]{0,2000}?)\}\s*\)''')
BASE=re.compile(r'''baseURL\s*:\s*[`"'](?P<url>[^`"']+)[`"']''')
WRAP=re.compile(r'''(?:function|const|let|var)\s+(?P<name>[A-Za-z_$][\w$]*)\s*(?:=\s*)?(?:async\s*)?(?:\([^)]*\)|function\s*\([^)]*\))\s*=>?[\s\S]{0,1000}?(?:fetch|axios|request|apiClient)\s*\(''', re.S)
INTERCEPT=re.compile(r'''\.interceptors\.(?P<kind>request|response)\.use\s*\(''', re.S)
CALL=re.compile(r'''(?P<client>[A-Za-z_$][\w$]*(?:Client|Api|Service|Request)?)\.(?P<method>get|post|put|patch|delete|request)\s*\(\s*[`"'](?P<path>[^`"']{1,400})[`"']''', re.I)

def rel(p,r):
    try: return str(p.resolve().relative_to(r.resolve())).replace('\\','/')
    except Exception: return str(p)

def main():
    ap=argparse.ArgumentParser(description='Resolve JS API wrappers, axios instances, baseURL and interceptor candidates. This complements AST extraction but never proves runtime reachability.')
    ap.add_argument('--root', default='.')
    ap.add_argument('--out', default='reports/js-top-tier')
    args=ap.parse_args(); root=Path(args.root).resolve(); out=Path(args.out); out.mkdir(parents=True, exist_ok=True)
    instances=[]; wrappers=[]; interceptors=[]; calls=[]
    for p in root.rglob('*'):
        if not p.is_file() or p.suffix.lower() not in JS: continue
        text=p.read_text(encoding='utf-8', errors='replace'); rp=rel(p,root)
        for m in CREATE.finditer(text):
            b=BASE.search(m.group('body') or '')
            instances.append({'file':rp,'line':text.count('\n',0,m.start())+1,'baseURL':b.group('url') if b else None,'rule':'axios.create'})
        for m in WRAP.finditer(text): wrappers.append({'file':rp,'line':text.count('\n',0,m.start())+1,'name':m.group('name'),'rule':'wrapper.function'})
        for m in INTERCEPT.finditer(text): interceptors.append({'file':rp,'line':text.count('\n',0,m.start())+1,'kind':m.group('kind'),'rule':'interceptor.use'})
        for m in CALL.finditer(text): calls.append({'file':rp,'line':text.count('\n',0,m.start())+1,'client':m.group('client'),'method':m.group('method').upper(),'path':m.group('path'),'rule':'wrapper.call'})
    res={'schema_version':'js-wrapper-resolution/v1','status':'partial' if (instances or wrappers or calls) else 'empty','instances':instances,'wrappers':wrappers,'interceptors':interceptors,'calls':calls,'downgrade':'wrapper resolution is static until cross-linked with AST call graph and runtime HAR.'}
    (out/'js_wrapper_resolution.json').write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'ok':True,'instances':len(instances),'wrappers':len(wrappers),'interceptors':len(interceptors),'calls':len(calls),'out':str(out/'js_wrapper_resolution.json')}, ensure_ascii=False, indent=2))
if __name__=='__main__': main()

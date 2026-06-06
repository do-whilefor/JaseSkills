#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, re
from pathlib import Path
SECRET=re.compile(r'(?i)(api[_-]?key|secret|token|jwt|internal|localhost|admin|debug|todo|fixme|password|private)')
API=re.compile(r'''[`"'](?P<path>/(?:api|admin|internal|graphql|rpc|v\d+|tenant|org|project|payment|refund|debug|download|export)[^`"']{0,500})[`"']''', re.I)

def rel(p,r):
    try: return str(p.resolve().relative_to(r.resolve())).replace('\\','/')
    except Exception: return str(p)

def safe_name(src):
    s=re.sub(r'^[a-z]+://','',src); s=s.replace('webpack://','').replace('../','__up__/').lstrip('/\\')
    s=re.sub(r'[^A-Za-z0-9._/\\-]+','_',s)
    return s[:240] or 'unknown.js'

def main():
    ap=argparse.ArgumentParser(description='Reconstruct sources from source maps and index hidden APIs / secret candidates. Works offline on authorized assets.')
    ap.add_argument('--root', default='.')
    ap.add_argument('--out', default='reports/js-top-tier/sourcemap-reconstructed')
    args=ap.parse_args(); root=Path(args.root).resolve(); out=Path(args.out).resolve(); out.mkdir(parents=True, exist_ok=True)
    findings=[]; written=[]; maps=0
    for p in root.rglob('*.map'):
        try: obj=json.loads(p.read_text(encoding='utf-8', errors='replace'))
        except Exception as e:
            findings.append({'kind':'sourcemap-parse-error','map':rel(p,root),'error':str(e)}); continue
        maps+=1; sources=obj.get('sources') or []; contents=obj.get('sourcesContent') or []
        for i,content in enumerate(contents):
            if not isinstance(content,str): continue
            src=sources[i] if i < len(sources) else f'sourcesContent[{i}]'
            dst=out/safe_name(src)
            dst.parent.mkdir(parents=True, exist_ok=True); dst.write_text(content, encoding='utf-8', errors='replace')
            written.append({'map':rel(p,root),'source':src,'out':str(dst.relative_to(out)),'size':len(content)})
            for m in API.finditer(content): findings.append({'kind':'hidden-api-from-sourcemap','map':rel(p,root),'source':src,'line':content.count('\n',0,m.start())+1,'value':m.group('path'),'status':'candidate-only'})
            for m in SECRET.finditer(content): findings.append({'kind':'sourcemap-sensitive-token-candidate','map':rel(p,root),'source':src,'line':content.count('\n',0,m.start())+1,'value':content[m.start():m.start()+160],'status':'candidate-only'})
    res={'schema_version':'js-sourcemap-reconstruction/v1','status':'partial' if maps else 'missing','maps':maps,'written_sources':written[:5000],'findings':findings[:5000],'downgrade':'source map reconstruction proves exposure of source text only; vulnerability claims require runtime/API impact evidence.'}
    (out.parent/'js_sourcemap_reconstruction.json').write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'ok':True,'maps':maps,'sources':len(written),'findings':len(findings),'out':str(out.parent/'js_sourcemap_reconstruction.json')}, ensure_ascii=False, indent=2))
if __name__=='__main__': main()

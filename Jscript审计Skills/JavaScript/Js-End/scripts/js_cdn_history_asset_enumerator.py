#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, re
from pathlib import Path
HASH=re.compile(r'([A-Za-z0-9_.-]+?)[._-]([a-f0-9]{6,32})(\.js|\.css|\.map)$', re.I)
VERSION=re.compile(r'(?:v|version|release)[=/._-]?([0-9]+(?:\.[0-9]+){1,3})', re.I)

def main():
    ap=argparse.ArgumentParser(description='Offline CDN/history asset candidate enumerator. It does not fetch remote assets unless a separate authorized downloader imports them.')
    ap.add_argument('--ledger', required=True)
    ap.add_argument('--out', default='reports/js-top-tier')
    args=ap.parse_args(); out=Path(args.out); out.mkdir(parents=True, exist_ok=True)
    ledger=json.loads(Path(args.ledger).read_text(encoding='utf-8'))
    candidates=[]
    for a in ledger.get('assets',[]):
        path=a.get('path',''); name=Path(path).name
        m=HASH.search(name)
        if m:
            base, h, ext=m.groups()
            candidates.append({'asset':path,'kind':'hash-versioned-asset','base':base,'hash':h,'extension':ext,'candidate_old_patterns':[f'{base}.*{ext}', f'{base}.[oldhash]{ext}'], 'status':'candidate-only'})
        v=VERSION.search(path)
        if v:
            candidates.append({'asset':path,'kind':'versioned-path','version':v.group(1),'candidate_previous_versions':'manual/authorized enumeration required','status':'candidate-only'})
        if path.startswith(('http://','https://','//')):
            candidates.append({'asset':path,'kind':'remote-cdn-reference','status':'candidate-only','fetch_rule':'do not fetch unless domain is explicitly in scope allowlist'})
    res={'schema_version':'js-cdn-history-enumeration/v1','status':'partial' if candidates else 'empty','candidates':candidates,'downgrade':'offline candidate list only; stale assets are not proven accessible until imported HAR/request evidence exists.'}
    (out/'js_cdn_history_assets.json').write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'ok':True,'candidates':len(candidates),'out':str(out/'js_cdn_history_assets.json')}, ensure_ascii=False, indent=2))
if __name__=='__main__': main()

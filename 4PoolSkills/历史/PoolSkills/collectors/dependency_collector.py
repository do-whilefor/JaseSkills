#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, sys, hashlib
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.scope_guard import load_scope, iter_scoped_files, sha256_file
LOCKS={'package-lock.json':'npm','pnpm-lock.yaml':'pnpm','yarn.lock':'yarn','requirements.txt':'pip','poetry.lock':'poetry','Pipfile.lock':'pipenv','Cargo.lock':'cargo','go.mod':'go','composer.lock':'composer','Gemfile.lock':'bundler'}
def collect(root, scope_file=None, verify_online=False):
    root=Path(root).resolve(); scope=load_scope(root,scope_file); deps=[]
    for p in iter_scoped_files(root,scope,include_exts={'.json','.yaml','.yml','.txt','.lock','.mod'}):
        if p.name in LOCKS:
            deps.append({'id':'dep-'+hashlib.sha256(str(p).encode()).hexdigest()[:12],'file':str(p.relative_to(root)),'ecosystem':LOCKS[p.name],'sha256':sha256_file(p),'cve_status':'not_checked_offline_mode' if not verify_online else 'verified_tool_required','verified':False if not verify_online else None})
    return {'schema_version':'dependency-inventory-v1','root':str(root),'verify_online':verify_online,'dependencies':deps,'policy':'CVE names are not asserted unless verify_online is true and a tool result is attached.'}
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('root'); ap.add_argument('--scope-file'); ap.add_argument('--verify-online',action='store_true'); ap.add_argument('--out',required=True); ns=ap.parse_args(); data=collect(ns.root,ns.scope_file,ns.verify_online); Path(ns.out).parent.mkdir(parents=True,exist_ok=True); Path(ns.out).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); print(json.dumps({'dependencies':len(data['dependencies']),'verify_online':ns.verify_online},ensure_ascii=False))
if __name__=='__main__': main()

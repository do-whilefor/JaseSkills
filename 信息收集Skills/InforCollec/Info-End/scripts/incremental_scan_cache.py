#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import json, os
from _info_collect_lib import common_parser, parse_scope, enforce_scope, iter_scoped_files, dry_run_report, stable_hash, read_text, now_iso
COLLECTOR_VERSION='incremental-cache.v1'
def fingerprint(p:Path):
    st=p.stat(); return {'path':str(p),'size':st.st_size,'mtime':int(st.st_mtime),'hash':stable_hash(read_text(p,500000)),'collector_version':COLLECTOR_VERSION}
def main():
    ap=common_parser('Build or diff incremental scan cache by file hash, mtime and collector version.')
    ap.add_argument('--previous-cache', default=None)
    args=ap.parse_args(); root=Path(args.input).resolve(); scope=parse_scope(args.scope,root); ok,reason=enforce_scope(root,scope)
    if args.dry_run: return dry_run_report(args,'incremental_scan_cache',root,scope)
    if not ok: print(json.dumps({'status':'FAIL','reason':reason},ensure_ascii=False)); return 2
    current={}
    for p in (iter_scoped_files(root,scope,args.max_files,args.timeout,args.scan_profile,args.follow_symlinks) if root.is_dir() else [root]):
        fp=fingerprint(p); current[str(Path(fp['path']).resolve())]=fp
    prev={}
    if args.previous_cache and Path(args.previous_cache).exists():
        prev=json.loads(Path(args.previous_cache).read_text()).get('files',{})
    added=sorted(set(current)-set(prev)); removed=sorted(set(prev)-set(current)); changed=sorted(k for k in set(current)&set(prev) if current[k].get('hash')!=prev[k].get('hash') or current[k].get('collector_version')!=prev[k].get('collector_version'))
    report={'schema_version':'incremental-scan-cache.v1','generated_at':now_iso(),'root':str(root),'files':current,'diff':{'added':added,'removed':removed,'changed':changed}}
    text=json.dumps(report,ensure_ascii=False,indent=2)
    if args.output=='-': print(text)
    else: Path(args.output).write_text(text,encoding='utf-8')
    return 0
if __name__=='__main__': raise SystemExit(main())

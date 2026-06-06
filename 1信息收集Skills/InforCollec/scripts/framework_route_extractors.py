#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _info_collect_lib import common_parser, parse_scope, enforce_scope, iter_scoped_files, output_report, evidence, dry_run_report, read_text
from framework_route_extractors import extract_framework_routes

def main():
    ap=common_parser('Framework-aware route extractor for Express, Next.js, NestJS, FastAPI, Django, Spring, Laravel, Go and Rust.')
    args=ap.parse_args(); root=Path(args.input).resolve(); scope=parse_scope(args.scope,root); ok,reason=enforce_scope(root,scope)
    if args.dry_run: return dry_run_report(args,'framework_route_extractors',root,scope)
    if not ok: return output_report(args,'framework_route_extractors',[evidence('framework_route_extractors',root,root.parent,'out_of_scope_blocked',reason,1,confidence=1,severity_hint='blocker',needs_review=True)], {'scope_check':'FAIL'}) or 2
    items=[]
    for p in (iter_scoped_files(root,scope,args.max_files,args.timeout,args.scan_profile,args.follow_symlinks) if root.is_dir() else [root]):
        text=read_text(p)
        for r in extract_framework_routes(p, root if root.is_dir() else p.parent, text):
            items.append(evidence('framework_route_extractors',p,root if root.is_dir() else p.parent,'framework_route',r,r.get('line',1),confidence=r.get('confidence',.75),endpoint_relevance='high',scope_id=scope['scope_id'],needs_review=True,linked_report_section='route-api-inventory',collector_provenance={'collector':'framework_route_extractors','source':'framework-regex-parser','network':'disabled','framework':r.get('framework')}))
    return output_report(args,'framework_route_extractors',items,{'frameworks_supported':['Express','Next.js','NestJS','FastAPI','Django','Spring','Laravel','Go','Rust']})
if __name__=='__main__': raise SystemExit(main())

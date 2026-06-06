#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import json, re, subprocess, sys, tempfile
from _info_collect_lib import common_parser, parse_scope, enforce_scope, iter_scoped_files, dry_run_report, output_report, evidence, read_text, PATH_RE

def collect_openapi_paths(root, scope, args):
    paths=set()
    for p in (iter_scoped_files(root,scope,args.max_files,args.timeout,args.scan_profile,args.follow_symlinks) if root.is_dir() else [root]):
        if p.suffix.lower()=='.json':
            try:
                d=json.loads(read_text(p));
                if isinstance(d,dict) and isinstance(d.get('paths'),dict): paths.update(d['paths'].keys())
            except Exception: pass
        if p.suffix.lower() in {'.graphql','.gql'}:
            txt=read_text(p)
            for m in re.finditer(r'\b(query|mutation|subscription)\s+([A-Za-z_][A-Za-z0-9_]*)', txt): paths.add('graphql:'+m.group(2))
    return paths

def collect_code_paths(root, scope, args):
    paths=set()
    for p in (iter_scoped_files(root,scope,args.max_files,args.timeout,args.scan_profile,args.follow_symlinks) if root.is_dir() else [root]):
        txt=read_text(p)
        for m in PATH_RE.finditer(txt): paths.add(m.group(0).split('?')[0])
    return paths

def main():
    ap=common_parser('Diff OpenAPI/Postman/GraphQL declared APIs against static code and frontend literal references.')
    args=ap.parse_args(); root=Path(args.input).resolve(); scope=parse_scope(args.scope,root); ok,reason=enforce_scope(root,scope)
    if args.dry_run: return dry_run_report(args,'openapi_code_diff',root,scope)
    if not ok: return output_report(args,'openapi_code_diff',[evidence('openapi_code_diff',root,root.parent,'out_of_scope_blocked',reason,1,confidence=1,severity_hint='blocker',needs_review=True)], {'scope_check':'FAIL'}) or 2
    spec=collect_openapi_paths(root,scope,args); code=collect_code_paths(root,scope,args)
    items=[]
    for x in sorted(spec-code): items.append(evidence('openapi_code_diff',root,root,'openapi_spec_only_endpoint',x,1,confidence=.65,endpoint_relevance='high',scope_id=scope['scope_id'],needs_review=True,linked_report_section='route-api-inventory'))
    for x in sorted(code-spec): items.append(evidence('openapi_code_diff',root,root,'code_only_endpoint_literal',x,1,confidence=.55,endpoint_relevance='medium',scope_id=scope['scope_id'],needs_review=True,linked_report_section='hidden-information'))
    return output_report(args,'openapi_code_diff',items,{'summary':{'spec_paths':len(spec),'code_paths':len(code),'spec_only':len(spec-code),'code_only':len(code-spec)},'quality_note':'Diff is candidate static comparison; path templating and runtime reachability require manual review.'})
if __name__=='__main__': raise SystemExit(main())

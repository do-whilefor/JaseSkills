#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import json, sys
from _info_collect_lib import common_parser, parse_scope, enforce_scope, iter_scoped_files, output_report, evidence, dry_run_report

def main():
    ap=common_parser('Validate authorized local scope and block out-of-scope paths. No network calls are made.')
    args=ap.parse_args()
    root=Path(args.input).resolve()
    scope=parse_scope(args.scope, root)
    ok, reason=enforce_scope(root, scope)
    if args.dry_run:
        return dry_run_report(args, 'scope_guard', root, scope)
    items=[]
    if not ok:
        items.append(evidence('scope_guard', root, root.parent if root.parent.exists() else Path('/'), 'out_of_scope_blocked', {'path':str(root),'reason':reason}, 1, confidence=1.0, severity_hint='blocker', needs_review=True, linked_report_section='authorization-scope'))
        output_report(args, 'scope_guard', items, {'scope_check':{'status':'FAIL','reason':reason,'allowed_roots':[str(x) for x in scope['allowed_roots']],'denied_paths':[str(x) for x in scope['denied_paths']]}})
        return 2
    if root.is_dir():
        for i,p in enumerate(iter_scoped_files(root, scope, args.max_files, args.timeout, args.scan_profile, args.follow_symlinks)):
            fok, freason=enforce_scope(p, scope)
            if not fok:
                items.append(evidence('scope_guard', p, root, 'out_of_scope_file_blocked', {'path':str(p),'reason':freason}, 1, confidence=1.0, severity_hint='blocker', needs_review=True, linked_report_section='authorization-scope'))
                break
    items.append(evidence('scope_guard', root, root if root.is_dir() else root.parent, 'authorized_scope_confirmed', {'root':str(root),'files_sampled':len(items)}, 1, confidence=1.0, linked_report_section='authorization-scope'))
    return output_report(args, 'scope_guard', items, {'scope_check':{'status':'PASS','reason':'input is inside allowed scope','allowed_roots':[str(x) for x in scope['allowed_roots']],'denied_paths':[str(x) for x in scope['denied_paths']]}})
if __name__=='__main__':
    raise SystemExit(main())

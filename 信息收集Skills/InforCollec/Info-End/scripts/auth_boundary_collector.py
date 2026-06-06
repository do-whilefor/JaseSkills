#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import re
from _info_collect_lib import common_parser, parse_scope, enforce_scope, iter_scoped_files, output_report, evidence, dry_run_report, read_text, line_no
PATTERNS=[
('authentication_entry',r'(?i)\b(login|logout|signin|signup|register|password reset|oauth|saml|oidc|jwt|passport|auth0|clerk|nextauth|session)\b','high','medium'),
('authorization_middleware',r'(?i)\b(requireAuth|authorize|can\(|policy|permission|guard|middleware|before_action|isAdmin|hasRole|role_required|rbac|abac)\b','high','high'),
('role_model_signal',r'(?i)\b(role|roles|admin|owner|member|viewer|editor|superuser|root|staff)\b','medium','medium'),
('tenant_boundary_signal',r'(?i)\b(tenant|org|organization|workspace|account_id|company_id|project_id|owner_id|created_by|user_id)\b','medium','high'),
]
def main():
    ap=common_parser('Collect authentication, authorization, role, tenant, owner and admin boundary signals.')
    args=ap.parse_args(); root=Path(args.input).resolve(); scope=parse_scope(args.scope, root); ok,reason=enforce_scope(root, scope)
    if args.dry_run: return dry_run_report(args,'auth_boundary_collector',root,scope)
    if not ok: return output_report(args,'auth_boundary_collector',[evidence('auth_boundary_collector',root,root.parent,'out_of_scope_blocked',reason,1,confidence=1,severity_hint='blocker',needs_review=True)], {'scope_check':'FAIL'}) or 2
    items=[]
    for p in (iter_scoped_files(root, scope, args.max_files, args.timeout, args.scan_profile, args.follow_symlinks) if root.is_dir() else [root]):
        text=read_text(p)
        for typ,pat,auth_rel,tenant_rel in PATTERNS:
            for m in re.finditer(pat,text):
                items.append(evidence('auth_boundary_collector',p,root,typ,m.group(0),line_no(text,m.group(0)),confidence=.55,auth_relevance=auth_rel,tenant_relevance=tenant_rel,role_relevance='high' if 'role' in typ else 'medium',scope_id=scope['scope_id'],needs_review=True,linked_report_section='auth-role-tenant'))
    return output_report(args,'auth_boundary_collector',items)
if __name__=='__main__': raise SystemExit(main())

#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import re
from _info_collect_lib import common_parser, parse_scope, enforce_scope, iter_scoped_files, output_report, evidence, dry_run_report, read_text, line_no, PATH_RE, URL_RE
COMMENT=re.compile(r'(?://|#|/\*|<!--)\s*(.{0,300})')
PATTERNS=[
('comment_old_endpoint_or_token_hint',r'(?i)\b(api|endpoint|deprecated|legacy|old|token|secret|staging|test|admin|internal|todo|fixme)\b'),
('backup_temp_or_legacy_file',r'(?i)(\.bak$|\.old$|\.orig$|\.tmp$|backup|legacy|deprecated|migration)'),
('seed_mock_fixture_account_signal',r'(?i)\b(seed|fixture|mock|demo|test).*\b(admin|owner|role|tenant|password|email|user)\b|\b(admin|owner|role|tenant|password|email|user).*\b(seed|fixture|mock|demo|test)\b'),
('notification_template_hidden_link',r'(?i)\b(email|sms|notification|template|reset|verify|invite)\b'),
('reverse_proxy_hidden_path',r'(?i)\b(location|proxy_pass|route|handle_path|PathPrefix|RewriteRule)\b'),
('role_tenant_keyword_family',r'(?i)\b(role|tenant|organization|workspace|owner|admin|permission|scope|policy)\b'),
]
def main():
    ap=common_parser('Collect hidden information from comments, old docs, backup/temp files, mock/seed/fixtures, migrations, templates and reverse proxies.')
    args=ap.parse_args(); root=Path(args.input).resolve(); scope=parse_scope(args.scope, root); ok,reason=enforce_scope(root, scope)
    if args.dry_run: return dry_run_report(args,'hidden_info_collector',root,scope)
    if not ok: return output_report(args,'hidden_info_collector',[evidence('hidden_info_collector',root,root.parent,'out_of_scope_blocked',reason,1,confidence=1,severity_hint='blocker',needs_review=True)], {'scope_check':'FAIL'}) or 2
    items=[]
    for p in (iter_scoped_files(root, scope, args.max_files, args.timeout, args.scan_profile, args.follow_symlinks) if root.is_dir() else [root]):
        text=read_text(p); low=str(p).lower()
        for typ,pat in PATTERNS:
            if typ=='backup_temp_or_legacy_file' and re.search(pat,p.name): items.append(evidence('hidden_info_collector',p,root,typ,p.name,1,confidence=.8,needs_review=True,linked_report_section='hidden-information'))
            for m in re.finditer(pat,text): items.append(evidence('hidden_info_collector',p,root,typ,m.group(0),line_no(text,m.group(0)),confidence=.55,needs_review=True,auth_relevance='medium' if 'role' in typ else 'unknown',tenant_relevance='medium' if 'tenant' in typ else 'unknown',linked_report_section='hidden-information'))
        for m in COMMENT.finditer(text):
            c=m.group(1)
            if re.search(r'(?i)\b(api|endpoint|token|secret|old|deprecated|staging|admin|debug|internal)\b',c): items.append(evidence('hidden_info_collector',p,root,'comment_hidden_info',c,line_no(text,m.group(0)),confidence=.55,needs_review=True,linked_report_section='hidden-information'))
        if any(k in low for k in ['seed','mock','fixture','migration','template','email','sms','notification']):
            for m in PATH_RE.finditer(text): items.append(evidence('hidden_info_collector',p,root,'hidden_path_in_auxiliary_file',m.group(0),line_no(text,m.group(0)),confidence=.6,endpoint_relevance='medium',needs_review=True,linked_report_section='hidden-information'))
            for m in URL_RE.finditer(text): items.append(evidence('hidden_info_collector',p,root,'hidden_link_or_domain_in_auxiliary_file',m.group(0),line_no(text,m.group(0)),confidence=.6,endpoint_relevance='medium',needs_review=True,linked_report_section='hidden-information'))
    return output_report(args,'hidden_info_collector',items)
if __name__=='__main__': raise SystemExit(main())

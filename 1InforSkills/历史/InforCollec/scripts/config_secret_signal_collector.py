#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import re
from _info_collect_lib import common_parser, parse_scope, enforce_scope, iter_scoped_files, output_report, evidence, dry_run_report, read_text, line_no
PATTERNS=[
('environment_variable_reference',r'(?i)\b[A-Z][A-Z0-9_]{2,}\b'),
('secret_name_signal',r'(?i)\b([A-Z0-9_]*(SECRET|TOKEN|PASSWORD|PASSWD|PRIVATE_KEY|API_KEY|CLIENT_SECRET|COOKIE|SESSION)[A-Z0-9_]*)\b'),
('cicd_deployment_domain_or_registry',r'(?i)\b(deploy|staging|production|registry|image|environment|runner|workflow|pipeline|secrets\.)\b'),
('container_k8s_iac_service_signal',r'(?i)\b(containerPort|ports:|service:|image:|env:|ConfigMap|Secret|Ingress|terraform|bucket|queue|iam|vpc|redis|postgres|mysql|mongodb|internal)\b'),
('third_party_service_signal',r'(?i)\b(s3|oss|cos|stripe|sendgrid|twilio|firebase|supabase|redis|rabbitmq|kafka|elasticsearch|opensearch|sentry|datadog|grafana|prometheus)\b'),
('security_config_signal',r'(?i)\b(CORS|Access-Control-Allow-Origin|connect-src|Content-Security-Policy|cookie|SameSite|Secure|HttpOnly|redirect_uri|trustedOrigins|allowedOrigins|jwt|saml|oidc|oauth)\b'),
]
def main():
    ap=common_parser('Collect config, deployment, CI/CD, cloud, monitoring, third-party and secret-name signals with redaction.')
    args=ap.parse_args(); root=Path(args.input).resolve(); scope=parse_scope(args.scope, root); ok,reason=enforce_scope(root, scope)
    if args.dry_run: return dry_run_report(args,'config_secret_signal_collector',root,scope)
    if not ok: return output_report(args,'config_secret_signal_collector',[evidence('config_secret_signal_collector',root,root.parent,'out_of_scope_blocked',reason,1,confidence=1,severity_hint='blocker',needs_review=True)], {'scope_check':'FAIL'}) or 2
    items=[]
    for p in (iter_scoped_files(root, scope, args.max_files, args.timeout, args.scan_profile, args.follow_symlinks) if root.is_dir() else [root]):
        low=str(p).lower(); text=read_text(p)
        if any(x in low for x in ['.env','docker','compose','k8s','kubernetes','helm','.github','gitlab-ci','jenkins','terraform','.tf','ansible','config','settings']):
            items.append(evidence('config_secret_signal_collector',p,root,'config_or_deployment_file',p.name,1,confidence=.8,linked_report_section='configuration-deployment',scope_id=scope['scope_id']))
        for typ,pat in PATTERNS:
            for m in re.finditer(pat,text):
                val=m.group(0)
                if typ in {'environment_variable_reference','secret_name_signal'} and ('_' not in val and not val.isupper()):
                    continue
                items.append(evidence('config_secret_signal_collector',p,root,typ,val,line_no(text,val),confidence=.55,data_sensitivity='medium' if 'secret' in typ else 'low',needs_review=('secret' in typ),scope_id=scope['scope_id'],linked_report_section='configuration-deployment'))
    return output_report(args,'config_secret_signal_collector',items)
if __name__=='__main__': raise SystemExit(main())

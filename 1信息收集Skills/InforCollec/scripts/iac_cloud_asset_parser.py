#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import re, json
from _info_collect_lib import common_parser, parse_scope, enforce_scope, iter_scoped_files, dry_run_report, output_report, evidence, read_text, line_no
PATTERNS=[
 ('terraform_resource',r'\bresource\s+"([^"]+)"\s+"([^"]+)"'),
 ('terraform_data_source',r'\bdata\s+"([^"]+)"\s+"([^"]+)"'),
 ('k8s_kind',r'(?m)^kind:\s*([A-Za-z0-9_\-]+)'),
 ('k8s_secret_ref',r'(?i)\b(secretRef|secretKeyRef|configMapRef|imagePullSecrets)\b'),
 ('compose_service',r'(?m)^\s{0,4}([A-Za-z0-9_.-]+):\s*$'),
 ('github_actions_secret_name',r'\$\{\{\s*secrets\.([A-Za-z0-9_]+)\s*\}\}'),
 ('gitlab_ci_variable',r'\$([A-Z][A-Z0-9_]{5,})'),
 ('ingress_or_domain',r'(?i)\b(host|server_name|rule)\s*[:=]\s*["\']?([A-Za-z0-9_.-]+\.[A-Za-z]{2,})'),
 ('cloud_bucket_signal',r'(?i)\b(bucket|s3_bucket|oss_bucket|cos_bucket|storage_bucket)\b'),
 ('container_image',r'(?i)\bimage:\s*([^\s#]+)')
]
IAC_NAMES={'.tf','.tfvars','.yaml','.yml','.json','.conf'}
def main():
    ap=common_parser('Parse Terraform, Kubernetes, Helm, Compose, GitHub Actions, GitLab CI and reverse-proxy cloud asset signals.')
    args=ap.parse_args(); root=Path(args.input).resolve(); scope=parse_scope(args.scope,root); ok,reason=enforce_scope(root,scope)
    if args.dry_run: return dry_run_report(args,'iac_cloud_asset_parser',root,scope)
    if not ok: return output_report(args,'iac_cloud_asset_parser',[evidence('iac_cloud_asset_parser',root,root.parent,'out_of_scope_blocked',reason,1,confidence=1,severity_hint='blocker',needs_review=True)], {'scope_check':'FAIL'}) or 2
    items=[]
    for p in (iter_scoped_files(root,scope,args.max_files,args.timeout,args.scan_profile,args.follow_symlinks) if root.is_dir() else [root]):
        if p.suffix.lower() not in IAC_NAMES and not any(x in str(p).lower() for x in ['dockerfile','compose','nginx','caddy','traefik','.github','gitlab-ci','helm']): continue
        text=read_text(p)
        for typ,pat in PATTERNS:
            for m in re.finditer(pat,text):
                val=m.groups() if m.groups() else m.group(0)
                items.append(evidence('iac_cloud_asset_parser',p,root,'iac_cloud_asset',{'signal_type':typ,'value':val},line_no(text,m.group(0)),confidence=.62,endpoint_relevance='medium',data_sensitivity='medium' if 'secret' in typ else 'unknown',scope_id=scope['scope_id'],needs_review=True,linked_report_section='configuration-deployment'))
    return output_report(args,'iac_cloud_asset_parser',items,{'parser_scope':'Terraform/K8s/Helm/Compose/GitHubActions/GitLabCI/Nginx/Caddy/Traefik candidate static parsing'})
if __name__=='__main__': raise SystemExit(main())

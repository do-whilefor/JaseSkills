#!/usr/bin/env python3
"""Local code surface inventory for authorized repositories.

This script reads files and emits normalized candidate surfaces. It does not
execute project code, contact networks, or prove vulnerabilities.
"""
from __future__ import annotations
import argparse, hashlib, json, re
from pathlib import Path

SKIP={'.git','node_modules','vendor','__pycache__','.venv','venv','target','.next/cache','dist-info'}
TEXT={'.py','.js','.mjs','.cjs','.ts','.tsx','.jsx','.java','.go','.rs','.php','.rb','.cs','.html','.vue','.svelte','.json','.yaml','.yml','.toml','.xml','.properties','.conf','.env','.ini','.sh','.ps1','.graphql','.proto'}
PATTERNS=[
 ('http_route', re.compile(r"(?:app|router|route)\.(get|post|put|delete|patch|options|head)\s*\(\s*['\"]([^'\"]+)",re.I)),
 ('flask_django_fastapi_route', re.compile(r"@(?:app|router|bp)\.(get|post|put|delete|patch|route)\s*\(\s*['\"]([^'\"]+)",re.I)),
 ('spring_route', re.compile(r"@(GetMapping|PostMapping|PutMapping|DeleteMapping|PatchMapping|RequestMapping)\s*(?:\(|\(\s*value\s*=\s*)['\"]([^'\"]+)",re.I)),
 ('laravel_route', re.compile(r"Route::(get|post|put|delete|patch|any)\s*\(\s*['\"]([^'\"]+)",re.I)),
 ('go_route', re.compile(r"\.(GET|POST|PUT|DELETE|PATCH|HandleFunc|Handle)\s*\(\s*['\"]([^'\"]+)",re.I)),
 ('graphql_resolver_or_schema', re.compile(r"\b(type|query|mutation|subscription|resolver|GraphQLObjectType)\b",re.I)),
 ('websocket_event', re.compile(r"\b(socket\.on|io\.on|ws\.on|WebSocket|@SubscribeMessage|channel\(|broadcast\()",re.I)),
 ('rpc_method', re.compile(r"\b(service\s+\w+\s*\{|rpc\s+\w+\s*\(|grpc|tRPC|procedure\()",re.I)),
 ('cli_command', re.compile(r"\b(click\.command|argparse|commander\(|cobra\.Command|thor|Rake::Task|console\.command)",re.I)),
 ('cron_job', re.compile(r"\b(cron|schedule|Celery beat|@Scheduled|sidekiq-cron|node-cron|crontab)",re.I)),
 ('webhook', re.compile(r"\b(webhook|callbackUrl|callback_url|stripe\.webhooks|github webhook|slack/events)",re.I)),
 ('admin_debug_health_metrics', re.compile(r"/(admin|debug|health|metrics|actuator|swagger|openapi|docs)(?:/|['\"\s)]|$)",re.I)),
 ('upload_download', re.compile(r"\b(upload|download|send_file|sendFile|res\.download|multer|multipart|FormData|objectKey|bucket|Blob)",re.I)),
 ('authn_authz', re.compile(r"\b(login|logout|register|password reset|reset_password|OAuth|OIDC|SAML|JWT|session|cookie|CSRF|RBAC|ABAC|ACL|permission|policy|guard|middleware|tenant)",re.I)),
 ('config_risk', re.compile(r"\b(DEBUG\s*=\s*True|debug:\s*true|CORS|Access-Control-Allow-Origin|JWT_SECRET|SECRET_KEY|default password|0\.0\.0\.0|public-read|allow_credentials)",re.I)),
 ('dependency_manifest', re.compile(r"\b(package\.json|package-lock\.json|pnpm-lock\.yaml|yarn\.lock|requirements\.txt|poetry\.lock|pom\.xml|build\.gradle|go\.mod|Cargo\.toml|composer\.json|Gemfile\.lock)",re.I)),
 ('data_asset', re.compile(r"\b(user|account|organization|tenant|order|invoice|billing|file|document|report|export|backup|audit|token|key|secret)\b",re.I)),
]
MANIFEST_NAMES={'package.json','package-lock.json','pnpm-lock.yaml','yarn.lock','requirements.txt','poetry.lock','pyproject.toml','pom.xml','build.gradle','go.mod','Cargo.toml','composer.json','Gemfile','Gemfile.lock','Dockerfile','docker-compose.yml','docker-compose.yaml','Chart.yaml','values.yaml','nginx.conf'}

def h(s:str)->str: return hashlib.sha256(s.encode()).hexdigest()[:12]
def skip(p:Path)->bool: return any(x in p.parts for x in SKIP)
def line(text:str, off:int)->int: return text.count('\n',0,off)+1
def redact(s:str)->str:
    s=str(s).replace('\n',' ').strip()
    s=re.sub(r'(?i)(secret|token|password|api[_-]?key)\s*[:=]\s*[^\s,;]+', r'\1=****', s)
    return s[:240]

def scan(p:Path, root:Path):
    rel=str(p.relative_to(root)); out=[]
    try: text=p.read_text(encoding='utf-8', errors='ignore')
    except Exception: return out
    if p.name in MANIFEST_NAMES:
        out.append({'asset_id':'SURF-'+h(rel+':manifest'),'type':'dependency_or_deployment_manifest','source_file':rel,'line':1,'value':p.name,'status':'static_inventory_candidate'})
    for kind,rx in PATTERNS:
        for m in rx.finditer(text):
            val=m.group(0)
            if len(m.groups())>=2 and m.group(2): val=m.group(2)
            elif len(m.groups())>=1 and m.group(1): val=m.group(1)
            out.append({'asset_id':'SURF-'+h(f'{rel}:{kind}:{line(text,m.start())}:{val}'),'type':kind,'source_file':rel,'line':line(text,m.start()),'value':redact(val),'status':'static_candidate_needs_dynamic_validation','evidence_status':'candidate','dynamic_status':'not_validated'})
    return out

def main():
    ap=argparse.ArgumentParser(description='Build static code surface inventory from a local authorized repository.')
    ap.add_argument('root'); ap.add_argument('-o','--output',default='code-surface-inventory.jsonl'); ap.add_argument('--max-bytes',type=int,default=2_000_000)
    args=ap.parse_args(); root=Path(args.root).resolve(); count=0
    with Path(args.output).open('w',encoding='utf-8') as wf:
        for p in sorted(root.rglob('*')):
            if skip(p) or not p.is_file(): continue
            if p.suffix.lower() not in TEXT and p.name not in MANIFEST_NAMES: continue
            try:
                if p.stat().st_size>args.max_bytes: continue
            except Exception: continue
            for item in scan(p,root): wf.write(json.dumps(item,ensure_ascii=False)+'\n'); count+=1
    print(f'wrote {count} surface candidates to {args.output}')
if __name__=='__main__': main()

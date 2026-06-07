#!/usr/bin/env python3
"""Static hidden-information miner for authorized local repositories.

The script is intentionally read-only. It never contacts a network target and
never proves a vulnerability. It emits evidence candidates with redacted values
for follow-up by the runtime validation and quality-gate Skills.
"""
from __future__ import annotations
import argparse, hashlib, json, os, re, sys
from pathlib import Path
from typing import Iterable

SKIP_DIRS={'.git','node_modules','vendor','__pycache__','.pytest_cache','.mypy_cache','.ruff_cache','.venv','venv','target','coverage','dist-info','.idea','.vscode'}
TEXT_SUFFIXES={'.py','.js','.mjs','.cjs','.ts','.tsx','.jsx','.java','.go','.rs','.php','.rb','.cs','.html','.htm','.vue','.svelte','.json','.map','.yaml','.yml','.toml','.xml','.properties','.conf','.env','.ini','.sh','.bash','.zsh','.ps1','.graphql','.gql','.proto','.tf','.tfvars','.hcl','.md','.txt','.nginx','.caddy','.lock'}
MAX_FILE_SIZE=2_000_000
URL_PATH_RE=re.compile(r"(?<![A-Za-z0-9_])/(?:api|graphql|admin|internal|debug|health|metrics|docs|swagger|openapi|oauth|callback|webhook|ws|socket|upload|download|files|export|import|reports|tenant|org|user|v\d+)[A-Za-z0-9_./{}:<>?=&%-]*", re.I)
FULL_URL_RE=re.compile(r"https?://[^\s'\"<>`]+", re.I)
GRAPHQL_OP_RE=re.compile(r"\b(query|mutation|subscription)\s+([A-Za-z_][A-Za-z0-9_]*)", re.I)
WS_EVENT_RE=re.compile(r"\b(?:socket|io|ws|channel|consumer)\.(?:on|emit|subscribe)\s*\(\s*['\"]([^'\"]{2,120})", re.I)
FEATURE_RE=re.compile(r"\b(feature[_-]?flag|experiment|ab[_-]?test|rollout|remoteConfig|launchdarkly|splitio|unleash|optimizely|beta|preview)[A-Za-z0-9_ .:-]{0,120}", re.I)
AUTH_RE=re.compile(r"\b(jwt|session|cookie|csrf|oauth|oidc|saml|redirect_uri|redirectUri|trusted[_-]?origin|cors|allow[_-]?origin|sameSite|httpOnly|secure)\b", re.I)
SECRET_NAME_RE=re.compile(r"\b([A-Z0-9_]*(?:SECRET|TOKEN|PASSWORD|PASS|API[_-]?KEY|PRIVATE[_-]?KEY|ACCESS[_-]?KEY|CLIENT[_-]?SECRET|JWT)[A-Z0-9_]*)\b", re.I)
ACCOUNT_RE=re.compile(r"\b(admin|root|superuser|tenant|org|role|password|passwd|pwd|demo|seed|fixture|test account|default user)[A-Za-z0-9_@. :='\"-]{0,160}", re.I)
CLOUD_RE=re.compile(r"\b(aws_|azurerm_|google_|s3://|gs://|oss-|cos-|bucket|iam_role|iam_policy|vpc|subnet|queue|sns|sqs|rds|redis|elasticsearch|opensearch|firebase|supabase|stripe|sendgrid|twilio|datadog|sentry|grafana|prometheus)\b", re.I)
PROXY_RE=re.compile(r"\b(location\s+/[^\s{]+|ProxyPass\s+/[^\s]+|route\s+[^\s]+|PathPrefix\(`[^`]+`\)|handle_path\s+/[^\s]+|rewrite\s+[^\s]+)", re.I)
ERROR_RE=re.compile(r"\b(Traceback|stack trace|at\s+[A-Za-z0-9_$.]+\(|/home/[A-Za-z0-9_./-]+|/var/www/[A-Za-z0-9_./-]+|C:\\\\[A-Za-z0-9_\\. -]+)", re.I)
COMMENT_RE=re.compile(r"^\s*(#|//|/\*|\*|<!--|--|;)\s*(.{0,400})")


def sha(s: str) -> str:
    return hashlib.sha256(s.encode('utf-8', 'ignore')).hexdigest()[:16]

def redact(value: object) -> object:
    if not isinstance(value, str):
        return value
    s=value[:1000]
    s=re.sub(r"(eyJ[A-Za-z0-9_.-]{20,})", lambda m: m.group(1)[:3]+'****'+m.group(1)[-3:], s)
    s=re.sub(r"(?i)(secret|token|password|passwd|pwd|api[_-]?key|client[_-]?secret|jwt|private[_-]?key)(\s*[:=]\s*)['\"]?([^'\"\s,;]+)", lambda m: m.group(1)+m.group(2)+'****', s)
    s=re.sub(r"(?i)(sk_live|sk_test|AKIA|ASIA|ghp_|glpat-|xox[baprs]-)[A-Za-z0-9_\-]{8,}", lambda m: m.group(0)[:6]+'****'+m.group(0)[-4:], s)
    s=re.sub(r"\b[A-Za-z0-9_+./=-]{32,}\b", lambda m: m.group(0)[:4]+'****'+m.group(0)[-4:], s)
    return s

def emit(out: list[dict], root: Path, path: Path, line: int, typ: str, value: object, reason: str, extra: dict|None=None):
    rel=str(path.relative_to(root)).replace('\\','/')
    raw=json.dumps(value, ensure_ascii=False, sort_keys=True) if not isinstance(value,str) else value
    item={
        'asset_id':'HID-'+sha(f'{rel}:{line}:{typ}:{raw}'),
        'type':typ,
        'source_file':rel,
        'line':line,
        'value':redact(value),
        'value_sha256':sha(raw),
        'reason':reason,
        'evidence_status':'static_candidate_needs_dynamic_validation',
        'dynamic_status':'not_validated',
        'redaction_status':'redacted_or_metadata_only',
        'review_status':'needs_review',
        'next_step':'Correlate with source/runtime/docs ledgers, then validate only inside the authorized local scope.'
    }
    if extra: item.update(extra)
    out.append(item)

def safe_read(path: Path) -> str:
    try:
        if path.stat().st_size > MAX_FILE_SIZE:
            return ''
        return path.read_text(encoding='utf-8', errors='ignore')
    except Exception:
        return ''

def walk(root: Path, max_files: int|None=None) -> Iterable[Path]:
    count=0
    for p in root.rglob('*'):
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        if not p.is_file():
            continue
        if p.suffix.lower() not in TEXT_SUFFIXES and p.name not in {'Dockerfile','Makefile','Jenkinsfile','Caddyfile','robots.txt','sitemap.xml','security.txt'} and not p.name.startswith('.env'):
            continue
        count+=1
        if max_files and count>max_files:
            break
        yield p

def line_no(text: str, needle: str) -> int:
    idx=text.find(needle)
    if idx<0: return 1
    return text[:idx].count('\n')+1

def scan_json_struct(root: Path, path: Path, text: str, out: list[dict]):
    try:
        data=json.loads(text)
    except Exception:
        return
    name=path.name.lower()
    if name.endswith('.map'):
        for src in data.get('sources',[])[:1000]:
            emit(out, root, path, 1, 'source_map_original_source', src, 'source map reveals original source path/name')
        for src_text in data.get('sourcesContent',[])[:200]:
            for m in URL_PATH_RE.finditer(src_text or ''):
                emit(out, root, path, line_no(src_text,m.group(0)), 'source_map_endpoint_literal', m.group(0), 'source map sourcesContent contains endpoint literal')
    if 'postman' in name or (isinstance(data,dict) and 'item' in data and 'info' in data):
        def rec(items):
            for it in items or []:
                if isinstance(it,dict) and 'item' in it:
                    rec(it.get('item'))
                else:
                    req=(it or {}).get('request',{}) if isinstance(it,dict) else {}
                    url=req.get('url')
                    method=req.get('method')
                    raw=url.get('raw') if isinstance(url,dict) else url
                    if raw:
                        emit(out, root, path, 1, 'postman_hidden_endpoint', {'method':method,'url':str(raw)}, 'Postman collection may expose API not present in frontend')
        rec(data.get('item',[]) if isinstance(data,dict) else [])
    if isinstance(data,dict) and ('openapi' in data or 'swagger' in data):
        for route, methods in (data.get('paths') or {}).items():
            if isinstance(methods,dict):
                for method in methods.keys():
                    if str(method).lower() in {'get','post','put','delete','patch','options','head'}:
                        emit(out, root, path, 1, 'openapi_hidden_endpoint', {'method':str(method).upper(),'path':route}, 'OpenAPI/Swagger path may expose non-frontend API')
    if name in {'manifest.json','asset-manifest.json'} or name.endswith('manifest.json'):
        for key in ('start_url','scope','launch_path'):
            if isinstance(data,dict) and data.get(key):
                emit(out, root, path, 1, 'web_manifest_hidden_page', {key:data.get(key)}, 'web manifest contains navigable scope/start path')
                emit(out, root, path, 1, 'manifest_path_or_asset', str(data.get(key)), 'manifest/asset manifest contains route or asset path')
        def nested(v):
            if isinstance(v,dict):
                for vv in v.values(): yield from nested(vv)
            elif isinstance(v,list):
                for vv in v: yield from nested(vv)
            elif isinstance(v,str):
                yield v
        for v in nested(data):
            if URL_PATH_RE.search(v):
                emit(out, root, path, 1, 'manifest_path_or_asset', v, 'manifest/asset manifest contains route or asset path')

def scan_text(root: Path, path: Path, text: str, out: list[dict]):
    rel=str(path.relative_to(root)).replace('\\','/')
    low=rel.lower()
    lines=text.splitlines()
    for i,line in enumerate(lines,1):
        cm=COMMENT_RE.search(line)
        if cm and re.search(r"\b(api|endpoint|token|secret|password|todo|fixme|deprecated|staging|prod|admin|oauth|cors|tenant|role|debug|internal)\b", cm.group(2), re.I):
            emit(out, root, path, i, 'comment_hidden_security_hint', cm.group(2)[:300], 'comment may reveal endpoint, old domain, token name, account, or internal context')
        if 'sourceMappingURL=' in line:
            emit(out, root, path, i, 'source_map_reference', line.strip()[-300:], 'JS/CSS references a source map artifact')
        for m in GRAPHQL_OP_RE.finditer(line):
            emit(out, root, path, i, 'graphql_operation_name', {'operation_type':m.group(1),'operation_name':m.group(2)}, 'GraphQL operation name may reveal hidden query/mutation/subscription')
        for m in WS_EVENT_RE.finditer(line):
            emit(out, root, path, i, 'websocket_event_name', m.group(1), 'WebSocket/event channel name may define protocol surface')
        if FEATURE_RE.search(line):
            emit(out, root, path, i, 'feature_flag_or_experiment', FEATURE_RE.search(line).group(0), 'feature flag/experiment can hide disabled or role-gated functionality')
        if SECRET_NAME_RE.search(line):
            emit(out, root, path, i, 'secret_name_or_credential_key', SECRET_NAME_RE.search(line).group(1), 'credential variable name should be inventoried without exposing raw secret')
        if CLOUD_RE.search(line):
            emit(out, root, path, i, 'cloud_or_third_party_service_hint', CLOUD_RE.search(line).group(0), 'cloud/third-party asset or integration hint')
        if AUTH_RE.search(line):
            emit(out, root, path, i, 'auth_cors_cookie_oauth_hint', line.strip()[:300], 'auth/CORS/cookie/OAuth/SAML/OIDC configuration hint')
        if ERROR_RE.search(line):
            emit(out, root, path, i, 'error_or_internal_path_hint', ERROR_RE.search(line).group(0), 'error text or path can reveal deployment internals')
        if PROXY_RE.search(line):
            emit(out, root, path, i, 'reverse_proxy_hidden_path', PROXY_RE.search(line).group(0), 'reverse proxy config can expose hidden routes')
        if ACCOUNT_RE.search(line) and any(x in low for x in ('test','fixture','seed','migration','mock','example','demo')):
            emit(out, root, path, i, 'test_seed_default_account_or_role', ACCOUNT_RE.search(line).group(0), 'test/seed/migration files can reveal roles, tenants, default accounts')
        if any(x in low for x in ('.github/workflows','.gitlab-ci','jenkinsfile','circleci','buildkite','azure-pipelines')) and re.search(r'\b(deploy|staging|production|registry|image|secrets\.|environment|url|host)\b', line, re.I):
            emit(out, root, path, i, 'cicd_deployment_or_secret_name_hint', line.strip()[:300], 'CI/CD config can reveal environments, registries, deployment domains, or secret names')
        if any(x in low for x in ('dockerfile','docker-compose','compose.yml','.k8s','kubernetes','helm','terraform','.tf','ansible')) and re.search(r'\b(ports:|containerPort|service|image:|env:|environment:|host|bucket|queue|iam|vpc|redis|postgres|mysql|mongodb|internal)\b', line, re.I):
            emit(out, root, path, i, 'container_iac_internal_service_hint', line.strip()[:300], 'container/IaC file can reveal internal services, ports, env keys, or cloud assets')
    # URL/path literals and minified JS endpoint concentration
    minified = path.suffix.lower() in {'.js','.mjs','.cjs'} and ('.min.' in path.name or any(len(l)>500 for l in lines[:80]))
    for m in URL_PATH_RE.finditer(text):
        typ='minified_js_hidden_api' if minified else 'url_or_path_hidden_candidate'
        emit(out, root, path, line_no(text,m.group(0)), typ, m.group(0), 'literal endpoint/path found in artifact or source')
    for m in FULL_URL_RE.finditer(text):
        emit(out, root, path, line_no(text,m.group(0)), 'domain_or_callback_url_hint', m.group(0), 'full URL/domain/callback discovered in local artifact; do not contact unless authorized')
    if any(x in low for x in ('service-worker','sw.js','workbox')):
        for m in re.finditer(r"(?:precache|addAll|registerRoute|url:)\s*[^\n]{0,200}", text, re.I):
            emit(out, root, path, line_no(text,m.group(0)), 'service_worker_cache_or_route_hint', m.group(0), 'service worker/precache can reveal offline-only or lazy routes')
    if path.name in {'robots.txt','sitemap.xml','security.txt'} or '.well-known' in low:
        emit(out, root, path, 1, 'well_known_public_path_file', path.name, 'well-known/robots/sitemap/security file should be inventoried within authorization scope')
    if path.name in {'package.json'}:
        try:
            data=json.loads(text)
            for k,v in (data.get('scripts') or {}).items():
                if re.search(r'\b(debug|dev|staging|seed|migrate|admin|token|secret|deploy|proxy|mock)\b', k+' '+str(v), re.I):
                    emit(out, root, path, 1, 'package_script_hidden_command', {k:v}, 'package script can reveal debug, seed, deploy, proxy, or admin workflow')
        except Exception:
            pass
    if path.name in {'Makefile','Taskfile.yml','Taskfile.yaml','Justfile'}:
        for i,line in enumerate(lines,1):
            if re.match(r'^[A-Za-z0-9_.-]+\s*:', line) and re.search(r'\b(debug|dev|seed|migrate|deploy|admin|proxy|mock|staging)\b', line, re.I):
                emit(out, root, path, i, 'taskfile_hidden_command', line.strip()[:200], 'task/build target can reveal hidden operational workflow')
    if re.search(r'\.(dev|development|staging|stage|test|local|example)(\.|$)', path.name, re.I) or path.name.startswith('.env'):
        emit(out, root, path, 1, 'environment_variant_config', path.name, 'environment-specific config can reveal dev/staging/test differences')

def main() -> int:
    ap=argparse.ArgumentParser(description='Read-only hidden information miner for authorized local repositories.')
    ap.add_argument('root', help='Authorized local repository/project root')
    ap.add_argument('-o','--out',default='-', help='JSONL output path, or - for stdout')
    ap.add_argument('--dry-run', action='store_true', help='Only report scanned files and safety policy; no candidate extraction')
    ap.add_argument('--max-files', type=int, default=None, help='Maximum files to read')
    args=ap.parse_args()
    root=Path(args.root).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        print(f'root not found or not a directory: {root}', file=sys.stderr)
        return 2
    files=list(walk(root,args.max_files))
    if args.dry_run:
        meta={'schema_version':'hidden-info-miner.dry-run.v1','root':str(root),'files_to_scan':len(files),'network':'disabled','mode':'read_only'}
        print(json.dumps(meta, ensure_ascii=False))
        return 0
    out=[]
    for p in files:
        text=safe_read(p)
        if not text: continue
        scan_json_struct(root,p,text,out)
        scan_text(root,p,text,out)
    # de-duplicate by stable id
    seen=set(); unique=[]
    for item in out:
        if item['asset_id'] in seen: continue
        seen.add(item['asset_id']); unique.append(item)
    fh=sys.stdout if args.out=='-' else open(args.out,'w',encoding='utf-8')
    try:
        for item in unique:
            fh.write(json.dumps(item, ensure_ascii=False, sort_keys=True)+'\n')
    finally:
        if fh is not sys.stdout: fh.close()
    print(f'wrote {len(unique)} hidden information candidates', file=sys.stderr)
    return 0
if __name__=='__main__':
    raise SystemExit(main())

#!/usr/bin/env python3
"""Project inventory extractor v2 for local authorized repositories.

Read-only. Builds project_inventory_v2 for 03/04/05/07 without executing project code.
Covers ordinary and non-obvious information sources: language/framework/dependency,
config/env, API schemas, DB models/migrations/seeds/fixtures, auth/authz/tenant,
workers/queues/cron/CLI/RPC/webhook, Docker/Kubernetes/CI/CD, i18n, feature flags,
analytics, Storybook/MSW/E2E, fallback routes, debug flags and high-risk file flows.
"""
from __future__ import annotations
import argparse, json, re, hashlib
from pathlib import Path
from typing import Any

LANG_EXT = {'.py':'python','.js':'javascript','.jsx':'javascript','.ts':'typescript','.tsx':'typescript','.java':'java','.go':'go','.rs':'rust','.php':'php','.rb':'ruby','.cs':'csharp','.kt':'kotlin','.swift':'swift','.vue':'vue','.svelte':'svelte'}
DEPENDENCY_FILES = {'package.json','pnpm-lock.yaml','yarn.lock','package-lock.json','requirements.txt','pyproject.toml','poetry.lock','Pipfile','go.mod','Cargo.toml','composer.json','Gemfile','pom.xml','build.gradle','build.gradle.kts','.csproj'}
CONFIG_RE = re.compile(r"(config|settings|\.env|application\.(yml|yaml|properties)|docker-compose|helm|kustomization|values\.ya?ml|nginx|apache|vite|webpack|next\.config|nuxt\.config|tsconfig|babel)", re.I)
SCHEMA_RE = re.compile(r"(swagger|openapi|graphql|schema\.graphql|\.proto$|grpc|rpc|asyncapi|postman|insomnia)", re.I)
AUTH_RE = re.compile(r"(auth|login|logout|session|jwt|oauth|saml|sso|magic.?link|api.?key|passport|keycloak|casbin|rbac|abac|acl|policy|guard|permission|role)", re.I)
TENANT_RE = re.compile(r"(tenant|org|organization|workspace|company|team_id|tenant_id|org_id|workspace_id)", re.I)
WORKER_RE = re.compile(r"(worker|queue|consumer|job|cron|schedule|celery|bullmq|sidekiq|resque|rq|kafka|rabbit|sqs|pubsub|webhook|cli|command|grpc|rpc)", re.I)
DB_RE = re.compile(r"(model|models|entity|entities|migration|migrations|seed|seeds|factory|fixture|fixtures|prisma|typeorm|sequelize|sqlalchemy|hibernate|doctrine|eloquent)", re.I)
HIGH_RISK_RE = re.compile(r"(upload|download|import|export|preview|convert|transform|extract|unzip|archive|template|report|rich.?text|plugin|extension|loader|render|file)", re.I)
DEBUG_RE = re.compile(r"(debug|trace|verbose|devtools|error.?page|exception|fallback|catch.?all|health|metrics|admin)", re.I)
FEATURE_RE = re.compile(r"(feature.?flag|flags?|experiment|abtest|growthbook|launchdarkly|unleash|split\.io|variant)", re.I)
I18N_RE = re.compile(r"(i18n|locale|locales|translations?|messages|lang|\.po$|\.pot$)", re.I)
ANALYTICS_RE = re.compile(r"(track\(|analytics|segment|amplitude|mixpanel|posthog|gtag|dataLayer|eventName)", re.I)
TEST_FLOW_RE = re.compile(r"(storybook|stories\.|msw|mock|fixture|playwright|cypress|e2e|selenium|test|spec)", re.I)
DEFAULT_ACCOUNT_RE = re.compile(r"(admin@example|password|default.?user|demo.?user|test.?user|seed.?user|is_admin|role.?admin|superuser)", re.I)
ROUTE_RE = re.compile(r"(@(?:app|router)\.(?:get|post|put|patch|delete)\(['\"]([^'\"]+)|\.(?:get|post|put|patch|delete)\(['\"]([^'\"]+)|Route\(['\"]([^'\"]+)|path\(['\"]([^'\"]+))")

def safe_read(path: Path, limit: int = 200_000) -> str:
    try:
        if path.stat().st_size > limit:
            return path.read_text(encoding='utf-8', errors='ignore')[:limit]
        return path.read_text(encoding='utf-8', errors='ignore')
    except Exception:
        return ''

def sha16(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8','ignore')).hexdigest()[:16]

def add_signal(out: dict[str, list], key: str, path: str, signal: str, evidence: str = ''):
    out.setdefault(key, []).append({'path': path, 'signal': signal, 'evidence_hash': sha16(evidence or signal)})


def parse_dependency_semantics(path: Path, rel: str, text: str) -> list[dict[str, Any]]:
    rows=[]; name=path.name
    def add(kind, ecosystem='', package='', version='', script='', risk=''):
        rows.append({'path':rel,'kind':kind,'ecosystem':ecosystem,'package':package,'version':version,'script':script,'risk':risk,'evidence_hash':sha16('|'.join([kind,ecosystem,package,version,script,risk]))})
    try:
        if name=='package.json':
            obj=json.loads(text)
            for sec in ['dependencies','devDependencies','peerDependencies','optionalDependencies']:
                for pkg,ver in (obj.get(sec) or {}).items(): add('declared_dependency','npm',pkg,str(ver),risk='review_reachability')
            for s,cmd in (obj.get('scripts') or {}).items():
                risk='build_script_risk' if re.search(r'(postinstall|preinstall|curl|wget|bash|sh\s+-c|node\s+-e|eval|rm\s+-rf)',s+' '+cmd,re.I) else 'build_script'
                add('build_script','npm','', '', f'{s}: {cmd}', risk)
        elif name in {'package-lock.json','pnpm-lock.yaml','yarn.lock'}: add('lockfile','npm','','',risk='lockfile_present_requires_version_diff_review')
        elif name=='requirements.txt':
            for line in text.splitlines():
                line=line.strip();
                if line and not line.startswith('#'): add('declared_dependency','python',line.split('==')[0],line,'', 'review_reachability')
        elif name=='pyproject.toml': add('declared_dependency','python','','','pyproject dependency table','review_reachability')
        elif name=='go.mod':
            for m in re.finditer(r'\n\s*([A-Za-z0-9_./-]+)\s+(v[0-9][^\s]+)', text): add('declared_dependency','go',m.group(1),m.group(2),'','review_reachability')
        elif name=='Cargo.toml': add('declared_dependency','rust','','','Cargo.toml dependency/build sections','review_reachability_or_build_rs')
        elif name=='composer.json':
            obj=json.loads(text); 
            for sec in ['require','require-dev']:
                for pkg,ver in (obj.get(sec) or {}).items(): add('declared_dependency','composer',pkg,str(ver),'','review_reachability')
            for s,cmd in (obj.get('scripts') or {}).items(): add('build_script','composer','', '', f'{s}: {cmd}', 'build_script_risk')
        elif name in {'pom.xml','build.gradle','build.gradle.kts','Gemfile'}: add('declared_dependency','jvm_or_ruby','','',name,'review_reachability')
    except Exception as exc:
        rows.append({'path':rel,'kind':'dependency_parse_error','error':str(exc)[:200]})
    return rows

def parse_config_semantics(rel: str, text: str) -> list[dict[str, Any]]:
    rows=[]
    rules=[('cors','cors_policy',r'(Access-Control-Allow-Origin|allowedOrigins?|cors\(|credentials\s*[:=]\s*true|origin\s*[:=]\s*["\']\*)'),('auth','auth_config',r'(jwt|session|cookie|sameSite|secure\s*[:=]|oauth|saml|issuer|audience|jwks|callback|redirect_uri)'),('debug','debug_or_admin',r'(DEBUG\s*=\s*true|debug\s*[:=]\s*true|admin|actuator|swagger-ui|graphiql)'),('storage','storage_secret',r'(s3|bucket|blob|gcs|private_key|connectionString|DATABASE_URL|REDIS_URL)'),('tenant','tenant_config',r'(tenant|organization|workspace|multi.?tenant)')]
    for family,kind,rx in rules:
        if re.search(rx,text[:50000],re.I): rows.append({'path':rel,'family':family,'kind':kind,'evidence_hash':sha16(kind+rel),'confirmation_policy':'config signal only; requires code path and runtime evidence'})
    return rows


def extract(root: Path) -> dict[str, Any]:
    root = root.resolve()
    counters: dict[str,int] = {}
    files=[]
    signals: dict[str, list] = {
        'dependency_files': [], 'config_files': [], 'env_files': [], 'api_schema_files': [],
        'db_model_migration_seed_fixture': [], 'auth_signals': [], 'authz_policy_guard': [],
        'tenant_model_signals': [], 'default_test_demo_accounts': [], 'admin_debug_fallback': [],
        'worker_queue_cron_cli_rpc_webhook': [], 'docker_kubernetes_files': [], 'cicd_files': [],
        'high_risk_file_flows': [], 'feature_flags': [], 'i18n_messages': [], 'analytics_events': [],
        'storybook_mock_e2e_flows': [], 'routes': [], 'dependency_semantics': [], 'config_semantics': [], 'lockfile_version_reachability': [], 'build_script_risks': []
    }
    for p in sorted(root.rglob('*')):
        if not p.is_file():
            continue
        if any(part in {'.git','node_modules','vendor','__pycache__','.venv','dist-info'} for part in p.parts):
            continue
        rel = str(p.relative_to(root))
        ext = p.suffix.lower(); lang = LANG_EXT.get(ext)
        if lang: counters[lang] = counters.get(lang,0)+1
        text = safe_read(p)
        name = p.name
        files.append({'path': rel, 'suffix': ext, 'language': lang, 'size': p.stat().st_size})
        if name in DEPENDENCY_FILES:
            add_signal(signals, 'dependency_files', rel, name, text[:5000])
            dep_rows=parse_dependency_semantics(p, rel, text); signals['dependency_semantics'].extend(dep_rows)
            signals['lockfile_version_reachability'].extend([r for r in dep_rows if r.get('kind') in {'lockfile','declared_dependency'}])
            signals['build_script_risks'].extend([r for r in dep_rows if 'script' in r.get('kind','') or 'build_script' in r.get('risk','')])
        if CONFIG_RE.search(rel):
            add_signal(signals, 'config_files', rel, 'config_or_settings_file', text[:5000])
            signals['config_semantics'].extend(parse_config_semantics(rel, text))
        if '.env' in name.lower() or 'secret' in rel.lower(): add_signal(signals, 'env_files', rel, 'env_secret_candidate_file', text[:5000])
        if SCHEMA_RE.search(rel) or SCHEMA_RE.search(text[:5000]): add_signal(signals, 'api_schema_files', rel, 'api_schema_or_rpc_contract', text[:5000])
        if DB_RE.search(rel): add_signal(signals, 'db_model_migration_seed_fixture', rel, 'db_model_migration_seed_fixture', text[:5000])
        if AUTH_RE.search(rel) or AUTH_RE.search(text[:20000]): add_signal(signals, 'auth_signals', rel, 'auth_authz_token_policy_keyword', text[:5000])
        if re.search(r"(guard|policy|permission|role|rbac|abac|acl|canActivate|authorize)", rel + '\n' + text[:20000], re.I): add_signal(signals, 'authz_policy_guard', rel, 'authorization_policy_guard_signal', text[:5000])
        if TENANT_RE.search(rel) or TENANT_RE.search(text[:20000]): add_signal(signals, 'tenant_model_signals', rel, 'tenant_org_workspace_boundary_signal', text[:5000])
        if DEFAULT_ACCOUNT_RE.search(text[:50000]): add_signal(signals, 'default_test_demo_accounts', rel, 'default_demo_test_account_keyword', text[:5000])
        if DEBUG_RE.search(rel) or DEBUG_RE.search(text[:20000]): add_signal(signals, 'admin_debug_fallback', rel, 'admin_debug_fallback_health_signal', text[:5000])
        if WORKER_RE.search(rel) or WORKER_RE.search(text[:20000]): add_signal(signals, 'worker_queue_cron_cli_rpc_webhook', rel, 'non_http_or_async_entrypoint_signal', text[:5000])
        if re.search(r"(Dockerfile|docker-compose|k8s|kubernetes|helm|values\.ya?ml|deployment\.ya?ml|service\.ya?ml)", rel, re.I): add_signal(signals, 'docker_kubernetes_files', rel, 'container_or_kubernetes_surface', text[:5000])
        if re.search(r"(\.github/workflows|gitlab-ci|circleci|jenkins|azure-pipelines|buildkite|drone\.yml)", rel, re.I): add_signal(signals, 'cicd_files', rel, 'ci_cd_surface', text[:5000])
        if HIGH_RISK_RE.search(rel) or HIGH_RISK_RE.search(text[:20000]): add_signal(signals, 'high_risk_file_flows', rel, 'upload_download_import_export_preview_convert_template_plugin', text[:5000])
        if FEATURE_RE.search(rel) or FEATURE_RE.search(text[:20000]): add_signal(signals, 'feature_flags', rel, 'feature_flag_or_experiment_signal', text[:5000])
        if I18N_RE.search(rel): add_signal(signals, 'i18n_messages', rel, 'i18n_locale_message_source', text[:5000])
        if ANALYTICS_RE.search(text[:50000]): add_signal(signals, 'analytics_events', rel, 'analytics_event_signal', text[:5000])
        if TEST_FLOW_RE.search(rel): add_signal(signals, 'storybook_mock_e2e_flows', rel, 'storybook_mock_fixture_e2e_flow_source', text[:5000])
        for m in ROUTE_RE.finditer(text):
            route = next((g for g in m.groups()[1:] if g), '')
            if route:
                signals['routes'].append({'path': rel, 'route': route, 'line': text[:m.start()].count('\n')+1, 'evidence_hash': sha16(m.group(0))})
    return {
        'schema_version':'project_inventory_v2', 'root': str(root), 'non_destructive': True,
        'file_count': len(files), 'languages': counters, 'files': files[:8000],
        **signals,
        'coverage_contract': {
            'feeds': ['03-code-knowledge-graph','04-attack-surface-mapping','05-js-audit-runtime','07-vulnerability-hunting-engine'],
            'confirmation_policy': 'inventory signals are never vulnerabilities; they only create mapped candidates and coverage obligations'
        }
    }

def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument('project_root'); ap.add_argument('--out','-o')
    args = ap.parse_args(); root = Path(args.project_root).resolve()
    if not root.exists() or not root.is_dir():
        print(json.dumps({'error':'project_root must be an existing local directory','path':str(root)}, ensure_ascii=False, indent=2)); return 2
    result = extract(root); text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True); Path(args.out).write_text(text+'\n', encoding='utf-8')
    else: print(text)
    return 0
if __name__ == '__main__': raise SystemExit(main())

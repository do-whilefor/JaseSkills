#!/usr/bin/env python3
"""Read-only config and dependency inventory for authorized local repositories.

Outputs JSONL candidates with source file and line evidence. It does not install,
execute dependency scripts, contact package registries, or claim CVE status.
"""
from __future__ import annotations
import argparse, hashlib, json, re, tomllib
from pathlib import Path
from typing import Any

SKIP = {'.git','node_modules','vendor','__pycache__','.venv','venv','target','.next/cache','dist-info'}
DEP_FILES = {'package.json','package-lock.json','pnpm-lock.yaml','yarn.lock','requirements.txt','pyproject.toml','poetry.lock','pom.xml','build.gradle','composer.json','composer.lock','Gemfile','Gemfile.lock','go.mod','go.sum','Cargo.toml','Cargo.lock'}
CONFIG_NAMES = {'.env','.env.example','settings.py','application.yml','application.yaml','config.yml','config.yaml','config.json','docker-compose.yml','docker-compose.yaml','Dockerfile','nginx.conf','apache.conf','httpd.conf','Caddyfile','.gitlab-ci.yml','Jenkinsfile'}
CONFIG_SUFFIXES = {'.env','.yaml','.yml','.json','.toml','.ini','.conf','.properties'}
RISK_PATTERNS = [
    ('debug_enabled', re.compile(r'(?i)\b(DEBUG\s*=\s*True|debug\s*[:=]\s*true|NODE_ENV\s*[:=]\s*development)')),
    ('cors_candidate', re.compile(r'(?i)(Access-Control-Allow-Origin|cors|allow_origins|allowedOrigins|allow_credentials)')),
    ('cookie_session_candidate', re.compile(r'(?i)(session|cookie|SameSite|HttpOnly|Secure|SESSION_SECRET)')),
    ('jwt_oauth_candidate', re.compile(r'(?i)(JWT|OIDC|OAuth|SAML|client_secret|redirect_uri|issuer|audience|jwks)')),
    ('object_storage_candidate', re.compile(r'(?i)(S3|bucket|gcs|blob|object_storage|public-read|signed_url|presigned)')),
    ('database_cache_queue_candidate', re.compile(r'(?i)(DATABASE_URL|postgres|mysql|mongodb|redis|rabbitmq|kafka|celery|queue)')),
    ('reverse_proxy_surface', re.compile(r'(?i)(proxy_pass|server_name|listen\s+\d+|location\s+/|root\s+|alias\s+)')),
    ('ci_artifact_secret_risk', re.compile(r'(?i)(artifacts?:|cache:|upload|secrets\.|env:|GITHUB_TOKEN|CI_JOB_TOKEN)')),
    ('feature_flag_candidate', re.compile(r'(?i)(feature[_-]?flag|experiment|ab[_-]?test|rollout|launchdarkly|split\.io)')),
]
DEP_NAME_RE = re.compile(r'^\s*([A-Za-z0-9_.\-]+)(?:\[.*?\])?\s*(?:==|>=|<=|~=|>|<|=)\s*([^\s;#]+)', re.M)

def skip(p: Path) -> bool:
    return any(x in p.parts for x in SKIP)

def h(*parts: Any) -> str:
    return 'CFG-' + hashlib.sha256('|'.join(map(str, parts)).encode()).hexdigest()[:14]

def line_of(text: str, offset: int) -> int:
    return text.count('\n', 0, offset) + 1

def redact(s: str) -> str:
    s = str(s).replace('\n', ' ').strip()
    s = re.sub(r'(?i)(secret|token|password|passwd|api[_-]?key|client[_-]?secret)(\s*[:=]\s*)([^\s,;]+)', r'\1\2****', s)
    s = re.sub(r'(?i)((?:mysql|postgres|postgresql|mongodb|redis)://[^:]+:)[^@]+(@)', r'\1****\2', s)
    return s[:260]

def emit(kind: str, root: Path, path: Path, line: int, value: Any, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    rel = str(path.relative_to(root))
    row = {
        'asset_id': h(rel, kind, line, value),
        'type': kind,
        'source_file': rel,
        'line': line,
        'value': value,
        'evidence_status': 'static_candidate_needs_dynamic_validation',
        'dynamic_status': 'not_validated',
        'redaction_status': 'redacted_or_metadata_only'
    }
    if extra:
        row.update(extra)
    return row

def parse_package_json(root: Path, p: Path, text: str) -> list[dict[str, Any]]:
    rows = []
    try:
        data = json.loads(text)
    except Exception:
        return [emit('dependency_manifest_parse_error', root, p, 1, 'package.json parse failed')]
    for section in ['dependencies','devDependencies','peerDependencies','optionalDependencies']:
        deps = data.get(section) or {}
        if isinstance(deps, dict):
            for name, ver in deps.items():
                rows.append(emit('dependency_entry', root, p, 1, {'ecosystem':'npm','section':section,'name':name,'version':str(ver)}, {'dependency_name':name,'dependency_version':str(ver)}))
    scripts = data.get('scripts') or {}
    if isinstance(scripts, dict):
        for name, cmd in scripts.items():
            kind = 'dependency_script_candidate'
            rows.append(emit(kind, root, p, 1, {'script':name,'command_preview':redact(cmd)}, {'script_name':name}))
    return rows

def parse_pyproject(root: Path, p: Path, text: str) -> list[dict[str, Any]]:
    rows = []
    try:
        data = tomllib.loads(text)
    except Exception:
        return [emit('dependency_manifest_parse_error', root, p, 1, 'pyproject.toml parse failed')]
    project = data.get('project') or {}
    for dep in project.get('dependencies') or []:
        rows.append(emit('dependency_entry', root, p, 1, {'ecosystem':'python','name_spec':str(dep)}))
    poetry = ((data.get('tool') or {}).get('poetry') or {}).get('dependencies') or {}
    if isinstance(poetry, dict):
        for name, ver in poetry.items():
            rows.append(emit('dependency_entry', root, p, 1, {'ecosystem':'python-poetry','name':name,'version':str(ver)}))
    return rows

def parse_requirements(root: Path, p: Path, text: str) -> list[dict[str, Any]]:
    rows = []
    for m in DEP_NAME_RE.finditer(text):
        rows.append(emit('dependency_entry', root, p, line_of(text, m.start()), {'ecosystem':'python','name':m.group(1),'version':m.group(2)}))
    return rows

def scan_text(root: Path, p: Path, text: str) -> list[dict[str, Any]]:
    rows = []
    name = p.name
    if name in DEP_FILES:
        rows.append(emit('dependency_manifest', root, p, 1, name))
    if name in CONFIG_NAMES or p.suffix.lower() in CONFIG_SUFFIXES:
        rows.append(emit('configuration_file', root, p, 1, name))
    for kind, rx in RISK_PATTERNS:
        for m in rx.finditer(text):
            start = max(0, m.start() - 80); end = min(len(text), m.end() + 120)
            rows.append(emit(kind, root, p, line_of(text, m.start()), redact(text[start:end])))
    if name == 'package.json': rows.extend(parse_package_json(root, p, text))
    elif name == 'pyproject.toml': rows.extend(parse_pyproject(root, p, text))
    elif name == 'requirements.txt': rows.extend(parse_requirements(root, p, text))
    elif name in {'go.mod','Cargo.toml','composer.json','Gemfile','pom.xml','build.gradle'}:
        rows.append(emit('dependency_manifest_requires_backend_parser', root, p, 1, name, {'notes':'Recorded for parser/backend-specific follow-up; no CVE claim.'}))
    return rows

def main() -> int:
    ap = argparse.ArgumentParser(description='Collect config/dependency candidates from a local authorized repository.')
    ap.add_argument('root')
    ap.add_argument('-o','--output', default='config-dependency-inventory.jsonl')
    ap.add_argument('--max-bytes', type=int, default=2_000_000)
    args = ap.parse_args(); root = Path(args.root).resolve(); count = 0
    with Path(args.output).open('w', encoding='utf-8') as wf:
        for p in sorted(root.rglob('*')):
            if skip(p) or not p.is_file():
                continue
            if p.name not in DEP_FILES and p.name not in CONFIG_NAMES and p.suffix.lower() not in CONFIG_SUFFIXES:
                continue
            try:
                if p.stat().st_size > args.max_bytes: continue
                text = p.read_text(encoding='utf-8', errors='ignore')
            except Exception:
                continue
            for row in scan_text(root, p, text):
                wf.write(json.dumps(row, ensure_ascii=False) + '\n'); count += 1
    print(f'wrote {count} config/dependency candidates to {args.output}')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())

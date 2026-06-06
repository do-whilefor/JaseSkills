#!/usr/bin/env python3
"""Read-only lazy JS asset discovery ledger.

The extractor scans local project files for lazy-loading, chunk, source-map,
service-worker, route, API-client, GraphQL, WebSocket/SSE and feature-flag
signals. It does not fetch remote assets and never confirms vulnerabilities.
"""
from __future__ import annotations
import argparse, hashlib, json, re, sys
from pathlib import Path
from typing import Any

JS_EXT = {'.js', '.jsx', '.ts', '.tsx', '.mjs', '.cjs', '.vue', '.svelte'}
HTML_EXT = {'.html', '.htm'}
CONFIG_EXT = {'.json', '.yaml', '.yml', '.toml', '.config.js', '.config.ts'}
SKIP = {'.git', 'node_modules', 'vendor', '__pycache__', '.venv', 'venv', 'target', '.next/cache', '.nuxt/cache'}
MANIFEST_NAMES = {'asset-manifest.json', 'manifest.json', 'precache-manifest.json', 'build-manifest.json', 'routes-manifest.json', 'server-reference-manifest.json'}
SERVICE_WORKER_NAMES = {'service-worker.js', 'serviceworker.js', 'sw.js', 'workbox-*.js'}

PATTERNS = {
    'dynamic_import': re.compile(r"import\s*\(\s*([`'\"])(?P<target>[^`'\"]+)\1", re.I),
    'react_lazy': re.compile(r"React\.lazy\s*\(|lazy\s*\(\s*\(\s*\)\s*=>\s*import\s*\(", re.I),
    'next_dynamic': re.compile(r"\bdynamic\s*\(\s*\(\s*\)\s*=>\s*import\s*\(", re.I),
    'vue_async': re.compile(r"defineAsyncComponent\s*\(|component\s*:\s*\(\s*\)\s*=>\s*import\s*\(", re.I),
    'angular_lazy': re.compile(r"loadChildren\s*:\s*\(\s*\)\s*=>\s*import\s*\(", re.I),
    'route_path': re.compile(r"\bpath\s*[:=]\s*([`'\"])(?P<route>/(?:admin|internal|debug|test|mock|preview|api|v\d+|[A-Za-z0-9_./:$-]+))\1", re.I),
    'next_page': re.compile(r"/(?:app|pages)/(?P<page>[^\n\r]+?)\.(?:js|jsx|ts|tsx)$", re.I),
    'api_path': re.compile(r"([`'\"])(?P<api>/(?:api|graphql|rpc|admin|internal|v\d+|legacy|old|beta)/[^`'\"\s<>()]+)\1", re.I),
    'fetch_call': re.compile(r"\b(fetch|axios\.(?:get|post|put|patch|delete)|[A-Za-z0-9_$]+\.(?:get|post|put|patch|delete))\s*\(\s*([`'\"])(?P<api>[^`'\"]+)\2", re.I),
    'graphql': re.compile(r"\b(gql`|query\s+[A-Za-z0-9_]+|mutation\s+[A-Za-z0-9_]+|subscription\s+[A-Za-z0-9_]+|fragment\s+[A-Za-z0-9_]+|persistedQuery|sha256Hash)", re.I),
    'ws_sse': re.compile(r"\b(new\s+WebSocket|EventSource)\s*\(", re.I),
    'service_worker': re.compile(r"\b(register\s*\(\s*['\"][^'\"]*(?:sw|service-worker)|caches\.open|cache\.addAll|workbox|precacheAndRoute|__WB_MANIFEST)", re.I),
    'sourcemap_comment': re.compile(r"//#\s*sourceMappingURL=(?P<map>[^\s]+)"),
    'preload': re.compile(r"<link[^>]+rel=[\"'](?P<rel>preload|prefetch|modulepreload)[\"'][^>]+href=[\"'](?P<href>[^\"']+)[\"']", re.I),
    'script_src': re.compile(r"<script[^>]+src=[\"'](?P<src>[^\"']+)[\"']", re.I),
    'feature_flag': re.compile(r"\b(featureFlags?|flags?|experiments?|abTest|launchdarkly|unleash|growthbook|isAdmin|hasPermission|can\(|tenant|orgId|workspaceId|role)\b.{0,180}", re.I),
    'hidden_route': re.compile(r"\b(admin|internal|debug|dev|test|mock|preview|staging|legacy|old|beta|graphql|graphiql|swagger|storybook|redoc|playground)\b", re.I),
}

REDACT = re.compile(r"(token|secret|password|authorization|cookie|api[_-]?key)", re.I)

def safe_read(path: Path) -> str:
    try:
        if path.stat().st_size > 5_000_000:
            return ''
        return path.read_text(encoding='utf-8', errors='ignore')
    except Exception:
        return ''

def rel(root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve())).replace('\\', '/')
    except Exception:
        return str(path)

def line_of(text: str, pos: int) -> int:
    return text[:pos].count('\n') + 1

def should_skip(path: Path) -> bool:
    parts = set(path.parts)
    return bool(parts & SKIP) or any('/' + s + '/' in str(path).replace('\\', '/') for s in SKIP)

def sha16(s: str) -> str:
    return hashlib.sha256(s.encode('utf-8', 'ignore')).hexdigest()[:16]

def add(row_list: list[dict[str, Any]], root: Path, path: Path, line: int, kind: str, value: str, extra: dict[str, Any] | None = None) -> None:
    item = {'id': f'{kind}-{sha16(rel(root, path)+str(line)+value)}', 'file': rel(root, path), 'line': line, 'kind': kind, 'value': '<redacted>' if REDACT.search(value) else value}
    if extra:
        item.update(extra)
    row_list.append(item)

def scan_file(root: Path, path: Path, out: dict[str, Any]) -> None:
    text = safe_read(path)
    if not text and path.suffix.lower() != '.map':
        return
    rp = rel(root, path)
    suffix = path.suffix.lower()
    if suffix in JS_EXT:
        out['static_js_assets'].append({'file': rp, 'sha256_16': sha16(text), 'size': path.stat().st_size if path.exists() else 0})
    if suffix == '.map' or rp.endswith('.js.map'):
        out['source_maps'].append({'file': rp, 'kind': 'source_map_file', 'has_sources_content': 'sourcesContent' in text, 'size': path.stat().st_size if path.exists() else 0})
    if path.name in MANIFEST_NAMES or ('manifest' in path.name.lower() and suffix == '.json'):
        out['build_manifests'].append({'file': rp, 'kind': 'manifest_candidate', 'size': path.stat().st_size if path.exists() else 0})
        try:
            obj = json.loads(text or '{}')
            blob = json.dumps(obj, ensure_ascii=False)
            for m in re.finditer(r"[\w./-]+\.js(?:\?[^\"']*)?", blob):
                out['build_manifests'].append({'file': rp, 'kind': 'manifest_js_chunk', 'chunk': m.group(0)})
        except Exception:
            pass
    if 'service-worker' in path.name.lower() or path.name.lower() == 'sw.js' or 'workbox' in path.name.lower():
        out['service_workers'].append({'file': rp, 'kind': 'service_worker_file', 'size': path.stat().st_size if path.exists() else 0})
    if suffix in HTML_EXT:
        for m in PATTERNS['script_src'].finditer(text):
            add(out['html_js_references'], root, path, line_of(text, m.start()), 'script_src', m.group('src'))
        for m in PATTERNS['preload'].finditer(text):
            add(out['html_js_references'], root, path, line_of(text, m.start()), m.group('rel'), m.group('href'))
    if suffix in JS_EXT or suffix in HTML_EXT or suffix in {'.json', '.map'}:
        for name, rx in PATTERNS.items():
            if name in {'script_src', 'preload'}:
                continue
            for m in rx.finditer(text):
                line = line_of(text, m.start())
                if name == 'dynamic_import':
                    add(out['dynamic_imports'], root, path, line, name, m.group('target'), {'browser_trigger_required': True})
                elif name in {'react_lazy', 'next_dynamic', 'vue_async', 'angular_lazy'}:
                    add(out['framework_lazy_routes'], root, path, line, name, m.group(0)[:120], {'browser_trigger_required': True})
                elif name == 'route_path':
                    add(out['frontend_routes'], root, path, line, name, m.group('route'))
                elif name == 'api_path':
                    add(out['api_clients'], root, path, line, name, m.group('api'), {'confirmation_policy': 'candidate_only_requires_backend_guard_and_dynamic_evidence'})
                elif name == 'fetch_call':
                    add(out['api_clients'], root, path, line, name, m.group('api'), {'confirmation_policy': 'candidate_only_requires_backend_guard_and_dynamic_evidence'})
                elif name == 'graphql':
                    add(out['graphql'], root, path, line, name, m.group(0)[:120])
                elif name == 'ws_sse':
                    add(out['websocket_sse'], root, path, line, name, m.group(0)[:120])
                elif name == 'service_worker':
                    add(out['service_workers'], root, path, line, name, m.group(0)[:160])
                elif name == 'sourcemap_comment':
                    add(out['source_maps'], root, path, line, name, m.group('map'))
                elif name == 'feature_flag':
                    add(out['feature_flags'], root, path, line, name, m.group(0)[:180])
                elif name == 'hidden_route':
                    add(out['hidden_route_signals'], root, path, line, name, m.group(0)[:120])


def discover(root: Path) -> dict[str, Any]:
    root = root.resolve()
    out: dict[str, Any] = {
        'schema_version': 'lazy_js_asset_ledger_v1',
        'non_destructive': True,
        'root': str(root),
        'files_scanned': 0,
        'static_js_assets': [],
        'html_js_references': [],
        'build_manifests': [],
        'source_maps': [],
        'service_workers': [],
        'dynamic_imports': [],
        'framework_lazy_routes': [],
        'frontend_routes': [],
        'api_clients': [],
        'graphql': [],
        'websocket_sse': [],
        'feature_flags': [],
        'hidden_route_signals': [],
        'browser_trigger_required': [],
        'evidence_gaps': [],
        'completion_policy': 'candidate_only_until_browser_interaction_matrix_and_backend_guard_mapping_exist'
    }
    for path in sorted(root.rglob('*')):
        if not path.is_file() or should_skip(path):
            continue
        lower = path.name.lower()
        suffix = path.suffix.lower()
        if suffix in JS_EXT or suffix in HTML_EXT or suffix in {'.json', '.map'} or lower in MANIFEST_NAMES or 'manifest' in lower or 'service-worker' in lower or lower == 'sw.js':
            out['files_scanned'] += 1
            scan_file(root, path, out)
    for key in ['dynamic_imports', 'framework_lazy_routes', 'source_maps', 'service_workers', 'build_manifests', 'api_clients']:
        if not out[key]:
            out['evidence_gaps'].append({'missing': key, 'impact': 'cannot claim complete lazy JS coverage without explicitly absent evidence or deeper scan'})
    for item in out['dynamic_imports'] + out['framework_lazy_routes'] + out['frontend_routes'] + out['hidden_route_signals']:
        out['browser_trigger_required'].append({'source_id': item.get('id'), 'file': item.get('file'), 'line': item.get('line'), 'reason': 'requires browser navigation/interaction to prove runtime reachability'})
    out['summary'] = {k: len(v) for k, v in out.items() if isinstance(v, list)}
    return out

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('root', nargs='?', default='.')
    ap.add_argument('--out')
    args = ap.parse_args()
    result = discover(Path(args.root))
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(text + '\n', encoding='utf-8')
    print(text)
    return 0

if __name__ == '__main__':
    raise SystemExit(main())

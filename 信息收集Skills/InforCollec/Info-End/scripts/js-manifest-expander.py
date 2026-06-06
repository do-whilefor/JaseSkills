#!/usr/bin/env python3
"""Expand local frontend manifests/service-worker/build artifacts into JS asset candidates."""
from __future__ import annotations
import argparse, hashlib, json, re
from pathlib import Path
from typing import Any

SKIP = {'.git','node_modules','vendor','__pycache__','.venv','venv','.next/cache'}
MANIFEST_NAMES = {'asset-manifest.json','build-manifest.json','react-loadable-manifest.json','manifest.json','service-worker.js','sw.js','precache-manifest.js','precache-manifest.json'}
JS_RE = re.compile(r"(?P<asset>[/A-Za-z0-9_.\-@]+\.(?:js|mjs|cjs|map))(?:[?#][^'\"\s,)}\]]*)?", re.I)
URL_RE = re.compile(r"(?P<url>[/A-Za-z0-9_.\-{}:$?&=%+]+)")

def h(*parts: Any) -> str:
    return 'JSM-' + hashlib.sha256('|'.join(map(str, parts)).encode()).hexdigest()[:14]

def skip(p: Path) -> bool:
    return any(x in p.parts for x in SKIP)

def line_of(text: str, off: int) -> int:
    return text.count('\n', 0, off) + 1

def emit(root: Path, p: Path, line: int, kind: str, value: Any) -> dict[str, Any]:
    rel = str(p.relative_to(root))
    return {
        'asset_id': h(rel, line, kind, value),
        'type': kind,
        'source_file': rel,
        'line': line,
        'value': value,
        'evidence_status': 'static_candidate_needs_dynamic_validation',
        'dynamic_status': 'not_validated',
        'redaction_status': 'metadata_only'
    }

def walk_json(obj: Any, out: list[str]) -> None:
    if isinstance(obj, dict):
        for v in obj.values(): walk_json(v, out)
    elif isinstance(obj, list):
        for v in obj: walk_json(v, out)
    elif isinstance(obj, str):
        if re.search(r'\.(js|mjs|cjs|map)(?:[?#]|$)', obj, re.I) or obj.startswith('/'):
            out.append(obj)

def scan_file(root: Path, p: Path) -> list[dict[str, Any]]:
    try: text = p.read_text(encoding='utf-8', errors='ignore')
    except Exception: return []
    rows = []
    lower = p.name.lower()
    if p.suffix.lower() == '.json':
        try:
            vals: list[str] = []
            walk_json(json.loads(text), vals)
            for v in vals:
                kind = 'frontend_manifest_asset' if re.search(r'\.(js|mjs|cjs|map)', v, re.I) else 'frontend_manifest_url_hint'
                rows.append(emit(root, p, 1, kind, v))
        except Exception:
            rows.append(emit(root, p, 1, 'frontend_manifest_parse_error', lower))
    if 'service-worker' in lower or lower in {'sw.js','precache-manifest.js'} or 'workbox' in text:
        rows.append(emit(root, p, 1, 'service_worker_or_precache_file', lower))
    for m in JS_RE.finditer(text):
        rows.append(emit(root, p, line_of(text, m.start()), 'js_asset_from_manifest_or_worker', m.group('asset')))
    for m in re.finditer(r'__WB_MANIFEST|precacheAndRoute|workbox|CacheStorage|caches\.open|importScripts', text, re.I):
        rows.append(emit(root, p, line_of(text, m.start()), 'service_worker_cache_hint', m.group(0)))
    return rows

def main() -> int:
    ap = argparse.ArgumentParser(description='Expand local JS manifest and service-worker artifacts into candidate asset rows.')
    ap.add_argument('root'); ap.add_argument('-o','--output', default='js-manifest-assets.jsonl')
    args = ap.parse_args(); root = Path(args.root).resolve(); count = 0
    with Path(args.output).open('w', encoding='utf-8') as wf:
        for p in sorted(root.rglob('*')):
            if skip(p) or not p.is_file(): continue
            lower = p.name.lower()
            if lower not in MANIFEST_NAMES and not lower.endswith(('.webmanifest','.map')) and 'manifest' not in lower:
                continue
            for row in scan_file(root, p):
                wf.write(json.dumps(row, ensure_ascii=False)+'\n'); count += 1
    print(f'wrote {count} JS manifest/worker candidates to {args.output}')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())

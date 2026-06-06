#!/usr/bin/env python3
"""Safe static route/artifact extractor for authorized local projects.
It emits candidates only. It does not prove exposure.
"""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path

URL_RE = re.compile(r"(?P<url>(?:https?://[^\s'\"<>]+)|(?:/[A-Za-z0-9_./{}:$?&=%-]{2,}))")
FETCH_RE = re.compile(r"\b(fetch|axios\.(?:get|post|put|delete|patch)|request|graphql|WebSocket|EventSource)\b", re.I)
SOURCEMAP_RE = re.compile(r"sourceMappingURL=([^\s]+)")
SENSITIVE_NAME_RE = re.compile(r"(token|secret|api[_-]?key|password|passwd|private[_-]?key|session|cookie|database[_-]?url|client[_-]?secret)", re.I)
ROUTE_HINT_RE = re.compile(r"\b(router|route|controller|handler|endpoint|app\.(get|post|put|delete|patch)|@Get|@Post|@RequestMapping)\b", re.I)

SKIP_DIRS = {'.git', 'node_modules', 'vendor', '__pycache__', '.venv', 'venv', 'dist-info', '.next/cache'}
TEXT_EXTS = {'.js', '.ts', '.tsx', '.jsx', '.vue', '.svelte', '.py', '.java', '.go', '.rs', '.php', '.rb', '.cs', '.json', '.yml', '.yaml', '.toml', '.xml', '.md', '.conf', '.env', '.properties', '.html', '.css'}

def redact(s: str) -> str:
    if len(s) <= 12:
        return s
    return s[:6] + '****' + s[-4:]

def should_skip(path: Path) -> bool:
    return any(part in SKIP_DIRS for part in path.parts)

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('root', help='project root')
    ap.add_argument('-o', '--output', default='static-candidates.jsonl')
    ap.add_argument('--max-bytes', type=int, default=2_000_000)
    args = ap.parse_args()
    root = Path(args.root).resolve()
    out = Path(args.output)
    count = 0
    with out.open('w', encoding='utf-8') as wf:
        for p in root.rglob('*'):
            if should_skip(p) or not p.is_file() or p.suffix.lower() not in TEXT_EXTS:
                continue
            try:
                if p.stat().st_size > args.max_bytes:
                    continue
                text = p.read_text(encoding='utf-8', errors='ignore')
            except Exception:
                continue
            rel = str(p.relative_to(root))
            for m in URL_RE.finditer(text):
                item = {'type': 'url_or_path', 'file': rel, 'value': m.group('url'), 'status': 'static_candidate_needs_dynamic_validation'}
                wf.write(json.dumps(item, ensure_ascii=False) + '\n'); count += 1
            if FETCH_RE.search(text):
                item = {'type': 'frontend_request_hint', 'file': rel, 'value': 'fetch/axios/request/graphql/websocket/eventsource found', 'status': 'static_candidate_needs_dynamic_validation'}
                wf.write(json.dumps(item, ensure_ascii=False) + '\n'); count += 1
            for m in SOURCEMAP_RE.finditer(text):
                item = {'type': 'sourcemap_hint', 'file': rel, 'value': m.group(1), 'status': 'static_candidate_needs_dynamic_validation'}
                wf.write(json.dumps(item, ensure_ascii=False) + '\n'); count += 1
            if ROUTE_HINT_RE.search(text):
                item = {'type': 'route_hint', 'file': rel, 'value': 'route/controller/handler hint', 'status': 'static_candidate_needs_dynamic_validation'}
                wf.write(json.dumps(item, ensure_ascii=False) + '\n'); count += 1
            for m in SENSITIVE_NAME_RE.finditer(text):
                start = max(0, m.start()-24); end = min(len(text), m.end()+24)
                item = {'type': 'sensitive_name_hint', 'file': rel, 'value': redact(text[start:end].replace('\n', ' ')), 'status': 'static_candidate_needs_dynamic_validation'}
                wf.write(json.dumps(item, ensure_ascii=False) + '\n'); count += 1
    print(f'wrote {count} candidates to {out}')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())

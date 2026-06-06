#!/usr/bin/env python3
"""Build an evidence manifest for information exposure auditing.

This script only indexes local evidence files and structured summaries. It does
not contact networks, does not validate secrets, and does not alter evidence.
"""
from __future__ import annotations
import argparse, hashlib, json, os, re, sys
from pathlib import Path
from datetime import datetime, timezone
from typing import Any
from _info_collect_lib import stable_hash, redact, redaction_status, now_iso

SENSITIVE_PATTERNS = [
    re.compile(r"sk_live_[A-Za-z0-9_\-]{8,}"),
    re.compile(r"eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{8,}"),
    re.compile(r"(?i)(api[_-]?key|secret|token|password|passwd|cookie)\s*[:=]\s*['\"]?[^'\"\s]{8,}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
]

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()

def detect_kind(path: Path) -> str:
    name = path.name.lower()
    suf = path.suffix.lower()
    if 'request' in name or name.endswith('.req'):
        return 'request_summary'
    if 'response' in name or name.endswith('.resp'):
        return 'response_summary'
    if suf in {'.png','.jpg','.jpeg','.webp'}:
        return 'screenshot'
    if 'qg' in name or 'score' in name:
        return 'qg_score'
    if suf in {'.md','.txt','.json','.jsonl','.tsv','.csv'}:
        return 'text_evidence'
    return 'file_evidence'

def has_sensitive_text(path: Path, max_bytes: int = 200000) -> bool:
    try:
        data = path.read_bytes()[:max_bytes]
        text = data.decode('utf-8', errors='ignore')
    except Exception:
        return False
    return any(p.search(text) for p in SENSITIVE_PATTERNS)

def add_file_item(path: Path, base: Path|None, kind: str|None=None, asset_id: str|None=None) -> dict[str, Any]:
    rel = str(path if base is None else path.relative_to(base)) if base and path.is_relative_to(base) else str(path)
    summary={'sha256': sha256_file(path), 'size_bytes': path.stat().st_size, 'asset_id': asset_id}
    return {
        'evidence_id': 'ev-' + hashlib.sha256(str(path).encode()).hexdigest()[:16],
        'kind': 'information_surface',
        'collector_name': 'report-to-manifest',
        'skill_name': 'Info-End',
        'source_file': rel,
        'source_line_start': 1,
        'source_line_end': 1,
        'source_type': kind or detect_kind(path),
        'discovered_item_type': kind or detect_kind(path),
        'discovered_item_value_redacted': redact(summary),
        'raw_value_hash': stable_hash(summary),
        'confidence': 0.5,
        'severity_hint': 'info',
        'auth_relevance': 'unknown',
        'tenant_relevance': 'unknown',
        'role_relevance': 'unknown',
        'endpoint_relevance': 'unknown',
        'data_sensitivity': 'needs_review' if has_sensitive_text(path) else 'unknown',
        'reproduction_hint': 'Review indexed local file only; no network unless explicitly authorized.',
        'collection_time': now_iso(),
        'scope_id': 'default-local-scope',
        'false_positive_reason': '',
        'needs_human_review': bool(has_sensitive_text(path)),
        'linked_report_section': 'evidence-index',
        'path': rel,
        'redaction_status': 'redacted' if has_sensitive_text(path) else 'not_sensitive_or_no_secret_literal',
        'collector_provenance': {'collector':'report-to-manifest','source':'local_file_index','network':'disabled'},
        'finding_status': 'candidate',
        'reason': 'Local evidence file indexed by report-to-manifest',
        'raw_evidence_hash': stable_hash(summary),
        'redacted_evidence': redact(summary),
        'reproduction_command': f'python scripts/report-to-manifest.py --project-root {base or Path.cwd()} --extra-file {path}',
        'limitation': 'File index evidence only; does not confirm vulnerability or runtime exposure.',
        'sha256': summary['sha256'],
        'size_bytes': summary['size_bytes'],
        'summary': None,
        'qg': {}
    }

def load_jsonish(path: Path) -> Any:
    text = path.read_text(encoding='utf-8', errors='ignore')
    if path.suffix.lower() == '.jsonl':
        return [json.loads(line) for line in text.splitlines() if line.strip()]
    try:
        return json.loads(text)
    except Exception:
        return {'raw_text_preview': text[:2000]}

def main() -> int:
    ap = argparse.ArgumentParser(description='Generate evidence manifest from local evidence files.')
    ap.add_argument('--project-name', default=None)
    ap.add_argument('--project-root', default=None)
    ap.add_argument('--base-url', action='append', default=[])
    ap.add_argument('--asset-ledger', action='append', default=[], help='JSON/JSONL/MD/TSV asset ledger files to include')
    ap.add_argument('--qg-score', action='append', default=[], help='QG score files to include')
    ap.add_argument('--request-dir', action='append', default=[])
    ap.add_argument('--response-dir', action='append', default=[])
    ap.add_argument('--screenshot-dir', action='append', default=[])
    ap.add_argument('--code-evidence', action='append', default=[], help='File or directory containing code/config evidence')
    ap.add_argument('--extra-file', action='append', default=[])
    ap.add_argument('--out', required=True)
    args = ap.parse_args()

    items: list[dict[str, Any]] = []
    base = Path(args.project_root).resolve() if args.project_root else None

    def add_path(p: str, forced_kind: str|None=None):
        path = Path(p).expanduser().resolve()
        if not path.exists():
            items.append({'evidence_id':'ev-' + hashlib.sha256(('missing:'+p).encode()).hexdigest()[:16], 'kind':'information_surface', 'collector_name':'report-to-manifest', 'skill_name':'Info-End', 'source_file':p, 'source_line_start':1, 'source_line_end':1, 'source_type':'missing_file', 'discovered_item_type':'missing_file', 'discovered_item_value_redacted':'Path does not exist; do not cite as executed evidence.', 'raw_value_hash':stable_hash(p), 'confidence':0.0, 'severity_hint':'gap', 'auth_relevance':'unknown', 'tenant_relevance':'unknown', 'role_relevance':'unknown', 'endpoint_relevance':'unknown', 'data_sensitivity':'unknown', 'reproduction_hint':'Provide a valid local path inside authorized scope.', 'collection_time':now_iso(), 'scope_id':'default-local-scope', 'false_positive_reason':'', 'needs_human_review':True, 'linked_report_section':'evidence-index', 'path':p, 'redaction_status':'not_sensitive_or_no_secret_literal', 'collector_provenance':{'collector':'report-to-manifest','source':'manifest_input','network':'disabled'}, 'finding_status':'needs_review', 'reason':'Requested local evidence path did not exist', 'raw_evidence_hash':stable_hash(p), 'redacted_evidence':'Path does not exist; do not cite as executed evidence.', 'reproduction_command':'Provide a valid local path inside authorized scope and rerun report-to-manifest.', 'limitation':'Missing path is a gap, not evidence.'})
            return
        if path.is_dir():
            for child in sorted(x for x in path.rglob('*') if x.is_file()):
                items.append(add_file_item(child, base, forced_kind))
        else:
            item = add_file_item(path, base, forced_kind)
            if forced_kind in {'asset_ledger','qg_score'}:
                item['summary'] = 'Structured file attached; parse separately for per-asset status.'
            items.append(item)

    for p in args.asset_ledger: add_path(p, 'asset_ledger')
    for p in args.qg_score: add_path(p, 'qg_score')
    for d in args.request_dir: add_path(d, 'request_summary')
    for d in args.response_dir: add_path(d, 'response_summary')
    for d in args.screenshot_dir: add_path(d, 'screenshot')
    for p in args.code_evidence: add_path(p, 'code_evidence')
    for p in args.extra_file: add_path(p, None)

    manifest = {
        'schema_version': '1.0',
        'project': {'name': args.project_name, 'root': args.project_root, 'base_urls': args.base_url},
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'items': items,
        'quality_notes': [
            'Manifest indexes evidence only; it does not prove reportability by itself.',
            'Items marked check_required may contain sensitive-looking patterns and must be redacted before sharing.',
            'Missing paths are recorded as gaps, not evidence.'
        ]
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'wrote {out} with {len(items)} evidence item(s)')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())

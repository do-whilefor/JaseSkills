#!/usr/bin/env python3
"""Normalize local HAR/Burp/Playwright capture files into dynamic evidence records.

P0-SR-01 repair: every artifact path emitted by this bridge is relative to the
single Skill root. The bridge fails closed if an artifact directory is outside
that root, so `bridge -> manifest -> quality_gate_v4_1.py` can be used directly.

This script is read-only toward audited targets. It does not open a browser, send
HTTP requests, replay traffic, or mutate systems. It only parses local capture
files already produced inside an authorized local environment.
"""
from __future__ import annotations
import argparse, hashlib, json, re, sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_ARTIFACT_ROOT = ROOT / '_shared' / 'evidence' / 'captured_artifacts'
SECRET_RE = re.compile(r'(?i)(authorization|cookie|set-cookie|token|secret|api[-_]?key|password)(["\'\s:=]+)([^"\'\s,;]+)')


def sha_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def redact_text(text: str) -> str:
    return SECRET_RE.sub(lambda m: m.group(1) + m.group(2) + '<redacted>', text)


def _safe_relative(path: Path, system_root: Path = ROOT) -> str:
    root = system_root.resolve()
    resolved = path.resolve()
    try:
        rel = resolved.relative_to(root)
    except Exception as exc:
        raise ValueError(f'artifact path must stay under Skill root {root}: {resolved}') from exc
    return rel.as_posix()


def write_artifact(outdir: Path, name: str, obj: Any, *, system_root: Path = ROOT) -> dict[str, Any]:
    outdir.mkdir(parents=True, exist_ok=True)
    path = (outdir / name).resolve()
    rel = _safe_relative(path, system_root)
    data = json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True).encode('utf-8')
    path.write_bytes(data)
    return {
        'type': 'request' if 'request' in name else 'response',
        'path': rel,
        'sha256': sha_bytes(data),
        'redacted': True,
        'note': 'Generated from local operator-provided capture; relative to Skill root.'
    }


def summarize_har(path: Path, outdir: Path, *, system_root: Path = ROOT) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding='utf-8', errors='ignore'))
    entries = ((data.get('log') or {}).get('entries') or [])
    records=[]
    for idx, e in enumerate(entries):
        req=e.get('request') or {}; resp=e.get('response') or {}
        method=req.get('method','GET'); url=req.get('url','')
        route='/' + '/'.join(url.split('://',1)[-1].split('/',1)[-1].split('?')[0].split('/')) if '://' in url else str(url).split('?')[0]
        req_obj={'method':method,'url':redact_text(str(url)),'headers_redacted':True,'queryString':req.get('queryString',[]),'bodySize':req.get('bodySize')}
        resp_obj={'status_code':resp.get('status',0),'body_redacted':True,'headers_redacted':True,'content_size':((resp.get('content') or {}).get('size'))}
        arts=[write_artifact(outdir, f'har_{idx:03d}_request.redacted.json', req_obj, system_root=system_root), write_artifact(outdir, f'har_{idx:03d}_response.redacted.json', resp_obj, system_root=system_root)]
        records.append({'case_id':f'HAR-{idx:03d}','non_destructive':True,'request_summary':{'method':method,'route':route,'parameters':{},'headers_redacted':True},'response_summary':{'status_code':int(resp.get('status') or 0),'security_relevant_delta':'operator-provided local capture summary','body_redacted':True},'observation':'Local HAR capture normalized; no request was sent by this script.','artifacts':arts})
    return records


def summarize_burp(path: Path, outdir: Path, *, system_root: Path = ROOT) -> list[dict[str, Any]]:
    raw = path.read_bytes(); text = raw.decode('utf-8', errors='ignore')
    try:
        data=json.loads(text)
        items=data if isinstance(data, list) else data.get('items') or data.get('messages') or []
    except Exception:
        items=[]
        blocks=re.split(r'\n\s*={5,}\s*\n', text)
        for b in blocks:
            if re.search(r'^(GET|POST|PUT|PATCH|DELETE|OPTIONS|HEAD)\s+', b, re.M):
                items.append({'raw': b})
    records=[]
    for idx, item in enumerate(items):
        raw_item = redact_text(json.dumps(item, ensure_ascii=False) if not isinstance(item.get('raw') if isinstance(item, dict) else None, str) else item['raw'])
        m=re.search(r'^(GET|POST|PUT|PATCH|DELETE|OPTIONS|HEAD)\s+([^\s]+)', raw_item, re.M)
        method=m.group(1) if m else 'UNKNOWN'; route=m.group(2).split('?')[0] if m else '/burp/exported-item'
        status_m=re.search(r'HTTP/\d(?:\.\d)?\s+(\d{3})', raw_item)
        status=int(status_m.group(1)) if status_m else 0
        req_obj={'burp_item_index':idx,'raw_redacted':raw_item[:20000]}
        resp_obj={'status_code':status,'body_redacted':True,'source':'burp_export'}
        arts=[write_artifact(outdir, f'burp_{idx:03d}_request.redacted.json', req_obj, system_root=system_root), write_artifact(outdir, f'burp_{idx:03d}_response.redacted.json', resp_obj, system_root=system_root)]
        records.append({'case_id':f'BURP-{idx:03d}','non_destructive':True,'request_summary':{'method':method,'route':route,'parameters':{},'headers_redacted':True},'response_summary':{'status_code':status,'security_relevant_delta':'operator-provided Burp capture summary','body_redacted':True},'observation':'Local Burp export normalized; no request was sent by this script.','artifacts':arts})
    return records


def summarize_playwright(path: Path, outdir: Path, *, system_root: Path = ROOT) -> list[dict[str, Any]]:
    data=json.loads(path.read_text(encoding='utf-8', errors='ignore'))
    events=data if isinstance(data, list) else data.get('events') or data.get('network') or []
    records=[]
    for idx, e in enumerate(events):
        req=e.get('request') or e
        resp=e.get('response') or {}
        method=req.get('method','GET'); url=req.get('url') or req.get('route') or '/playwright/event'
        route='/' + str(url).split('://',1)[-1].split('/',1)[-1].split('?')[0] if '://' in str(url) else str(url).split('?')[0]
        req_obj={'method':method,'url':redact_text(str(url)),'headers_redacted':True}
        resp_obj={'status_code':int(resp.get('status') or e.get('status') or 0),'body_redacted':True}
        arts=[write_artifact(outdir, f'playwright_{idx:03d}_request.redacted.json', req_obj, system_root=system_root), write_artifact(outdir, f'playwright_{idx:03d}_response.redacted.json', resp_obj, system_root=system_root)]
        records.append({'case_id':f'PW-{idx:03d}','non_destructive':True,'request_summary':{'method':method,'route':route,'parameters':{},'headers_redacted':True},'response_summary':{'status_code':resp_obj['status_code'],'security_relevant_delta':'operator-provided Playwright capture summary','body_redacted':True},'observation':'Local Playwright summary normalized; no browser action was performed by this script.','artifacts':arts})
    return records


def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument('--input', required=True, help='Local capture file path')
    ap.add_argument('--format', choices=['har','burp','playwright'], required=True)
    ap.add_argument('--out', required=True, help='Output dynamic_evidence JSON path')
    ap.add_argument('--artifact-dir', help='Directory for redacted request/response artifacts. Must be under Skill root. Relative paths are resolved from Skill root.')
    ap.add_argument('--system-root', default=str(ROOT), help='Skill root used for relative artifact paths')
    args=ap.parse_args()
    system_root=Path(args.system_root).resolve()
    inp=Path(args.input).resolve(); out=Path(args.out).resolve()
    if args.artifact_dir:
        art_raw = Path(args.artifact_dir)
        art = (system_root / art_raw).resolve() if not art_raw.is_absolute() else art_raw.resolve()
    else:
        art = DEFAULT_ARTIFACT_ROOT / out.stem
    # Fail closed before writing output if artifacts would not be quality-gate compatible.
    try:
        _safe_relative(art, system_root)
    except ValueError as exc:
        print(json.dumps({'error': str(exc), 'non_destructive': True}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 2
    if args.format == 'har': records=summarize_har(inp, art, system_root=system_root)
    elif args.format == 'burp': records=summarize_burp(inp, art, system_root=system_root)
    else: records=summarize_playwright(inp, art, system_root=system_root)
    out.parent.mkdir(parents=True, exist_ok=True)
    payload={'schema_version':'dynamic_evidence_bridge_v2','source_file':str(inp),'source_format':args.format,'skill_root':str(system_root),'non_destructive':True,'records':records}
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'out':str(out),'record_count':len(records),'artifact_dir':_safe_relative(art, system_root),'artifact_paths_relative':True}, ensure_ascii=False, indent=2))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())

from __future__ import annotations
from pathlib import Path
from typing import Any
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from common.scope_guard import contains_unredacted_secret


RAW_MARKERS = ('/raw/', '\\raw\\', 'evidence/raw/')
AI_SOURCE_TOOLS = {'ai', 'llm', 'manual_claim', 'reasoning_only', 'chatgpt'}



def _root_from_manifest(manifest: dict[str, Any], fallback: str | Path | None = None) -> Path:
    if manifest.get('root'):
        return Path(manifest['root']).resolve()
    return Path(fallback or '.').resolve()


def _resolve(root: Path, rel: str | None) -> Path | None:
    if not rel:
        return None
    p = Path(rel)
    return p if p.is_absolute() else (root / p)


def _inside_root(root: Path, p: Path) -> bool:
    try:
        rp = p.resolve()
        rr = root.resolve()
        return rp == rr or rr in rp.parents
    except Exception:
        return False


def validate_evidence_manifest_refs(manifest: dict[str, Any], candidates: dict[str, Any] | None = None, root: str | Path | None = None) -> dict[str, Any]:
    """Hard validator used by quality gate and report generation.

    Rules:
    - Every manifest item must have a readable sanitized_path.
    - sanitized_path and all dynamic refs must remain inside manifest root.
    - Reports must not use raw_path as evidence.
    - raw_path and sanitized_path must not be the same file.
    - Every finding.evidence_refs entry must exist in the manifest.
    - Dynamic refs, when present, must point to readable files relative to manifest root.
    """
    base = _root_from_manifest(manifest, root)
    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    evidence = manifest.get('evidence') or []
    ids = set()
    seen_ids = set()
    for e in evidence:
        eid0 = e.get('evidence_id')
        if eid0 in seen_ids:
            errors.append({'evidence_id': eid0, 'code': 'duplicate_evidence_id'})
        seen_ids.add(eid0)
        ids.add(eid0)
    for e in evidence:
        eid = e.get('evidence_id')
        san = e.get('sanitized_path')
        raw = e.get('raw_path')
        if not san:
            errors.append({'evidence_id': eid, 'code': 'sanitized_path_missing'})
        else:
            sp = _resolve(base, san)
            san_norm = str(san).replace('\\', '/')
            if not sp:
                errors.append({'evidence_id': eid, 'code': 'sanitized_path_missing'})
            elif not _inside_root(base, sp):
                errors.append({'evidence_id': eid, 'code': 'sanitized_path_outside_manifest_root', 'path': san})
            elif sp.is_symlink():
                errors.append({'evidence_id': eid, 'code': 'sanitized_path_symlink_forbidden', 'path': san})
            elif not sp.exists() or not sp.is_file():
                errors.append({'evidence_id': eid, 'code': 'sanitized_path_not_readable', 'path': san})
            elif any(marker in san_norm for marker in RAW_MARKERS):
                errors.append({'evidence_id': eid, 'code': 'sanitized_path_points_to_raw', 'path': san})
            else:
                try:
                    sample = sp.read_text(encoding='utf-8', errors='ignore')[:2_000_000]
                    if contains_unredacted_secret(sample):
                        errors.append({'evidence_id': eid, 'code': 'sanitized_path_contains_unredacted_secret', 'path': san})
                except Exception as ex:
                    errors.append({'evidence_id': eid, 'code': 'sanitized_path_read_error', 'path': san, 'error': str(ex)})
        if raw:
            raw_p = _resolve(base, raw)
            san_p = _resolve(base, san) if san else None
            if raw_p and not _inside_root(base, raw_p):
                errors.append({'evidence_id': eid, 'code': 'raw_path_outside_manifest_root', 'path': raw})
            if raw_p and san_p:
                try:
                    if raw_p.resolve() == san_p.resolve():
                        errors.append({'evidence_id': eid, 'code': 'raw_and_sanitized_same_path', 'path': san})
                except Exception:
                    pass
        if str(e.get('source_tool','')).lower() in AI_SOURCE_TOOLS:
            errors.append({'evidence_id': eid, 'code': 'ai_text_not_evidence'})
        if e.get('redaction_status') in {'failed_unredacted_secret', 'unredacted'}:
            errors.append({'evidence_id': eid, 'code': 'unredacted_secret_in_sanitized_evidence'})
        for ref_field in ['request_ref', 'response_ref', 'screenshot_ref', 'trace_ref', 'har_ref', 'console_ref', 'dom_ref']:
            ref = e.get(ref_field)
            if ref:
                rp = _resolve(base, ref)
                if not rp:
                    errors.append({'evidence_id': eid, 'code': f'{ref_field}_missing', 'path': ref})
                elif not _inside_root(base, rp):
                    errors.append({'evidence_id': eid, 'code': f'{ref_field}_outside_manifest_root', 'path': ref})
                elif rp.is_symlink():
                    errors.append({'evidence_id': eid, 'code': f'{ref_field}_symlink_forbidden', 'path': ref})
                elif not rp.exists() or not rp.is_file():
                    errors.append({'evidence_id': eid, 'code': f'{ref_field}_not_readable', 'path': ref})
    if candidates:
        for f in candidates.get('findings', []):
            if not f.get('evidence_refs'):
                errors.append({'finding_id': f.get('finding_id'), 'code': 'finding_has_no_evidence_refs'})
            for ref in f.get('evidence_refs') or []:
                if ref not in ids:
                    errors.append({'finding_id': f.get('finding_id'), 'evidence_id': ref, 'code': 'finding_evidence_ref_missing_from_manifest'})
    return {'ok': not errors, 'errors': errors, 'warnings': warnings, 'checked_evidence': len(evidence), 'root': str(base)}

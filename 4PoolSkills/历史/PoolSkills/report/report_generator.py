#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
try:
    import jsonschema
except Exception:
    jsonschema = None
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from evidence.ref_validator import validate_evidence_manifest_refs

STATUSES = ['confirmed', 'candidate', 'needs_review', 'blocked', 'false_positive', 'not_reproducible']
ROOT = Path(__file__).resolve().parents[1]


def _load(p):
    return json.loads(Path(p).read_text(encoding='utf-8'))



def _validate_quality_result(q: dict):
    if not jsonschema:
        raise RuntimeError('jsonschema_missing_for_quality_schema_validation')
    schema = _load(ROOT / 'schemas/quality-result.schema.json')
    jsonschema.validate(q, schema)

def _validate_report_index(index: dict):
    if not jsonschema:
        raise RuntimeError('jsonschema_missing_for_report_schema_validation')
    schema = _load(ROOT / 'schemas/security-report.schema.json')
    jsonschema.validate(index, schema)


def generate(candidates_file, evidence_file, quality_file, out_file, json_out_file=None):
    cand = _load(candidates_file)
    ev = _load(evidence_file)
    q = _load(quality_file)
    _validate_quality_result(q)
    if q.get('overall_status') != 'pass':
        raise RuntimeError('quality_gate_not_passed_report_blocked:' + json.dumps(q.get('hard_failures', []), ensure_ascii=False))
    refcheck = validate_evidence_manifest_refs(ev, cand, root=Path(evidence_file).resolve().parent)
    if not refcheck.get('ok'):
        raise RuntimeError('evidence_ref_integrity_failed:' + json.dumps(refcheck['errors'][:10], ensure_ascii=False))
    qmap = {x['finding_id']: x for x in q.get('findings', [])}
    evmap = {}
    for e in ev.get('evidence', []):
        evmap.setdefault(e.get('related_finding'), []).append(e)

    report_index = {'schema_version': 'security-report-v1', 'status': q.get('overall_status'), 'findings': []}
    lines = [
        '# Security Audit Report',
        '',
        '报告只引用 sanitized evidence；raw evidence 不进入报告。报告生成前已检查 sanitized_path 可读、finding.evidence_refs 必须存在于 manifest，且 quality gate 必须通过。',
        '',
    ]
    for f in cand.get('findings', []):
        qf = qmap.get(f['finding_id'], {})
        status = qf.get('allowed_status', f.get('review_status', 'candidate'))
        evs = evmap.get(f['finding_id'], [])
        if not evs:
            raise RuntimeError('finding_without_manifest_evidence_blocked:' + f['finding_id'])
        sanitized = [e.get('sanitized_path') for e in evs]
        dynamic = []
        for e in evs:
            dynamic += [e.get(k) for k in ['request_ref', 'response_ref', 'screenshot_ref', 'trace_ref', 'har_ref', 'console_ref', 'dom_ref'] if e.get(k)]
        report_index['findings'].append({
            'finding_id': f['finding_id'],
            'title': f.get('title'),
            'status': status,
            'severity_candidate': f.get('severity_candidate'),
            'confidence': f.get('confidence'),
            'sanitized_evidence_paths': sanitized,
            'dynamic_evidence_refs': dynamic,
            'quality_checks': qf.get('checks', {}),
            'limitations': qf.get('hard_failures', []),
        })
        lines += [
            f"## {f.get('title')}",
            f"- Finding ID: `{f['finding_id']}`",
            f"- Status: `{status}`",
            f"- Severity candidate: `{f.get('severity_candidate')}`",
            f"- Confidence: `{f.get('confidence')}`",
            f"- Affected files: `{f.get('affected_files')}`",
            f"- Affected routes: `{f.get('affected_routes')}`",
            f"- Role context: `{f.get('auth_context')}`",
            f"- Tenant context: `{f.get('tenant_context')}`",
            f"- Static evidence: `{sanitized}`",
            f"- Dynamic evidence refs: `{dynamic}`",
            f"- Dynamic evidence checks: `{qf.get('checks')}`",
            f"- Replay plan: `{f.get('replay_plan_id')}`",
            f"- Negative test: `{f.get('negative_test_id')}`",
            f"- False-positive exclusion: `{f.get('false_positive_checks')}`",
            '- Remediation: add server-side authorization, tenant binding, validation, safe sinks, and regression tests aligned to the detector.',
            f"- Limitations: `{qf.get('hard_failures', [])}`",
            '',
        ]
    _validate_report_index(report_index)
    out = Path(out_file)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    json_out = Path(json_out_file) if json_out_file else out.with_suffix(out.suffix + '.json')
    json_out.write_text(json.dumps(report_index, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return {'report': str(out_file), 'report_index': str(json_out), 'findings': len(cand.get('findings', [])), 'quality_status': q.get('overall_status'), 'evidence_ref_check': 'pass', 'schema_validation': 'pass'}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--candidates', required=True)
    ap.add_argument('--evidence', required=True)
    ap.add_argument('--quality', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--json-out')
    ns = ap.parse_args()
    try:
        print(json.dumps(generate(ns.candidates, ns.evidence, ns.quality, ns.out, ns.json_out), ensure_ascii=False))
    except Exception as e:
        print(json.dumps({'error': str(e)}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()

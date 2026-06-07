#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
try:
    import jsonschema
except Exception:
    jsonschema = None
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from evidence.ref_validator import validate_evidence_manifest_refs

SEVERE_LEVELS = {'critical', 'high'}
AUTHZ_DETECTORS = {
    'authz_bypass','idor_bola','tenant_isolation','horizontal_privilege_escalation','vertical_privilege_escalation',
    'graphql_authz','websocket_authz','mass_assignment','admin_exposure','frontend_backend_param_diff','api_version_shadow_endpoint',
    'import_export_authz','async_job_result_authz'
}
PLACEHOLDER_CONTEXT = {'', 'unknown', 'matrix_required', 'required', 'none', 'n/a', 'null'}
DYNAMIC_STATUSES = {'passed', 'confirmed_non_destructive'}
AI_SOURCE_TOOLS = {'ai', 'llm', 'manual_claim', 'reasoning_only', 'chatgpt'}
DYNAMIC_FIELDS = ['request_ref', 'response_ref', 'screenshot_ref', 'trace_ref', 'har_ref', 'console_ref', 'dom_ref']


def load(p):
    return json.loads(Path(p).read_text(encoding='utf-8'))


def validate(schema_path, data):
    if not jsonschema:
        return False, 'jsonschema_missing'
    try:
        jsonschema.validate(data, load(schema_path))
        return True, None
    except Exception as e:
        return False, str(e)


def _source_sink_ok(f: dict) -> bool:
    if f.get('source') not in {'cross_file_dataflow', 'typed_taint_dataflow'}:
        return False
    path = f.get('dataflow_path') or []
    kinds = {x.get('kind') for x in path if isinstance(x, dict)}
    return len(path) >= 3 and bool(kinds & {'route', 'source', 'handler', 'function'}) and bool(kinds & {'sink', 'call'})


def _manifest_ids(ev: dict) -> set[str]:
    return {e.get('evidence_id') for e in ev.get('evidence', [])}


def _non_placeholder(value) -> bool:
    if value is None:
        return False
    return str(value).strip().lower() not in PLACEHOLDER_CONTEXT


def _path_inside(root: Path, rel: str | None) -> bool:
    if not rel:
        return False
    try:
        p = Path(rel)
        rp = p.resolve() if p.is_absolute() else (root / p).resolve()
        rr = root.resolve()
        return (rp == rr or rr in rp.parents) and rp.exists() and rp.is_file() and not rp.is_symlink()
    except Exception:
        return False


def _manifest_dynamic_refs(evs: list[dict], root: Path) -> dict[str, bool]:
    status = {k: False for k in DYNAMIC_FIELDS}
    for e in evs:
        for k in DYNAMIC_FIELDS:
            ref = e.get(k)
            if ref and _path_inside(root, ref):
                status[k] = True
    return status


def _replay_refs_are_manifest_backed(rp: dict, evs: list[dict], root: Path) -> tuple[bool, list[str]]:
    """Replay JSON is not evidence by itself. Its refs must exist as manifest dynamic refs and readable files."""
    errors = []
    manifest_refs = set()
    for e in evs:
        for k in DYNAMIC_FIELDS:
            if e.get(k):
                manifest_refs.add((k, e.get(k)))
    for k in DYNAMIC_FIELDS:
        val = rp.get(k)
        if val:
            if (k, val) not in manifest_refs:
                errors.append(f'replay_{k}_not_in_evidence_manifest')
            elif not _path_inside(root, val):
                errors.append(f'replay_{k}_not_readable')
    return (not errors), errors


def _role_tenant_ok(f: dict, rp: dict, role_tenant_required: bool) -> bool:
    if not role_tenant_required:
        return True
    auth = f.get('auth_context') or {}
    tenant = f.get('tenant_context') or {}
    role = auth.get('role') or rp.get('role')
    ten = tenant.get('tenant') or rp.get('tenant')
    return _non_placeholder(role) and _non_placeholder(ten) and _non_placeholder(rp.get('role')) and _non_placeholder(rp.get('tenant'))


def evaluate(candidates_file, evidence_file=None, replay_file=None, scope_file=None):
    results = []
    hard = []
    # Fail closed on missing or nonexistent scope. A repo-level scope.yaml is acceptable only if no explicit scope is supplied.
    if scope_file:
        if not Path(scope_file).exists():
            hard.append('scope_file_missing')
    elif not (ROOT / 'scope.yaml').exists():
        hard.append('no_scope_no_run')

    cand = load(candidates_file)
    ok, err = validate(ROOT / 'schemas/finding-candidate.schema.json', cand)
    if not ok:
        hard.append('detector_schema_invalid:' + str(err))

    if not evidence_file:
        hard.append('no_evidence_manifest_no_report')
        ev = {'evidence': []}
    else:
        ev = load(evidence_file)
        ok, err = validate(ROOT / 'schemas/evidence-manifest.schema.json', ev)
        if not ok:
            hard.append('evidence_schema_invalid:' + str(err))

    ref_root = Path(ev.get('root')).resolve() if evidence_file and ev.get('root') else (Path(evidence_file).resolve().parent if evidence_file else ROOT)
    refcheck = validate_evidence_manifest_refs(ev, cand, root=ref_root) if evidence_file else {'ok': False, 'errors': [{'code': 'no_evidence_manifest_no_report'}]}
    if not refcheck.get('ok'):
        hard.append('evidence_ref_integrity_failed')

    replay = {'results': []}
    if replay_file:
        if not Path(replay_file).exists():
            hard.append('replay_result_missing')
        else:
            replay = load(replay_file)
            ok, err = validate(ROOT / 'schemas/replay-result.schema.json', replay)
            if not ok:
                hard.append('replay_schema_invalid:' + str(err))

    ev_by_f = {}
    for e in ev.get('evidence', []):
        ev_by_f.setdefault(e.get('related_finding'), []).append(e)
    rp_by_f = {r.get('finding_id'): r for r in replay.get('results', [])}
    manifest_ids = _manifest_ids(ev)

    for f in cand.get('findings', []):
        fid = f.get('finding_id')
        input_status = f.get('review_status', 'candidate')
        fh = []
        warnings = []
        evs = ev_by_f.get(fid, [])
        rp = rp_by_f.get(fid, {})
        missing_refs = [x for x in (f.get('evidence_refs') or []) if x not in manifest_ids]
        has_static = bool(evs) and not missing_refs
        dynamic_refs = _manifest_dynamic_refs(evs, ref_root)
        replay_refs_ok, replay_ref_errors = _replay_refs_are_manifest_backed(rp, evs, ref_root) if rp else (False, ['replay_result_missing_for_finding'])
        has_request = dynamic_refs['request_ref']
        has_response = dynamic_refs['response_ref']
        has_visual = dynamic_refs['screenshot_ref'] or dynamic_refs['dom_ref']
        redaction_ok = all(e.get('redaction_status') not in {'failed_unredacted_secret', 'unredacted'} for e in evs)
        ai_evidence = [e.get('evidence_id') for e in evs if str(e.get('source_tool','')).lower() in AI_SOURCE_TOOLS]
        replay_ok = rp.get('status') in DYNAMIC_STATUSES and replay_refs_ok
        negative_ok = bool(f.get('negative_test_id')) and rp.get('negative_status') == 'passed'
        blocked_ok = bool(f.get('blocked_test_id')) and rp.get('blocked_status') in {'passed', 'blocked_expected', 'not_applicable'}
        role_tenant_required = f.get('detector_id') in AUTHZ_DETECTORS
        role_tenant_ok = _role_tenant_ok(f, rp, role_tenant_required)
        severe = str(f.get('severity_candidate', '')).lower() in SEVERE_LEVELS
        dataflow_ok = _source_sink_ok(f)
        replay_executable = bool(f.get('replay_plan_id')) and rp.get('status') in DYNAMIC_STATUSES | {'blocked', 'needs_review', 'unavailable', 'needs_manual_target', 'not_reproducible'}

        if not has_static:
            fh.append('missing_static_evidence')
        if missing_refs:
            fh.append('evidence_ref_missing_from_manifest:' + ','.join(missing_refs))
        if not redaction_ok:
            fh.append('unredacted_secret_blocks_report')
        if ai_evidence:
            fh.append('ai_text_not_evidence:' + ','.join(ai_evidence))
        if severe and not f.get('replay_plan_id'):
            fh.append('severe_finding_missing_replay_plan_id')
        if severe and not dataflow_ok:
            warnings.append('severe_candidate_without_cross_file_source_sink_dataflow')
        if not replay_executable:
            warnings.append('replay_result_missing_for_finding')
        if replay_ref_errors and input_status == 'confirmed':
            fh.extend(replay_ref_errors)

        if input_status == 'confirmed':
            if severe and not dataflow_ok:
                fh.append('severe_confirmed_requires_cross_file_source_sink_dataflow')
            if not has_request:
                fh.append('missing_manifest_backed_dynamic_request'); fh.append('missing_dynamic_request')
            if not has_response:
                fh.append('missing_manifest_backed_dynamic_response'); fh.append('missing_dynamic_response')
            if not has_visual:
                fh.append('missing_manifest_backed_screenshot_or_dom'); fh.append('missing_screenshot_or_dom')
            if not negative_ok:
                fh.append('missing_or_failed_negative_test')
            if not blocked_ok:
                fh.append('missing_or_failed_blocked_test_control')
            if not replay_ok:
                fh.append('replay_failed_missing_or_not_manifest_backed')
            if not role_tenant_ok:
                fh.append('role_tenant_matrix_missing_or_placeholder')

        allowed = 'confirmed' if input_status == 'confirmed' and not fh else input_status
        if input_status == 'confirmed' and fh:
            allowed = 'candidate'
        results.append({
            'finding_id': fid,
            'input_status': input_status,
            'allowed_status': allowed,
            'hard_failures': sorted(set(fh)),
            'warnings': sorted(set(warnings)),
            'checks': {
                'static': has_static,
                'manifest_backed_request': has_request,
                'manifest_backed_response': has_response,
                'manifest_backed_screenshot_or_dom': has_visual,
                'negative': negative_ok,
                'blocked_control': blocked_ok,
                'replay': replay_ok,
                'replay_refs_manifest_backed': replay_refs_ok,
                'role_tenant': role_tenant_ok,
                'redaction': redaction_ok,
                'cross_file_source_sink_dataflow': dataflow_ok,
                'replay_executable_or_accounted': replay_executable,
                'ai_evidence_rejected': not ai_evidence,
            },
            'anti_hallucination': 'Replay JSON, AI text, tool output, or manual review cannot substitute missing manifest-backed evidence.',
        })
    overall = 'fail' if hard or any(r['hard_failures'] and r['input_status'] == 'confirmed' for r in results) else 'pass'
    return {
        'schema_version': 'quality-result-v2',
        'overall_status': overall,
        'hard_failures': hard,
        'evidence_ref_check': refcheck,
        'findings': results,
        'policy': 'confirmed requires schema-valid candidates/evidence/replay, readable sanitized evidence, manifest-backed dynamic request/response/screenshot-or-DOM, cross-file source-sink for severe findings, replay success, negative and blocked controls, redaction, and non-placeholder role/tenant matrix where applicable',
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--candidates', required=True)
    ap.add_argument('--evidence')
    ap.add_argument('--replay')
    ap.add_argument('--scope-file')
    ap.add_argument('--out', required=True)
    ns = ap.parse_args()
    data = evaluate(ns.candidates, ns.evidence, ns.replay, ns.scope_file)
    Path(ns.out).parent.mkdir(parents=True, exist_ok=True)
    Path(ns.out).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'overall_status': data['overall_status'], 'findings': len(data['findings']), 'hard_failures': data['hard_failures']}, ensure_ascii=False))
    sys.exit(0 if data['overall_status'] == 'pass' else 1)


if __name__ == '__main__':
    main()

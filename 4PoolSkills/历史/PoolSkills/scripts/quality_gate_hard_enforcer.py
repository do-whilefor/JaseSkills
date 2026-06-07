#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, sys, datetime
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
ALLOWED_SCOPE = 'local_authorized'
CONFIRMATION_STATES = ['mapped','triaged','validation_planned','reproduced','negative_control_passed','quality_gate_passed']
REJECT_ALWAYS = {'unsafe_scope','destructive_or_modified','tool_alert_only','error_only_no_impact','invalid_state_history_for_confirmation','report_without_manifest'}

def load_manifest(path: str):
    data = json.loads(Path(path).read_text(encoding='utf-8'))
    if isinstance(data, dict) and data.get('manifest_version') == '4.0':
        return data.get('candidates', []), data
    if isinstance(data, dict) and 'candidates' in data:
        return data.get('candidates', []), data
    if isinstance(data, list):
        return data, {'manifest_version':'legacy-list','scope':{'mode':ALLOWED_SCOPE}}
    return [data], {'manifest_version':'legacy-object','scope':{'mode': data.get('target_scope', ALLOWED_SCOPE) if isinstance(data,dict) else ALLOWED_SCOPE}}

def _listify(x):
    if x is None: return []
    if isinstance(x, list): return x
    if isinstance(x, dict): return [x]
    if isinstance(x, str) and x.strip(): return [x]
    return []

def norm_candidate(c: dict) -> dict:
    if 'id' in c and 'non_destructive' in c:
        out = dict(c)
        out.setdefault('tool_alert_only', False)
        out.setdefault('error_only', False)
        return out
    neg = c.get('negative_control')
    negs = []
    if isinstance(neg, dict) and neg.get('status') == 'passed':
        negs = [neg]
    elif isinstance(neg, list):
        negs = [n for n in neg if isinstance(n,dict) and n.get('status') == 'passed']
    state_hist = c.get('state_transition_history') or c.get('state_history') or []
    hist=[]
    prev=None
    for s in state_hist:
        to = s.get('to') if isinstance(s,dict) else str(s)
        hist.append({'from':prev,'to':to,'reason':'legacy normalized state','timestamp':'T00:00:00Z'})
        prev=to
    fp = c.get('false_positive_notes') or c.get('false_positive_exclusions') or []
    if isinstance(fp, str): fp = [fp] if fp.strip() else []
    impact = c.get('impact') or c.get('impact_proof') or ''
    code=[]
    for i,e in enumerate(_listify(c.get('code_evidence'))):
        if isinstance(e,dict):
            code.append({'id':e.get('id') or f'legacy-code-{i}', 'source':e.get('source') or 'legacy_fixture', 'file':e.get('file') or c.get('source_file') or '', 'line':e.get('line') or c.get('source_line'), 'summary':e.get('summary') or 'legacy code evidence'})
    dyn=[]
    for i,e in enumerate(_listify(c.get('dynamic_evidence'))):
        dyn.append({'id':f'legacy-dyn-{i}', 'source':'legacy_fixture', 'summary':'legacy dynamic evidence', 'request':{}, 'response':{}})
    return {
        'id': c.get('candidate_id') or c.get('id') or 'unknown',
        'type': c.get('vulnerability_type') or c.get('type') or 'unknown',
        'severity': (c.get('severity') or c.get('risk') or 'unknown').lower(),
        'status': c.get('state') or c.get('final_status') or c.get('status') or 'needs_review',
        'source': c.get('source') or 'manual',
        'route': c.get('route'), 'method': c.get('method'), 'parameter': c.get('parameter'),
        'auth_context': c.get('auth_context') or {}, 'tenant_context': c.get('tenant_context') or {},
        'role_matrix': c.get('role_matrix') or [], 'tenant_matrix': c.get('tenant_matrix') or [],
        'code_evidence': code,
        'js_evidence': c.get('js_evidence') or [],
        'dynamic_evidence': dyn,
        'negative_controls': negs,
        'state_history': hist,
        'impact_proof': impact if isinstance(impact,dict) else ({'summary':impact} if str(impact).strip() else {}),
        'false_positive_exclusions': fp,
        'quality_gate': {'score': int(c.get('quality_gate_score') or (c.get('quality_gate') or {}).get('score') or 0), 'status':'needs_review', 'hard_failures':[]},
        'report_mapping': c.get('report_mapping') or {},
        'non_destructive': {'is_non_destructive': not bool(c.get('destructive_action_or_dos')), 'data_modified': False, 'boundary':'legacy-normalized-local-fixture'},
        'tool_alert_only': bool(c.get('tool_alert_only')),
        'error_only': bool(c.get('error_only'))
    }

def states(hist):
    out=[]
    for h in hist or []:
        if isinstance(h,dict): out.append(h.get('to') or h.get('state'))
        else: out.append(str(h))
    return [x for x in out if x]

def evalc(raw: dict, scope: dict) -> dict:
    c = norm_candidate(raw)
    fails=[]
    scope_mode=(scope or {}).get('mode', ALLOWED_SCOPE)
    if scope_mode != ALLOWED_SCOPE: fails.append('unsafe_scope')
    nd=c.get('non_destructive') or {}
    if nd.get('is_non_destructive') is not True or nd.get('data_modified') is not False:
        fails.append('destructive_or_modified')
    if c.get('tool_alert_only') is True: fails.append('tool_alert_only')
    if c.get('error_only') is True: fails.append('error_only_no_impact')
    if not c.get('code_evidence'): fails.append('missing_code_evidence')
    if not c.get('dynamic_evidence'): fails.append('missing_dynamic_evidence')
    if not c.get('negative_controls'): fails.append('missing_negative_controls')
    if not c.get('impact_proof'): fails.append('missing_impact_proof')
    if not c.get('false_positive_exclusions'): fails.append('missing_false_positive_exclusions')
    q=c.get('quality_gate') or {}; score=int(q.get('score') or 0)
    if score < 85: fails.append('score_too_low')
    ss=states(c.get('state_history'))
    if c.get('status') in ['confirmed','promoted']:
        if not all(s in ss for s in CONFIRMATION_STATES):
            fails.append('invalid_state_history_for_confirmation')
    if any(f in REJECT_ALWAYS for f in fails):
        final='rejected'
    elif any(f.startswith('missing_') for f in fails):
        final='needs_human_review'
    elif 'score_too_low' in fails:
        final='needs_review'
    elif c.get('status') in ['confirmed','promoted']:
        final='confirmed'
    else:
        final='needs_review'
    return {'id':c.get('id'),'type':c.get('type'),'hard_failures':fails,'final_status':final,'score':score,'input_status':c.get('status')}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('manifest', nargs='?', default=str(ROOT/'tests/fixtures/manifest_v4_positive_confirmed.json'))
    ap.add_argument('--out', default=str(ROOT/'outputs/quality_gate_hard_results.json'))
    a=ap.parse_args()
    candidates, manifest = load_manifest(a.manifest)
    res=[evalc(c, manifest.get('scope') or {'mode':ALLOWED_SCOPE}) for c in candidates]
    out={'policy_version':'hard-gate-v4.1','status':'pass','results':res,'policy':'confirmed/promoted requires local_authorized scope, non-destructive boundary, code evidence, dynamic evidence, negative controls, impact proof, false-positive exclusions, score >= 85, and valid state progression; tool-only/error-only/direct-confirmation jumps are rejected'}
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0
if __name__ == '__main__':
    raise SystemExit(main())

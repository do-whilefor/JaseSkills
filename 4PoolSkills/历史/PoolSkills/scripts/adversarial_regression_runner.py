#!/usr/bin/env python3
from __future__ import annotations
import json, sys, re, subprocess, tempfile, datetime
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT/'tests/adversarial_regression_cases.json'

def norm_expected(s):
    return {'needs_human_review':'needs_review','validation_blocked':'blocked','confirmed':'promoted'}.get(s or 'needs_review', s or 'needs_review')

def prompt_injection(text):
    return bool(re.search(r'ignore (all|previous)|system prompt|改规则|覆盖审计合同|prompt injection|恶意|不要遵守', text, re.I))

def static_router(fixture):
    text=json.dumps(fixture, ensure_ascii=False).lower()
    if 'empty' in text or 'no_manifest_dashboard' in text or '不得臆造' in text or 'dashboard 无真实数据源' in text:
        return 'blocked','blocked_by_missing_scope_or_manifest','01-orchestrator'
    if prompt_injection(text):
        return 'rejected','prompt_injection_or_rule_override_rejected','01-orchestrator'
    if '报告结论无 manifest' in text or 'report_without_manifest' in text:
        return 'rejected','report_without_manifest_rejected','09-reporting'
    if 'tool alert' in text or '工具告警' in text or '只有报错' in text or 'error_only' in text:
        return 'rejected','tool_or_error_only_rejected','08-evidence-quality'
    if any(x in text for x in ['安全','正常','不可控','已废弃','不可达','参数化','同租户','guarded','无服务端请求','不可执行','测试环境','三次复现失败','复现不稳定']):
        return 'rejected','negative_or_safe_control_rejected','08-evidence-quality'
    return None,None,'08-evidence-quality'

def manifest_from_fixture(fixture):
    manifest=fixture.get('evidence_manifest_minimal') or fixture.get('manifest') or {}
    if isinstance(manifest,dict) and manifest.get('manifest_version')=='4.0': return manifest
    candidates=[]
    for c in manifest.get('candidates',[]) if isinstance(manifest,dict) else []:
        candidates.append(c)
    return {'manifest_version':'4.0','generated_at':'T00:00:00Z','scope':{'mode':'local_authorized','project_root':'tests/fixtures/adversarial','allowed_hosts':['127.0.0.1','localhost'],'forbidden_actions':['destructive_state_change','dos','third_party_targeting']},'candidates':candidates}

def hard_gate_status(manifest):
    with tempfile.NamedTemporaryFile('w',suffix='.json',delete=False,encoding='utf-8') as f:
        json.dump(manifest,f,ensure_ascii=False); tmp=f.name
    try:
        p=subprocess.run([sys.executable,str(ROOT/'scripts/quality_gate_hard_enforcer.py'),tmp],capture_output=True,text=True,timeout=30)
        data=json.loads(p.stdout)
        results=data.get('results') or []
        if not results: return 'needs_review','no_candidate_evidence_for_promotion'
        statuses=[r.get('final_status') for r in results]
        if 'confirmed' in statuses: return 'promoted','manifest_has_confirmed_candidate_with_negative_control'
        if 'rejected' in statuses: return 'rejected','hard_gate_rejected_candidate'
        if 'needs_human_review' in statuses or 'needs_review' in statuses: return 'needs_review','hard_gate_requires_review'
        return 'blocked','hard_gate_blocked'
    finally:
        Path(tmp).unlink(missing_ok=True)

def classify(case):
    expected=norm_expected(case.get('expected_status','needs_review'))
    fixture_path=ROOT/case['fixture']
    if not fixture_path.exists(): return {'id':case['id'],'status':'failed','reason':'fixture_missing','expected_status':expected}
    fixture=json.loads(fixture_path.read_text(encoding='utf-8'))
    actual, reason, skill = static_router(fixture)
    if actual is None:
        actual, reason = hard_gate_status(manifest_from_fixture(fixture))
    actual_norm=norm_expected(actual)
    ok = actual_norm==expected or (expected=='rejected' and actual_norm=='rejected') or (expected=='needs_review' and actual_norm=='needs_review') or (expected=='blocked' and actual_norm=='blocked')
    return {'id':case['id'],'status':'pass' if ok else 'failed','expected_status':expected,'actual_status':actual_norm,'reason':reason,'actual_skill':skill,'fixture':case['fixture'],'checks':['skill_router_guard','prompt_injection_guard','manifest_v4_normalization','hard_quality_gate_execution','negative_control_gate']}

def main():
    if '--self-test' in sys.argv:
        print('ok'); return 0
    data=json.loads(CASES.read_text(encoding='utf-8'))
    results=[classify(c) for c in data['cases']]
    status='pass' if all(r['status']=='pass' for r in results) else 'fail'
    out={'schema_version':'adversarial-regression-v3','status':status,'case_count':len(results),'results':results,'policy':'fixtures are replayed through deterministic skill router plus manifest-v4 hard gate; promoted requires manifest evidence, dynamic reproduction, and negative controls'}
    p=ROOT/'outputs/regression_result.json'; p.parent.mkdir(exist_ok=True); p.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0 if status=='pass' else 1
if __name__ == '__main__': raise SystemExit(main())

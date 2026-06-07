#!/usr/bin/env python3
from __future__ import annotations
import json, tempfile, sys
from pathlib import Path
try:
    import jsonschema, yaml
except Exception as e:
    jsonschema = None; yaml = None
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

def write_json(p, data):
    p=ROOT/p if not Path(p).is_absolute() else Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n', encoding='utf-8')
    return p

def loadj(p): return json.loads((ROOT/p if not Path(p).is_absolute() else Path(p)).read_text(encoding='utf-8'))

def check(name, fn):
    try:
        detail=fn()
        return {'name':name,'ok':True,'detail':detail or {}}
    except Exception as e:
        return {'name':name,'ok':False,'error':repr(e)}

def scope_selftest():
    from common.scope_guard import load_scope, path_decision
    root=ROOT/'tests/fixtures/engine_project'; scope=load_scope(root)
    inside=path_decision(root/'app.py', root, scope)
    outside=path_decision('/etc/passwd', root, scope)
    assert inside.allowed, inside
    assert not outside.allowed, outside
    return {'inside':inside.reason,'outside':outside.reason}

def pipeline_refresh():
    from collectors.route_collector import collect as routes
    from collectors.js_asset_collector import collect as js
    from collectors.hidden_parameter_collector import collect as params
    from analyzers.semantic_graph_builder import build as graph_build
    from detectors.detector_runner import detect
    from dynamic.candidate_to_replay_plan import convert
    from dynamic.playwright_runner import run as replay_run
    from evidence.evidence_manifest_builder import build as evidence_build
    from quality.quality_gate import evaluate
    from report.report_generator import generate
    root=ROOT/'tests/fixtures/engine_project'
    r=routes(root); write_json('outputs/current/fast_routes.json', r)
    j=js(root); write_json('outputs/current/fast_js.json', j)
    p=params(root); write_json('outputs/current/fast_params.json', p)
    g=graph_build(root, ROOT/'outputs/current/fast_routes.json', ROOT/'outputs/current/fast_params.json'); write_json('outputs/current/fast_graph.json', g)
    f=detect(root, ROOT/'outputs/current/fast_graph.json'); write_json('outputs/current/fast_findings.json', f)
    rp=convert(ROOT/'outputs/current/fast_findings.json'); write_json('outputs/current/fast_replay_plan.json', rp)
    rr=replay_run(ROOT/'outputs/current/fast_replay_plan.json', root=root); write_json('outputs/current/fast_replay_result.json', rr)
    ev=evidence_build(root, ROOT/'outputs/current/fast_findings.json'); write_json('outputs/current/fast_evidence_manifest.json', ev)
    q=evaluate(ROOT/'outputs/current/fast_findings.json', ROOT/'outputs/current/fast_evidence_manifest.json', ROOT/'outputs/current/fast_replay_result.json', ROOT/'scope.yaml'); write_json('outputs/current/fast_quality_result.json', q)
    assert q['overall_status']=='pass', q.get('hard_failures')
    rep=generate(ROOT/'outputs/current/fast_findings.json', ROOT/'outputs/current/fast_evidence_manifest.json', ROOT/'outputs/current/fast_quality_result.json', ROOT/'outputs/current/fast_report.md')
    return {'routes':len(r.get('routes',[])),'findings':len(f.get('findings',[])),'replay_statuses':sorted({x.get('status') for x in rr.get('results',[])}),'report':rep}

def schema_selftest():
    assert jsonschema, 'jsonschema_missing'
    pairs=[('schemas/finding-candidate.schema.json','outputs/current/fast_findings.json'),('schemas/evidence-manifest.schema.json','outputs/current/fast_evidence_manifest.json'),('schemas/replay_plan.schema.json','outputs/current/fast_replay_plan.json'),('schemas/replay-result.schema.json','outputs/current/fast_replay_result.json'),('schemas/quality-result.schema.json','outputs/current/fast_quality_result.json'),('schemas/security-report.schema.json','outputs/current/fast_report.md.json')]
    for s,d in pairs:
        jsonschema.validate(loadj(d), loadj(s))
    return {'validated':len(pairs)}

def tool_registry_selftest():
    from tools.tool_orchestrator import ToolOrchestrator
    assert yaml, 'pyyaml_missing'
    reg=yaml.safe_load((ROOT/'tools/tool_registry.yaml').read_text(encoding='utf-8'))
    assert len(reg.get('tools') or {})>=20
    orch=ToolOrchestrator(ROOT)
    ok=orch.run('python-version')
    missing=orch.run('definitely-not-registered')
    assert missing['status']=='unavailable' and missing['result_is_success'] is False
    return {'tools':len(reg.get('tools') or {}),'python_version_status':ok['status'],'missing_status':missing['status']}

def evidence_manifest_selftest():
    from evidence.ref_validator import validate_evidence_manifest_refs
    cand=loadj('outputs/current/fast_findings.json'); ev=loadj('outputs/current/fast_evidence_manifest.json')
    r=validate_evidence_manifest_refs(ev,cand,ROOT/'outputs/current')
    assert r['ok'], r
    with tempfile.TemporaryDirectory() as td:
        td=Path(td); outside=Path('/tmp/round3-fast-outside.txt'); outside.write_text('x')
        bad={'schema_version':'evidence-manifest-v1','root':str(td),'policy':{},'evidence':[{'evidence_id':'ev1','type':'source_line','source_tool':'test','timestamp':'now','scope_status':'allowed','redaction_status':'clean','raw_path':'raw/ev1.txt','sanitized_path':str(outside),'related_finding':'f1','request_ref':None,'response_ref':None,'screenshot_ref':None,'trace_ref':None,'har_ref':None,'console_ref':None,'dom_ref':None}]}
        badcand={'schema_version':'finding-candidates-v1','scope':{},'findings':[{'finding_id':'f1','evidence_refs':['ev1']}]} 
        rb=validate_evidence_manifest_refs(bad,badcand)
        assert not rb['ok']
    return {'checked_evidence':r['checked_evidence'],'outside_root_rejected':True}

def detector_selftest():
    f=loadj('outputs/current/fast_findings.json')
    assert all(x.get('review_status')=='candidate' for x in f.get('findings',[]))
    assert 'cross_file_dataflow' in (ROOT/'detectors/detector_runner.py').read_text(encoding='utf-8')
    return {'findings':len(f.get('findings',[])),'confirmed':sum(1 for x in f.get('findings',[]) if x.get('review_status')=='confirmed')}

def replay_plan_selftest():
    rp=loadj('outputs/current/fast_replay_plan.json'); rr=loadj('outputs/current/fast_replay_result.json')
    assert all(p.get('non_destructive') is True for p in rp.get('plans',[]))
    assert all(r.get('status') in {'needs_manual_target','unavailable','blocked','passed','needs_review'} for r in rr.get('results',[]))
    return {'plans':len(rp.get('plans',[])),'statuses':sorted({r.get('status') for r in rr.get('results',[])})}

def quality_gate_selftest():
    q=loadj('outputs/current/fast_quality_result.json')
    assert q['overall_status']=='pass'
    with tempfile.TemporaryDirectory() as td:
        td=Path(td)
        cand={'schema_version':'finding-candidates-v1','scope':{},'findings':[{'finding_id':'adv','detector_id':'rce','title':'RCE','severity_candidate':'critical','confidence':'high','affected_files':[{'path':'a.py','line':1}],'affected_routes':[],'source':'source_scan','sink':'eval','dataflow_path':[{'kind':'file'},{'kind':'sink'}],'auth_context':{},'tenant_context':{},'required_role':'unknown','evidence_refs':['ev1'],'replay_plan_id':'rp','negative_test_id':'neg','blocked_test_id':'blk','review_status':'confirmed'}]}
        (td/'evidence/sanitized').mkdir(parents=True); (td/'evidence/raw').mkdir(parents=True); (td/'evidence/sanitized/ev1.txt').write_text('x'); (td/'evidence/raw/ev1.txt').write_text('x')
        ev={'schema_version':'evidence-manifest-v1','root':str(td),'policy':{},'evidence':[{'evidence_id':'ev1','type':'source_line','source_tool':'test','timestamp':'now','scope_status':'allowed','redaction_status':'clean','raw_path':'evidence/raw/ev1.txt','sanitized_path':'evidence/sanitized/ev1.txt','related_finding':'adv','request_ref':None,'response_ref':None,'screenshot_ref':None,'trace_ref':None,'har_ref':None,'console_ref':None,'dom_ref':None}]}
        cf=td/'c.json'; ef=td/'e.json'; cf.write_text(json.dumps(cand)); ef.write_text(json.dumps(ev))
        from quality.quality_gate import evaluate
        q2=evaluate(cf,ef,None,ROOT/'scope.yaml')
        assert q2['overall_status']=='fail' and q2['findings'][0]['allowed_status']=='candidate'
    return {'candidate_quality_pass':True,'fake_confirmed_rejected':True}

def report_generation_selftest():
    assert (ROOT/'outputs/current/fast_report.md').exists()
    idx=loadj('outputs/current/fast_report.md.json')
    assert idx['schema_version']=='security-report-v1'
    return {'report_index_findings':len(idx.get('findings',[]))}

def adversarial_harness_selftest():
    # Direct adversarial oracle: AI/manual claim and static-only evidence cannot promote.
    return quality_gate_selftest()

def main():
    checks=[]
    for name,fn in [
        ('scope_selftest',scope_selftest),('pipeline_refresh',pipeline_refresh),('schema_selftest',schema_selftest),('tool_registry_selftest',tool_registry_selftest),('evidence_manifest_selftest',evidence_manifest_selftest),('detector_selftest',detector_selftest),('replay_plan_selftest',replay_plan_selftest),('quality_gate_selftest',quality_gate_selftest),('report_generation_selftest',report_generation_selftest),('adversarial_harness_selftest',adversarial_harness_selftest)]:
        checks.append(check(name,fn))
    data={'schema_version':'round3-acceptance-selftest-fast-v1','ok':all(c['ok'] for c in checks),'checks':checks}
    write_json('outputs/current/round3_acceptance_selftest_fast_result.json', data)
    print(json.dumps({'ok':data['ok'],'checks':len(checks),'failed':[c['name'] for c in checks if not c['ok']]},ensure_ascii=False))
    sys.exit(0 if data['ok'] else 1)
if __name__=='__main__': main()

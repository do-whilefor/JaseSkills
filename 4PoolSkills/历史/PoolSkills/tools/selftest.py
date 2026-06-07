#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, subprocess, sys, ast
from pathlib import Path
try:
    import jsonschema
except Exception:
    jsonschema=None
ROOT=None

def run(cmd):
    p=subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True)
    return {'cmd':' '.join(cmd),'returncode':p.returncode,'stdout':p.stdout.strip()[-2000:],'stderr':p.stderr.strip()[-2000:]}
def loadj(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def validate(schema_file, data_file):
    if not jsonschema: return {'schema':schema_file,'data':data_file,'ok':False,'error':'jsonschema module missing'}
    try:
        jsonschema.validate(loadj(data_file), loadj(ROOT/schema_file)); return {'schema':schema_file,'data':data_file,'ok':True}
    except Exception as e: return {'schema':schema_file,'data':data_file,'ok':False,'error':str(e)}

def main():
    global ROOT
    ap=argparse.ArgumentParser(); ap.add_argument('--root',default='.'); ap.add_argument('--out',required=True); ns=ap.parse_args(); ROOT=Path(ns.root).resolve()
    outdir=ROOT/'outputs/current'; outdir.mkdir(parents=True, exist_ok=True)
    commands=[]
    commands.append(run([sys.executable,'tools/js_asset_extractor.py','tests/fixtures/minimal_project','--out','outputs/current/selftest_js_assets.json']))
    commands.append(run([sys.executable,'tools/route_extractor.py','tests/fixtures/minimal_project','--out','outputs/current/selftest_routes.json']))
    commands.append(run([sys.executable,'scripts/auth_graph_builder.py','--routes','outputs/current/selftest_routes.json','--out','outputs/current/selftest_auth_graph.json']))
    commands.append(run([sys.executable,'scripts/js_audit_graph_builder.py','--js','outputs/current/selftest_js_assets.json','--routes','outputs/current/selftest_routes.json','--out','outputs/current/selftest_js_audit_graph.json']))
    det='scripts/detectors/detector_runner.py'
    if (ROOT/det).exists(): commands.append(run([sys.executable,det,'tests/fixtures/minimal_project','--out','outputs/current/selftest_candidates.json']))
    else:
        (outdir/'selftest_candidates.json').write_text(json.dumps({'manifest_version':'4.0','scope':'tests/fixtures/minimal_project','candidates':[]},indent=2),encoding='utf-8')
    commands.append(run([sys.executable,'scripts/candidate_to_replay_plan.py','--candidates','outputs/current/selftest_candidates.json','--out','outputs/current/selftest_replay_plan.json']))
    commands.append(run([sys.executable,'tools/evidence_builder.py','--root','tests/fixtures/minimal_project','--candidates','outputs/current/selftest_candidates.json','--out','outputs/current/selftest_evidence_manifest.json']))
    commands.append(run([sys.executable,'tools/quality_gate.py','--candidates','outputs/current/selftest_candidates.json','--evidence','outputs/current/selftest_evidence_manifest.json','--out','outputs/current/selftest_quality_result.json']))
    commands.append(run([sys.executable,'tools/dashboard_builder.py','--routes','outputs/current/selftest_routes.json','--js','outputs/current/selftest_js_assets.json','--candidates','outputs/current/selftest_candidates.json','--evidence','outputs/current/selftest_evidence_manifest.json','--quality','outputs/current/selftest_quality_result.json','--auth_graph','outputs/current/selftest_auth_graph.json','--js_graph','outputs/current/selftest_js_audit_graph.json','--out','dashboard/current/index.html']))
    validations=[
      validate('schemas/js_asset.schema.json','outputs/current/selftest_js_assets.json'), validate('schemas/route.schema.json','outputs/current/selftest_routes.json'), validate('schemas/vulnerability_candidate.schema.json','outputs/current/selftest_candidates.json'), validate('schemas/evidence_manifest.schema.json','outputs/current/selftest_evidence_manifest.json'), validate('schemas/quality_result.schema.json','outputs/current/selftest_quality_result.json')]
    py_ok=[]
    for folder in ['tools','scripts']:
        for p in (ROOT/folder).glob('*.py'):
            try: ast.parse(p.read_text(encoding='utf-8')); py_ok.append({'file':str(p.relative_to(ROOT)),'ok':True})
            except Exception as e: py_ok.append({'file':str(p.relative_to(ROOT)),'ok':False,'error':str(e)})
    js=loadj(outdir/'selftest_js_assets.json'); routes=loadj(outdir/'selftest_routes.json'); cand=loadj(outdir/'selftest_candidates.json'); qual=loadj(outdir/'selftest_quality_result.json'); auth=loadj(outdir/'selftest_auth_graph.json'); jsg=loadj(outdir/'selftest_js_audit_graph.json'); replay=loadj(outdir/'selftest_replay_plan.json')
    thresholds={'routes_min_6':len(routes.get('routes',[]))>=6,'js_endpoints_min_2':len(js.get('endpoints',[]))>=2,'sourcemap_min_1':len(js.get('sourcemaps',[]))>=1,'graphql_min_1':len(js.get('graphql_operations',[]))>=1,'service_worker_min_1':len(js.get('service_workers',[]))>=1,'candidate_min_1':len(cand.get('candidates',[]))>=1,'replay_plan_per_candidate':len(replay.get('plans',[]))==len(cand.get('candidates',[])),'quality_not_confirming_static':all(f.get('output_status')!='promoted' for f in qual.get('findings',[]) if f.get('dynamic_state')!='DYNAMIC_CONFIRMED'),'auth_graph_nodes':len(auth.get('nodes',[]))>0,'js_graph_nodes':len(jsg.get('nodes',[]))>0}
    ok=all(c['returncode']==0 for c in commands) and all(v['ok'] for v in validations) and all(x['ok'] for x in py_ok) and all(thresholds.values())
    data={'schema_version':'selftest-result-v1','ok':ok,'commands':commands,'validations':validations,'python_syntax':py_ok,'thresholds':thresholds,'counts':{'routes':len(routes.get('routes',[])),'js_endpoints':len(js.get('endpoints',[])),'sourcemaps':len(js.get('sourcemaps',[])),'graphql':len(js.get('graphql_operations',[])),'service_workers':len(js.get('service_workers',[])),'candidates':len(cand.get('candidates',[])),'auth_graph_nodes':len(auth.get('nodes',[])),'js_graph_edges':len(jsg.get('edges',[]))},'quality_overall':qual.get('overall_status')}
    Path(ns.out).write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'ok':ok,'counts':data['counts'],'quality_overall':data['quality_overall']}, ensure_ascii=False))
    sys.exit(0 if ok else 1)
if __name__=='__main__': main()

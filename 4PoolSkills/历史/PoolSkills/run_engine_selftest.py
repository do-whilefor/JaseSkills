#!/usr/bin/env python3
from __future__ import annotations
import json, os, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
TIMEOUT_SECONDS=90
cmds=[
 [sys.executable,'collectors/route_collector.py','tests/fixtures/engine_project','--out','outputs/current/engine_routes.json'],
 [sys.executable,'collectors/js_asset_collector.py','tests/fixtures/engine_project','--out','outputs/current/engine_js.json'],
 [sys.executable,'collectors/hidden_parameter_collector.py','tests/fixtures/engine_project','--out','outputs/current/engine_params.json'],
 [sys.executable,'analyzers/semantic_graph_builder.py','tests/fixtures/engine_project','--routes','outputs/current/engine_routes.json','--params','outputs/current/engine_params.json','--out','outputs/current/engine_graph.json'],
 [sys.executable,'analyzers/frontend_backend_correlation_analyzer.py','--js','outputs/current/engine_js.json','--routes','outputs/current/engine_routes.json','--out','outputs/current/engine_correlation.json'],
 [sys.executable,'analyzers/taint_engine.py','--graph','outputs/current/engine_graph.json','--out','outputs/current/engine_taint_paths.json'],
 [sys.executable,'js/js_deep_pipeline.py','tests/fixtures/ast_project','--out-dir','outputs/current/js_deep'],
 [sys.executable,'business_logic/property_oracle.py','--spec','tests/fixtures/business_oracle/invariants.json','--events','tests/fixtures/business_oracle/events_pass.json','--out','outputs/current/property_oracle_pass.json'],
 [sys.executable,'business_logic/state_machine_replay.py','--machine','tests/fixtures/business_oracle/machine.json','--events','tests/fixtures/business_oracle/events_pass.json','--out','outputs/current/state_machine_pass.json'],
 [sys.executable,'scripts/windows_preflight.py'],
 [sys.executable,'detectors/detector_runner.py','tests/fixtures/engine_project','--graph','outputs/current/engine_graph.json','--out','outputs/current/engine_findings.json'],
 [sys.executable,'dynamic/candidate_to_replay_plan.py','--candidates','outputs/current/engine_findings.json','--out','outputs/current/engine_replay_plan.json'],
 [sys.executable,'dynamic/playwright_runner.py','--plan','outputs/current/engine_replay_plan.json','--root','tests/fixtures/engine_project','--out','outputs/current/engine_replay_result.json'],
 [sys.executable,'evidence/evidence_manifest_builder.py','--root','tests/fixtures/engine_project','--candidates',str(ROOT/'outputs/current/engine_findings.json'),'--out','outputs/current/engine_evidence_manifest.json'],
 [sys.executable,'quality/quality_gate.py','--candidates','outputs/current/engine_findings.json','--evidence','outputs/current/engine_evidence_manifest.json','--replay','outputs/current/engine_replay_result.json','--out','outputs/current/engine_quality_result.json'],
 [sys.executable,'report/report_generator.py','--candidates','outputs/current/engine_findings.json','--evidence','outputs/current/engine_evidence_manifest.json','--quality','outputs/current/engine_quality_result.json','--out','outputs/current/engine_report.md'],
]

def run_cmd(c):
    env=os.environ.copy(); env['PYTHONDONTWRITEBYTECODE']='1'
    try:
        p=subprocess.run(c,cwd=ROOT,text=True,capture_output=True,timeout=TIMEOUT_SECONDS,env=env)
        return {'cmd':' '.join(map(str,c)),'returncode':p.returncode,'stdout':(p.stdout or '')[-4000:],'stderr':(p.stderr or '')[-4000:]}
    except subprocess.TimeoutExpired as e:
        return {'cmd':' '.join(map(str,c)),'returncode':124,'stdout':(e.stdout or '')[-4000:] if isinstance(e.stdout,str) else '', 'stderr':((e.stderr or '')[-4000:] if isinstance(e.stderr,str) else '') + f'\ntimeout_after_seconds={TIMEOUT_SECONDS}'}

results=[]
for c in cmds:
    r=run_cmd(c); results.append(r)
    if r['returncode'] != 0:
        break
out={'ok':all(x['returncode']==0 for x in results) and len(results)==len(cmds),'results':results,'timeout_seconds':TIMEOUT_SECONDS}
Path('outputs/current/engine_selftest_result.json').parent.mkdir(parents=True,exist_ok=True)
Path('outputs/current/engine_selftest_result.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'ok':out['ok'],'commands':len(results),'out':'outputs/current/engine_selftest_result.json'},ensure_ascii=False))
sys.exit(0 if out['ok'] else 1)

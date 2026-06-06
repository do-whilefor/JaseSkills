#!/usr/bin/env python3
from __future__ import annotations
import argparse, importlib.util, json, subprocess, sys, os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load_mod(path,name):
    spec=importlib.util.spec_from_file_location(name,path); mod=importlib.util.module_from_spec(spec); assert spec and spec.loader; spec.loader.exec_module(mod); return mod
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--out',default='_audit_outputs/selftest_result.json'); args=ap.parse_args(); errors=[]; warnings=[]
    for p in sorted((ROOT/'schemas').glob('*.json')):
        try: json.loads(p.read_text(encoding='utf-8'))
        except Exception as exc: errors.append(f'schema json parse failed {p}: {exc}')
    fixture=ROOT/'tests/fixtures/local_minimal'; js=load_mod(ROOT/'tools/js_asset_extractor.py','js_asset_extractor').extract(fixture); routes=load_mod(ROOT/'tools/route_extractor.py','route_extractor').extract(fixture)
    if len(js.get('endpoints',[]))<3: errors.append('js endpoint extraction found fewer than 3 endpoints')
    for key in ['source_maps','graphql','storage','post_message','secret_like']:
        if not js.get(key): errors.append(f'{key} extraction failed')
    if len(routes.get('routes',[]))<3: errors.append('route extraction found fewer than 3 routes')
    ev=load_mod(ROOT/'tools/evidence_builder.py','evidence_builder'); qg=load_mod(ROOT/'tools/quality_gate.py','quality_gate')
    manifest=ev.build('fixture-candidate-1','DYNAMIC_CONFIRMED',[str(fixture/'request.txt'),str(fixture/'response.txt')],[{'path':'routes.js','line':1}],'local-fixture-replay'); q=qg.evaluate(manifest)
    if not q.get('passed'): errors.append(f'quality gate should pass confirmed fixture: {q}')
    qb=qg.evaluate(ev.build('fixture-candidate-2','STATIC_CANDIDATE',[],[],'local-fixture-replay'))
    if qb.get('passed'): errors.append('quality gate incorrectly passed static candidate')
    replay_results={}
    for label,rel in [('adversarial','_shared/tests/adversarial_test_harness.py'),('e2e','_shared/tests/e2e_replay/e2e_replay_runner.py'),('high_risk','_shared/tests/high_risk_replay/high_risk_replay_runner.py')]:
        try:
            cp=subprocess.run([sys.executable,str(ROOT/rel)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=40,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'}); replay_results[label]={'returncode':cp.returncode,'stdout_head':cp.stdout[:1000],'stderr_head':cp.stderr[:500]}
            if cp.returncode!=0: errors.append(f'{label} replay returned {cp.returncode}')
        except subprocess.TimeoutExpired: errors.append(f'{label} replay timed out')
    result={'schema_version':'hardening_selftest_v1','passed':not errors,'errors':errors,'warnings':warnings,'js_endpoint_count':len(js.get('endpoints',[])),'route_count':len(routes.get('routes',[])),'quality_confirmed_passed':q.get('passed'),'quality_static_passed':qb.get('passed'),'replay_results':replay_results}
    out=ROOT/args.out; out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); print(json.dumps(result,ensure_ascii=False,indent=2)); return 0 if not errors else 1
if __name__=='__main__': raise SystemExit(main())

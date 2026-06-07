#!/usr/bin/env python3
from __future__ import annotations
import json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; cases=json.loads((ROOT/'tests'/'quality_gate_hard_cases.json').read_text(encoding='utf-8'))
failed=[]; results=[]
for c in cases:
    fixture=str(ROOT/c['fixture'])
    if 'expected_final_status' in c:
        p=subprocess.run([sys.executable,str(ROOT/'scripts'/'quality_gate_hard_enforcer.py'),fixture,'--out',str(ROOT/'outputs'/(c['name']+'.json'))],capture_output=True,text=True)
        got=json.loads(p.stdout)['results'][0]['final_status']; exp=c['expected_final_status']
    else:
        p=subprocess.run([sys.executable,str(ROOT/'scripts'/'chain_evidence_validator.py'),fixture,'--out',str(ROOT/'outputs'/(c['name']+'.json'))],capture_output=True,text=True)
        got=json.loads(p.stdout)['results'][0]['status']; exp=c['expected_chain_status']
    ok=got==exp; results.append({'case':c['name'],'got':got,'expected':exp,'ok':ok})
    if not ok: failed.append(c['name'])
out={'status':'pass' if not failed else 'fail','failed':failed,'results':results}; (ROOT/'outputs'/'quality_gate_hard_test_results.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8'); print(json.dumps(out,ensure_ascii=False,indent=2)); sys.exit(0 if not failed else 1)

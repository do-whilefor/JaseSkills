#!/usr/bin/env python3
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'outputs/metrics'; OUT.mkdir(parents=True,exist_ok=True)
cases=[]
for f in [ROOT/'tests/regression_cases.json', ROOT/'tests/adversarial_regression_cases.json']:
    if f.exists():
        data=json.loads(f.read_text(encoding='utf-8')); cases.extend(data.get('cases',data if isinstance(data,list) else []))
out={'status':'ok','total_cases':len(cases),'labeled_cases':sum(1 for c in cases if c.get('expected_skill') or c.get('expected_status')),'trigger_accuracy':'requires runner output; not inferred','policy':'Do not claim trigger accuracy without expected labels and actual route logs.'}
(OUT/'skill_trigger_accuracy.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8'); print(json.dumps(out,ensure_ascii=False,indent=2))

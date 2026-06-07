#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
try:
    import jsonschema
except Exception:
    jsonschema = None
ROOT=Path(__file__).resolve().parents[1]
DEFAULT_PAIRS=[
    ('schemas/finding-candidate.schema.json','outputs/current/engine_findings.json'),
    ('schemas/evidence-manifest.schema.json','outputs/current/engine_evidence_manifest.json'),
    ('schemas/replay_plan.schema.json','outputs/current/engine_replay_plan.json'),
    ('schemas/replay-result.schema.json','outputs/current/engine_replay_result.json'),
    ('schemas/quality-result.schema.json','outputs/current/engine_quality_result.json'),
    ('schemas/security-report.schema.json','outputs/current/engine_report.md.json'),
]

def load(p): return json.loads((ROOT/p).read_text(encoding='utf-8'))
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--out', default='outputs/current/schema_selftest_result.json'); ns=ap.parse_args()
    results=[]
    if not jsonschema:
        data={'ok':False,'error':'jsonschema_missing','results':[]}
    else:
        for schema,data_file in DEFAULT_PAIRS:
            item={'schema':schema,'data':data_file,'ok':False}
            try:
                jsonschema.validate(load(data_file), load(schema)); item['ok']=True
            except Exception as e:
                item['error']=str(e)
            results.append(item)
        data={'ok':all(x['ok'] for x in results),'results':results}
    out=ROOT/ns.out; out.parent.mkdir(parents=True, exist_ok=True); out.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'ok':data['ok'],'checked':len(data.get('results',[]))}, ensure_ascii=False))
    sys.exit(0 if data['ok'] else 1)
if __name__=='__main__': main()

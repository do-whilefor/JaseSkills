#!/usr/bin/env python3
import json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'outputs/chains'; OUT.mkdir(parents=True, exist_ok=True)
REQUIRED=['source_file','route','request_summary','response_summary','auth_context','role_context','tenant_context']
mp=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'outputs/evidence_manifest.dynamic.json'
if not mp.exists(): out={'status':'validation_blocked','reason':'missing evidence manifest','confirmed_allowed':False}
else:
    m=json.loads(mp.read_text(encoding='utf-8')); stitched=[]
    for c in m.get('candidates',[]):
        missing=[f for f in REQUIRED if not c.get(f)]
        stitched.append({'candidate_id':c.get('candidate_id'),'missing_node_fields':missing,'chain_status':'quality_gate_candidate' if not missing else 'candidate','confirmed_allowed':False if missing else c.get('quality_gate_score',0)>=90})
    out={'status':'ok','stitched':stitched,'policy':'All chain nodes require real file/route/request/response/auth/role/tenant evidence.'}
(OUT/'stitched_chain_evidence.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8'); print(json.dumps(out,ensure_ascii=False,indent=2))

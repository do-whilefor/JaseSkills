#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import json
from _info_collect_lib import common_parser, parse_scope, enforce_scope
REVIEW_TERMS=('secret','token','password','admin','tenant','owner','role','hidden','source_map','dangerous','authorization','authentication','cors','oauth','webhook')
def main():
    ap=common_parser('Export human review queue for suspicious secrets, hidden APIs, auth/tenant boundaries and high-value candidates.')
    args=ap.parse_args(); path=Path(args.input).resolve(); scope=parse_scope(args.scope,path); ok,reason=enforce_scope(path,scope)
    if not ok: print(json.dumps({'status':'FAIL','reason':reason},ensure_ascii=False)); return 2
    data=json.loads(path.read_text(encoding='utf-8',errors='ignore'))
    items=data.get('items',[]) if isinstance(data,dict) else []
    queue=[]
    for it in items:
        typ=str(it.get('discovered_item_type','')).lower(); val=json.dumps(it.get('discovered_item_value_redacted',''),ensure_ascii=False).lower()
        if it.get('needs_human_review') or any(t in typ or t in val for t in REVIEW_TERMS):
            queue.append({'review_id':'hr-'+it.get('evidence_id','unknown').replace('ev-','')[:16],'reason':'candidate requires manual review before promotion','evidence_id':it.get('evidence_id'),'source_file':it.get('source_file'),'line':it.get('source_line_start'),'type':it.get('discovered_item_type'),'value_redacted':it.get('discovered_item_value_redacted'),'recommended_action':'Verify authorization, business context, role/tenant impact and false-positive conditions.'})
    out=args.output or '-'
    if args.format=='jsonl':
        text='\n'.join(json.dumps(q,ensure_ascii=False) for q in queue)+'\n'
    else:
        text=json.dumps({'schema_version':'human-review-queue.v1','items':queue,'count':len(queue)},ensure_ascii=False,indent=2)
    if out=='-': print(text)
    else: Path(out).write_text(text,encoding='utf-8')
    return 0
if __name__=='__main__': raise SystemExit(main())

#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import json
from _info_collect_lib import common_parser, parse_scope, enforce_scope, now_iso
ALLOWED={'promoted','needs_review','conflict','rejected'}
def load_json_or_jsonl(p:Path):
    text=p.read_text(encoding='utf-8',errors='ignore')
    try:
        data=json.loads(text); return data.get('items',data if isinstance(data,list) else [])
    except Exception:
        rows=[]
        for line in text.splitlines():
            try: rows.append(json.loads(line))
            except Exception: pass
        return rows

def main():
    ap=common_parser('Reviewer workflow: merge human decisions and emit promoted/needs_review/conflict/rejected ledgers.')
    ap.add_argument('--decisions', required=True, help='JSON/JSONL decisions with evidence_id,status,reviewer,reason')
    args=ap.parse_args(); manifest_path=Path(args.input).resolve(); scope=parse_scope(args.scope,manifest_path); ok,reason=enforce_scope(manifest_path,scope)
    if not ok: print(json.dumps({'status':'FAIL','reason':reason},ensure_ascii=False)); return 2
    manifest=json.loads(manifest_path.read_text(encoding='utf-8',errors='ignore')); items={it.get('evidence_id'):it for it in manifest.get('items',[]) if isinstance(it,dict)}
    decisions=load_json_or_jsonl(Path(args.decisions)); buckets={s:[] for s in ALLOWED}; errors=[]
    for d in decisions:
        if not isinstance(d,dict): continue
        eid=d.get('evidence_id'); status=d.get('status')
        if status not in ALLOWED: errors.append({'evidence_id':eid,'error':'invalid_status','status':status}); continue
        if eid not in items: errors.append({'evidence_id':eid,'error':'unknown_evidence_id'}); continue
        rec={'evidence_id':eid,'status':status,'reviewer':d.get('reviewer','manual'), 'reason':d.get('reason',''), 'decided_at':d.get('decided_at') or now_iso(), 'evidence':items[eid]}
        buckets[status].append(rec)
    report={'schema_version':'reviewer-workflow.v1','allowed_statuses':sorted(ALLOWED),'counts':{k:len(v) for k,v in buckets.items()},'errors':errors,'items':buckets}
    text=json.dumps(report,ensure_ascii=False,indent=2)
    if args.output=='-': print(text)
    else: Path(args.output).write_text(text,encoding='utf-8')
    return 0 if not errors else 1
if __name__=='__main__': raise SystemExit(main())

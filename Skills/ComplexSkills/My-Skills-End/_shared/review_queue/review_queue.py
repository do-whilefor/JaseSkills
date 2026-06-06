#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, datetime as dt, hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parent; QUEUE=ROOT/'queue.json'
def load(): return json.loads(QUEUE.read_text(encoding='utf-8')) if QUEUE.exists() else {'schema_version':'human_review_queue_v1','items':[]}
def save(q): QUEUE.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def rid(candidate_id, template_id): return 'REV-'+hashlib.sha256((candidate_id+'|'+template_id).encode()).hexdigest()[:12]
def main():
    ap=argparse.ArgumentParser(); sub=ap.add_subparsers(dest='cmd',required=True)
    a=sub.add_parser('add'); a.add_argument('--candidate-id',required=True); a.add_argument('--template-id',required=True); a.add_argument('--reason',required=True)
    for c in ['promote','reject','conflict']:
        p=sub.add_parser(c); p.add_argument('--review-id',required=True); p.add_argument('--reason',required=True)
    sub.add_parser('list'); args=ap.parse_args(); q=load()
    if args.cmd=='add':
        item={'review_id':rid(args.candidate_id,args.template_id),'candidate_id':args.candidate_id,'template_id':args.template_id,'status':'needs_review','reason':args.reason,'created_at':dt.datetime.utcnow().isoformat()+'Z','decision_log':[]}; q['items'].append(item); save(q); print(json.dumps(item,ensure_ascii=False,indent=2)); return
    if args.cmd=='list': print(json.dumps(q,ensure_ascii=False,indent=2)); return
    target=next((x for x in q['items'] if x.get('review_id')==args.review_id),None)
    if not target: print(json.dumps({'error':'review_id_not_found'},ensure_ascii=False)); raise SystemExit(2)
    target['status']={'promote':'promoted','reject':'rejected','conflict':'conflict'}[args.cmd]; target.setdefault('decision_log',[]).append({'status':target['status'],'reason':args.reason,'changed_at':dt.datetime.utcnow().isoformat()+'Z'}); save(q); print(json.dumps(target,ensure_ascii=False,indent=2))
if __name__=='__main__': main()

#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import json, yaml
from _info_collect_lib import common_parser, parse_scope, enforce_scope

def main():
    ap=common_parser('Evaluate rule precision/recall from labeled replay decisions. Inputs are manifest JSON and optional review decisions.')
    ap.add_argument('--decisions', default=None, help='JSON/JSONL with evidence_id and status promoted/rejected/needs_review/conflict')
    ap.add_argument('--rules', default='rules/top-tier-hidden-info-rules.yaml')
    args=ap.parse_args(); path=Path(args.input).resolve(); scope=parse_scope(args.scope,path); ok,reason=enforce_scope(path,scope)
    if not ok: print(json.dumps({'status':'FAIL','reason':reason},ensure_ascii=False)); return 2
    manifest=json.loads(path.read_text(encoding='utf-8',errors='ignore')); items=manifest.get('items',[])
    decisions={}
    if args.decisions and Path(args.decisions).exists():
        text=Path(args.decisions).read_text(encoding='utf-8',errors='ignore')
        try:
            data=json.loads(text); rows=data.get('items',data if isinstance(data,list) else [])
        except Exception:
            rows=[]
            for line in text.splitlines():
                try: rows.append(json.loads(line))
                except Exception: pass
        decisions={r.get('evidence_id'):r.get('status') for r in rows if isinstance(r,dict)}
    by_rule={}
    for it in items:
        rid=it.get('collector_provenance',{}).get('rule_id') or it.get('discovered_item_type')
        s=decisions.get(it.get('evidence_id'),'needs_review' if it.get('needs_human_review') else 'unlabeled')
        by_rule.setdefault(rid,{'tp':0,'fp':0,'fn':0,'needs_review':0,'unlabeled':0,'conflict':0})
        if s=='promoted': by_rule[rid]['tp']+=1
        elif s=='rejected': by_rule[rid]['fp']+=1
        elif s=='conflict': by_rule[rid]['conflict']+=1
        elif s=='needs_review': by_rule[rid]['needs_review']+=1
        else: by_rule[rid]['unlabeled']+=1
    for rid,stat in by_rule.items():
        denom=stat['tp']+stat['fp']
        stat['precision']=round(stat['tp']/denom,3) if denom else None
        stat['status']='measured' if denom else 'needs_labeled_replay'
    report={'schema_version':'rule-precision-evaluation.v1','rules_file':args.rules,'rules':by_rule,'note':'FN requires a golden corpus; absent golden data is reported as needs_labeled_replay, not as zero false negatives.'}
    text=json.dumps(report,ensure_ascii=False,indent=2)
    if args.output=='-': print(text)
    else: Path(args.output).write_text(text,encoding='utf-8')
    return 0
if __name__=='__main__': raise SystemExit(main())

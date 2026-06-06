#!/usr/bin/env python3
"""Report-claim evidence gate. Every structured claim must bind evidence_id.
Markdown files that assert confirmed without an EVID-* token are blocked.
"""
from __future__ import annotations
import argparse, json, re
from pathlib import Path
CONFIRM_RE=re.compile(r'(?i)\b(confirmed|已确认|确认漏洞|validated)\b')
EVID_RE=re.compile(r'EVID-[A-Za-z0-9_-]+')
def load_json(p):
    try: return json.loads(Path(p).read_text(encoding='utf-8'))
    except Exception: return None
def claims_from_obj(obj):
    out=[]
    def walk(x):
        if isinstance(x,dict):
            if {'claim_id','level','text'} & set(x): out.append(x)
            for v in x.values(): walk(v)
        elif isinstance(x,list):
            for v in x: walk(v)
    walk(obj); return out
def check_file(p: Path):
    errs=[]; obj=load_json(p) if p.suffix.lower()=='.json' else None
    if obj is not None:
        for i,c in enumerate(claims_from_obj(obj)):
            if c.get('level') in {'confirmed','candidate','needs_review','blocked','rejected','inconclusive'} and not c.get('evidence_id'):
                errs.append(f'{p}: claim[{i}] missing evidence_id')
            if c.get('level')=='confirmed' and not str(c.get('evidence_id','')).startswith('EVID-'):
                errs.append(f'{p}: confirmed claim[{i}] invalid evidence_id')
    elif p.suffix.lower() in {'.md','.txt'}:
        text=p.read_text(encoding='utf-8',errors='ignore')
        if CONFIRM_RE.search(text) and not EVID_RE.search(text): errs.append(f'{p}: confirmed wording without EVID-* token')
    return errs
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('paths',nargs='+'); ap.add_argument('--out')
    a=ap.parse_args(); errs=[]; scanned=0
    for s in a.paths:
        p=Path(s); fs=[p] if p.is_file() else [x for x in p.rglob('*') if x.is_file() and x.suffix.lower() in {'.json','.md','.txt'}]
        for f in fs: scanned+=1; errs.extend(check_file(f))
    res={'schema_version':'report_claim_evidence_gate_v2','scanned_file_count':scanned,'passed':not errs,'errors':errs[:200]}
    text=json.dumps(res,ensure_ascii=False,indent=2)
    if a.out: Path(a.out).parent.mkdir(parents=True,exist_ok=True); Path(a.out).write_text(text+'\n',encoding='utf-8')
    print(text); return 0 if res['passed'] else 1
if __name__=='__main__': raise SystemExit(main())

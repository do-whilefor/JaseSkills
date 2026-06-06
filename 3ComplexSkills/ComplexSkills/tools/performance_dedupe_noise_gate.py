#!/usr/bin/env python3
"""Candidate performance, duplicate and noise gate."""
from __future__ import annotations
import argparse, json, time, hashlib, re
from pathlib import Path
NOISE=re.compile(r'(?i)(node_modules|vendor|__pycache__|\.min\.js|dist/|build/|coverage/)')
def load(p): return json.loads(Path(p).read_text(encoding='utf-8', errors='ignore'))
def main():
    start=time.time(); ap=argparse.ArgumentParser(); ap.add_argument('--candidates', required=True); ap.add_argument('--max-candidates', type=int, default=5000); ap.add_argument('--max-duplicates', type=int, default=0); ap.add_argument('--out')
    a=ap.parse_args(); obj=load(a.candidates); cands=obj.get('candidates') or []
    seen=set(); dup=0; noise=0
    for c in cands:
        key=json.dumps({'detector':c.get('detector_id'),'file':c.get('source_file'),'line':c.get('source_line'),'route':c.get('route'),'sink':c.get('sink_type'),'param':c.get('parameter'),'raw':c.get('raw_signal_hash')}, sort_keys=True, ensure_ascii=False)
        h=hashlib.sha256(key.encode()).hexdigest()
        if h in seen: dup+=1
        seen.add(h)
        if NOISE.search(str(c.get('source_file') or '')): noise+=1
    blockers=[]
    if len(cands)>a.max_candidates: blockers.append('candidate_count_exceeds_limit')
    if dup>a.max_duplicates: blockers.append('duplicate_count_exceeds_limit')
    if noise: blockers.append('noise_paths_present')
    res={'schema_version':'performance_dedupe_noise_gate_v1','passed':not blockers,'candidate_count':len(cands),'duplicate_count':dup,'noise_filtered_count':noise,'elapsed_seconds':time.time()-start,'limits':{'max_candidates':a.max_candidates,'max_duplicates':a.max_duplicates},'blockers':blockers,'policy':'Candidate flooding, duplicates and dependency-noise paths block report promotion until deduped or suppressed with evidence.'}
    text=json.dumps(res, ensure_ascii=False, indent=2)
    if a.out: Path(a.out).parent.mkdir(parents=True, exist_ok=True); Path(a.out).write_text(text+'\n', encoding='utf-8')
    print(text); return 0 if res['passed'] else 1
if __name__=='__main__': raise SystemExit(main())

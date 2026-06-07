#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
rules={r['id']:r for r in json.loads((ROOT/'config'/'high_value_chain_rules.json').read_text(encoding='utf-8'))['chains']}
def load(p):
    d=json.loads(Path(p).read_text(encoding='utf-8')); return d['candidates'] if isinstance(d,dict) and 'candidates' in d else (d if isinstance(d,list) else [d])
def check(c):
    cid=c.get('vulnerability_chain') or c.get('chain_id')
    if not cid: return {'candidate_id':c.get('candidate_id'),'status':'not_chain_candidate','missing_nodes':[]}
    r=rules.get(cid)
    if not r: return {'candidate_id':c.get('candidate_id'),'status':'unknown_chain','missing_nodes':[]}
    have={n.get('node_id') for n in c.get('chain_evidence_nodes',[]) if isinstance(n,dict)}
    miss=[n for n in r['nodes'] if n not in have]
    return {'candidate_id':c.get('candidate_id'),'chain_id':cid,'status':'pass' if not miss else 'needs_human_review','missing_nodes':miss}
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('manifest',nargs='?',default=str(ROOT/'tests'/'fixtures'/'chain_positive_sourcemap_idor.json')); ap.add_argument('--out',default=str(ROOT/'outputs'/'chain_evidence_validation_results.json')); a=ap.parse_args()
    res=[check(c) for c in load(a.manifest)]; Path(a.out).parent.mkdir(parents=True,exist_ok=True); Path(a.out).write_text(json.dumps({'results':res},ensure_ascii=False,indent=2),encoding='utf-8'); print(json.dumps({'status':'pass' if all(r['status'] in ('pass','not_chain_candidate') for r in res) else 'needs_human_review','results':res},ensure_ascii=False,indent=2))
if __name__=='__main__': main()

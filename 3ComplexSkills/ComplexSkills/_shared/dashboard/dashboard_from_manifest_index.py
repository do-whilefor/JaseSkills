#!/usr/bin/env python3
"""Build dashboard only from an explicit manifest index.
This avoids dashboards silently mixing examples, stale fixtures, and real evidence.
"""
from __future__ import annotations
import argparse, html, json, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def esc(x): return html.escape(str(x))
def load(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--manifest-index',required=True); ap.add_argument('--out',required=True); a=ap.parse_args()
    idx=load(a.manifest_index); rows=[]
    if idx.get('schema_version')!='manifest_index_v1' or idx.get('source_policy')!='explicit_manifest_index_only':
        raise SystemExit('manifest_index_schema_or_source_policy_invalid')
    for item in idx.get('manifests',[]):
        if item.get('fixture_allowed') is True:
            continue
        p=ROOT/item['path']; m=load(p); cp=subprocess.run([sys.executable,str(ROOT/'_shared/quality/quality_gate_v4_1.py'),str(p)],text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        try: q=json.loads(cp.stdout)
        except Exception: q={'passed':False,'hard_blocks':['quality_gate_non_json']}
        rows.append(f"<tr><td>{esc(item['path'])}</td><td>{esc(m.get('candidate_id'))}</td><td>{esc(m.get('evidence_id'))}</td><td>{esc(m.get('final_status'))}</td><td>{esc(q.get('passed'))}</td><td>{esc(','.join(q.get('hard_blocks') or []))}</td></tr>")
    out=Path(a.out); out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text("<!doctype html><meta charset='utf-8'><h1>Manifest-backed dashboard</h1><p>source=explicit_manifest_index_only; fixture_confirmed_default_view=disabled</p><table><tr><th>Manifest</th><th>Candidate</th><th>Evidence</th><th>Status</th><th>QG</th><th>Blocks</th></tr>"+''.join(rows)+"</table>",encoding='utf-8')
    print(out); return 0
if __name__=='__main__': raise SystemExit(main())

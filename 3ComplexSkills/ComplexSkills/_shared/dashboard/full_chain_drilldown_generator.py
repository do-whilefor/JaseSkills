#!/usr/bin/env python3
"""Generate full-chain drill-down dashboard data and static HTML.

Inputs are optional JSON artifacts produced by semantic graph, candidates,
replay plan, browser matrix, evidence manifest, role/tenant matrix, variant
expansion and final claim guard.
"""
from __future__ import annotations
import argparse, json, html
from pathlib import Path
from typing import Any

def load(path: str|None):
    if not path: return None
    p=Path(path)
    if not p.exists(): return {'_missing':path}
    try: return json.loads(p.read_text(encoding='utf-8', errors='ignore'))
    except Exception as exc: return {'_error':str(exc),'_path':path}

def rows(obj, key):
    return obj.get(key) if isinstance(obj,dict) and isinstance(obj.get(key),list) else []

def build(args):
    semantic=load(args.semantic_graph) or {}; candidates=load(args.candidates) or {}; replay=load(args.replay_plan) or {}; browser=load(args.browser_matrix) or {}; evidence=load(args.evidence_manifest) or {}; matrix=load(args.role_tenant_matrix) or {}; variant=load(args.variant_expansion) or {}; guard=load(args.final_guard) or {}
    chain=[]
    cand_rows=rows(candidates,'candidates') or ([candidates] if isinstance(candidates,dict) and (candidates.get('type') or candidates.get('candidate_id')) else [])
    for r in rows(semantic,'routes')[:1000]:
        related=[c for c in cand_rows if (c.get('path') or c.get('route')) == r.get('path') or c.get('file') == r.get('file')]
        chain.append({'route':r,'candidates':related,'browser_status':browser.get('runtime_status'),'evidence_count':len(evidence.get('network_requests') or []),'role_tenant_status':matrix.get('status'),'variant_status':variant.get('schema_version'),'claim_allowed':guard.get('allowed')})
    return {'schema_version':'full_chain_dashboard_v1','counts':{'routes':len(rows(semantic,'routes')),'candidates':len(cand_rows),'replay_plans':len(rows(replay,'plans')),'network_requests':len(evidence.get('network_requests') or []) if isinstance(evidence,dict) else 0},'chain':chain,'component_status':{'semantic_graph':bool(semantic),'candidates':bool(candidates),'replay_plan':bool(replay),'browser_matrix':bool(browser),'evidence_manifest':bool(evidence),'role_tenant_matrix':bool(matrix),'variant_expansion':bool(variant),'final_guard':bool(guard)},'claim_policy':'Every route-to-report chain is incomplete until required components are present and final guard allows promotion.'}

def render_html(data):
    rows_html=[]
    for item in data.get('chain',[])[:500]:
        r=item['route']; rows_html.append('<tr>' + ''.join(f'<td>{html.escape(str(x))}</td>' for x in [r.get('method'), r.get('path'), r.get('framework'), r.get('file'), len(item.get('candidates') or []), item.get('browser_status'), item.get('evidence_count'), item.get('role_tenant_status'), item.get('claim_allowed')]) + '</tr>')
    return """<!doctype html><meta charset='utf-8'><title>Full chain drill-down</title><style>body{font-family:system-ui,Segoe UI,Arial;margin:24px}table{border-collapse:collapse;width:100%}td,th{border:1px solid #ccc;padding:6px;vertical-align:top}th{background:#f3f3f3}.bad{color:#900}</style><h1>Route → Candidate → Evidence → Quality Gate → Report</h1><pre>COUNTS</pre><table><thead><tr><th>Method</th><th>Route</th><th>Framework</th><th>File</th><th>Candidates</th><th>Browser</th><th>Evidence</th><th>Role/Tenant</th><th>Claim allowed</th></tr></thead><tbody>ROWS</tbody></table>""".replace('COUNTS', html.escape(json.dumps(data.get('counts',{}),ensure_ascii=False,indent=2))).replace('ROWS','\n'.join(rows_html))

def main():
    ap=argparse.ArgumentParser()
    for n in ['semantic_graph','candidates','replay_plan','browser_matrix','evidence_manifest','role_tenant_matrix','variant_expansion','final_guard']:
        ap.add_argument('--'+n.replace('_','-'), dest=n)
    ap.add_argument('--out-json', required=True); ap.add_argument('--out-html')
    args=ap.parse_args(); data=build(args)
    Path(args.out_json).parent.mkdir(parents=True, exist_ok=True); Path(args.out_json).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    if args.out_html:
        Path(args.out_html).parent.mkdir(parents=True, exist_ok=True); Path(args.out_html).write_text(render_html(data),encoding='utf-8')
    print(json.dumps({'ok':True,'routes':data['counts']['routes'],'out_json':args.out_json,'out_html':args.out_html},ensure_ascii=False))
if __name__=='__main__': main()

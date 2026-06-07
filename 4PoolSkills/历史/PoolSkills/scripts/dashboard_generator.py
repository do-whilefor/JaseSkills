#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,html
from pathlib import Path

def load(p,d):
    p=Path(p); return json.loads(p.read_text(encoding='utf-8')) if p.exists() else d

def td(v): return '<td>'+html.escape(json.dumps(v,ensure_ascii=False) if isinstance(v,(dict,list)) else str(v))+'</td>'

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--manifest',default='outputs/detector_candidates_v4.json'); ap.add_argument('--quality',default='outputs/quality_gate_hard_results.json'); ap.add_argument('--routes',default='outputs/attack_surface.json'); ap.add_argument('--graph',default='outputs/security_graph.json'); ap.add_argument('--ledger',default='outputs/asset_ledger.json'); ap.add_argument('--js',default='outputs/js_assets.json'); ap.add_argument('--sourcemap',default='outputs/js_sourcemap_inventory.json'); ap.add_argument('--out',default='dashboard/index.html'); a=ap.parse_args()
    manifest=load(a.manifest,{}); q=load(a.quality,{}); routes=load(a.routes,{}); graph=load(a.graph,{}); ledger=load(a.ledger,{}); js=load(a.js,{}); sm=load(a.sourcemap,{})
    candidates=manifest.get('candidates',[]) if isinstance(manifest,dict) else []
    qmap={x.get('id') or x.get('candidate_id'):x for x in q.get('results',[])} if isinstance(q,dict) else {}
    rr=''.join('<tr>'+''.join(td(v) for v in [r.get('method'),r.get('route'),r.get('framework_hint'),r.get('file'),r.get('line'),r.get('handler_hint'),r.get('parameters')])+'</tr>' for r in routes.get('routes',[]))
    cr=''.join('<tr>'+''.join(td(v) for v in [c.get('id'),c.get('type'),c.get('status'),c.get('source'),c.get('route'),c.get('method'),len(c.get('code_evidence',[])),len(c.get('js_evidence',[])),len(c.get('dynamic_evidence',[])),len(c.get('negative_controls',[])),(c.get('quality_gate') or {}).get('score'),qmap.get(c.get('id'),{}).get('final_status'),qmap.get(c.get('id'),{}).get('hard_failures'),c.get('report_mapping')])+'</tr>' for c in candidates)
    jsrows=''.join('<tr>'+''.join(td(v) for v in [x.get('file'),x.get('endpoint'),x.get('line')])+'</tr>' for x in js.get('endpoints',[])[:300])
    bridge=''.join('<tr>'+''.join(td(v) for v in [x.get('file'),x.get('signal'),x.get('line'),x.get('boundary_review_required')])+'</tr>' for x in js.get('platform_bridges',[])[:200])
    sourcerows=''.join('<tr>'+''.join(td(v) for v in [x.get('file'),x.get('kind'),x.get('source'),x.get('value')])+'</tr>' for x in sm.get('extracted_candidate_signals',[])[:300])
    doc=f"""<!doctype html><meta charset=utf-8><title>Security Dashboard</title><style>body{{font-family:system-ui;margin:24px}}table{{border-collapse:collapse;width:100%;margin-bottom:24px}}td,th{{border:1px solid #ddd;padding:7px;vertical-align:top;font-size:13px}}code{{background:#f6f6f6;padding:2px 4px}}</style><h1>Route → Candidate → Evidence → Quality Gate → Report</h1><p>Policy: dashboard is a traceability view only; it must not create vulnerability conclusions without manifest v4 and hard quality gate.</p><h2>Asset Ledger</h2><p>Files: {html.escape(str(ledger.get('file_count','n/a')))} | Languages: {html.escape(json.dumps(ledger.get('languages',{}),ensure_ascii=False))} | Frameworks: {html.escape(json.dumps(ledger.get('frameworks',[]),ensure_ascii=False))}</p><h2>Security Graph</h2><p>Nodes: {len(graph.get('nodes',[]))} | Edges: {len(graph.get('edges',[]))} | Quality: {html.escape(json.dumps(graph.get('quality',{}),ensure_ascii=False))}</p><h2>Routes</h2><table><tr><th>Method</th><th>Route</th><th>Framework</th><th>File</th><th>Line</th><th>Handler</th><th>Params</th></tr>{rr}</table><h2>Candidates</h2><table><tr><th>ID</th><th>Type</th><th>Status</th><th>Source</th><th>Route</th><th>Method</th><th>Code Ev</th><th>JS Ev</th><th>Dynamic Ev</th><th>Neg Ctrl</th><th>Score</th><th>Hard Gate</th><th>Failures</th><th>Report Mapping</th></tr>{cr}</table><h2>JS Endpoint Candidates</h2><table><tr><th>File</th><th>Endpoint</th><th>Line</th></tr>{jsrows}</table><h2>JS Platform Boundary Bridges</h2><table><tr><th>File</th><th>Signal</th><th>Line</th><th>Boundary Review</th></tr>{bridge}</table><h2>Sourcemap / Feature Flag / i18n / Telemetry Signals</h2><table><tr><th>File</th><th>Kind</th><th>Source</th><th>Value</th></tr>{sourcerows}</table>"""
    Path(a.out).parent.mkdir(parents=True,exist_ok=True); Path(a.out).write_text(doc,encoding='utf-8'); print(a.out)
if __name__=='__main__': main()

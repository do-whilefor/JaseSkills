#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, html
from pathlib import Path

def load(p): return json.loads(Path(p).read_text(encoding='utf-8')) if p and Path(p).exists() else {}
def esc(x): return html.escape(json.dumps(x,ensure_ascii=False) if isinstance(x,(dict,list)) else str(x or ''))

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--routes'); ap.add_argument('--js'); ap.add_argument('--candidates'); ap.add_argument('--evidence'); ap.add_argument('--quality'); ap.add_argument('--auth_graph'); ap.add_argument('--js_graph'); ap.add_argument('--out',required=True); ns=ap.parse_args()
    routes=load(ns.routes).get('routes',[]); js=load(ns.js); candidates=load(ns.candidates).get('candidates',[]); evidence=load(ns.evidence).get('findings',[]); quality=load(ns.quality).get('findings',[]); auth=load(ns.auth_graph); jsg=load(ns.js_graph)
    rows=[]
    for c in candidates[:500]:
        q=next((x for x in quality if x.get('candidate_id')==c.get('id')), {})
        e=next((x for x in evidence if x.get('candidate_id')==c.get('id')), {})
        rows.append('<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>'.format(esc(c.get('id')),esc(c.get('type')),esc(c.get('status')),esc(c.get('reachability_status')),esc(q.get('output_status')),esc(q.get('allowed_report_level')),esc(q.get('hard_failures')),len(e.get('evidence',[]))))
    route_rows=''.join('<tr><td>{}</td><td>{}</td><td>{}</td><td>{}:{}</td><td>{}</td><td>{}</td></tr>'.format(esc(r.get('method')),esc(r.get('path')),esc(r.get('framework')),esc(r.get('file')),esc(r.get('line')),esc(r.get('authn_hint')),esc(r.get('authz_hint'))) for r in routes[:500])
    js_rows=''.join('<tr><td>{}</td><td>{}</td><td>{}:{}</td><td>{}</td></tr>'.format(esc(e.get('path')),esc(e.get('evidence')),esc(e.get('file')),esc(e.get('line')),esc(e.get('requires_backend_correlation'))) for e in js.get('endpoints',[])[:500])
    doc=f"""<!doctype html><meta charset='utf-8'><title>Authorized Security Audit Dashboard</title>
<style>body{{font-family:system-ui,Arial;margin:24px}}table{{border-collapse:collapse;width:100%;margin:16px 0}}td,th{{border:1px solid #ddd;padding:6px;font-size:13px;vertical-align:top}}.warn{{background:#fff6cc}}</style>
<h1>Asset → Route → JS API → Auth Graph → Candidate → Evidence → Quality Gate → Report</h1>
<p class='warn'>This dashboard is traceability only. Static signals are not confirmed vulnerabilities. Promotion requires runtime evidence, negative controls, report mapping and non-destructive boundary.</p>
<h2>Counts</h2><p>Routes: {len(routes)} | JS endpoints: {len(js.get('endpoints',[]))} | JS sourcemaps: {len(js.get('sourcemaps',[]))} | GraphQL ops: {len(js.get('graphql_operations',[]))} | Auth graph nodes: {len(auth.get('nodes',[]))} | JS graph correlations: {len(jsg.get('edges',[]))} | Candidates: {len(candidates)} | Evidence bindings: {len(evidence)}</p>
<h2>Routes</h2><table><tr><th>Method</th><th>Path</th><th>Framework</th><th>Source</th><th>AuthN</th><th>AuthZ</th></tr>{route_rows}</table>
<h2>JS API Candidates</h2><table><tr><th>URL</th><th>Evidence</th><th>Source</th><th>Backend Correlation Required</th></tr>{js_rows}</table>
<h2>Candidate Chain</h2><table><tr><th>ID</th><th>Type</th><th>Input</th><th>Reachability</th><th>Quality Output</th><th>Report Level</th><th>Hard Failures</th><th>Evidence</th></tr>{''.join(rows)}</table>
"""
    out=Path(ns.out); out.parent.mkdir(parents=True, exist_ok=True); out.write_text(doc, encoding='utf-8')
    print(json.dumps({'ok':True,'out':str(out),'candidates':len(candidates)}, ensure_ascii=False))
if __name__=='__main__': main()

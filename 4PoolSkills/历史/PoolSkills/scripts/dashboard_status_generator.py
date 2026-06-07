#!/usr/bin/env python3
import json, html, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if '--self-test' in sys.argv:
    print('ok'); raise SystemExit(0)

def load(rel, default):
    p=ROOT/rel
    if not p.exists(): return default, 'missing'
    try: return json.loads(p.read_text(encoding='utf-8')), 'ready'
    except Exception as e: return {'error':str(e)}, 'failed'
manifest, mstat = load('outputs/evidence_manifest.json', {'candidates':[]})
qg, qstat = load('outputs/quality_gate_result.json', {})
health, hstat = load('outputs/tool_health_score.json', {})
reg, rstat = load('outputs/regression_result.json', {})
rows=[]
for c in manifest.get('candidates',[]):
    rows.append('<tr>' + ''.join(f'<td>{html.escape(str(c.get(k,"")))}</td>' for k in ['candidate_id','vulnerability_type','state','route','method','quality_gate_score','final_status']) + '</tr>')
html_doc=f"""<!doctype html><meta charset="utf-8"><title>Authorized Security Audit Dashboard</title>
<h1>Authorized Security Audit Dashboard</h1>
<p>Data sources: manifest={mstat}, quality_gate={qstat}, tool_health={hstat}, regression={rstat}</p>
<h2>Tool Health</h2><pre>{html.escape(json.dumps(health, ensure_ascii=False, indent=2)[:5000])}</pre>
<h2>Regression</h2><pre>{html.escape(json.dumps(reg, ensure_ascii=False, indent=2)[:5000])}</pre>
<h2>Route → Candidate → Evidence → Quality Gate → Report</h2>
<table border="1"><tr><th>candidate_id</th><th>type</th><th>state</th><th>route</th><th>method</th><th>qg</th><th>final</th></tr>{''.join(rows) or '<tr><td colspan="7">blocked: no manifest candidates</td></tr>'}</table>"""
out=ROOT/'dashboard/index.html'; out.write_text(html_doc, encoding='utf-8')
print(json.dumps({'status':'pass','dashboard':str(out),'data_sources':{'manifest':mstat,'quality_gate':qstat,'tool_health':hstat,'regression':rstat}}, ensure_ascii=False, indent=2))

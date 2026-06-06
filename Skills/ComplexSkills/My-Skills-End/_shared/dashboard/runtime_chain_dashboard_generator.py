#!/usr/bin/env python3
from __future__ import annotations
import html, json, hashlib, sys, subprocess, os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]

def esc(x): return html.escape(str(x))
def load(path, default=None):
    try: return json.loads(Path(path).read_text(encoding='utf-8'))
    except Exception: return default

def sha(path):
    h=hashlib.sha256(); h.update(Path(path).read_bytes()); return h.hexdigest()

def main():
    out=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'_shared/dashboard/runtime_chain_dashboard_v4_3.html'
    manifests=sorted((ROOT/'_shared/tests/fixtures').glob('C[0-9][0-9]-*.json'))
    parser=load(ROOT/'_shared/tools/parser_runtime_readiness_v4_3.json', {})
    playwright=load(ROOT/'_shared/runs/playwright_runtime_readiness_v4_3.json', {})
    oss=load(ROOT/'_shared/tests/oss_replay/oss_replay_last_result.json', {})
    high=load(ROOT/'_shared/tests/high_risk_replay/high_risk_replay_last_result.json', {})
    rows=[]
    for p in manifests[:200]:
        m=load(p,{})
        rows.append(f"<tr><td>{esc(p.relative_to(ROOT))}<br><small>{sha(p)[:16]}</small></td><td>{esc(m.get('template_id'))}</td><td>{esc(m.get('route'))}</td><td>{esc(m.get('candidate_id'))}</td><td>{len(m.get('code_evidence') or [])}</td><td>{len(m.get('dynamic_evidence') or [])}</td><td>{esc(m.get('quality_gate',{}).get('passed'))}</td><td>{esc(m.get('final_status'))}</td></tr>")
    html_text=f"""<!doctype html><meta charset='utf-8'><title>Runtime Chain Dashboard v4.3</title><style>body{{font-family:system-ui;margin:24px}}table{{border-collapse:collapse;width:100%}}td,th{{border:1px solid #bbb;padding:6px;vertical-align:top}}pre{{background:#f6f6f6;padding:8px}}</style><h1>Runtime Chain Dashboard v4.3</h1><p>Run → Skill → Extractor → Parser readiness → Candidate → Evidence → Quality Gate → Report → Human Review.</p><h2>Runtime readiness</h2><pre>{esc(json.dumps({'parser':parser,'playwright':playwright,'oss':oss,'high_risk':high},ensure_ascii=False,indent=2))}</pre><h2>Manifest chain</h2><table><tr><th>Manifest</th><th>Template</th><th>Route</th><th>Candidate</th><th>Code evidence</th><th>Dynamic evidence</th><th>Quality</th><th>Status</th></tr>{''.join(rows)}</table>"""
    out.parent.mkdir(parents=True,exist_ok=True); out.write_text(html_text,encoding='utf-8'); print(out); return 0
if __name__=='__main__': raise SystemExit(main())

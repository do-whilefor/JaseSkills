#!/usr/bin/env python3
from __future__ import annotations
import argparse, html, json
from pathlib import Path
from datetime import datetime, timezone

def read_json(path:Path):
    try: return json.loads(path.read_text(encoding='utf-8', errors='ignore'))
    except Exception as e: return {'_error':str(e)}

def count_jsonl(path:Path):
    if not path.exists(): return 0
    return sum(1 for line in path.read_text(encoding='utf-8', errors='ignore').splitlines() if line.strip())

def status_badge(status:str)->str:
    status=str(status or 'UNKNOWN')
    return f'<span class="badge {html.escape(status.lower())}">{html.escape(status)}</span>'

def main():
    ap=argparse.ArgumentParser(description='Generate static HTML dashboard from real selftest artifacts.')
    ap.add_argument('--root',default='.')
    ap.add_argument('--selftest-dir',default='selftest/out')
    ap.add_argument('--out',default='dashboard/security-audit-dashboard.html')
    args=ap.parse_args(); root=Path(args.root); st=Path(args.selftest_dir)
    skill=read_json(st/'skill-selftest.json')
    parser=read_json(st/'parser-backend-check.json')
    runtime=read_json(st/'runtime-readiness-check.json')
    schema=read_json(st/'evidence-schema-validate.json')
    js_count=count_jsonl(st/'js-fixture-candidates.jsonl')
    surf_count=count_jsonl(st/'code-surface-fixture.jsonl')
    manifest_count=count_jsonl(st/'js-manifest-candidates.jsonl')
    cfg_count=count_jsonl(st/'config-dependency-fixture.jsonl')
    norm_count=count_jsonl(st/'info-surface.normalized.jsonl')
    manifest=read_json(st/'evidence-manifest.json')
    template_index=read_json(root/'manifests/template_index.json') if (root/'manifests/template_index.json').exists() else {'templates':[]}
    knowledge_index=read_json(root/'manifests/knowledge_index.json') if (root/'manifests/knowledge_index.json').exists() else {'entries':[]}
    parser_rows=[]
    for k,v in sorted((parser.get('checks') or {}).items()):
        parser_rows.append(f'<tr><td>{html.escape(k)}</td><td>{status_badge("PASS" if v.get("available") else "MISSING")}</td><td><code>{html.escape(str(v.get("version") or v.get("reason") or v.get("path") or ""))}</code></td></tr>')
    skill_rows=[]
    for r in skill.get('results',[]):
        skill_rows.append(f'<tr><td><code>{html.escape(r.get("path",""))}</code></td><td>{status_badge(r.get("status"))}</td><td>{html.escape(str(r.get("score")))} / {html.escape(str(r.get("max_score")))}</td><td>{html.escape(", ".join(r.get("missing",[])))}</td></tr>')
    html_text=f'''<!doctype html><html lang="zh"><head><meta charset="utf-8"><title>Security Audit Skills Dashboard</title>
<style>body{{font-family:system-ui,-apple-system,Segoe UI,sans-serif;margin:28px;line-height:1.45}}table{{border-collapse:collapse;width:100%;margin:12px 0 24px}}td,th{{border:1px solid #ddd;padding:8px;vertical-align:top}}th{{background:#f6f6f6;text-align:left}}code{{word-break:break-all}}.badge{{display:inline-block;padding:2px 8px;border-radius:999px;background:#eee}}.pass{{background:#d9f7d9}}.fail,.missing{{background:#ffdada}}.unknown{{background:#fff1c2}}.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px}}.card{{border:1px solid #ddd;border-radius:8px;padding:12px}}.num{{font-size:28px;font-weight:700}}</style></head><body>
<h1>Security Audit Skills Dashboard</h1>
<p>Generated at {html.escape(datetime.now(timezone.utc).isoformat())}. This dashboard only reflects real local files and selftest outputs; it does not prove vulnerabilities.</p>
<div class="cards">
<div class="card"><div>Skill selftest</div><div class="num">{html.escape(str(skill.get('overall_status','UNKNOWN')))}</div></div>
<div class="card"><div>JS fixture candidates</div><div class="num">{js_count}</div></div>
<div class="card"><div>Code surface candidates</div><div class="num">{surf_count}</div></div>
<div class="card"><div>JS manifest candidates</div><div class="num">{manifest_count}</div></div>
<div class="card"><div>Config/dependency candidates</div><div class="num">{cfg_count}</div></div>
<div class="card"><div>Normalized info surface</div><div class="num">{norm_count}</div></div>
<div class="card"><div>Evidence manifest items</div><div class="num">{html.escape(str(len(manifest.get('items',[])) if isinstance(manifest.get('items'),list) else '0'))}</div></div>
<div class="card"><div>Templates indexed</div><div class="num">{html.escape(str(len(template_index.get('templates',[]))))}</div></div>
<div class="card"><div>Knowledge entries indexed</div><div class="num">{html.escape(str(len(knowledge_index.get('entries',[]))))}</div></div>
</div>
<h2>Skill Structural Checks</h2><table><tr><th>Path</th><th>Status</th><th>Score</th><th>Missing</th></tr>{''.join(skill_rows)}</table>
<h2>Parser Backend Availability</h2><table><tr><th>Backend</th><th>Status</th><th>Version / Reason</th></tr>{''.join(parser_rows)}</table>
<h2>Runtime Required Files</h2><pre>{html.escape(json.dumps(runtime.get('required_package_files',{}),ensure_ascii=False,indent=2))}</pre>
<h2>Evidence Schema Check</h2><pre>{html.escape(json.dumps(schema,ensure_ascii=False,indent=2))}</pre>
<h2>Route → Candidate → Evidence → Quality Gate → Report Status</h2>
<table><tr><th>Stage</th><th>Current artifact</th><th>Status</th><th>Limitation</th></tr>
<tr><td>Source / JS / config collection</td><td>js-fixture-candidates.jsonl, js-manifest-candidates.jsonl, code-surface-fixture.jsonl, config-dependency-fixture.jsonl</td><td>{status_badge('PASS' if js_count and surf_count and cfg_count else 'UNKNOWN')}</td><td>Fixture proof only; project runtime required for real target.</td></tr>
<tr><td>Normalizer / detector routing</td><td>info-surface.normalized.jsonl</td><td>{status_badge('PASS' if norm_count else 'UNKNOWN')}</td><td>Maps candidates to severe-vulnerability entry signals; does not confirm vulnerabilities.</td></tr>
<tr><td>Evidence manifest</td><td>evidence-manifest.json</td><td>{status_badge(schema.get('status','UNKNOWN'))}</td><td>Indexes evidence only; does not prove vulnerability.</td></tr>
<tr><td>Quality gate</td><td>qg-finding-score.py / quality-gate-check.py</td><td>{status_badge('AVAILABLE')}</td><td>Needs actual draft report per finding.</td></tr>
<tr><td>Report</td><td>templates/final-report.md</td><td>{status_badge('TEMPLATE_ONLY')}</td><td>Cannot be used as finding without dynamic evidence.</td></tr></table>
</body></html>'''
    out=Path(args.out); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(html_text,encoding='utf-8')
    print(f'wrote {out}')
if __name__=='__main__': main()

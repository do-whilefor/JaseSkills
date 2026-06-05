#!/usr/bin/env python3
from __future__ import annotations
import argparse, html, json
from pathlib import Path

def load(p: Path, default):
    try:
        return json.loads(p.read_text(encoding='utf-8'))
    except Exception:
        return default

def main():
    ap=argparse.ArgumentParser(description='Generate report and HTML dashboard from real JS top-tier artifacts')
    ap.add_argument('--report-dir', default='reports/js-top-tier')
    args=ap.parse_args()
    d=Path(args.report_dir)
    d.mkdir(parents=True, exist_ok=True)
    ledger=load(d/'js_asset_ledger.json', {})
    analysis=load(d/'js_analysis.json', {})
    findings=load(d/'js_findings.json', {'findings':[]}).get('findings', [])
    runtime=load(d/'js_runtime_evidence.json', {})
    diff=load(d/'js_role_tenant_diff.json', {})
    stats=ledger.get('stats', {})
    md=[]
    md += ['# JS 顶级收集/分析/审计运行报告','']
    md += ['## 1. 资产收集摘要','']
    md += [f"- JS assets: {stats.get('javascript_assets',0)}", f"- Source maps: {stats.get('sourcemaps',0)}", f"- Manifests: {stats.get('manifests',0)}", f"- Service workers: {stats.get('service_workers',0)}", f"- WASM: {stats.get('wasm',0)}", f"- Evidence items: {stats.get('evidence_items',0)}", '']
    md += ['## 2. Parser backend 状态','']
    for b in analysis.get('backend_status', []):
        md.append(f"- `{b.get('name')}`: `{b.get('status')}` — {b.get('reason')}")
    md += ['', '## 3. Findings 状态统计','']
    counts={}
    for f in findings:
        counts[f.get('status','unknown')] = counts.get(f.get('status','unknown'), 0) + 1
    for k,v in sorted(counts.items()):
        md.append(f'- `{k}`: {v}')
    md += ['', '## 4. 动态证据与 role/tenant','']
    md.append(f"- Runtime evidence: `{runtime.get('status','missing')}`")
    md.append(f"- Role/tenant diff: `{diff.get('status','missing')}`")
    md += ['', '## 5. 前 30 条候选','']
    md.append('| id | rule | status | asset | line | reason |')
    md.append('| --- | --- | --- | --- | ---: | --- |')
    for f in findings[:30]:
        reason = str(f.get('reason','')).replace('|','/')
        md.append(f"| {f.get('finding_id')} | {f.get('rule_id')} | {f.get('status')} | `{f.get('asset_path')}` | {f.get('line') or ''} | {reason} |")
    md += ['', '## 6. 强制结论','']
    md.append('没有动态证据、role/tenant replay 或真实后端验证的 finding 不得写成 verified。')
    (d/'js_top_tier_report.md').write_text('\n'.join(md)+'\n', encoding='utf-8')
    rows=[]
    cols=['finding_id','rule_id','status','asset_path','line','dynamic_validation','role_tenant_replay']
    for f in findings[:200]:
        rows.append('<tr>' + ''.join(f'<td>{html.escape(str(f.get(c,"")))}</td>' for c in cols) + '</tr>')
    stats_html = html.escape(json.dumps(stats, ensure_ascii=False, indent=2))
    backend_html = html.escape(json.dumps(analysis.get('backend_status', []), ensure_ascii=False, indent=2))
    page = '<!doctype html><meta charset="utf-8"><title>JS Top Tier Dashboard</title>'
    page += '<style>body{font-family:sans-serif}table{border-collapse:collapse;width:100%}td,th{border:1px solid #ccc;padding:4px;font-size:12px}</style>'
    page += '<h1>JS Top Tier Dashboard</h1><h2>Stats</h2><pre>' + stats_html + '</pre>'
    page += '<h2>Backend</h2><pre>' + backend_html + '</pre>'
    page += '<h2>Findings</h2><table><tr><th>id</th><th>rule</th><th>status</th><th>asset</th><th>line</th><th>dynamic</th><th>role/tenant</th></tr>' + ''.join(rows) + '</table>'
    (d/'js_top_tier_dashboard.html').write_text(page, encoding='utf-8')
    print(json.dumps({'ok':True,'report':str(d/'js_top_tier_report.md'),'dashboard':str(d/'js_top_tier_dashboard.html'),'findings':len(findings)}, ensure_ascii=False, indent=2))
if __name__=='__main__':
    main()

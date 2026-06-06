#!/usr/bin/env python3
from __future__ import annotations
import argparse, html, json
from pathlib import Path

def load(p, default=None):
    try: return json.loads(Path(p).read_text(encoding='utf-8'))
    except Exception: return default if default is not None else {}

def table(rows, cols):
    s='<table><thead><tr>'+''.join(f'<th>{html.escape(c)}</th>' for c in cols)+'</tr></thead><tbody>'
    for r in rows:
        s+='<tr>'+''.join(f'<td>{html.escape(str(r.get(c,"")))}</td>' for c in cols)+'</tr>'
    return s+'</tbody></table>'

def main():
    ap=argparse.ArgumentParser(description='Generate evidence-chain drill-down dashboard: Finding -> JS -> API -> params -> browser action -> HAR -> role/tenant -> quality gate.')
    ap.add_argument('--report-dir', default='reports/js-top-tier')
    args=ap.parse_args(); d=Path(args.report_dir); d.mkdir(parents=True, exist_ok=True)
    findings=load(d/'js_findings.json', {'findings':[]}).get('findings',[])
    api=load(d/'js_api_parameter_model.json', {'apis':[]}).get('apis',[])
    manifest=load(d/'js_evidence_manifest.json', {})
    runtime=load(d/'js_runtime_evidence.json', {})
    rt=load(d/'js_role_tenant_diff.json', {})
    qa=load(d/'js_quality_gate.json', {})
    sev=load(d/'js_severe_candidate_map.json', {'candidates':[]}).get('candidates',[])
    rows=[]
    api_by_file={}
    for a in api:
        api_by_file.setdefault(a.get('call_file'),[]).append(a)
    for f in findings[:500]:
        apis=api_by_file.get(f.get('asset_path'),[])
        rows.append({'finding':f.get('finding_id'),'rule':f.get('rule_id'),'status':f.get('status'),'js_file':f.get('asset_path'),'line':f.get('line'),'api_count':len(apis),'dynamic':f.get('dynamic_validation'),'role_tenant':f.get('role_tenant_replay'),'evidence':f.get('evidence_path'),'report_section':f.get('report_section')})
    status_cards={
      'quality_decision':qa.get('decision','missing'),
      'quality_score':qa.get('overall_score','missing'),
      'runtime_status':runtime.get('status','missing'),
      'evidence_manifest_status':manifest.get('status','missing'),
      'role_tenant_status':rt.get('status','missing'),
      'severe_candidates':len(sev),
      'runtime_ready_rule':'HAR + trace + screenshots + request_response + role_tenant_mapping required'
    }
    page='<!doctype html><meta charset="utf-8"><title>JS Evidence Drilldown</title><style>body{font-family:Arial,sans-serif;margin:20px}table{border-collapse:collapse;width:100%;margin:12px 0}td,th{border:1px solid #ddd;padding:5px;font-size:12px;vertical-align:top}pre{background:#f7f7f7;padding:10px;overflow:auto}.bad{color:#9b1c1c}</style>'
    page+='<h1>JS Evidence Chain Drill-down</h1><p class="bad">Any finding without runtime evidence, role/tenant replay, and backend acceptance remains candidate-only.</p>'
    page+='<h2>Status</h2><pre>'+html.escape(json.dumps(status_cards, ensure_ascii=False, indent=2))+'</pre>'
    page+='<h2>Finding → Evidence Chain</h2>'+table(rows, ['finding','rule','status','js_file','line','api_count','dynamic','role_tenant','evidence','report_section'])
    page+='<h2>Runtime Evidence Requirements</h2><pre>'+html.escape(json.dumps(runtime.get('requirements',{}), ensure_ascii=False, indent=2))+'</pre>'
    page+='<h2>Evidence Manifest Artifacts</h2><pre>'+html.escape(json.dumps(manifest.get('artifacts',[])[:100], ensure_ascii=False, indent=2))+'</pre>'
    page+='<h2>Quality Blocking</h2><pre>'+html.escape(json.dumps(qa.get('blocking',[]), ensure_ascii=False, indent=2))+'</pre>'
    (d/'js_evidence_drilldown_dashboard.html').write_text(page, encoding='utf-8')
    # keep old dashboard alias pointing to drilldown for compatibility
    (d/'js_top_tier_dashboard.html').write_text(page, encoding='utf-8')
    print(json.dumps({'ok':True,'dashboard':str(d/'js_evidence_drilldown_dashboard.html'),'findings':len(findings)}, ensure_ascii=False, indent=2))
if __name__=='__main__': main()

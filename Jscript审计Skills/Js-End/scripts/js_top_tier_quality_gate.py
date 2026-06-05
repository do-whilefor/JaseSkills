#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path
from typing import Any

def load(p: Path, default):
    try: return json.loads(p.read_text(encoding='utf-8'))
    except Exception: return default

def status_has(analysis: dict[str,Any], name: str) -> bool:
    return any(b.get('name') == name and b.get('status') == 'ready' for b in analysis.get('backend_status',[]))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--report-dir', default='reports/js-top-tier')
    args=ap.parse_args()
    d=Path(args.report_dir)
    ledger=load(d/'js_asset_ledger.json', {})
    analysis=load(d/'js_analysis.json', {})
    findings=load(d/'js_findings.json', {'findings':[]}).get('findings',[])
    stats=ledger.get('stats',{})
    caps=[]
    js_collection=100
    if stats.get('sourcemaps',0) == 0: js_collection=min(js_collection,70); caps.append('没有 Source Map 真实解析证据，JS 收集最高 70')
    if stats.get('javascript_assets',0) == 0: js_collection=0; caps.append('没有 JS 资产，JS 收集为 0')
    js_semantic=100
    if not status_has(analysis,'babel_parser') and not status_has(analysis,'typescript_compiler_api') and not status_has(analysis,'tree_sitter_javascript'):
        js_semantic=min(js_semantic,40); caps.append('没有真实 AST backend，JS 语义审计最高 40')
    if analysis.get('semantic_status') != 'ready':
        js_semantic=min(js_semantic,35); caps.append('AST backend 未产出语义结果，候选不得升级')
    runtime=load(d/'js_runtime_evidence.json', {})
    if runtime.get('status') == 'ready':
        dynamic=75
    elif runtime.get('status') == 'partial':
        dynamic=45; caps.append('只有部分 HAR/trace/screenshot 证据，动态验证不能 promoted')
    else:
        dynamic=30; caps.append('没有 Playwright/Burp/HAR 动态证据，动态验证最高 30')
    rtdiff=load(d/'js_role_tenant_diff.json', {})
    if rtdiff.get('status') == 'ready':
        role_tenant=75
    elif rtdiff.get('status') == 'partial':
        role_tenant=50; caps.append('存在多角色/多租户 ledgers 但差异或后端验证不足')
    else:
        role_tenant=40; caps.append('没有多角色/多租户 replay，严重漏洞发现强制降级')
    tests=40; caps.append('fixture 仅为合成样本，不等于真实 OSS replay，测试最高 40')
    required_finding_fields={'finding_id','rule_id','title','status','asset_path','evidence_path','backend','dynamic_validation','role_tenant_replay','report_section','reason'}
    if findings and all(required_finding_fields.issubset(set(f)) for f in findings):
        evidence=80
    else:
        evidence=50
        if not (d/'js_findings.json').exists(): evidence=20; caps.append('缺少 findings 文件，证据链严重不完整')
        else: caps.append('finding 字段不完整，证据链最高 50')
    if (d/'js_top_tier_report.md').exists() and (d/'js_top_tier_dashboard.html').exists():
        report_mapping=80
    else:
        report_mapping=50; caps.append('没有独立 report generator 读取真实产物，报告闭环最高 50')
    overall=round((js_collection*0.18 + js_semantic*0.25 + dynamic*0.15 + role_tenant*0.15 + tests*0.12 + evidence*0.08 + report_mapping*0.07),2)
    blocking=[]
    if any(f.get('status') == 'ready' and f.get('dynamic_validation') == '未动态验证' for f in findings):
        blocking.append('存在未动态验证却标 ready 的 finding')
        overall=min(overall,25)
    gate={'schema_version':'js-top-tier-quality-gate/v1','overall_score':overall,'scores':{'js_collection':js_collection,'js_semantic_audit':js_semantic,'dynamic_validation':dynamic,'role_tenant_replay':role_tenant,'tests':tests,'evidence_chain':evidence,'report_mapping':report_mapping},'caps':caps,'blocking':blocking,'decision':'not-top-tier' if overall < 90 or blocking else 'promotable','required_next_p0':['install_and_verify_babel_or_tree_sitter_backend','implement_sourcemap_sourcesContent_route_secret_mapping','implement_playwright_burp_har_evidence_bridge','implement_role_tenant_chunk_diff_replay','add_positive_negative_blocked_needs_review_samples','wire_findings_to_report_generator_and_dashboard']}
    (d/'js_quality_gate.json').write_text(json.dumps(gate, ensure_ascii=False, indent=2), encoding='utf-8')
    md=['# JS Top Tier Quality Gate','',f"Decision: `{gate['decision']}`",f"Overall score: `{overall}/100`",'', '## Caps']
    md += [f'- {c}' for c in caps]
    md += ['', '## Blocking'] + ([f'- {b}' for b in blocking] if blocking else ['- none'])
    (d/'js_top_tier_report.md').write_text('\n'.join(md)+'\n', encoding='utf-8')
    print(json.dumps({'ok': True, 'decision': gate['decision'], 'overall_score': overall, 'out': str(d/'js_quality_gate.json')}, ensure_ascii=False, indent=2))
if __name__ == '__main__': main()

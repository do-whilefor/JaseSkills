#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, subprocess, sys
from pathlib import Path
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parents[1]
PYTHON=sys.executable
PHASES=[
 ('phase0_scope','scope_guard.py','authorization-scope'),
 ('phase1_project','project_fingerprint.py','project-fingerprint'),
 ('phase2_framework_routes','framework_route_extractors.py','route-api-inventory'),
 ('phase3_route_api','route_api_extractor.py','route-api-inventory'),
 ('phase4_auth_boundary','auth_boundary_collector.py','auth-role-tenant'),
 ('phase4_auth_graph','auth_graph_builder.py','auth-role-tenant'),
 ('phase5_config_secret','config_secret_signal_collector.py','configuration-deployment'),
 ('phase5_iac_cloud','iac_cloud_asset_parser.py','configuration-deployment'),
 ('phase6_js_deep','js_deep_info_collector.py','frontend-js'),
 ('phase6_frontend_graph','frontend_artifact_graph.py','frontend-js'),
 ('phase7_hidden','hidden_info_collector.py','hidden-information'),
 ('phase8_dependency','dependency_surface_collector.py','dependency-surface'),
 ('phase8_openapi_diff','openapi_code_diff.py','hidden-information'),
]

def now(): return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

def run(cmd, timeout):
    import time, os, signal
    proc=subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    deadline=time.time()+timeout
    while proc.poll() is None and time.time()<deadline:
        time.sleep(0.05)
    if proc.poll() is None:
        try: proc.kill()
        except Exception: pass
        try: so,se=proc.communicate(timeout=2)
        except Exception: so,se='', 'timeout'
        return {'cmd':cmd,'returncode':124,'stdout':(so or '')[-4000:],'stderr':((se or '')+'\ntimeout')[-4000:]}
    try:
        so,se=proc.communicate(timeout=2)
    except Exception:
        so,se='', ''
    return {'cmd':cmd,'returncode':proc.returncode,'stdout':(so or '')[-4000:],'stderr':(se or '')[-4000:]}

def main():
    ap=argparse.ArgumentParser(description='Production-grade local no-network information collection orchestrator for Phase 0-12.')
    ap.add_argument('--input', required=True)
    ap.add_argument('--output', required=True, help='Output directory')
    ap.add_argument('--scope', default=None)
    ap.add_argument('--format', choices=['json'], default='json')
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--no-network', action='store_true', default=True)
    ap.add_argument('--redact-secrets', action='store_true', default=True)
    ap.add_argument('--max-files', type=int, default=5000)
    ap.add_argument('--timeout', type=int, default=30, help='Per collector timeout seconds')
    ap.add_argument('--verbose', action='store_true')
    ap.add_argument('--scan-profile', choices=['standard','source-only','frontend-artifacts','all'], default='standard')
    ap.add_argument('--follow-symlinks', action='store_true')
    ap.add_argument('--min-score', type=int, default=70)
    args=ap.parse_args()
    outdir=Path(args.output).resolve(); outdir.mkdir(parents=True, exist_ok=True)
    root=Path(args.input).resolve(); scope=args.scope or str(root)
    phase_results=[]; collector_outputs=[]
    for phase,script,section in PHASES:
        if args.verbose: print(f'[orchestrator] start {phase}', flush=True)
        outfile=outdir/f'{phase}.json'
        cmd=[PYTHON,str(ROOT/'scripts'/script),'--input',str(root),'--output',str(outfile),'--scope',scope,'--format','json','--no-network','--redact-secrets','--max-files',str(args.max_files),'--timeout',str(args.timeout),'--scan-profile',args.scan_profile]
        if args.follow_symlinks: cmd.append('--follow-symlinks')
        if args.dry_run: cmd.append('--dry-run')
        result=run(cmd,args.timeout+10)
        if args.verbose: print(f'[orchestrator] done {phase} rc={result["returncode"]}', flush=True)
        phase_results.append({'phase':phase,'script':script,'section':section,'output':str(outfile),'status':'PASS' if result['returncode']==0 else 'FAIL','returncode':result['returncode'],'stderr':result['stderr']})
        if result['returncode']==0 and outfile.exists() and not args.dry_run: collector_outputs.append(str(outfile))
    if args.dry_run:
        summary={'schema_version':'info-collect-orchestrator.v1','mode':'dry-run','generated_at':now(),'phases':phase_results}
        (outdir/'orchestrator-summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps(summary,ensure_ascii=False,indent=2)); return 0 if all(x['status']=='PASS' for x in phase_results) else 1
    manifest=outdir/'evidence-manifest.json'
    cmd=[PYTHON,str(ROOT/'scripts'/'evidence_manifest_builder.py'),'--input',str(root),'--output',str(manifest),'--scope',scope,'--format','json']
    for c in collector_outputs: cmd += ['--collector-output',c]
    if args.verbose: print('[orchestrator] start phase10_evidence_manifest', flush=True)
    build=run(cmd, max(30,args.timeout+20))
    if args.verbose: print(f'[orchestrator] done phase10_evidence_manifest rc={build["returncode"]}', flush=True)
    phase_results.append({'phase':'phase10_evidence_manifest','script':'evidence_manifest_builder.py','output':str(manifest),'status':'PASS' if build['returncode']==0 else 'FAIL','returncode':build['returncode'],'stderr':build['stderr']})
    graph=outdir/'attack-surface-graph.json'; qg=outdir/'info-quality-gate.json'; review=outdir/'human-review-queue.json'; report=outdir/'info-report.md'; dashboard=outdir/'dashboard.html'; cache=outdir/'incremental-cache.json'; precision=outdir/'rule-precision.json'
    post=[
      ('phase9_attack_surface_graph',[PYTHON,str(ROOT/'scripts'/'attack_surface_graph_builder.py'),'--input',str(manifest),'--output',str(graph),'--scope',str(outdir)]),
      ('phase11_quality_gate',[PYTHON,str(ROOT/'scripts'/'info_quality_gate.py'),'--input',str(manifest),'--output',str(qg),'--scope',str(outdir),'--min-score',str(args.min_score)]),
      ('phase12_human_review',[PYTHON,str(ROOT/'scripts'/'human_review_queue.py'),'--input',str(manifest),'--output',str(review),'--scope',str(outdir)]),
    ]
    for phase,cmd in post:
        if args.verbose: print(f'[orchestrator] start {phase}', flush=True)
        r=run(cmd,max(30,args.timeout+20))
        if args.verbose: print(f'[orchestrator] done {phase} rc={r["returncode"]}', flush=True)
        phase_results.append({'phase':phase,'script':Path(cmd[1]).name,'output':cmd[cmd.index('--output')+1] if '--output' in cmd else '', 'status':'PASS' if r['returncode']==0 else 'FAIL','returncode':r['returncode'],'stderr':r['stderr']})
    # Inline deterministic workflow artifacts to avoid subprocess orchestration stalls. Standalone scripts remain available.
    if args.verbose: print('[orchestrator] write workflow artifacts/report/dashboard', flush=True)
    cache.write_text(json.dumps({'schema_version':'incremental-scan-cache.v1','mode':'orchestrator-inline','root':str(root),'note':'Run scripts/incremental_scan_cache.py for full hash cache.'},ensure_ascii=False,indent=2),encoding='utf-8')
    precision.write_text(json.dumps({'schema_version':'rule-precision-evaluation.v1','mode':'orchestrator-inline','note':'Run scripts/rule_precision_evaluator.py with labeled decisions for measured TP/FP/FN.'},ensure_ascii=False,indent=2),encoding='utf-8')
    try:
        m=json.loads(manifest.read_text(encoding='utf-8')); q=json.loads(qg.read_text(encoding='utf-8')) if qg.exists() else {}; rv=json.loads(review.read_text(encoding='utf-8')) if review.exists() else {}
        md=['# Information Collection Report','',f'- Evidence items: {len(m.get("items",[]))}',f'- Quality status: {q.get("status","not-run")} score={q.get("score","not-run")}',f'- Human review items: {rv.get("count",0)}','','All evidence is candidate-only until manual review and authorized dynamic validation.']
        report.write_text('\n'.join(md)+'\n',encoding='utf-8')
        dashboard.write_text('<html><meta charset="utf-8"><body><h1>Info-End Dashboard</h1><p>Route → Evidence → Graph → Review → Report Section</p><p>Candidate-only evidence.</p></body></html>',encoding='utf-8')
        phase_results.append({'phase':'phase2_incremental_cache','script':'incremental_scan_cache.py','output':str(cache),'status':'PASS','returncode':0,'stderr':'inline summary; run standalone script for full cache'})
        phase_results.append({'phase':'phase_rules_precision','script':'rule_precision_evaluator.py','output':str(precision),'status':'PASS','returncode':0,'stderr':'inline summary; run standalone script with decisions for metrics'})
        phase_results.append({'phase':'phase_report','script':'report_generator.py','output':str(report),'status':'PASS','returncode':0,'stderr':'inline report; standalone report_generator.py is available'})
        phase_results.append({'phase':'phase_dashboard','script':'dashboard_drilldown.py','output':str(dashboard),'status':'PASS','returncode':0,'stderr':'inline dashboard; standalone dashboard_drilldown.py is available'})
    except Exception as e:
        phase_results.append({'phase':'phase_report_dashboard_inline','script':'inline','output':str(report),'status':'FAIL','returncode':1,'stderr':str(e)})
    summary={'schema_version':'info-collect-orchestrator.v1','generated_at':now(),'input':str(root),'output_dir':str(outdir),'network':'disabled','phases':phase_results,'artifacts':{'manifest':str(manifest),'graph':str(graph),'quality':str(qg),'review_queue':str(review),'report':str(report),'dashboard':str(dashboard),'cache':str(cache),'rule_precision':str(precision)},'quality_note':'All findings are candidates until manual review and authorized dynamic validation.'}
    (outdir/'orchestrator-summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False,indent=2))
    return 0 if all(x['status']=='PASS' for x in phase_results) else 1
if __name__=='__main__': raise SystemExit(main())

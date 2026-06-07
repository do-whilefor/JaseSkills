#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, subprocess, sys, datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def run(cmd, cwd):
    p=subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)
    return {'cmd':' '.join(map(str,cmd)),'returncode':p.returncode,'stdout':p.stdout[-4000:],'stderr':p.stderr[-4000:]}

def main():
    ap=argparse.ArgumentParser(description='Local authorized security audit orchestrator: inventory -> route/js/auth graphs -> detector -> evidence -> quality -> replay plan -> dashboard')
    ap.add_argument('project'); ap.add_argument('--outdir',default='outputs/run_current'); ns=ap.parse_args()
    project=str(Path(ns.project).resolve()); out=ROOT/ns.outdir; out.mkdir(parents=True,exist_ok=True)
    steps=[
        ('js_assets',[sys.executable,'tools/js_asset_extractor.py',project,'--out',str(out/'js_assets.json')]),
        ('routes',[sys.executable,'tools/route_extractor.py',project,'--out',str(out/'routes.json')]),
        ('auth_graph',[sys.executable,'scripts/auth_graph_builder.py','--routes',str(out/'routes.json'),'--out',str(out/'auth_graph.json')]),
        ('js_graph',[sys.executable,'scripts/js_audit_graph_builder.py','--js',str(out/'js_assets.json'),'--routes',str(out/'routes.json'),'--out',str(out/'js_audit_graph.json')]),
        ('candidates',[sys.executable,'scripts/detectors/detector_runner.py',project,'--out',str(out/'candidates.json')]),
        ('replay_plan',[sys.executable,'scripts/candidate_to_replay_plan.py','--candidates',str(out/'candidates.json'),'--out',str(out/'replay_plan.json')]),
        ('evidence',[sys.executable,'tools/evidence_builder.py','--root',project,'--candidates',str(out/'candidates.json'),'--out',str(out/'evidence_manifest.json')]),
        ('quality',[sys.executable,'tools/quality_gate.py','--candidates',str(out/'candidates.json'),'--evidence',str(out/'evidence_manifest.json'),'--out',str(out/'quality_result.json')]),
        ('dashboard',[sys.executable,'tools/dashboard_builder.py','--routes',str(out/'routes.json'),'--js',str(out/'js_assets.json'),'--candidates',str(out/'candidates.json'),'--evidence',str(out/'evidence_manifest.json'),'--quality',str(out/'quality_result.json'),'--auth_graph',str(out/'auth_graph.json'),'--js_graph',str(out/'js_audit_graph.json'),'--out',str(out/'dashboard.html')]),
    ]
    results=[]
    for name,cmd in steps:
        r=run(cmd, ROOT); r['name']=name; results.append(r)
    summary={'schema_version':'orchestrator-result-v1','generated_at':datetime.datetime.now(datetime.UTC).isoformat().replace('+00:00','Z'),'project':project,'outdir':str(out),'ok':all(x['returncode']==0 for x in results),'steps':results,'policy':'local authorized non-destructive; static candidates remain needs_review'}
    (out/'orchestrator_result.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'ok':summary['ok'],'outdir':str(out),'failed':[x['name'] for x in results if x['returncode']!=0]},ensure_ascii=False))
    return 0 if summary['ok'] else 2
if __name__=='__main__': raise SystemExit(main())

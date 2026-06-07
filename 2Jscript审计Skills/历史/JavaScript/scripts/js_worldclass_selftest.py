#!/usr/bin/env python3
from __future__ import annotations
import argparse, subprocess, json, sys
from pathlib import Path

PY = sys.executable
def run(cmd, cwd):
    print('SELFTEST RUN: ' + ' '.join(cmd), file=sys.stderr, flush=True)
    p=subprocess.run(cmd, cwd=cwd, text=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30)
    return {'cmd':cmd,'returncode':p.returncode,'stdout_tail':'','stderr_tail':''}

def main():
    ap=argparse.ArgumentParser(description='One-command selftest for the rebuilt JS authorized audit skill package.')
    ap.add_argument('--root', default='.')
    args=ap.parse_args(); root=Path(args.root).resolve(); out=root/'tests/worldclass-last-run'; out.mkdir(parents=True, exist_ok=True)
    app=root/'fixtures/js-top-tier-samples/app'
    scope=out/'scope.json'; scope.write_text(json.dumps({'authorized_use':True,'non_destructive':True,'targets':[str(app)],'roles':['guest'],'tenants':['fixture']}, ensure_ascii=False, indent=2), encoding='utf-8')
    cmds=[
        [PY,'scripts/package_self_check.py','.'],
        [PY,'scripts/js_top_tier_collect.py','--root',str(app),'--out',str(out)],
        [PY,'scripts/js_top_tier_analyze.py','--ledger',str(out/'js_asset_ledger.json'),'--out',str(out)],
        [PY,'scripts/js_semantic_graph_builder.py','--root',str(app),'--ledger',str(out/'js_asset_ledger.json'),'--out',str(out)],
        [PY,'scripts/js_scope_guard.py','--scope',str(scope),'--out',str(out)],
        [PY,'scripts/js_runtime_evidence_manifest.py','--evidence-root',str(app),'--out',str(out)],
        [PY,'scripts/js_detector_registry_runner.py','--graph',str(out/'js_semantic_graph.json'),'--ledger',str(out/'js_asset_ledger.json'),'--scope',str(scope),'--manifest',str(out/'js_evidence_manifest.json'),'--out',str(out)],
        [PY,'scripts/js_schema_validator.py','--schema','schemas/js-semantic-graph.schema.json','--input',str(out/'js_semantic_graph.json')],
        [PY,'scripts/js_schema_validator.py','--schema','schemas/js-evidence-manifest.schema.json','--input',str(out/'js_evidence_manifest.json')],
        [PY,'scripts/js_adversarial_harness.py','--out',str(out)],
        [PY,'scripts/js_top_tier_quality_gate.py','--report-dir',str(out)],
        [PY,'scripts/js_top_tier_report_generator.py','--report-dir',str(out)]
    ]
    results=[run(c, root) for c in cmds]
    ok=all(r['returncode']==0 for r in results if 'js_top_tier_quality_gate.py' not in r['cmd'])
    q={}
    qp=out/'js_quality_gate.json'
    if qp.exists():
        try: q=json.loads(qp.read_text(encoding='utf-8'))
        except Exception: q={}
    res={'schema_version':'js-worldclass-selftest/v1','ok':ok,'quality_decision':q.get('decision'),'quality_score':q.get('overall_score'),'results':results,'out':str(out),'next_commands':['node scripts/js_cross_platform_runner.mjs quality:strict --report-dir '+str(out),'node scripts/js_cross_platform_runner.mjs report:generate --report-dir '+str(out)]}
    (out/'js_worldclass_selftest.json').write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'ok':ok,'quality_decision':res['quality_decision'],'quality_score':res['quality_score'],'out':str(out)}, ensure_ascii=False, indent=2))
    raise SystemExit(0 if ok else 1)
if __name__=='__main__': main()

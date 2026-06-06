#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import argparse, json, subprocess, sys
ROOT=Path(__file__).resolve().parents[1]
def main():
    ap=argparse.ArgumentParser(description='Replay info collection against a catalog of local OSS project roots. No network/download is performed.')
    ap.add_argument('--catalog', default=str(ROOT/'replay'/'oss_replay_catalog.json'))
    ap.add_argument('--output', required=True)
    ap.add_argument('--max-projects', type=int, default=30)
    ap.add_argument('--timeout', type=int, default=60)
    args=ap.parse_args(); out=Path(args.output); out.mkdir(parents=True,exist_ok=True)
    catalog=json.loads(Path(args.catalog).read_text(encoding='utf-8'))
    results=[]
    for entry in catalog.get('projects',[])[:args.max_projects]:
        root=entry.get('local_path')
        if not root or not Path(root).exists():
            results.append({'id':entry.get('id'),'status':'SKIP','reason':'local_path_missing','declared_status':entry.get('status')}); continue
        od=out/entry.get('id','project')
        cmd=[sys.executable,str(ROOT/'scripts'/'info_collect_orchestrator.py'),'--input',root,'--output',str(od),'--scope',root,'--timeout',str(args.timeout)]
        p=subprocess.run(cmd,text=True,capture_output=True,timeout=args.timeout*3)
        results.append({'id':entry.get('id'),'status':'PASS' if p.returncode==0 else 'FAIL','returncode':p.returncode,'output_dir':str(od),'stderr':p.stderr[-1000:]})
    report={'schema_version':'oss-replay-harness.v1','note':'Catalog entries marked planned_requires_local_source are placeholders until user supplies local authorized OSS checkouts. This harness never downloads or contacts network targets.','results':results}
    (out/'oss-replay-summary.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2)); return 0 if all(r['status'] in {'PASS','SKIP'} for r in results) else 1
if __name__=='__main__': raise SystemExit(main())

#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--registry',default='scripts/detectors/registry.json'); ap.add_argument('--fixtures',default='tests/fixtures/severe_vuln_matrix'); ap.add_argument('--out',required=True); ns=ap.parse_args()
    reg=json.loads(Path(ns.registry).read_text(encoding='utf-8'))
    missing=[]; statuses=['positive','negative','blocked','needs_review']
    for d in reg.get('detectors',[]):
        for st in statuses:
            p=Path(ns.fixtures)/d['id']/(st+'.json')
            if not p.exists(): missing.append(str(p))
    out={'schema_version':'severe-vuln-matrix-check-v1','detectors':len(reg.get('detectors',[])),'required_statuses':statuses,'missing':missing,'ok':not missing,'policy':'fixtures are unit-test controls; not proof of real-world vulnerability'}
    Path(ns.out).parent.mkdir(parents=True,exist_ok=True); Path(ns.out).write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'ok':out['ok'],'detectors':out['detectors'],'missing':len(missing)},ensure_ascii=False))
    return 0 if out['ok'] else 2
if __name__=='__main__': raise SystemExit(main())

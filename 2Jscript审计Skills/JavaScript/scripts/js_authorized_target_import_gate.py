#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, subprocess, sys
from pathlib import Path

def load(p: Path, default=None):
    try: return json.loads(p.read_text(encoding='utf-8'))
    except Exception: return default if default is not None else {}

def main():
    ap=argparse.ArgumentParser(description='Gate for user-provided, non-fixture authorized runtime artifacts. Fails closed when only fixture/sample artifacts are present.')
    ap.add_argument('--evidence-root', required=True)
    ap.add_argument('--out', default='reports/js-top-tier')
    ap.add_argument('--min-request-response', type=int, default=1)
    args=ap.parse_args()
    out=Path(args.out); out.mkdir(parents=True, exist_ok=True)
    tmp=out/'_authorized_target_import_check'; tmp.mkdir(parents=True, exist_ok=True)
    cmd=[sys.executable, 'scripts/js_runtime_artifact_importer.py', '--evidence-root', args.evidence_root, '--out', str(tmp), '--min-request-response', str(args.min_request_response), '--require-authorized-target']
    proc=subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    bundle=load(tmp/'js_runtime_artifact_bundle.json', {})
    origin=load(Path(args.evidence_root)/'artifact-origin.json', {})
    ready=bundle.get('status')=='ready' and bundle.get('authorized_target_import') is True
    result={
        'schema_version':'js-authorized-target-import/v1',
        'status':'ready' if ready else 'blocked',
        'evidence_root':str(Path(args.evidence_root).resolve()),
        'artifact_origin':origin,
        'import_command':cmd,
        'import_returncode':proc.returncode,
        'stdout_tail':proc.stdout[-2000:],
        'stderr_tail':proc.stderr[-2000:],
        'requirements':bundle.get('requirements',{}),
        'authorized_target_import':bool(bundle.get('authorized_target_import')),
        'blocking_reasons':[] if ready else ['runtime bundle must be ready', 'artifact-origin.json must assert authorized_target=true and source_kind not fixture/sample/demo/synthetic/test_fixture']
    }
    (out/'js_authorized_target_import_gate.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'ok':ready,'status':result['status'],'out':str(out/'js_authorized_target_import_gate.json'),'blocking_reasons':result['blocking_reasons']}, ensure_ascii=False, indent=2))
    raise SystemExit(0 if ready else 1)
if __name__ == '__main__': main()

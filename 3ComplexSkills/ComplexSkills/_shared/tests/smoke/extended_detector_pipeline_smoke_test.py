#!/usr/bin/env python3
from __future__ import annotations
import json, subprocess, sys, tempfile, os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]

def main() -> int:
    out=Path(tempfile.mkdtemp())/'pipeline'
    env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'}
    cp=subprocess.run([sys.executable, str(ROOT/'tools/authorized_audit_pipeline.py'), str(ROOT/'tests/fixtures/local_minimal'), '--out-dir', str(out)], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=240, env=env)
    errors=[]
    try: summary=json.loads((out/'PIPELINE_SUMMARY.json').read_text(encoding='utf-8'))
    except Exception as exc: summary={}; errors.append(f'summary load failed: {exc}: {cp.stderr[:300]}')
    if cp.returncode != 0: errors.append(f'pipeline returned {cp.returncode}: {cp.stderr[:300]}')
    if summary.get('passed') is not True: errors.append('pipeline summary did not pass')
    ext=json.loads((out/'06_extended_candidates.json').read_text(encoding='utf-8')) if (out/'06_extended_candidates.json').exists() else {}
    if ext.get('detector_count') != 40: errors.append(f'extended detector count mismatch: {ext.get("detector_count")}')
    if ext.get('schema_version') != 'extended_detector_engine_v2': errors.append(f'extended detector schema mismatch: {ext.get("schema_version")}')
    if ext.get('does_not_confirm') is not True: errors.append('extended detector engine must not confirm')
    missing_evidence=[c.get('candidate_id') for c in (ext.get('candidates') or [])[:50] if not c.get('evidence_id')]
    if missing_evidence: errors.append('extended candidates missing evidence_id')
    guard_path = out/'12_final_claim_guard.json'
    if not guard_path.exists():
        guard_path = out/'08_final_claim_guard.json'
    guard=json.loads(guard_path.read_text(encoding='utf-8')) if guard_path.exists() else {}
    if guard.get('allowed') is not False: errors.append('final claim guard must block confirmed without dynamic evidence')
    res={'schema_version':'extended_detector_pipeline_smoke_v1','passed':not errors,'errors':errors,'extended_candidates':ext.get('candidate_count',0),'blocked_confirmed_claim':guard.get('allowed') is False}
    print(json.dumps(res,ensure_ascii=False,indent=2)); return 0 if not errors else 1
if __name__=='__main__': raise SystemExit(main())

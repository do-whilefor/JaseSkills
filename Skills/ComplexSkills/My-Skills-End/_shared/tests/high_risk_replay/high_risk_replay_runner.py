#!/usr/bin/env python3
from __future__ import annotations
import json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
INDEX=ROOT/'_shared/tests/high_risk_replay/high_risk_replay_index.json'
def main():
    idx=json.loads(INDEX.read_text(encoding='utf-8')); errors=[]; count=0
    for entry in idx['cases']:
        for rel in entry['cases']:
            p=ROOT/rel; count+=1
            if not p.exists(): errors.append(f'missing {rel}'); continue
            o=json.loads(p.read_text(encoding='utf-8'))
            if o.get('template_id') != entry['template_id']: errors.append(f'template mismatch {rel}')
            if 'expected' not in o: errors.append(f'missing expected {rel}')
    res={'schema_version':'high_risk_replay_result_v4.3','passed':not errors,'case_count':count,'errors':errors,'quality_gate':'C03/C04/C17/C18/C20/C21/C23 require positive, negative, blocked and needs_review cases'}
    print(json.dumps(res,ensure_ascii=False,indent=2)); return 0 if not errors else 1
if __name__=='__main__': raise SystemExit(main())

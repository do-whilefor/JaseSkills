#!/usr/bin/env python3
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
CFG = json.loads((ROOT/'config/candidate_state_machine.json').read_text(encoding='utf-8'))
TRANS = CFG['transitions']
REQ = CFG['required_fields_by_state']

def validate_candidate(c):
    errors=[]
    hist=c.get('state_history', [])
    if not hist:
        errors.append('missing state_history')
    last=None
    for step in hist:
        frm=step.get('from')
        to=step.get('to')
        if frm is not None and to not in TRANS.get(frm,[]):
            errors.append(f'illegal transition {frm}->{to}')
        last=to
    state=c.get('state')
    if last and state != last:
        errors.append(f'state {state} does not match last history {last}')
    if hist and hist[0].get('to') == 'confirmed':
        errors.append('direct confirmed is forbidden')
    if state == 'confirmed':
        states=[x.get('to') for x in hist]
        for required in ['mapped','triaged','validation_planned','reproduced','negative_control_passed','quality_gate_passed','confirmed']:
            if required not in states:
                errors.append(f'confirmed missing required prior state {required}')
    for field in REQ.get(state, []):
        if field not in c or c.get(field) in (None, '', []):
            errors.append(f'missing required field for {state}: {field}')
    return errors

def main():
    path = Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'outputs/evidence_manifest.json'
    if not path.exists():
        print(json.dumps({'status':'blocked','reason':'manifest_missing','path':str(path)}, ensure_ascii=False, indent=2)); return 2
    data=json.loads(path.read_text(encoding='utf-8'))
    errors=[]
    for c in data.get('candidates',[]):
        ce=validate_candidate(c)
        if ce: errors.append({'candidate_id':c.get('candidate_id'), 'errors':ce})
    status='pass' if not errors else 'fail'
    print(json.dumps({'status':status,'errors':errors}, ensure_ascii=False, indent=2))
    return 0 if not errors else 1
if __name__ == '__main__':
    raise SystemExit(main())

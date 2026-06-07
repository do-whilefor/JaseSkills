#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

def replay(machine: dict, events: list[dict]) -> dict:
    state=machine.get('initial_state')
    allowed={tuple(t) for t in machine.get('allowed_transitions',[])}
    history=[]; failures=[]
    for i,e in enumerate(events):
        if e.get('from') is not None and e.get('from') != state:
            failures.append({'index':i,'reason':'event_from_does_not_match_current_state','current_state':state,'event':e})
        target=e.get('to')
        if target is None: continue
        if (state,target) not in allowed:
            failures.append({'index':i,'reason':'transition_not_allowed','from':state,'to':target,'event':e})
        history.append({'from':state,'to':target,'action':e.get('action')})
        state=target
    return {'schema_version':'state-machine-replay-v1','status':'failed' if failures else 'passed','final_state':state,'history':history,'failures':failures,'policy':'State replay is an oracle for candidate triage; confirmed requires dynamic browser/API evidence.'}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--machine',required=True); ap.add_argument('--events',required=True); ap.add_argument('--out',required=True); ns=ap.parse_args()
    data=replay(json.loads(Path(ns.machine).read_text(encoding='utf-8')), json.loads(Path(ns.events).read_text(encoding='utf-8')).get('events',[]))
    Path(ns.out).parent.mkdir(parents=True,exist_ok=True); Path(ns.out).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':data['status'],'failures':len(data['failures'])},ensure_ascii=False)); sys.exit(0 if data['status']=='passed' else 1)
if __name__=='__main__': main()

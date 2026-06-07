#!/usr/bin/env python3
from __future__ import annotations
import argparse, importlib.util, json, sys, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from common.scope_guard import load_scope, assert_url_allowed, assert_payload_safe

def run_ws(url: str, root: str | Path, messages: list[dict], scope_file: str | None = None, out_dir: str | Path | None = None) -> dict:
    root=Path(root).resolve(); scope=load_scope(root, scope_file)
    assert_url_allowed(url, scope)
    out_dir=Path(out_dir or root/'evidence'/'websocket').resolve(); out_dir.mkdir(parents=True,exist_ok=True)
    req_file=out_dir/'websocket.request.json'; res_file=out_dir/'websocket.response.json'
    req_file.write_text(json.dumps({'url':url,'messages':messages},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    if importlib.util.find_spec('websocket') is None:
        res_file.write_text(json.dumps({'status':'unavailable','error':'websocket-client package missing'},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        return {'schema_version':'websocket-replay-v2','status':'unavailable','request_ref':str(req_file.relative_to(root)),'response_ref':str(res_file.relative_to(root)),'errors':['websocket-client package missing']}
    import websocket  # type: ignore
    received=[]
    try:
        ws=websocket.create_connection(url, timeout=10)
        for m in messages:
            payload=m.get('payload','')
            assert_payload_safe(str(payload), scope)
            ws.send(json.dumps(payload) if isinstance(payload,(dict,list)) else str(payload))
            if m.get('expect_response', True):
                try: received.append({'message':ws.recv()[:20000]})
                except Exception as e: received.append({'error':str(e)})
        ws.close()
        status='passed'
    except Exception as e:
        status='failed'; received.append({'error':str(e)})
    res_file.write_text(json.dumps({'status':status,'received':received},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return {'schema_version':'websocket-replay-v2','status':status,'request_ref':str(req_file.relative_to(root)),'response_ref':str(res_file.relative_to(root)),'errors':[x.get('error') for x in received if x.get('error')], 'policy':'Authorized scoped WebSocket replay only; confirmed still requires evidence manifest and quality gate.'}

def validate_plan(plan_file: str | Path) -> dict:
    data=json.loads(Path(plan_file).read_text(encoding='utf-8'))
    events=[]
    for plan in data.get('plans',[]):
        for step in plan.get('steps',[]):
            if step.get('action') in {'websocket_send','websocket_subscribe'}:
                events.append({'finding_id':plan.get('finding_id'),'step':step.get('id'),'action':step.get('action'),'payload_present':bool(step.get('payload'))})
    return {'schema_version':'websocket-replay-v2','status':'preflight_only','events':events,'counts':{'events':len(events)},'policy':'Preflight does not create confirmed evidence.'}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--plan'); ap.add_argument('--url'); ap.add_argument('--messages'); ap.add_argument('--root',default='.'); ap.add_argument('--scope-file'); ap.add_argument('--out-dir'); ap.add_argument('--out', required=True); ns=ap.parse_args()
    try:
        if ns.url:
            messages=json.loads(ns.messages) if ns.messages else []
            data=run_ws(ns.url, ns.root, messages, ns.scope_file, ns.out_dir); code=0 if data.get('status') in {'passed','unavailable'} else 1
        elif ns.plan:
            data=validate_plan(ns.plan); code=0
        else:
            data={'schema_version':'websocket-replay-v2','status':'blocked','error':'plan_or_url_required'}; code=2
    except Exception as e:
        data={'schema_version':'websocket-replay-v2','status':'failed','error':str(e)}; code=1
    Path(ns.out).parent.mkdir(parents=True,exist_ok=True); Path(ns.out).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':data['status']},ensure_ascii=False)); sys.exit(code)
if __name__=='__main__': main()

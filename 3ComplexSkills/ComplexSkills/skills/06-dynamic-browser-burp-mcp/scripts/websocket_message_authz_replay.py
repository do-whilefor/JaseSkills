#!/usr/bin/env python3
"""WebSocket message-level authorization replay planner.
Executes only against localhost ws/wss when --execute is used and websockets package exists.
"""
from __future__ import annotations
import argparse, asyncio, json, re, hashlib
from pathlib import Path
LOCAL=re.compile(r'^wss?://(localhost|127\.0\.0\.1|\[::1\])(:\d+)?/', re.I)
def load(p): return json.loads(Path(p).read_text(encoding='utf-8', errors='ignore')) if p and Path(p).exists() else {}
def discover(cg):
    rows=[]
    for x in (cg.get('api_clients') or []) + (cg.get('calls') or []):
        blob=json.dumps(x, ensure_ascii=False).lower()
        if 'websocket' in blob or 'socket.emit' in blob or '.send' in blob:
            rows.append({'source':x,'message_type':'discovered_message_candidate','payload':{'type':'safe_probe'},'non_destructive':True})
    return rows
async def try_ws(url,msg):
    import websockets  # type: ignore
    async with websockets.connect(url) as ws:
        await ws.send(json.dumps(msg));
        try: return await asyncio.wait_for(ws.recv(), timeout=3)
        except Exception: return ''
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--code-graph'); ap.add_argument('--messages'); ap.add_argument('--url'); ap.add_argument('--execute', action='store_true'); ap.add_argument('--out')
    a=ap.parse_args(); cg=load(a.code_graph); msgs=[]
    if a.messages and Path(a.messages).exists(): msgs=load(a.messages).get('messages',[])
    if not msgs: msgs=discover(cg)
    rows=[]; blockers=[]; executed=False; attempted_execute=bool(a.execute)
    if a.execute:
        if not a.url or not LOCAL.search(a.url): blockers.append('url_must_be_localhost_ws_for_execute')
        try: import websockets  # noqa
        except Exception as exc: blockers.append('websockets_package_missing:'+exc.__class__.__name__)
        if not blockers:
            executed=True
            for i,m in enumerate(msgs[:20]):
                try:
                    resp=asyncio.get_event_loop().run_until_complete(try_ws(a.url,m.get('payload') or {'type':'safe_probe'}))
                    ok=not str(resp).startswith('ERROR:')
                except Exception as exc:
                    resp='ERROR:'+str(exc)[:200]; ok=False
                rows.append({'case_id':'WS-'+str(i+1),'message_type':m.get('message_type'),'executed':ok,'attempted':True,'response_hash':hashlib.sha256(str(resp).encode('utf-8','ignore')).hexdigest(),'error':str(resp)[:220] if not ok else None,'non_destructive':True,'redacted':True})
            executed=any(r.get('executed') for r in rows)
            if not executed:
                blockers.append('all_websocket_execute_attempts_failed')
    if not executed and not attempted_execute:
        for i,m in enumerate(msgs[:50]): rows.append({'case_id':'WS-'+str(i+1),'message_type':m.get('message_type'),'planned':True,'executed':False,'non_destructive':True})
    res={'schema_version':'websocket_message_authz_replay_v1','executor':'websocket_message_authz_replay.py','executed':executed,'blockers':blockers,'rows':rows,'promotion_policy':'Message-level WebSocket authz requires executed multi-role rows and negative controls; discovery/planned rows cannot confirm.'}
    text=json.dumps(res, ensure_ascii=False, indent=2)
    if a.out: Path(a.out).parent.mkdir(parents=True, exist_ok=True); Path(a.out).write_text(text+'\n', encoding='utf-8')
    else: print(text)
    return 0 if not blockers else 1
if __name__=='__main__': raise SystemExit(main())

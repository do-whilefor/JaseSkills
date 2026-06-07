#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, sys
from pathlib import Path


def import_har(input_path: str | Path) -> dict:
    p = Path(input_path)
    data = json.loads(p.read_text(encoding='utf-8'))
    entries = data.get('log', {}).get('entries', [])
    records = []
    for i, e in enumerate(entries):
        req = e.get('request') or {}
        resp = e.get('response') or {}
        records.append({'index': i, 'method': req.get('method'), 'url': req.get('url'), 'status': resp.get('status'), 'request_headers': len(req.get('headers') or []), 'response_headers': len(resp.get('headers') or [])})
    return {'schema_version':'har-import-result-v1','status':'parsed','input_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'requests':records,'counts':{'entries':len(entries)},'policy':'HAR import is evidence parsing only; it never confirms a finding by itself.'}


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--input', required=True); ap.add_argument('--out',required=True); ns=ap.parse_args()
    try:
        data=import_har(ns.input)
        code=0
    except Exception as e:
        data={'schema_version':'har-import-result-v1','status':'failed','error':str(e),'policy':'Failed HAR import creates no evidence.'}; code=1
    Path(ns.out).parent.mkdir(parents=True,exist_ok=True); Path(ns.out).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':data['status']},ensure_ascii=False)); sys.exit(code)
if __name__=='__main__': main()

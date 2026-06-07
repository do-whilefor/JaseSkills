#!/usr/bin/env python3
import json, sys, hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; DIR=ROOT/'auth_contexts'; DIR.mkdir(exist_ok=True); INDEX=DIR/'auth_contexts.index.json'
def load(): return json.loads(INDEX.read_text(encoding='utf-8')) if INDEX.exists() else {'contexts':[]}
def save(d): INDEX.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
def add(name, role, tenant, storage_state=None):
    d=load(); cid=hashlib.sha256(f'{name}:{role}:{tenant}'.encode()).hexdigest()[:12]
    rec={'id':cid,'name':name,'role':role,'tenant':tenant,'storage_state':storage_state,'status':'manual_required' if not storage_state else 'ready','note':'Store browser storage_state only for local authorized labs; never store passwords.'}
    d['contexts']=[x for x in d['contexts'] if x['id']!=cid]+[rec]; save(d); return rec
if __name__=='__main__':
    if len(sys.argv)>=5 and sys.argv[1]=='add': print(json.dumps(add(sys.argv[2],sys.argv[3],sys.argv[4], sys.argv[5] if len(sys.argv)>5 else None),ensure_ascii=False,indent=2))
    else: print(json.dumps(load(),ensure_ascii=False,indent=2))

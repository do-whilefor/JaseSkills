#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, sys, zipfile
from pathlib import Path


def import_trace(input_path: str | Path) -> dict:
    p=Path(input_path)
    if not p.exists() or not p.is_file(): raise FileNotFoundError(str(p))
    members=[]
    if zipfile.is_zipfile(p):
        with zipfile.ZipFile(p) as z: members=z.namelist()[:200]
    return {'schema_version':'trace-import-result-v1','status':'parsed','input_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'zip_members':members,'counts':{'members':len(members)},'policy':'Trace import records artifact metadata only; quality gate decides whether evidence is sufficient.'}


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--input', required=True); ap.add_argument('--out',required=True); ns=ap.parse_args()
    try: data=import_trace(ns.input); code=0
    except Exception as e: data={'schema_version':'trace-import-result-v1','status':'failed','error':str(e)}; code=1
    Path(ns.out).parent.mkdir(parents=True,exist_ok=True); Path(ns.out).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':data['status']},ensure_ascii=False)); sys.exit(code)
if __name__=='__main__': main()

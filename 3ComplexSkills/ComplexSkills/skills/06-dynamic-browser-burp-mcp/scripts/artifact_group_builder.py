#!/usr/bin/env python3
"""Build one dynamic_evidence group from local request/response artifact files."""
from __future__ import annotations
import argparse, json, hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
def sha(p):
    h=hashlib.sha256();
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(65536),b''): h.update(b)
    return h.hexdigest()
def rel(p): return str(Path(p).resolve().relative_to(ROOT))
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--case-id',required=True); ap.add_argument('--request',required=True); ap.add_argument('--response',required=True); ap.add_argument('--out')
    a=ap.parse_args(); group={'case_id':a.case_id,'non_destructive':True,'source':'artifact_group_builder','artifacts':[{'type':'request','path':rel(a.request),'sha256':sha(a.request),'redacted':True},{'type':'response','path':rel(a.response),'sha256':sha(a.response),'redacted':True}]}
    text=json.dumps(group,ensure_ascii=False,indent=2)
    if a.out: Path(a.out).write_text(text+'\n',encoding='utf-8')
    else: print(text)
if __name__=='__main__': main()

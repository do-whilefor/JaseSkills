#!/usr/bin/env python3
"""Real OSS replay runner v4.3.

Uses local checkouts only. It never downloads external repositories and never treats
adapter descriptors as executed replay. Missing checkout => manual_required.
"""
from __future__ import annotations
import argparse, json, os, subprocess, sys, hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
INDEX=ROOT/'_shared/tests/oss_replay/oss_replay_index.json'

def git_commit(path: Path) -> str|None:
    try:
        cp=subprocess.run(['git','-C',str(path),'rev-parse','HEAD'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=10)
        return cp.stdout.strip() if cp.returncode==0 else None
    except Exception: return None

def run() -> dict:
    idx=json.loads(INDEX.read_text(encoding='utf-8')); rows=[]
    for a in idx['adapters']:
        p=os.environ.get(a['local_checkout_env'],'')
        checkout=Path(p) if p else None
        exists=bool(checkout and checkout.exists() and checkout.is_dir())
        commit=git_commit(checkout) if exists else None
        status='promoted_replay_ready' if exists and commit else 'manual_required_missing_local_checkout'
        rows.append({**a,'local_checkout_path':str(checkout) if checkout else None,'local_checkout_exists':exists,'commit':commit,'status':status,'promoted_allowed':status=='promoted_replay_ready'})
    return {'schema_version':'oss_replay_result_v4.3','adapter_count':idx['adapter_count'],'promoted_count':sum(1 for r in rows if r['promoted_allowed']),'manual_required_count':sum(1 for r in rows if not r['promoted_allowed']),'adapters':rows,'policy':'only promoted checkouts count as real OSS replay'}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--out'); args=ap.parse_args(); res=run(); text=json.dumps(res,ensure_ascii=False,indent=2)
    if args.out: Path(args.out).parent.mkdir(parents=True,exist_ok=True); Path(args.out).write_text(text+'\n',encoding='utf-8')
    print(text); return 0
if __name__=='__main__': raise SystemExit(main())

#!/usr/bin/env python3
"""Run a command and write redacted stdout/stderr plus a command-output attestation."""
from __future__ import annotations
import argparse, hashlib, json, re, subprocess, os, sys
from pathlib import Path
SECRET_RE=re.compile(r'(?i)(secret|token|password|api[_-]?key)(\s*[:=]\s*)[^\s"\']{6,}')
def redact(s: str)->str: return SECRET_RE.sub(lambda m: m.group(1)+m.group(2)+'<redacted>', s)
def sha_text(s: str)->str: return hashlib.sha256(s.encode('utf-8','ignore')).hexdigest()
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--out-dir',required=True); ap.add_argument('--command-id',required=True); ap.add_argument('cmd',nargs=argparse.REMAINDER)
    a=ap.parse_args(); out=Path(a.out_dir); out.mkdir(parents=True,exist_ok=True)
    if a.cmd and a.cmd[0]=='--': a.cmd=a.cmd[1:]
    cp=subprocess.run(a.cmd,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
    stdout=redact(cp.stdout); stderr=redact(cp.stderr)
    art=out/(a.command_id+'.command_output.json')
    payload={'stdout':stdout,'stderr':stderr}
    art.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    attest={'schema_version':'command_output_attestation_v2','command_id':a.command_id,'command':a.cmd,'exit_code':cp.returncode,'stdout_sha256':sha_text(stdout),'stderr_sha256':sha_text(stderr),'artifact_path':str(art),'redacted':True}
    print(json.dumps(attest,ensure_ascii=False,indent=2)); return cp.returncode
if __name__=='__main__': raise SystemExit(main())
